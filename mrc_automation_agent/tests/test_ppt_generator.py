import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pptx import Presentation

from mrc_automation_agent import artifact_store, ppt_generator
from mrc_automation_agent.config import MrcConfig
from mrc_automation_agent.models import MrcArtifact


class PptGeneratorTests(unittest.TestCase):
    def test_generates_one_presentation_for_each_workbook(self) -> None:
        config = MrcConfig(
            sharepoint_site_url="",
            sharepoint_folder_template="",
            sharepoint_tenant="",
            sharepoint_client_id="",
            sharepoint_thumbprint="",
            sharepoint_certificate_path="",
            sharepoint_certificate_password="",
        )
        page2 = {
            "executive_summary": [
                {"bold_lead": "On track.", "normal_detail": "Most work is green."},
                {"bold_lead": "One risk.", "normal_detail": "Material is late."},
            ],
            "detail_sections": [],
        }
        page3 = {
            "sections": [
                {
                    "title": "Engineering",
                    "paragraphs": [
                        {"bold_lead": "Stable.", "normal_detail": "Milestones met."},
                        {"bold_lead": "Watch.", "normal_detail": "Supplier timing."},
                    ],
                }
            ]
        }

        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            excel_dir = workspace / "2026WW38" / "excel"
            excel_dir.mkdir(parents=True)
            execution = excel_dir / "CRI-ww38-MRC.xlsx"
            tracking = excel_dir / "DHE Execution MRC AR Tracking.xlsx"
            for path in (execution, tracking):
                path.write_bytes(b"test")
            artifacts = [
                MrcArtifact("excel", execution.name, execution.relative_to(workspace).as_posix()),
                MrcArtifact("excel", tracking.name, tracking.relative_to(workspace).as_posix()),
            ]
            with (
                patch.object(ppt_generator, "WORKSPACE_ROOT", workspace),
                patch.object(artifact_store, "WORKSPACE_ROOT", workspace),
                patch.object(
                    ppt_generator,
                    "_sheet_names",
                    side_effect=[["Status WW38", "Lookup"], ["AR tracking"]],
                ),
                patch.object(
                    ppt_generator,
                    "_call_copilot_json",
                    side_effect=[page2, page3, page2, page3],
                ) as copilot,
            ):
                generated = ppt_generator.generate_weekly_ppts(
                    config, "2026WW38", artifacts
                )

            self.assertEqual([execution.name, tracking.name], [item.source_workbook_name for item in generated])
            self.assertEqual(execution, copilot.call_args_list[0].args[2])
            self.assertEqual(tracking, copilot.call_args_list[2].args[2])
            self.assertIn('["Status WW38", "Lookup"]', copilot.call_args_list[0].args[0])
            self.assertIn('["AR tracking"]', copilot.call_args_list[2].args[0])
            for artifact in generated:
                output = workspace / artifact.relative_path
                self.assertTrue(output.is_file())
                self.assertEqual(3, len(Presentation(output).slides))


if __name__ == "__main__":
    unittest.main()