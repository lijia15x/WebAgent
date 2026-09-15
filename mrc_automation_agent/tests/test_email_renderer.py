import unittest

from mrc_automation_agent.email_renderer import render_drafts
from mrc_automation_agent.models import ProjectRecord


class EmailRendererTests(unittest.TestCase):
    def test_includes_each_owner_workbook_link(self) -> None:
        records = [
            ProjectRecord("One.xlsx", "https://example.invalid/one", "Status", 2, "Core", "A", "Alex", "alex@example.com", ""),
            ProjectRecord("Two.xlsx", "https://example.invalid/two", "Status", 3, "Core", "B", "Alex", "alex@example.com", ""),
        ]

        draft = render_drafts("2026WW38", 42, records, "reminder")[0]

        self.assertIn("One.xlsx", draft.body_html)
        self.assertIn("Two.xlsx", draft.body_html)
        self.assertIn("https://example.invalid/one", draft.body_html)
        self.assertIn("https://example.invalid/two", draft.body_html)


if __name__ == "__main__":
    unittest.main()