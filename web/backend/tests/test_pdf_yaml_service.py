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
    async def test_repairs_hard_error_with_patch_and_no_second_attachments(self) -> None:
        progress_events: list[tuple[str, int]] = []
        activity_events: list[str] = []
        process_events: list[str] = []

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
            patch_response = '[{"op":"replace","path":"/elements/0/board","value":"board_a"}]'
            responses = [invalid, patch_response]
            async def fake_ask(*args, **kwargs):
                callback = kwargs.get("on_delta")
                if callback is not None:
                    callback("output started")
                process_delta = kwargs.get("on_process_delta")
                if process_delta is not None:
                    process_delta("Tracing board connections against the selected architecture. ")
                    await asyncio.sleep(0)
                return responses.pop(0)

            with patch(
                "pdf_to_yaml_agent.converter.ask_copilot",
                new=AsyncMock(side_effect=fake_ask),
            ) as ask:
                content, validation = await generate_architecture_yaml(
                    source,
                    [guide],
                    model="test-model",
                    progress_callback=record_progress,
                    activity_callback=record_activity,
                    process_callback=record_process,
                )

            first_files = ask.await_args_list[0].kwargs["files"]
            second_files = ask.await_args_list[1].kwargs["files"]
            repair_prompt = ask.await_args_list[1].args[0]
            with pymupdf.open(first_files[0]) as document:
                filtered_page_count = document.page_count

        self.assertEqual(yaml.safe_load(VALID_YAML), yaml.safe_load(content))
        self.assertTrue(validation["valid"])
        self.assertEqual(2, ask.await_count)
        self.assertEqual(guide, first_files[1])
        self.assertEqual([], second_files)
        self.assertIn("minimal RFC 6902-style JSON patch", repair_prompt)
        self.assertIn("Never remove boards, elements, ports, or connections", repair_prompt)
        self.assertIn("_smbus_figures.pdf", first_files[0].name)
        self.assertEqual(2, filtered_page_count)
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
                "pdf_to_yaml_agent.converter.ask_copilot",
                new=AsyncMock(return_value=topology_warning),
            ) as ask:
                _, validation = await generate_architecture_yaml(source, [guide])

        self.assertEqual(1, ask.await_count)
        self.assertTrue(validation["valid"])
        self.assertTrue(validation["review_required"])


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