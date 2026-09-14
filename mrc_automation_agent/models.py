from dataclasses import dataclass


@dataclass(frozen=True)
class WorkbookFile:
    name: str
    source_url: str
    content: bytes


@dataclass(frozen=True)
class ProjectRecord:
    workbook_name: str
    workbook_url: str
    sheet_name: str
    source_row: int
    function_team: str
    project_name: str
    owner_name: str
    owner_email: str
    status_comments: str

    @property
    def is_missing_update(self) -> bool:
        return not self.status_comments.strip()


@dataclass(frozen=True)
class EmailDraft:
    owner_name: str
    owner_email: str
    subject: str
    body_html: str
    project_count: int
    idempotency_key: str
