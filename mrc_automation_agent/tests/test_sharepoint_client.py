import unittest

from mrc_automation_agent.sharepoint_client import _excel_web_url


class SharePointClientTests(unittest.TestCase):
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