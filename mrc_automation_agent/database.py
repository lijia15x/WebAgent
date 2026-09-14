from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from .config import MrcConfig
from .models import EmailDraft, ProjectRecord


class MrcDatabase:
    def __init__(self, config: MrcConfig) -> None:
        self._config = config

    @contextmanager
    def _connection(self) -> Iterator[Any]:
        self._config.require_database()
        import mysql.connector

        connection = mysql.connector.connect(
            host=self._config.database_host,
            port=self._config.database_port,
            database=self._config.database_name,
            user=self._config.database_user,
            password=self._config.database_password,
            charset="utf8mb4",
            connection_timeout=10,
        )
        try:
            yield connection
        finally:
            connection.close()

    def create_scan(self, cycle_code: str, triggered_by: str) -> int:
        with self._connection() as connection:
            cursor = connection.cursor()
            try:
                connection.start_transaction()
                cursor.execute(
                    """
                    INSERT INTO reporting_cycles (cycle_code)
                    VALUES (%s)
                    ON DUPLICATE KEY UPDATE cycle_code = VALUES(cycle_code)
                    """,
                    (cycle_code,),
                )
                cursor.execute(
                    """
                    INSERT INTO scan_runs (cycle_code, status, triggered_by)
                    VALUES (%s, 'running', %s)
                    """,
                    (cycle_code, triggered_by),
                )
                scan_run_id = int(cursor.lastrowid)
                connection.commit()
                return scan_run_id
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def complete_scan(
        self,
        scan_run_id: int,
        cycle_code: str,
        records: list[ProjectRecord],
        drafts: list[EmailDraft],
        files_found: int,
        reminder_type: str,
    ) -> None:
        owners = {record.owner_email for record in records if record.owner_email}
        missing_comments = sum(record.is_missing_update for record in records)
        with self._connection() as connection:
            cursor = connection.cursor()
            try:
                connection.start_transaction()
                cursor.executemany(
                    """
                    INSERT INTO scan_items (
                        scan_run_id, workbook_name, workbook_url, sheet_name,
                        source_row, function_team, project_name, owner_name,
                        owner_email, status_comments
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        (
                            scan_run_id,
                            record.workbook_name,
                            record.workbook_url,
                            record.sheet_name,
                            record.source_row,
                            record.function_team or None,
                            record.project_name,
                            record.owner_name or None,
                            record.owner_email or None,
                            record.status_comments or None,
                        )
                        for record in records
                    ],
                )
                cursor.executemany(
                    """
                    INSERT INTO email_deliveries (
                        cycle_code, scan_run_id, owner_email, reminder_type,
                        status, subject, body_html, idempotency_key
                    ) VALUES (%s, %s, %s, %s, 'draft', %s, %s, %s)
                    ON DUPLICATE KEY UPDATE id = id
                    """,
                    [
                        (
                            cycle_code,
                            scan_run_id,
                            draft.owner_email,
                            reminder_type,
                            draft.subject,
                            draft.body_html,
                            draft.idempotency_key,
                        )
                        for draft in drafts
                    ],
                )
                cursor.execute(
                    """
                    UPDATE scan_runs
                    SET status = 'succeeded', completed_at = CURRENT_TIMESTAMP(6),
                        files_found = %s, owners_found = %s, missing_comments = %s
                    WHERE id = %s
                    """,
                    (files_found, len(owners), missing_comments, scan_run_id),
                )
                cursor.execute(
                    """
                    UPDATE reporting_cycles SET latest_scan_id = %s
                    WHERE cycle_code = %s
                    """,
                    (scan_run_id, cycle_code),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                cursor.close()

    def fail_scan(self, scan_run_id: int, message: str) -> None:
        with self._connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    """
                    UPDATE scan_runs
                    SET status = 'failed', completed_at = CURRENT_TIMESTAMP(6),
                        error_message = %s
                    WHERE id = %s
                    """,
                    (message[:65535], scan_run_id),
                )
                connection.commit()
            finally:
                cursor.close()

    def get_automation_enabled(self) -> bool:
        with self._connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute("SELECT enabled FROM automation_settings WHERE id = 1")
                row = cursor.fetchone()
                return bool(row and row["enabled"])
            finally:
                cursor.close()

    def set_automation_enabled(self, enabled: bool) -> None:
        with self._connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(
                    "UPDATE automation_settings SET enabled = %s WHERE id = 1",
                    (enabled,),
                )
                connection.commit()
            finally:
                cursor.close()

    def get_latest_scan(self, cycle_code: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            cursor = connection.cursor(dictionary=True)
            try:
                cursor.execute(
                    """
                    SELECT id, cycle_code, status, triggered_by, started_at,
                           completed_at, files_found, owners_found, missing_comments
                    FROM scan_runs
                    WHERE cycle_code = %s AND status = 'succeeded'
                    ORDER BY completed_at DESC
                    LIMIT 1
                    """,
                    (cycle_code,),
                )
                scan = cursor.fetchone()
                if scan is None:
                    return None
                cursor.execute(
                    """
                    SELECT DISTINCT workbook_name
                    FROM scan_items
                    WHERE scan_run_id = %s
                    ORDER BY workbook_name
                    """,
                    (scan["id"],),
                )
                scan["workbook_names"] = [
                    row["workbook_name"] for row in cursor.fetchall()
                ]
                cursor.execute(
                    """
                    SELECT delivery.owner_email, delivery.subject,
                           delivery.body_html, delivery.reminder_type,
                           delivery.status, COALESCE(items.owner_name, '') AS owner_name,
                           COALESCE(items.project_count, 0) AS project_count
                    FROM email_deliveries AS delivery
                    LEFT JOIN (
                        SELECT scan_run_id, owner_email, MAX(owner_name) AS owner_name,
                               COUNT(*) AS project_count
                        FROM scan_items
                        WHERE scan_run_id = %s
                        GROUP BY scan_run_id, owner_email
                    ) AS items
                      ON items.scan_run_id = delivery.scan_run_id
                     AND items.owner_email = delivery.owner_email
                    WHERE delivery.scan_run_id = %s
                    ORDER BY delivery.owner_email
                    """,
                    (scan["id"], scan["id"]),
                )
                scan["drafts"] = cursor.fetchall()
                return scan
            finally:
                cursor.close()