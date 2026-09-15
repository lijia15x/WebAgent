import unittest
from contextlib import contextmanager

from mrc_automation_agent.database import MrcDatabase


class FakeCursor:
    def __init__(self) -> None:
        self.statements: list[str] = []
        self.lastrowid = 17

    def execute(self, statement, parameters=None) -> None:
        self.statements.append(" ".join(statement.split()))

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


if __name__ == "__main__":
    unittest.main()