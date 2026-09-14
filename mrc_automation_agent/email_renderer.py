from collections import defaultdict
from html import escape
from pathlib import Path

from .models import EmailDraft, ProjectRecord


TEMPLATE_PATH = Path(__file__).with_name("status_reminder_email.html")


def render_drafts(
    cycle_code: str,
    scan_run_id: int,
    records: list[ProjectRecord],
    reminder_type: str,
) -> list[EmailDraft]:
    grouped: dict[str, list[ProjectRecord]] = defaultdict(list)
    for record in records:
        if record.owner_email:
            grouped[record.owner_email].append(record)

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    drafts: list[EmailDraft] = []
    for owner_email, owner_records in sorted(grouped.items()):
        first = owner_records[0]
        function_teams = ", ".join(
            dict.fromkeys(record.function_team for record in owner_records if record.function_team)
        )
        projects = ", ".join(dict.fromkeys(record.project_name for record in owner_records))
        workbook_names = ", ".join(
            dict.fromkeys(record.workbook_name for record in owner_records)
        )
        body_html = (
            template.replace("{{OWNER}}", escape(first.owner_name or owner_email))
            .replace("{{FUNCTION_TEAM}}", escape(function_teams))
            .replace("{{PROJECT_NAME}}", escape(projects))
            .replace("{{EXCEL_LINK}}", escape(first.workbook_url, quote=True))
            .replace("{{EXCEL_FILE_NAME}}", escape(workbook_names))
        )
        drafts.append(
            EmailDraft(
                owner_name=first.owner_name,
                owner_email=owner_email,
                subject=f"Action required: update project status for {cycle_code}",
                body_html=body_html,
                project_count=len(owner_records),
                idempotency_key=(
                    f"{cycle_code}:{scan_run_id}:{reminder_type}:{owner_email}"
                ),
            )
        )
    return drafts
