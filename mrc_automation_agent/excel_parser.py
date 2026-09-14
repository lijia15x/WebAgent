import re
from io import BytesIO
from typing import Any

from .models import ProjectRecord, WorkbookFile


class WorkbookFormatError(ValueError):
    pass


HEADER_ALIASES = {
    "function_team": {"functionteam", "group", "team"},
    "project_name": {"project", "projectname"},
    "owner_name": {"owner", "ownername", "projectowner"},
    "owner_email": {"owneremail", "projectowneremail", "email"},
    "status_comments": {"comments", "statuscomment", "statuscomments"},
}
REQUIRED_HEADERS = {"function_team", "project_name", "owner_email", "status_comments"}


def _normalize_header(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value or "").strip().lower())


def _header_name(value: Any) -> str | None:
    normalized = _normalize_header(value)
    return next(
        (name for name, aliases in HEADER_ALIASES.items() if normalized in aliases),
        None,
    )


def _find_headers(worksheet, search_rows: int) -> tuple[int, dict[str, int]]:
    for row_number, row in enumerate(
        worksheet.iter_rows(min_row=1, max_row=search_rows, values_only=True),
        start=1,
    ):
        columns = {
            name: column
            for column, value in enumerate(row)
            if (name := _header_name(value)) is not None
        }
        if REQUIRED_HEADERS.issubset(columns):
            return row_number, columns
    raise WorkbookFormatError(
        f"Could not find required headers in the first {search_rows} rows"
    )


def parse_workbook(workbook: WorkbookFile, header_search_rows: int) -> list[ProjectRecord]:
    from openpyxl import load_workbook

    excel = load_workbook(BytesIO(workbook.content), read_only=True, data_only=True)
    try:
        if not excel.worksheets:
            raise WorkbookFormatError(f"Workbook has no worksheets: {workbook.name}")
        worksheet = excel.worksheets[0]
        header_row, columns = _find_headers(worksheet, header_search_rows)
        records: list[ProjectRecord] = []
        for source_row, values in enumerate(
            worksheet.iter_rows(min_row=header_row + 1, values_only=True),
            start=header_row + 1,
        ):
            def value(name: str) -> str:
                column = columns.get(name)
                if column is None or column >= len(values):
                    return ""
                return str(values[column] or "").strip()

            project_name = value("project_name")
            if not project_name:
                continue
            records.append(
                ProjectRecord(
                    workbook_name=workbook.name,
                    workbook_url=workbook.source_url,
                    sheet_name=worksheet.title,
                    source_row=source_row,
                    function_team=value("function_team"),
                    project_name=project_name,
                    owner_name=value("owner_name"),
                    owner_email=value("owner_email").lower(),
                    status_comments=value("status_comments"),
                )
            )
        return records
    finally:
        excel.close()
