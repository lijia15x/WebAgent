import unittest
from unittest.mock import Mock, patch

from mrc_automation_agent.sharepoint_client import SharePointClient, _excel_web_url


class SharePointClientTests(unittest.TestCase):
    def test_upload_ppts_targets_configured_workweek_folder(self) -> None:
        config = Mock(
            sharepoint_folder_template=(
                "/sites/DHE/Shared Documents/DHE Execution MRC/{cycle_code}"
            )
        )
        client = SharePointClient(config)
        context = Mock()
        folder = context.web.get_folder_by_server_relative_url.return_value
        upload = folder.upload_file.return_value

        with patch.object(client, "_create_context", return_value=context):
            uploaded = client.upload_ppts(
                "2026WW40", [("Weekly Summary.pptx", b"ppt-content")]
            )

        context.web.get_folder_by_server_relative_url.assert_called_once_with(
            "/sites/DHE/Shared Documents/DHE Execution MRC/2026WW40"
        )
        folder.upload_file.assert_called_once_with(
            "Weekly Summary.pptx", b"ppt-content"
        )
        upload.execute_query.assert_called_once_with()
        self.assertEqual(["Weekly Summary.pptx"], uploaded)

    def test_builds_excel_online_url(self) -> None:
        url = _excel_web_url(
            "https://intel.sharepoint.com/sites/DHE",
            "/sites/DHE/Shared Documents/MRC Status.xlsx",
        )

        self.assertEqual(
            "https://intel.sharepoint.com/sites/DHE/Shared Documents/MRC Status.xlsx?web=1",
            url,
        )

    def test_preserves_query_and_replaces_web_mode(self) -> None:
        url = _excel_web_url(
            "https://intel.sharepoint.com/sites/DHE",
            "/sites/DHE/MRC.xlsx?download=0&web=0",
        )

        self.assertIn("download=0", url)
        self.assertIn("web=1", url)
        self.assertEqual(1, url.count("web="))


if __name__ == "__main__":
    unittest.main()