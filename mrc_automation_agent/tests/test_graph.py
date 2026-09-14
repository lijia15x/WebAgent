import unittest

from mrc_automation_agent.config import MrcConfig
from mrc_automation_agent.graph import create_mrc_graph
from mrc_automation_agent.models import EmailDraft, ProjectRecord, WorkbookFile


def make_config() -> MrcConfig:
    return MrcConfig(
        database_host="localhost",
        database_port=3306,
        database_name="test",
        database_user="test",
        database_password="test",
        sharepoint_site_url="https://example.invalid",
        sharepoint_folder_template="/mrc/{cycle_code}",
        sharepoint_tenant="test",
        sharepoint_client_id="test",
        sharepoint_thumbprint="test",
        sharepoint_certificate_path="test.pfx",
        sharepoint_certificate_password="test",
    )


class FakeDatabase:
    def __init__(self) -> None:
        self.completed = None
        self.failed = None

    def create_scan(self, cycle_code: str, triggered_by: str) -> int:
        self.created = (cycle_code, triggered_by)
        return 42

    def complete_scan(self, *args) -> None:
        self.completed = args

    def fail_scan(self, scan_run_id: int, message: str) -> None:
        self.failed = (scan_run_id, message)


class FakeSharePoint:
    def __init__(self) -> None:
        self.calls = 0

    def fetch_workbooks(self, cycle_code: str) -> list[WorkbookFile]:
        self.calls += 1
        return [WorkbookFile("MRC.xlsx", "https://example.invalid/MRC.xlsx", b"fake")]


class MrcGraphTests(unittest.TestCase):
    def test_fixed_graph_builds_monday_draft_for_missing_owner(self) -> None:
        database = FakeDatabase()
        sharepoint = FakeSharePoint()
        events: list[dict] = []
        records = [
            ProjectRecord("MRC.xlsx", "url", "Sheet1", 2, "Core", "Atlas", "Alex", "alex@example.com", ""),
            ProjectRecord("MRC.xlsx", "url", "Sheet1", 3, "Data", "Metrics", "Maya", "maya@example.com", "Done"),
        ]

        def parser(workbook, header_search_rows):
            return records

        def renderer(cycle_code, scan_run_id, eligible, reminder_type):
            self.assertEqual(["alex@example.com"], [item.owner_email for item in eligible])
            return [EmailDraft("Alex", "alex@example.com", "Subject", "<p>Body</p>", 1, "key")]

        graph = create_mrc_graph(
            make_config(), database, sharepoint, events.append, parser, renderer
        )
        result = graph.invoke(
            {"cycle_code": "2026WW38", "reminder_type": "monday", "triggered_by": "manual"}
        )

        self.assertEqual("", result["error"])
        self.assertEqual(1, sharepoint.calls)
        self.assertEqual(2, len(database.completed[2]))
        self.assertEqual(1, len(database.completed[3]))
        self.assertEqual(
            [
                "prepare_cycle",
                "create_scan",
                "fetch_sharepoint",
                "parse_workbooks",
                "select_recipients",
                "build_drafts",
                "persist_snapshot",
            ],
            [event["stage"] for event in events],
        )

    def test_invalid_cycle_stops_before_external_calls(self) -> None:
        database = FakeDatabase()
        sharepoint = FakeSharePoint()
        graph = create_mrc_graph(make_config(), database, sharepoint)

        result = graph.invoke(
            {"cycle_code": "invalid", "reminder_type": "manual", "triggered_by": "manual"}
        )

        self.assertIn("cycle_code", result["error"])
        self.assertEqual(0, sharepoint.calls)
        self.assertIsNone(database.completed)


if __name__ == "__main__":
    unittest.main()