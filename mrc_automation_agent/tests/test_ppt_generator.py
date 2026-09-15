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
                        {
                            "bold_lead": "Stable.",
                            "normal_detail": "Milestones met.",
                            "source": "Status WW38!L12",
                        },
                        {
                            "bold_lead": "Watch.",
                            "normal_detail": "Supplier timing.",
                            "source": "Status WW38!L18",
                        },
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
                MrcArtifact(
                    "excel",
                    execution.name,
                    execution.relative_to(workspace).as_posix(),
                    source_url="https://example.invalid/execution.xlsx?web=1",
                ),
                MrcArtifact(
                    "excel",
                    tracking.name,
                    tracking.relative_to(workspace).as_posix(),
                    source_url="https://example.invalid/tracking.xlsx?web=1",
                ),
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
            expected_source_urls = {
                execution.name: "https://example.invalid/execution.xlsx?web=1",
                tracking.name: "https://example.invalid/tracking.xlsx?web=1",
            }
            for artifact in generated:
                output = workspace / artifact.relative_path
                self.assertTrue(output.is_file())
                presentation = Presentation(output)
                self.assertEqual(3, len(presentation.slides))
                hyperlinks = [
                    run.hyperlink.address
                    for shape in presentation.slides[2].shapes
                    if getattr(shape, "has_text_frame", False)
                    for paragraph in shape.text_frame.paragraphs
                    for run in paragraph.runs
                    if run.hyperlink.address
                ]
                self.assertEqual(2, len(hyperlinks))
                self.assertTrue(
                    hyperlinks[0].startswith(expected_source_urls[artifact.source_workbook_name])
                )
                self.assertIn("activeCell=Status%20WW38%21L12", hyperlinks[0])
                self.assertIn("wdActiveCell=Status%20WW38%21L12", hyperlinks[0])

    def test_source_link_opens_sharepoint_workbook_in_web_mode(self) -> None:
        link = ppt_generator._source_link(
            "https://example.invalid/MRC%20WW38.xlsx", "Status WW38!L12"
        )

        self.assertEqual(
            "https://example.invalid/MRC%20WW38.xlsx?web=1"
            "&activeCell=Status%20WW38%21L12"
            "&wdActiveCell=Status%20WW38%21L12",
            link,
        )


if __name__ == "__main__":
    unittest.main()