import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from mrc_automation_agent import artifact_store
from mrc_automation_agent.models import MrcArtifact
from web.backend.app import download_mrc_artifact
from web.backend.mrc_service import MrcService


class MrcArtifactApiTests(unittest.TestCase):
    def test_serializes_download_url_without_local_path(self) -> None:
        payload = MrcService._serialize_artifacts(
            "2026WW38",
            [MrcArtifact("ppt", "Weekly Report.pptx", "private/path.pptx")],
        )[0]

        self.assertEqual(
            "/api/agents/mrc-automation/cycles/2026WW38/artifacts/ppt/Weekly%20Report.pptx",
            payload["download_url"],
        )
        self.assertNotIn("private/path.pptx", payload["download_url"])

    def test_download_resolves_only_inside_cycle_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            ppt = workspace / "2026WW38" / "ppt" / "Weekly Report.pptx"
            ppt.parent.mkdir(parents=True)
            ppt.write_bytes(b"ppt")
            with patch.object(artifact_store, "WORKSPACE_ROOT", workspace):
                response = asyncio.run(
                    download_mrc_artifact(
                        "2026WW38", "ppt", "Weekly Report.pptx"
                    )
                )
                with self.assertRaises(HTTPException):
                    asyncio.run(
                        download_mrc_artifact(
                            "2026WW38", "ppt", "../secret.pptx"
                        )
                    )

        self.assertEqual(ppt, Path(response.path))
        self.assertEqual(
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            response.media_type,
        )


if __name__ == "__main__":
    unittest.main()