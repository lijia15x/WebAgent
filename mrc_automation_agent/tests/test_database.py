import unittest
from contextlib import contextmanager

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


if __name__ == "__main__":
    unittest.main()