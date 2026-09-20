from collections import defaultdict
from html import escape
from pathlib import Path
import re

from .models import EmailDraft, ProjectRecord


TEMPLATE_PATH = Path(__file__).with_name("templates") / "status_reminder_email.html"


def _mrc_project_name(workbook_name: str) -> str:
    name = Path(workbook_name).stem
    name = re.sub(r"\b(?:\d{2}'\s*)?WW\s*\d{1,2}(?:'\s*\d{2})?\b", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s*\(Template\)\s*$", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+Status\s*$", "", name, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", name).strip(" -_")


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
        projects = ", ".join(dict.fromkeys(record.project_name for record in owner_records))
        workbooks = {
            record.workbook_name: record.workbook_url for record in owner_records
        }
        mrc_projects = ", ".join(
            dict.fromkeys(_mrc_project_name(name) for name in workbooks)
        )
        workbook_links = "<br>".join(
            f'<a href="{escape(url, quote=True)}" style="color:#0f766e; font-weight:700; text-decoration:none;">{escape(name)}</a>'
            for name, url in workbooks.items()
        )
        first_workbook_url = next(iter(workbooks.values()), "")
        body_html = (
            template.replace("{{OWNER}}", escape(first.owner_name or owner_email))
            .replace("{{PROJECT_NAME}}", escape(projects))
            .replace("{{MRC_PROJECT}}", escape(mrc_projects))
            .replace("{{EXCEL_LINKS}}", workbook_links)
            .replace("{{EXCEL_LINK}}", escape(first_workbook_url, quote=True))
        )
        drafts.append(
            EmailDraft(
                owner_name=first.owner_name,
                owner_email=owner_email,
                subject=f'Action Required: update the "{mrc_projects}" MRC status.',
                body_html=body_html,
                project_count=len(owner_records),
                idempotency_key=(
                    f"{cycle_code}:{scan_run_id}:{reminder_type}:{owner_email}"
                ),
            )
        )
    return drafts
