import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from pdf_to_yaml_agent.converter import (
    build_generation_prompt,
    generate_architecture_yaml,
    strip_yaml_fence,
    validate_architecture_yaml,
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


class PdfYamlServiceTests(unittest.TestCase):
    def test_prompt_enforces_guide_shape_and_no_invention(self) -> None:
        prompt = build_generation_prompt("source.pdf", ["guide.md", "example.yml"])

        self.assertIn('Figure 12-7, "Johnson City Modular SMBus architecture"', prompt)
        self.assertIn("not authoritative for content scope", prompt)
        self.assertIn("do not limit extraction to SMB_MPIC / SMB C[10]", prompt)
        self.assertIn("Do not broaden the result beyond Figure 12-7", prompt)
        self.assertIn("Do not invent", prompt)
        self.assertIn("source.pdf", prompt)
        self.assertIn("guide.md", prompt)
        self.assertIn("example.yml", prompt)

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


class PdfYamlGenerationTests(unittest.IsolatedAsyncioTestCase):
    async def test_repairs_non_compliant_first_response_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            guide = Path(directory) / "guide.md"
            source.write_bytes(b"pdf")
            guide.write_text("guide", encoding="utf-8")
            responses = ["version: 1\nboards: []", VALID_YAML]
            with patch(
                "pdf_to_yaml_agent.converter.ask_copilot",
                new=AsyncMock(side_effect=responses),
            ) as ask:
                content, validation = await generate_architecture_yaml(
                    source, [guide], model="test-model"
                )

        self.assertEqual(VALID_YAML.strip(), content)
        self.assertTrue(validation["valid"])
        self.assertEqual(2, ask.await_count)
        self.assertEqual([source, guide], ask.await_args_list[0].kwargs["files"])
        self.assertEqual([source, guide], ask.await_args_list[1].kwargs["files"])


class PdfYamlApiTests(unittest.TestCase):
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