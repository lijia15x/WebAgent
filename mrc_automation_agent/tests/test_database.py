import unittest
from contextlib import contextmanager
from unittest.mock import Mock

from mrc_automation_agent.database import MrcDatabase


class FakeCursor:
    def __init__(self) -> None:
        self.statements: list[str] = []
        self.executemany_calls: list[tuple[str, list[tuple]]] = []
        self.rows: list[dict[str, str]] = []
        self.lastrowid = 17

    def execute(self, statement, parameters=None) -> None:
        self.statements.append(" ".join(statement.split()))

    def executemany(self, statement, parameters) -> None:
        normalized = " ".join(statement.split())
        values = list(parameters)
        self.statements.append(normalized)
        self.executemany_calls.append((normalized, values))

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def close(self) -> None:
        pass


class FakeConnection:
    def __init__(self) -> None:
        self.cursor_instance = FakeCursor()
        self.committed = False

    def cursor(self, **kwargs):
        return self.cursor_instance

    def start_transaction(self) -> None:
        pass

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        pass


class FakeMySqlDatabase:
    def __init__(self) -> None:
        self.connection_instance = FakeConnection()

    @contextmanager
    def connection(self):
        yield self.connection_instance


class MrcDatabaseTests(unittest.TestCase):
    def test_create_scan_uses_shared_connection_and_prefixed_tables(self) -> None:
        shared_database = FakeMySqlDatabase()
        database = MrcDatabase(shared_database)

        scan_run_id = database.create_scan("2026WW38", "manual")

        statements = "\n".join(
            shared_database.connection_instance.cursor_instance.statements
        )
        self.assertEqual(17, scan_run_id)
        self.assertIn("INSERT INTO mrc_reporting_cycles", statements)
        self.assertIn("INSERT INTO mrc_scan_runs", statements)
        self.assertNotIn("INSERT INTO reporting_cycles", statements)
        self.assertNotIn("INSERT INTO scan_runs", statements)
        self.assertTrue(shared_database.connection_instance.committed)

    def test_get_workbook_urls_returns_cycle_mapping(self) -> None:
        shared_database = FakeMySqlDatabase()
        cursor = shared_database.connection_instance.cursor_instance
        cursor.rows = [
            {
                "workbook_name": "MRC WW38.xlsx",
                "workbook_url": "https://example.invalid/MRC%20WW38.xlsx",
            }
        ]

        urls = MrcDatabase(shared_database).get_workbook_urls("2026WW38")

        self.assertEqual(
            {"MRC WW38.xlsx": "https://example.invalid/MRC%20WW38.xlsx"},
            urls,
        )
        self.assertIn(
            "FROM mrc_scan_workbooks WHERE cycle_code = %s",
            cursor.statements[-1],
        )

    def test_complete_scan_upserts_each_workbook_by_cycle_and_name(self) -> None:
        from mrc_automation_agent.models import WorkbookFile

        shared_database = FakeMySqlDatabase()
        database = MrcDatabase(shared_database)
        workbook = WorkbookFile(
            "MRC WW38.xlsx",
            "https://example.invalid/MRC%20WW38.xlsx",
            b"xlsx",
            "2026-09-15T08:00:00Z",
        )

        database.complete_scan(17, "2026WW38", [], [], 1, "reminder", [workbook])

        cursor = shared_database.connection_instance.cursor_instance
        workbook_calls = [
            call for call in cursor.executemany_calls if "mrc_scan_workbooks" in call[0]
        ]
        self.assertEqual(1, len(workbook_calls))
        statement, parameters = workbook_calls[0]
        self.assertIn("ON DUPLICATE KEY UPDATE", statement)
        self.assertEqual(
            [
                (
                    "2026WW38",
                    "MRC WW38.xlsx",
                    "https://example.invalid/MRC%20WW38.xlsx",
                    17,
                    "2026-09-15T08:00:00Z",
                )
            ],
            parameters,
        )
        self.assertTrue(shared_database.connection_instance.committed)

    def test_get_first_missing_draft_uses_source_order(self) -> None:
        shared_database = FakeMySqlDatabase()
        cursor = shared_database.connection_instance.cursor_instance
        cursor.rows = [{"owner_email": "first@example.com"}]
        database = MrcDatabase(shared_database)
        expected = {
            "owner_email": "first@example.com",
            "subject": "Reminder",
            "body_html": "<p>First owner</p>",
        }
        database.get_latest_scan = Mock(
            return_value={"id": 17, "drafts": [expected]}
        )

        result = database.get_first_missing_draft("2026WW38")

        self.assertIs(expected, result)
        statement = cursor.statements[-1]
        self.assertIn("status_comments IS NULL", statement)
        self.assertIn(
            "ORDER BY workbook_name, sheet_name, source_row, id", statement
        )

    def test_get_sendable_drafts_includes_all_owners_when_requested(self) -> None:
        database = MrcDatabase(FakeMySqlDatabase())
        drafts = [
            {"owner_email": "missing@example.com", "status": "draft", "missing_updates": 1},
            {"owner_email": "updated@example.com", "status": "draft", "missing_updates": 0},
        ]
        database.get_latest_scan = Mock(return_value={"drafts": drafts})

        self.assertEqual(drafts, database.get_sendable_drafts("2026WW38", True))

    def test_get_sendable_drafts_excludes_updated_owners_by_default(self) -> None:
        database = MrcDatabase(FakeMySqlDatabase())
        missing = {
            "owner_email": "missing@example.com",
            "status": "draft",
            "missing_updates": 1,
        }
        database.get_latest_scan = Mock(
            return_value={
                "drafts": [
                    missing,
                    {
                        "owner_email": "updated@example.com",
                        "status": "draft",
                        "missing_updates": 0,
                    },
                ]
            }
        )

        self.assertEqual(
            [missing], database.get_sendable_drafts("2026WW38", False)
        )


if __name__ == "__main__":
    unittest.main()