import unittest

from mrc_automation_agent.config import MrcConfig
from mrc_automation_agent.graph import create_mrc_graph
from mrc_automation_agent.models import EmailDraft, MrcArtifact, ProjectRecord, WorkbookFile


def make_config() -> MrcConfig:
    return MrcConfig(
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
    def test_fixed_graph_builds_last_reminder_draft_for_missing_owner(self) -> None:
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

        def store(cycle_code, workbooks):
            return [MrcArtifact("excel", "MRC.xlsx", "2026WW38/excel/MRC.xlsx")]

        graph = create_mrc_graph(
            make_config(),
            database,
            sharepoint,
            events.append,
            parser,
            renderer,
            store,
            lambda *args: self.fail("Last reminder must not generate a PPT"),
        )
        result = graph.invoke(
            {"cycle_code": "2026WW38", "reminder_type": "lastreminder", "triggered_by": "manual"}
        )

        self.assertEqual("", result["error"])
        self.assertEqual(1, sharepoint.calls)
        self.assertEqual(2, len(database.completed[2]))
        self.assertEqual(1, len(database.completed[3]))
        self.assertEqual(["excel"], [item.kind for item in result["artifacts"]])
        self.assertEqual(
            [
                "prepare_cycle",
                "create_scan",
                "fetch_sharepoint",
                "store_workbooks",
                "parse_workbooks",
                "select_recipients",
                "build_drafts",
                "persist_snapshot",
            ],
            [event["stage"] for event in events],
        )

    def test_ppt_run_generates_presentation_without_email_drafts(self) -> None:
        database = FakeDatabase()
        generated = []

        def generate_ppt(config, cycle_code, artifacts):
            generated.append(cycle_code)
            return [
                MrcArtifact(
                    "ppt",
                    "MRC_generated.pptx",
                    "2026WW38/ppt/MRC_generated.pptx",
                    "MRC.xlsx",
                )
            ]

        graph = create_mrc_graph(
            make_config(),
            database,
            FakeSharePoint(),
            workbook_parser=lambda workbook, rows: [],
            draft_renderer=lambda *args: self.fail("PPT run must not render email drafts"),
            workbook_store=lambda cycle, workbooks: [
                MrcArtifact("excel", "MRC.xlsx", f"{cycle}/excel/MRC.xlsx")
            ],
            ppt_generator=generate_ppt,
        )
        result = graph.invoke(
            {"cycle_code": "2026WW38", "reminder_type": "ppt", "triggered_by": "manual"}
        )

        self.assertEqual("", result["error"])
        self.assertEqual(["2026WW38"], generated)
        self.assertEqual([], result["drafts"])
        self.assertEqual(["excel", "ppt"], [item.kind for item in result["artifacts"]])

    def test_reminder_scan_stores_excel_without_generating_ppt(self) -> None:
        database = FakeDatabase()
        sharepoint = FakeSharePoint()
        generated = []

        graph = create_mrc_graph(
            make_config(),
            database,
            sharepoint,
            workbook_parser=lambda workbook, rows: [],
            workbook_store=lambda cycle, workbooks: [
                MrcArtifact("excel", "MRC.xlsx", f"{cycle}/excel/MRC.xlsx")
            ],
            ppt_generator=lambda *args: generated.append(args),
        )
        result = graph.invoke(
            {"cycle_code": "2026WW38", "reminder_type": "reminder", "triggered_by": "manual"}
        )

        self.assertEqual("", result["error"])
        self.assertEqual([], generated)
        self.assertEqual(["excel"], [item.kind for item in result["artifacts"]])

    def test_invalid_cycle_stops_before_external_calls(self) -> None:
        database = FakeDatabase()
        sharepoint = FakeSharePoint()
        graph = create_mrc_graph(make_config(), database, sharepoint)

        result = graph.invoke(
            {"cycle_code": "invalid", "reminder_type": "reminder", "triggered_by": "manual"}
        )

        self.assertIn("cycle_code", result["error"])
        self.assertEqual(0, sharepoint.calls)
        self.assertIsNone(database.completed)

    def test_legacy_reminder_types_are_rejected(self) -> None:
        for reminder_type in ("manual", "tuesday", "thursday", "monday"):
            with self.subTest(reminder_type=reminder_type):
                database = FakeDatabase()
                sharepoint = FakeSharePoint()
                graph = create_mrc_graph(make_config(), database, sharepoint)

                result = graph.invoke(
                    {
                        "cycle_code": "2026WW38",
                        "reminder_type": reminder_type,
                        "triggered_by": "manual",
                    }
                )

                self.assertEqual("Unsupported reminder type", result["error"])
                self.assertEqual(0, sharepoint.calls)
                self.assertIsNone(database.completed)


if __name__ == "__main__":
    unittest.main()