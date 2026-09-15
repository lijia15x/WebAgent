import asyncio
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

from openpyxl import load_workbook
from pptx import Presentation
from pptx.enum.text import MSO_AUTO_SIZE
from pptx.util import Pt

from common.skills.copilot_sdk.copilot_sdk_client import ask_copilot

from .artifact_store import WORKSPACE_ROOT, register_ppt
from .config import MrcConfig
from .models import MrcArtifact


SUMMARY_FONT_SIZE_PT = 10
PAGE3_FONT_SIZE_PT = 10
PAGE3_MAX_CHAR_COUNT = 4900
TEMPLATE_PATH = (
    Path(__file__).resolve().parent
    / "templates"
    / "DMR Johnson City SXT Executive Summary V2.pptx"
)

PAGE2_PROMPT = """You are preparing slide 2 of an executive summary PPT from the attached Excel workbook.
The workbook contains these worksheets: {sheet_names}.
Analyze the sheet or sheets containing execution status for {cycle_code}.
Do not assume a fixed worksheet name. Ignore administrative, lookup, and instruction sheets unless needed for context.
Return only valid JSON with this schema:
{{"executive_summary":[{{"bold_lead":"judgment","normal_detail":"supporting facts"}}],
"detail_sections":[{{"title":"engineering group","paragraphs":[{{"bold_lead":"judgment","normal_detail":"supporting facts"}}]}}]}}.
Use exactly 2 executive_summary paragraphs and the 2 engineering groups needing the most leadership attention,
with exactly 2 paragraphs per group. Use workbook facts, dates, quantities, status colors, risks, and milestones.
Do not use Markdown or code fences."""

PAGE3_PROMPT = """Create slide 3 detailed executive narrative for {cycle_code} from the attached Excel workbook.
The workbook contains these worksheets: {sheet_names}.
Identify the sheet or sheets containing the current execution status.
Do not assume a fixed worksheet name, header row, or column position. Use headers and values to identify engineering
groups, domains, status, risks, dates, and milestones for the requested week. Return only valid JSON with this schema:
{{"sections":[{{"title":"engineering group","paragraphs":[
{{"bold_lead":"synthesized conclusion","normal_detail":"supporting workbook facts",
"source":"worksheet name!L12"}}]}}]}}.
Include all major engineering groups with exactly 2 paragraphs each. Prioritize red, orange, and yellow risks,
consolidate green progress, and keep all returned text within {max_chars} characters. For every paragraph, source must
identify the most important original Excel evidence cell using the exact worksheet name and cell address. Prefer the
current-week status cell. Do not include a URL in source. No Markdown or code fences."""


