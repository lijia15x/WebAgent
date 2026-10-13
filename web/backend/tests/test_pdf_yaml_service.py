import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pymupdf
import yaml
from fastapi.testclient import TestClient

from pdf_to_yaml_agent.converter import (
    apply_repair_patch,
    build_generation_prompt,
    ensure_scope_preserved,
    generate_architecture_yaml,
    select_reference_files,
    strip_yaml_fence,
    validate_architecture_yaml,
)
from pdf_to_yaml_agent.pdf_filter import extract_architecture_pages
from pdf_to_yaml_agent.ollama_pipeline import (
    _reference_context,
    build_fragment_structure_prompt,
    build_topology_completion_prompt,
    build_vision_prompt,
    compile_architecture,
    compile_inventory_connections,
    collapse_nonphysical_elements,
    invalid_fragment_connections,
    isolated_physical_element_ids,
    materialize_connector_endpoints,
    merge_structures,
    normalize_structure,
    render_analysis_images,
)
from pdf_to_yaml_agent import reference_store
from web.backend.app import app


VALID_YAML = """version: 1
boards:
  - id: board_a
    label: "Board A"
elements:
  - id: controller_a
    board: board_a
    type: controller
    ports:
      - id: bus
connections: []
"""


def write_architecture_pdf(path: Path) -> None:
    document = pymupdf.open()
    try:
        base_page = document.new_page()
        base_page.insert_text(
            (72, 72), "Figure 3-1. Acme SMBus Architecture"
        )
        modular_page = document.new_page()
        modular_page.insert_text(
            (72, 72), "Figure 3-2. Acme Modular SMBus Architecture"
        )
        unrelated_page = document.new_page()
        unrelated_page.insert_text(
            (72, 72), "Figure 4-1. Other Board SMBus Architecture"
        )
        document.save(path)
    finally:
        document.close()


