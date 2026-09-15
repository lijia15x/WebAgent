import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mrc_automation_agent import artifact_store
from mrc_automation_agent.models import WorkbookFile


class ArtifactStoreTests(unittest.TestCase):
    def test_stores_and_lists_workbooks_by_cycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.object(artifact_store, "WORKSPACE_ROOT", root):
                stored = artifact_store.store_workbooks(
                    "2026WW38",
                    [
                        WorkbookFile(
                            "MRC WW38.xlsx",
                            "https://example.invalid",
                            b"xlsx",
                            "2026-09-15T08:00:00Z",
                        )
                    ],
                )
                listed = artifact_store.list_cycle_artifacts("2026WW38")

            self.assertEqual(stored[0].file_name, listed[0].file_name)
            self.assertEqual("", listed[0].source_url)
            self.assertEqual(b"xlsx", (root / stored[0].relative_path).read_bytes())
            self.assertFalse((root / "2026WW38" / "excel" / ".source_urls.json").exists())

    def test_rejects_path_traversal(self) -> None:
        with self.assertRaises(ValueError):
            artifact_store.safe_file_name("../secret.xlsx", ".xlsx")
        with self.assertRaises(ValueError):
            artifact_store.resolve_artifact("2026WW38", "ppt", "../secret.pptx")


if __name__ == "__main__":
    unittest.main()