def _parse_json_response(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("Copilot PPT response must be a JSON object")
    return payload


def _call_copilot_json(prompt: str, model: str, excel_path: Path) -> dict[str, Any]:
    content = asyncio.run(ask_copilot(prompt, model=model, files=[excel_path]))
    return _parse_json_response(content)


def _sheet_names(excel_path: Path) -> list[str]:
    workbook = load_workbook(excel_path, read_only=True, data_only=True)
    try:
        return workbook.sheetnames
    finally:
        workbook.close()


def _paragraphs(value: object, count: int | None = None) -> list[dict[str, str]]:
    normalized = []
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                lead = str(item.get("bold_lead") or item.get("lead") or "").strip()
                detail = str(item.get("normal_detail") or item.get("detail") or "").strip()
                source = str(item.get("source") or item.get("reference") or "").strip()
            else:
                lead, detail, source = str(item).strip(), "", ""
            if lead or detail:
                normalized.append(
                    {"bold_lead": lead, "normal_detail": detail, "source": source}
                )
    if count is not None:
        normalized = normalized[:count]
        while len(normalized) < count:
            normalized.append(
                {
                    "bold_lead": "No update available.",
                    "normal_detail": "",
                    "source": "",
                }
            )
    return normalized


def _prepare_text_frame(shape):
    frame = shape.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT
    frame.margin_left = frame.margin_right = frame.margin_top = frame.margin_bottom = Pt(0)
    return frame


def _source_link(source_url: str, source: str) -> str:
    encoded_source = quote(source, safe="")
    if "?" in source_url:
        return f"{source_url}&activeCell={encoded_source}&wdActiveCell={encoded_source}"
    return f"{source_url}?web=1&activeCell={encoded_source}&wdActiveCell={encoded_source}"


def _add_paragraph(
    frame,
    index: int,
    lead: str,
    detail: str = "",
    level: int = 0,
    source: str = "",
    source_url: str = "",
) -> int:
    paragraph = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
    paragraph.level = level
    paragraph.space_before = Pt(0 if index == 0 else 6)
    paragraph.space_after = Pt(0)
    paragraph.line_spacing = 1.0
    for text, bold in ((lead, True), ((" " if lead and detail else "") + detail, False)):
        if text:
            run = paragraph.add_run()
            run.text = text
            run.font.size = Pt(SUMMARY_FONT_SIZE_PT)
            run.font.bold = bold
    if source and source_url:
        run = paragraph.add_run()
        run.text = f" [{source}]"
        run.font.size = Pt(SUMMARY_FONT_SIZE_PT)
        run.font.underline = True
        run.hyperlink.address = _source_link(source_url, source)
    return index + 1


def _set_sections(
    shape,
    sections: list[dict[str, Any]],
    font_size: int = SUMMARY_FONT_SIZE_PT,
    source_url: str = "",
) -> None:
    frame = _prepare_text_frame(shape)
    index = 0
    for section in sections:
        title = str(section.get("title") or "Engineering Update").strip()
        index = _add_paragraph(frame, index, title)
        for paragraph in _paragraphs(section.get("paragraphs"), count=2):
            index = _add_paragraph(
                frame,
                index,
                paragraph["bold_lead"],
                paragraph["normal_detail"],
                source=paragraph["source"],
                source_url=source_url,
            )
    for paragraph in frame.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(font_size)


def _text_shapes(slide) -> list[Any]:
    return [shape for shape in slide.shapes if getattr(shape, "has_text_frame", False)]


def _replace_week_tokens(slide, cycle_code: str) -> None:
    label = f"WW{cycle_code[-2:]} {cycle_code[:4]}"
    for shape in _text_shapes(slide):
        if shape.text and re.search(r"(?i)WW\s*\d{1,2}", shape.text):
            shape.text = re.sub(r"(?i)WW\s*\d{1,2}(?:[' -]?\d{2,4})?", label, shape.text)


def _update_presentation(
    template_path: Path,
    output_path: Path,
    cycle_code: str,
    page2: dict[str, Any],
    page3: dict[str, Any],
) -> None:
    presentation = Presentation(str(template_path))
    while len(presentation.slides) > 3:
        slide_id = list(presentation.slides._sldIdLst)[-1]
        presentation.part.drop_rel(slide_id.rId)
        presentation.slides._sldIdLst.remove(slide_id)
    if len(presentation.slides) < 3:
        raise ValueError("PPT template must contain at least three slides")

    for slide in list(presentation.slides)[:3]:
        _replace_week_tokens(slide, cycle_code)

    page2_shapes = sorted(
        _text_shapes(presentation.slides[1]), key=lambda shape: len(shape.text or ""), reverse=True
    )
    if not page2_shapes:
        raise ValueError("PPT template slide 2 has no text area")
    summary = _paragraphs(page2.get("executive_summary"), count=2)
    _set_sections(page2_shapes[0], [{"title": "Executive Summary", "paragraphs": summary}])
    details = page2.get("detail_sections")
    if isinstance(details, list) and len(page2_shapes) > 1:
        _set_sections(page2_shapes[1], details[:2])

    page3_shapes = sorted(
        _text_shapes(presentation.slides[2]), key=lambda shape: len(shape.text or ""), reverse=True
    )
    if not page3_shapes:
        raise ValueError("PPT template slide 3 has no text area")
    sections = page3.get("sections")
    _set_sections(
        page3_shapes[0],
        sections if isinstance(sections, list) else [],
        PAGE3_FONT_SIZE_PT,
        source_url=str(page3.get("source_url") or ""),
    )
    presentation.save(str(output_path))


def generate_weekly_ppts(
    config: MrcConfig,
    cycle_code: str,
    excel_artifacts: list[MrcArtifact],
) -> list[MrcArtifact]:
    sources = sorted(
        (artifact for artifact in excel_artifacts if artifact.kind == "excel"),
        key=lambda artifact: artifact.file_name.casefold(),
    )
    if not sources:
        raise FileNotFoundError("No weekly Excel workbooks are available for PPT generation")
    if not TEMPLATE_PATH.is_file():
        raise FileNotFoundError(f"PPT template does not exist: {TEMPLATE_PATH}")

    output_dir = WORKSPACE_ROOT / cycle_code / "ppt"
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = []
    for source in sources:
        excel_path = WORKSPACE_ROOT / source.relative_path
        sheet_names = json.dumps(_sheet_names(excel_path), ensure_ascii=False)
        page2 = _call_copilot_json(
            PAGE2_PROMPT.format(cycle_code=cycle_code, sheet_names=sheet_names),
            config.ppt_model,
            excel_path,
        )
        page3 = _call_copilot_json(
            PAGE3_PROMPT.format(
                cycle_code=cycle_code,
                sheet_names=sheet_names,
                max_chars=PAGE3_MAX_CHAR_COUNT,
            ),
            config.ppt_model,
            excel_path,
        )
        page3["source_url"] = source.source_url
        output_path = output_dir / f"{excel_path.stem}_generated.pptx"
        _update_presentation(TEMPLATE_PATH, output_path, cycle_code, page2, page3)
        generated.append(register_ppt(cycle_code, output_path, source.file_name))
    return generated