class PdfYamlServiceTests(unittest.TestCase):
    def test_reference_selection_prefers_markdown_over_same_name_pdf(self) -> None:
        selected = select_reference_files(
            [Path("guide.pdf"), Path("example.yml"), Path("guide.md")]
        )

        self.assertEqual([Path("example.yml"), Path("guide.md")], selected)

    def test_prompt_enforces_guide_shape_and_no_invention(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            filtered = Path(directory) / "filtered.pdf"
            write_architecture_pdf(source)
            selection = extract_architecture_pages(source, filtered)
        prompt = build_generation_prompt(
            "filtered.pdf", ["guide.md", "example.yml"], selection
        )

        self.assertIn("selected Acme SMBus architecture", prompt)
        self.assertIn("Figure 3-2. Acme Modular SMBus Architecture", prompt)
        self.assertIn("Figure 3-1. Acme SMBus Architecture", prompt)
        self.assertNotIn("Johnson City", prompt)
        self.assertNotIn("Figure 12-7", prompt)
        self.assertIn("not authoritative for content scope", prompt)
        self.assertIn("Do not copy its limited topology", prompt)
        self.assertIn("Do not broaden the result beyond the authoritative target", prompt)
        self.assertIn("Do not invent", prompt)
        self.assertIn("Mandatory command-line agent workflow", prompt)
        self.assertIn("source_inventory.json", prompt)
        self.assertIn("high-resolution full image plus overlapping 3x-5x crops", prompt)
        self.assertIn("physical distribution layers that were collapsed or bypassed", prompt)
        self.assertIn("filtered.pdf", prompt)
        self.assertIn("guide.md", prompt)
        self.assertIn("example.yml", prompt)

    def test_extracts_modular_and_same_product_base_pages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            filtered = Path(directory) / "filtered.pdf"
            write_architecture_pdf(source)

            selection = extract_architecture_pages(source, filtered)
            with pymupdf.open(filtered) as document:
                page_count = document.page_count

        self.assertEqual("Acme", selection.product_name)
        self.assertTrue(selection.target.modular)
        self.assertEqual([1, 2], [figure.page_number for figure in selection.figures])
        self.assertEqual(2, page_count)

    def test_strips_yaml_markdown_fence(self) -> None:
        self.assertEqual(VALID_YAML.strip(), strip_yaml_fence(f"```yaml\n{VALID_YAML}```"))

    def test_rejects_unknown_connection_port(self) -> None:
        invalid = VALID_YAML.replace(
            "connections: []",
            """connections:
  - from: controller_a
    from_port: missing
    to: controller_a
    to_port: bus
    connection_type: internal_net""",
        )

        result = validate_architecture_yaml(invalid)

        self.assertFalse(result["valid"])
        self.assertFalse(result["checks"]["references"]["valid"])
        self.assertTrue(any("controller_a.missing" in error for error in result["errors"]))

    def test_rejects_empty_architecture_and_non_string_connection_type(self) -> None:
        empty_result = validate_architecture_yaml(
            "version: 1\nboards: []\nelements: []\nconnections: []\n"
        )
        invalid_type = validate_architecture_yaml(
            VALID_YAML.replace(
                "connections: []",
                """connections:
  - from: controller_a
    from_port: bus
    to: controller_a
    to_port: bus
    connection_type: [internal_net]""",
            )
        )

        self.assertFalse(empty_result["valid"])
        self.assertFalse(invalid_type["valid"])

class PdfYamlTopologyTests(unittest.TestCase):
    def test_flags_cross_board_internal_net_for_review(self) -> None:
        document = {
            "version": 1,
            "boards": [
                {"id": "board_a", "label": "Board A"},
                {"id": "board_b", "label": "Board B"},
            ],
            "elements": [
                {"id": "source", "board": "board_a", "type": "controller", "ports": [{"id": "bus"}]},
                {"id": "destination", "board": "board_b", "type": "sensor", "ports": [{"id": "bus"}]},
            ],
            "connections": [
                {"from": "source", "from_port": "bus", "to": "destination", "to_port": "bus", "connection_type": "internal_net"}
            ],
        }

        result = validate_architecture_yaml(yaml.safe_dump(document, sort_keys=False))

        self.assertTrue(result["valid"])
        self.assertTrue(result["review_required"])
        self.assertTrue(any("Cross-board connection" in warning for warning in result["warnings"]))

    def test_flags_disconnected_hub_and_incomplete_connector_mating_for_review(self) -> None:
        document = {
            "version": 1,
            "boards": [
                {"id": "board_a", "label": "Board A"},
                {"id": "board_b", "label": "Board B"},
            ],
            "elements": [
                {
                    "id": "controller",
                    "board": "board_a",
                    "type": "controller",
                    "ports": [{"id": "bus_a"}, {"id": "bus_b"}],
                },
                {
                    "id": "source_connector",
                    "board": "board_a",
                    "type": "connector",
                    "ports": [{"id": "bus_a"}, {"id": "bus_b"}],
                },
                {
                    "id": "destination_connector",
                    "board": "board_b",
                    "type": "connector",
                    "ports": [{"id": "bundle"}],
                },
                {
                    "id": "detached_hub",
                    "board": "board_b",
                    "type": "hub",
                    "ports": [{"id": "upstream"}, {"id": "downstream"}],
                },
                {
                    "id": "detached_device",
                    "board": "board_b",
                    "type": "endpoint",
                    "ports": [{"id": "bus"}],
                },
            ],
            "connections": [
                {"from": "controller", "from_port": "bus_a", "to": "source_connector", "to_port": "bus_a", "connection_type": "internal_net"},
                {"from": "controller", "from_port": "bus_b", "to": "source_connector", "to_port": "bus_b", "connection_type": "internal_net"},
                {"from": "source_connector", "from_port": "bus_a", "to": "destination_connector", "to_port": "bundle", "connection_type": "mating"},
                {"from": "detached_hub", "from_port": "downstream", "to": "detached_device", "to_port": "bus", "connection_type": "internal_net"},
            ],
        }

        result = validate_architecture_yaml(yaml.safe_dump(document, sort_keys=False))

        self.assertTrue(result["valid"])
        self.assertTrue(result["review_required"])
        self.assertFalse(result["checks"]["topology"]["valid"])
        self.assertEqual("Review required; inspect 3 warning(s)", result["checks"]["topology"]["detail"])
        self.assertEqual([], result["errors"])
        self.assertTrue(any("disconnected topology" in warning for warning in result["warnings"]))
        self.assertTrue(any("upstream port is unconnected" in warning for warning in result["warnings"]))
        self.assertTrue(any("without mating coverage: bus_b" in warning for warning in result["warnings"]))

    def test_flags_empty_hub_downstream_and_terminal_transit(self) -> None:
        document = {
            "version": 1,
            "boards": [{"id": "board_a", "label": "Board A"}],
            "elements": [
                {
                    "id": "controller",
                    "board": "board_a",
                    "type": "controller",
                    "ports": [{"id": "bus"}],
                },
                {
                    "id": "empty_hub",
                    "board": "board_a",
                    "type": "hub",
                    "ports": [{"id": "upstream"}, {"id": "downstream_0"}],
                },
                {
                    "id": "terminal",
                    "board": "board_a",
                    "type": "endpoint",
                    "ports": [{"id": "bus"}],
                },
                {
                    "id": "other_terminal",
                    "board": "board_a",
                    "type": "endpoint",
                    "ports": [{"id": "bus"}],
                },
            ],
            "connections": [
                {"from": "controller", "from_port": "bus", "to": "empty_hub", "to_port": "upstream", "connection_type": "internal_net"},
                {"from": "controller", "from_port": "bus", "to": "terminal", "to_port": "bus", "connection_type": "internal_net"},
                {"from": "terminal", "from_port": "bus", "to": "other_terminal", "to_port": "bus", "connection_type": "internal_net"},
            ],
        }

        result = validate_architecture_yaml(yaml.safe_dump(document, sort_keys=False))

        self.assertTrue(result["valid"])
        self.assertTrue(result["review_required"])
        self.assertTrue(any("no connected downstream ports" in warning for warning in result["warnings"]))
        self.assertTrue(any("may be modeled as a transit device" in warning for warning in result["warnings"]))


class PdfYamlGenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_repairs_hard_error_with_ollama_patch(self) -> None:
        progress_events: list[tuple[str, int]] = []
        activity_events: list[str] = []
        process_events: list[str] = []
        workspace_paths: list[Path] = []
        first_page_count = 0
        copied_guide_content = ""

        async def record_progress(stage: str, percent: int) -> None:
            progress_events.append((stage, percent))

        async def record_activity(activity: str) -> None:
            activity_events.append(activity)

        async def record_process(message: str) -> None:
            process_events.append(message)

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            guide = Path(directory) / "guide.md"
            write_architecture_pdf(source)
            guide.write_text("guide", encoding="utf-8")
            invalid = VALID_YAML.replace("board: board_a", "board: missing_board")
            patch_response = [{"op": "replace", "path": "/elements/0/board", "value": "board_a"}]

            async def fake_conversion(filtered_pdf, references, selection, workspace, **kwargs):
                nonlocal first_page_count, copied_guide_content
                workspace = Path(workspace)
                workspace_paths.append(workspace)
                self.assertTrue(workspace.is_dir())
                with pymupdf.open(filtered_pdf) as document:
                    first_page_count = document.page_count
                copied_guide_content = references[0].read_text(encoding="utf-8")
                analysis = workspace / "analysis"
                analysis.mkdir()
                (analysis / "source_inventory.json").write_text("[]", encoding="utf-8")
                await kwargs["activity_callback"]("writing_yaml")
                await kwargs["process_callback"](
                    "Tracing board connections against the selected architecture."
                )
                return invalid

            with (
                patch(
                    "pdf_to_yaml_agent.converter.run_ollama_conversion",
                    new=AsyncMock(side_effect=fake_conversion),
                ) as conversion,
                patch(
                    "pdf_to_yaml_agent.converter.OllamaClient.chat_json",
                    new=AsyncMock(return_value=patch_response),
                ) as repair,
            ):
                content, validation = await generate_architecture_yaml(
                    source,
                    [guide],
                    progress_callback=record_progress,
                    activity_callback=record_activity,
                    process_callback=record_process,
                )

            repair_prompt = repair.await_args.args[1]

        self.assertEqual(yaml.safe_load(VALID_YAML), yaml.safe_load(content))
        self.assertTrue(validation["valid"])
        self.assertEqual(1, conversion.await_count)
        self.assertEqual(1, repair.await_count)
        self.assertEqual("guide", copied_guide_content)
        self.assertIn("minimal RFC 6902-style JSON patch", repair_prompt)
        self.assertIn("Never remove boards, elements, ports, or connections", repair_prompt)
        self.assertIn("_smbus_figures.pdf", conversion.await_args.args[0].name)
        self.assertEqual(2, first_page_count)
        self.assertTrue(all(not path.exists() for path in workspace_paths))
        stages = [stage for stage, _ in progress_events]
        distinct_stages = [stage for index, stage in enumerate(stages) if index == 0 or stage != stages[index - 1]]
        self.assertEqual(
            ["filtering", "generating", "validating", "repairing", "revalidating", "completed"],
            distinct_stages,
        )
        self.assertEqual(100, progress_events[-1][1])
        self.assertIn("context_ready", activity_events)
        self.assertIn("writing_yaml", activity_events)
        self.assertIn("response_received", activity_events)
        self.assertIn("repairing_yaml", activity_events)
        self.assertEqual(
            ["Tracing board connections against the selected architecture."],
            process_events,
        )

    async def test_deletes_workspace_when_ollama_fails(self) -> None:
        observed_workspace: Path | None = None

        async def fail_conversion(filtered_pdf, references, selection, workspace, **kwargs):
            nonlocal observed_workspace
            observed_workspace = Path(workspace)
            self.assertTrue(observed_workspace.is_dir())
            (observed_workspace / "analysis").mkdir()
            (observed_workspace / "analysis" / "source_inventory.json").write_text(
                "{}", encoding="utf-8"
            )
            raise RuntimeError("generation failed")

        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            guide = Path(directory) / "guide.md"
            write_architecture_pdf(source)
            guide.write_text("guide", encoding="utf-8")
            with (
                patch(
                    "pdf_to_yaml_agent.converter.run_ollama_conversion",
                    new=AsyncMock(side_effect=fail_conversion),
                ),
                self.assertRaisesRegex(RuntimeError, "generation failed"),
            ):
                await generate_architecture_yaml(source, [guide])

        self.assertIsNotNone(observed_workspace)
        self.assertFalse(observed_workspace.exists())

    async def test_topology_warning_does_not_trigger_repair(self) -> None:
        topology_document = yaml.safe_load(VALID_YAML)
        topology_document["elements"].append(
            {
                "id": "detached_device",
                "board": "board_a",
                "type": "endpoint",
                "ports": [{"id": "bus"}],
            }
        )
        topology_warning = yaml.safe_dump(topology_document, sort_keys=False)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            guide = Path(directory) / "guide.md"
            write_architecture_pdf(source)
            guide.write_text("guide", encoding="utf-8")
            with patch(
                "pdf_to_yaml_agent.converter.run_ollama_conversion",
                new=AsyncMock(return_value=topology_warning),
            ) as conversion:
                _, validation = await generate_architecture_yaml(source, [guide])

        self.assertEqual(1, conversion.await_count)
        self.assertTrue(validation["valid"])
        self.assertTrue(validation["review_required"])


class PdfYamlOllamaPipelineTests(unittest.TestCase):
    def test_renders_overview_and_overlapping_target_crops(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / "source.pdf"
            filtered = workspace / "filtered.pdf"
            analysis = workspace / "analysis"
            write_architecture_pdf(source)
            selection = extract_architecture_pages(source, filtered)

            page_text, images = render_analysis_images(filtered, selection, analysis)

            self.assertIn("Acme Modular SMBus Architecture", page_text)
            self.assertEqual(10, len(images))
            self.assertEqual("target_overview.png", images[0].name)
            self.assertTrue(all(image.is_file() and image.stat().st_size > 0 for image in images))

    def test_vision_prompts_treat_legend_symbols_as_annotations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            source = workspace / "source.pdf"
            filtered = workspace / "filtered.pdf"
            write_architecture_pdf(source)
            selection = extract_architecture_pages(source, filtered)

            vision_prompt = build_vision_prompt(
                selection, "crop.png", 1, 1
            )
            topology_prompt = build_topology_completion_prompt(
                {"elements": [], "connections": []}, "crop 1"
            )

        expected_rule = "symbols defined by the figure legend as element annotations"
        self.assertIn(expected_rule, vision_prompt)
        self.assertIn(expected_rule, topology_prompt)

    def test_yaml_reference_contributes_shape_without_hardware_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "other_project.yml"
            reference.write_text(
                """version: 1
boards:
- id: forbidden_board
  label: Forbidden Product
elements:
- id: forbidden_device
  board: forbidden_board
  type: sensor
  part: SECRET123
  ports:
  - id: bus
connections: []
""",
                encoding="utf-8",
            )

            context = _reference_context([reference])
            prompt = build_fragment_structure_prompt(
                {"boards": [], "elements": [], "connections": []},
                "crop 1",
                context,
            )

        self.assertIn('"boards": ["id", "label"]', context)
        self.assertIn('"elements": ["board", "id", "part", "ports", "type"]', context)
        self.assertIn('"element_types": ["sensor"]', context)
        self.assertIn('"top_level_order": ["version", "boards", "elements", "connections"]', context)
        self.assertIn("Normative representation guidance", prompt)
        self.assertNotIn("Forbidden Product", context)
        self.assertNotIn("SECRET123", context)
        self.assertNotIn("forbidden_device", context)
        self.assertNotIn("Forbidden Product", prompt)

    def test_markdown_reference_keeps_rules_and_omits_fenced_examples(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            reference = Path(directory) / "authoring.md"
            reference.write_text(
                "Use port_display_order to preserve port order.\n\n"
                "```yaml\nboards:\n  - id: example_board\n"
                "    label: Other Product\n```\n",
                encoding="utf-8",
            )

            context = _reference_context([reference])
            prompt = build_fragment_structure_prompt(
                {"boards": [], "elements": [], "connections": []},
                "crop 1",
                context,
            )

        self.assertIn("Use port_display_order to preserve port order.", prompt)
        self.assertNotIn("example_board", prompt)
        self.assertNotIn("Other Product", prompt)

    def test_merge_and_connection_compiler_preserve_authoring_fields(self) -> None:
        structure = merge_structures(
            [
                {
                    "boards": [{"id": "board_a", "label": "Board A"}],
                    "elements": [
                        {
                            "id": "controller",
                            "board": "board_a",
                            "label": "Controller",
                            "type": "controller",
                            "mechanical": "2x6 connector",
                            "port_display_order": ["pI_C10"],
                            "ports": [
                                {
                                    "id": "pI_C10",
                                    "direction": "bidirectional",
                                    "electrical_class": "active",
                                    "i2c_role_capabilities": ["controller"],
                                }
                            ],
                        },
                        {
                            "id": "target",
                            "board": "board_a",
                            "label": "Target",
                            "type": "sensor",
                            "ports": [{"id": "qI", "direction": "bidirectional"}],
                        },
                    ],
                }
            ]
        )
        inventory = [
            {
                "connections": [
                    {
                        "from_element": "Controller",
                        "from_port": "pI_C10",
                        "to_element": "Target",
                        "to_port": "qI",
                        "connection_type": "cable",
                        "protocol": "i2c",
                        "speed_hz": 100000,
                        "medium": "picpwr_cable",
                        "length_mm": 500,
                        "from_role": "controller",
                        "to_role": "passive",
                    }
                ]
            }
        ]

        controller = structure["elements"][0]
        connections, unresolved = compile_inventory_connections(
            structure, inventory, [structure]
        )

        self.assertEqual("2x6 connector", controller["mechanical"])
        self.assertEqual(["pI_C10"], controller["port_display_order"])
        self.assertEqual("pI_C10", controller["ports"][0]["id"])
        self.assertEqual("active", controller["ports"][0]["electrical_class"])
        self.assertEqual("qI", structure["elements"][1]["ports"][0]["id"])
        self.assertEqual([], unresolved)
        self.assertEqual("pI_C10", connections[0]["from_port"])
        self.assertEqual("qI", connections[0]["to_port"])
        self.assertEqual(100000, connections[0]["speed_hz"])
        self.assertEqual(500, connections[0]["length_mm"])
        self.assertEqual("controller", connections[0]["from_role"])

    def test_compiles_separate_structure_and_connections(self) -> None:
        structure = normalize_structure(
            {
                "boards": [{"id": "board_a", "label": "Board A"}],
                "elements": [
                    {
                        "id": "controller",
                        "board": "board_a",
                        "type": "controller",
                        "ports": [{"id": "bus"}],
                    }
                ],
            }
        )

        architecture = compile_architecture(structure, {"connections": []})

        self.assertEqual(
            ["version", "boards", "elements", "connections"],
            list(architecture),
        )
        self.assertEqual("controller", architecture["elements"][0]["id"])

    def test_merges_crop_structures_without_collapsing_distinct_addresses(self) -> None:
        structures = [
            {
                "boards": [{"id": "board_a", "label": "Board A"}],
                "elements": [
                    {"id": "sensor", "board": "board_a", "label": "Sensor", "type": "sensor", "part": "TMP75", "address": "0x48", "ports": ["bus"]},
                ],
            },
            {
                "boards": [{"id": "board_a", "label": "Board A"}],
                "elements": [
                    {"id": "sensor", "board": "board_a", "label": "Sensor", "type": "sensor", "part": "TMP75", "address": "0x48", "ports": [{"id": "alert"}]},
                    {"id": "sensor", "board": "board_a", "label": "Sensor", "type": "sensor", "part": "TMP75", "address": "0x49", "ports": [{"id": "bus"}]},
                ],
            },
        ]

        merged = merge_structures(structures)

        self.assertEqual(1, len(merged["boards"]))
        self.assertEqual(2, len(merged["elements"]))
        self.assertEqual(["sensor", "sensor_2"], [item["id"] for item in merged["elements"]])
        self.assertEqual(
            {"bus", "alert"},
            {port["id"] for port in merged["elements"][0]["ports"]},
        )

    def test_compiles_resolvable_inventory_connections_and_adds_ports(self) -> None:
        structure = {
            "boards": [{"id": "board_a", "label": "Board A"}],
            "elements": [
                {"id": "controller", "board": "board_a", "label": "Main Controller", "type": "controller", "ports": [{"id": "bus"}]},
                {"id": "mux", "board": "board_a", "label": "PCA9546 Mux 0x70", "type": "mux", "part": "PCA9546", "ports": [{"id": "upstream"}]},
            ],
        }
        inventory = [
            {
                "connections": [
                    {"from_element": "Main Controller", "from_port": "SMB 1", "to_element": "PCA9546 Mux 0x70", "to_port": "C0", "connection_type": "direct", "protocol": "SMBus"},
                    {"from_element": "Unknown", "from_port": "bus", "to_element": "Main Controller", "to_port": "bus", "connection_type": "direct"},
                ]
            }
        ]

        connections, unresolved = compile_inventory_connections(structure, inventory)

        self.assertEqual(1, len(connections))
        self.assertEqual("internal_net", connections[0]["connection_type"])
        self.assertEqual("smbus", connections[0]["protocol"])
        self.assertEqual("SMB 1", connections[0]["from_port"])
        self.assertIn({"id": "C0"}, structure["elements"][1]["ports"])
        self.assertEqual(1, len(unresolved))

    def test_compiles_only_endpoints_preserved_as_local_physical_elements(self) -> None:
        structure = {
            "boards": [{"id": "board_a", "label": "Board A"}],
            "elements": [
                {"id": "controller", "board": "board_a", "label": "Controller", "type": "controller", "ports": [{"id": "bus"}]},
                {"id": "mux", "board": "board_a", "label": "Mux", "type": "mux", "ports": [{"id": "bus"}]},
            ],
        }
        inventory = [{"connections": [
            {"from_element": "Controller", "to_element": "Mux", "connection_type": "direct"},
            {"from_element": "SMB_HOST", "to_element": "Board A", "connection_type": "bus"},
        ]}]
        cleaned = [{"boards": [{"id": "board_a", "label": "Board A"}], "elements": [
            {"id": "controller", "board": "board_a", "label": "Controller", "type": "controller", "ports": [{"id": "bus"}]},
            {"id": "mux", "board": "board_a", "label": "Mux", "type": "mux", "ports": [{"id": "bus"}]},
        ]}]

        connections, unresolved = compile_inventory_connections(
            structure, inventory, cleaned
        )

        self.assertEqual(1, len(connections))
        self.assertEqual(1, len(unresolved))

    def test_finds_connections_with_undeclared_local_endpoints(self) -> None:
        fragment = {
            "elements": [{"id": "controller"}, {"id": "mux"}],
            "connections": [
                {"from_element": "controller", "to_element": "mux"},
                {"from_element": "controller", "to_element": "missing_connector"},
            ],
        }

        invalid = invalid_fragment_connections(fragment)

        self.assertEqual([fragment["connections"][1]], invalid)

    def test_materializes_named_connector_endpoints_but_not_bus_labels(self) -> None:
        fragment = {
            "boards": [{"id": "board_a", "label": "Board A"}],
            "elements": [{"id": "hub", "board": "board_a", "label": "Hub"}],
            "connections": [
                {"from_element": "hub", "to_element": "cpu_0_port_1_conn_1", "to_port": "mating"},
                {"from_element": "hub", "to_element": "smb_host"},
            ],
        }

        materialize_connector_endpoints(fragment)

        connector = next(
            item for item in fragment["elements"] if item["id"] == "cpu_0_port_1_conn_1"
        )
        self.assertEqual("connector", connector["type"])
        self.assertEqual("board_a", connector["board"])
        self.assertNotIn("smb_host", {item["id"] for item in fragment["elements"]})

    def test_collapses_bus_elements_into_physical_connections(self) -> None:
        architecture = {
            "version": 1,
            "boards": [{"id": "board", "label": "Board"}],
            "elements": [
                {"id": "controller", "type": "controller"},
                {"id": "smb_host", "type": "bus", "label": "SMB_HOST"},
                {"id": "i2c_channel", "type": "i2c_channel", "label": "I2C Channel"},
                {"id": "physical_interface", "type": "bus_interface", "part": "PCA9617"},
                {"id": "mux", "type": "mux"},
                {"id": "sensor", "type": "sensor"},
            ],
            "connections": [
                {"from": "controller", "from_port": "bus", "to": "smb_host", "to_port": "bus", "connection_type": "internal_net", "protocol": "smbus"},
                {"from": "smb_host", "from_port": "bus", "to": "mux", "to_port": "upstream", "connection_type": "internal_net", "protocol": "smbus"},
                {"from": "smb_host", "from_port": "bus", "to": "sensor", "to_port": "bus", "connection_type": "internal_net", "protocol": "smbus"},
            ],
        }

        collapsed = collapse_nonphysical_elements(architecture)

        self.assertNotIn("smb_host", {item["id"] for item in collapsed["elements"]})
        self.assertNotIn("i2c_channel", {item["id"] for item in collapsed["elements"]})
        self.assertIn("physical_interface", {item["id"] for item in collapsed["elements"]})
        self.assertEqual(2, len(collapsed["connections"]))
        self.assertEqual(
            {"controller", "mux", "sensor"},
            {
                endpoint
                for connection in collapsed["connections"]
                for endpoint in (connection["from"], connection["to"])
            },
        )

    def test_finds_only_isolated_physical_elements(self) -> None:
        fragment = {
            "elements": [
                {"id": "controller", "type": "controller"},
                {"id": "mux", "type": "mux"},
                {"id": "smb_host", "type": "bus"},
            ],
            "connections": [
                {"from_element": "controller", "to_element": "smb_host"}
            ],
        }

        self.assertEqual(["mux"], isolated_physical_element_ids(fragment))


class PdfYamlPatchTests(unittest.TestCase):
    def test_patch_rejects_removing_architecture_content(self) -> None:
        document = yaml.safe_load(VALID_YAML)

        with self.assertRaisesRegex(Exception, "cannot remove architecture content"):
            apply_repair_patch(document, '[{"op":"remove","path":"/elements/0/ports"}]')

    def test_scope_guard_rejects_reduced_element_count(self) -> None:
        before = yaml.safe_load(VALID_YAML)
        after = yaml.safe_load(VALID_YAML)
        after["elements"] = []

        with self.assertRaisesRegex(Exception, "reduced architecture scope: elements"):
            ensure_scope_preserved(before, after)


class PdfYamlApiTests(unittest.TestCase):
    def test_generate_stream_reports_progress_and_result(self) -> None:
        async def fake_generate(source: Path, references: list[Path], progress_callback=None, activity_callback=None, process_callback=None):
            self.assertTrue(source.is_file())
            if progress_callback is not None:
                await progress_callback("generating", 25)
            if activity_callback is not None:
                await activity_callback("analyzing")
            if process_callback is not None:
                await process_callback("Tracing board connections.")
            if progress_callback is not None:
                await progress_callback("validating", 65)
                await progress_callback("completed", 100)
            return VALID_YAML, validate_architecture_yaml(VALID_YAML)

        with (
            TestClient(app) as client,
            patch("web.backend.app.list_reference_paths", return_value=[Path(__file__)]),
            patch("web.backend.app.generate_architecture_yaml", side_effect=fake_generate),
        ):
            response = client.post(
                "/api/agents/pdf-yaml/generate-stream",
                files=[("pdf", ("source.pdf", b"pdf-content", "application/pdf"))],
            )

        events = [json.loads(line) for line in response.text.splitlines()]
        self.assertEqual(200, response.status_code)
        self.assertEqual("application/x-ndjson", response.headers["content-type"].split(";")[0])
        self.assertEqual(
            ["starting", "generating", "validating", "completed"],
            [event["stage"] for event in events if event["type"] == "progress"],
        )
        self.assertEqual(
            ["analyzing"],
            [event["activity"] for event in events if event["type"] == "activity"],
        )
        self.assertEqual(
            ["Tracing board connections."],
            [event["message"] for event in events if event["type"] == "process"],
        )
        self.assertEqual("result", events[-1]["type"])
        self.assertEqual("source.yml", events[-1]["file_name"])

    def test_prepare_returns_reduced_pdf_without_persisting_it(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            write_architecture_pdf(source)
            with TestClient(app) as client:
                response = client.post(
                    "/api/agents/pdf-yaml/prepare",
                    files=[
                        ("pdf", ("source.pdf", source.read_bytes(), "application/pdf"))
                    ],
                )

            prepared = Path(directory) / "prepared.pdf"
            prepared.write_bytes(response.content)
            with pymupdf.open(prepared) as document:
                page_count = document.page_count

        self.assertEqual(200, response.status_code)
        self.assertEqual("Acme", response.headers["x-architecture-product"])
        self.assertEqual("1,2", response.headers["x-architecture-pages"])
        self.assertEqual(2, page_count)

    def test_prepare_rejects_pdf_without_architecture_figure(self) -> None:
        document = pymupdf.open()
        page = document.new_page()
        page.insert_text((72, 72), "Unrelated product documentation")
        content = document.tobytes()
        document.close()

        with TestClient(app) as client:
            response = client.post(
                "/api/agents/pdf-yaml/prepare",
                files=[("pdf", ("source.pdf", content, "application/pdf"))],
            )

        self.assertEqual(422, response.status_code)
        self.assertIn("SMBus", response.json()["detail"])
        self.assertIn("Architecture", response.json()["detail"])

    def test_generate_uses_workspace_references_and_removes_only_pdf(self) -> None:
        observed_paths: list[Path] = []

        async def fake_generate(source: Path, references: list[Path]):
            observed_paths.extend([source, *references])
            self.assertEqual(b"pdf-content", source.read_bytes())
            self.assertEqual("guide-content", references[0].read_text(encoding="utf-8"))
            return VALID_YAML, validate_architecture_yaml(VALID_YAML)

        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            guide = workspace / "guide.md"
            guide.write_text("guide-content", encoding="utf-8")
            with (
                patch.object(reference_store, "REFERENCE_WORKSPACE", workspace),
                TestClient(app) as client,
                patch("web.backend.app.generate_architecture_yaml", side_effect=fake_generate),
            ):
                response = client.post(
                    "/api/agents/pdf-yaml/generate",
                    files=[("pdf", ("source.pdf", b"pdf-content", "application/pdf"))],
                )

            self.assertEqual(200, response.status_code)
            self.assertEqual("source.yml", response.json()["file_name"])
            self.assertTrue(response.json()["validation"]["valid"])
            self.assertFalse(observed_paths[0].exists())
            self.assertTrue(guide.exists())

    def test_uses_default_guide_when_workspace_is_empty(self) -> None:
        observed_names: list[str] = []

        async def fake_generate(source: Path, references: list[Path]):
            observed_names.extend(path.name for path in references)
            return VALID_YAML, validate_architecture_yaml(VALID_YAML)

        with (
            TestClient(app) as client,
            patch("web.backend.app.list_reference_paths", return_value=[]),
            patch("web.backend.app.generate_architecture_yaml", side_effect=fake_generate),
        ):
            response = client.post(
                "/api/agents/pdf-yaml/generate",
                files=[("pdf", ("source.pdf", b"pdf-content", "application/pdf"))],
            )

        self.assertEqual(200, response.status_code)
        self.assertIn("I2C_architecture_YAML_authoring_guide.md", observed_names)

    def test_reference_files_persist_across_requests_and_can_be_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            with (
                patch.object(reference_store, "REFERENCE_WORKSPACE", workspace),
                TestClient(app) as client,
            ):
                upload = client.post(
                    "/api/agents/pdf-yaml/references",
                    files=[("files", ("guide.md", b"guide-content", "text/markdown"))],
                )
                listed = client.get("/api/agents/pdf-yaml/references")
                downloaded = client.get("/api/agents/pdf-yaml/references/guide.md")
                deleted = client.delete("/api/agents/pdf-yaml/references/guide.md")
                listed_after_delete = client.get("/api/agents/pdf-yaml/references")

        self.assertEqual(200, upload.status_code)
        self.assertEqual(["guide.md"], [item["name"] for item in listed.json()["files"]])
        self.assertEqual(b"guide-content", downloaded.content)
        self.assertEqual(200, deleted.status_code)
        self.assertEqual([], listed_after_delete.json()["files"])

    def test_reference_store_rejects_unsupported_files(self) -> None:
        self.assertEqual(
            "I2C_architecure.yml.txt",
            reference_store.normalize_reference_name("I2C_architecure.yml.txt"),
        )
        with self.assertRaises(reference_store.InvalidReferenceFile):
            reference_store.normalize_reference_name("notes.exe")


if __name__ == "__main__":
    unittest.main()