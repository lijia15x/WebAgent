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
PAGE2_DETAIL_TEXTBOX_LEFT = 588135
PAGE2_DETAIL_TEXTBOX_TOP = 2871854
PAGE2_DETAIL_TEXTBOX_WIDTH = 11168038
PAGE2_DETAIL_TEXTBOX_HEIGHT = 2808461
DEFAULT_TEMPLATE_PATH = (
    Path(__file__).resolve().parent
    / "templates"
    / "DMR Johnson City SXT Executive Summary V2.pptx"
)
DMR_RS_TEMPLATE_PATH = (
    Path(__file__).resolve().parent / "templates" / "DMR-RS_template.pptx"
)
TEMPLATE_PATH = DEFAULT_TEMPLATE_PATH

PAGE2_PROMPT = """You are preparing slide 2 of an executive summary PPT from the attached Excel workbook.

Reporting cycle: {cycle_code}
Workbook worksheets: {sheet_names}

Identify the execution-status worksheet and the current reporting-week columns. Convert {cycle_code} from YYYYWWNN
to the workbook label WWNN'YY when necessary. For example, 2026WW40 corresponds to WW40'26.
A merged week heading may cover two columns:
- Status Comments / Status & Problem Statement
- Mitigation Plan

Use the Platform and Engineering Domain columns as the reporting hierarchy. Platform is the engineering group;
Engineering Domain is the project or domain within that group. Carry merged or blank Platform cells downward until
the next non-empty Platform value.

Treat the workbook's color-grading key as authoritative:
- R = Blocked: critical issue with no mitigation plan
- O = At Risk: mitigation plan is still work in progress
- Y = On Track: approved mitigation plan exists
- G = On Track: no issue
- Done = all deliverables completed
- N/A = not applicable

The status columns such as Schedule, Resource and Spending, Platform PCOS, NUDDs, Quality, and Technical Execution
are independent health dimensions. Rank attention using R > O > Y > G > Done; ignore N/A.
Do not describe Y as blocked or at risk.

Use the current-week status and mitigation columns as the primary narrative evidence. Use older weekly columns only
to identify an explicit trend or change. If the current-week status cell is blank, state that no current-week
narrative update was provided; never substitute historical text as a current update.

Return only valid JSON with this schema:
{{"executive_summary":[
  {{"bold_lead":"leadership judgment","normal_detail":"supporting workbook facts"}},
  {{"bold_lead":"leadership judgment","normal_detail":"supporting workbook facts"}}
],
"detail_sections":[
  {{"title":"Platform name","paragraphs":[
    {{"bold_lead":"priority judgment","normal_detail":"supporting Domain, status dimension, current-week facts and mitigation"}},
    {{"bold_lead":"priority judgment","normal_detail":"supporting Domain, status dimension, current-week facts and mitigation"}}
  ]}}
]}}

Requirements:
- Produce exactly 2 executive_summary paragraphs.
- Select exactly 2 Platforms requiring the most leadership attention.
- Produce exactly 2 paragraphs for each selected Platform.
- Name the relevant Engineering Domain and status dimension in supporting details.
- Prioritize blocked and at-risk items, missing mitigation, schedule impact, dependencies, and dated milestones.
- Consolidate healthy progress instead of listing every green item.
- Do not invent facts, dates, quantities, status meanings, risks, causes, or mitigations.
- Do not mention cell addresses in slide 2.
- Do not use Markdown or code fences."""

PAGE3_PROMPT = """Create slide 3 detailed executive narrative for {cycle_code} from the attached Excel workbook.

Workbook worksheets: {sheet_names}

Identify the execution-status worksheet and the current reporting-week columns. Convert {cycle_code} from YYYYWWNN
to the workbook label WWNN'YY when necessary. For example, 2026WW40 corresponds to WW40'26.
A merged week heading may cover the Status & Problem Statement column and its Mitigation Plan column.

Organize the narrative by Platform and describe the Engineering Domain rows within each Platform.
Carry merged or blank Platform cells downward until the next non-empty Platform value.

Treat the workbook's color-grading key as authoritative:
- R = Blocked: critical issue with no mitigation plan
- O = At Risk: mitigation plan is still work in progress
- Y = On Track: approved mitigation plan exists
- G = On Track: no issue
- Done = all deliverables completed
- N/A = not applicable

Evaluate Schedule, Resource and Spending, Platform PCOS, NUDDs, Quality, and Technical Execution independently.
Use severity R > O > Y > G > Done and ignore N/A. Do not describe Y as blocked or at risk.

Use the current-week Status & Problem Statement and Mitigation Plan cells as primary evidence.
Historical week columns may be used only for an explicit trend comparison.
If the current-week narrative is blank, say that no current-week update was provided and rely only on the structured
status cells; never present historical text as a current-week update.

Return only valid JSON with this schema:
{{"sections":[
  {{"title":"Platform name","paragraphs":[
    {{"bold_lead":"synthesized conclusion","normal_detail":"supporting Domain, status dimension, current-week facts and mitigation","source":"exact worksheet name!L12"}},
    {{"bold_lead":"synthesized conclusion","normal_detail":"supporting Domain, status dimension, current-week facts and mitigation","source":"exact worksheet name!E12"}}
  ]}}
]}}

Requirements:
- Include every major Platform represented in the execution-status table.
- Produce exactly 2 paragraphs per Platform.
- Prioritize R and O items, then Y items needing monitoring; consolidate G progress.
- Identify the Engineering Domain and affected status dimension.
- Mention concrete dates, quantities, dependencies, milestones, and mitigation only when present in the workbook.
- Keep all returned narrative text within {max_chars} characters.
- Every source must be an existing cell using the exact worksheet name and address.
- Prefer the current-week narrative or mitigation cell as the source.
- When no current-week narrative exists, cite the relevant structured status cell instead.
- Never cite a blank cell, merged placeholder cell, historical cell presented as current, or invented address.
- Do not include URLs, Markdown, or code fences."""


def _parse_json_response(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.IGNORECASE)
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("Copilot PPT response must be a JSON object")
    return payload


def _call_copilot_json(prompt: str, model: str, excel_path: Path) -> dict[str, Any]:
    content = asyncio.run(
        ask_copilot(prompt, model=model, files=[excel_path], workspace="")
    )
    return _parse_json_response(content)


def _sheet_names(excel_path: Path) -> list[str]:
    workbook = load_workbook(excel_path, read_only=True, data_only=True)
    try:
        return workbook.sheetnames
    finally:
        workbook.close()


def _template_path_for(file_name: str) -> Path:
    if "dmr-rs" in file_name.casefold():
        return DMR_RS_TEMPLATE_PATH
    return DEFAULT_TEMPLATE_PATH


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


def _first_font_size(shape):
    for paragraph in shape.text_frame.paragraphs:
        for run in paragraph.runs:
            if run.font.size is not None:
                return run.font.size
    return None


def _set_text_preserving_font_size(shape, text: str) -> None:
    font_size = _first_font_size(shape)
    shape.text = text
    if font_size is not None:
        for paragraph in shape.text_frame.paragraphs:
            for run in paragraph.runs:
                run.font.size = font_size


def _replace_week_tokens(slide, label: str) -> None:
    for shape in _text_shapes(slide):
        if shape.text and re.search(r"(?i)WW\s*\d{1,2}", shape.text):
            _set_text_preserving_font_size(
                shape,
                re.sub(
                    r"(?i)WW\s*\d{1,2}(?:\s*[‘’']?\s*\d{2,4})?",
                    label,
                    shape.text,
                ),
            )


def _update_page2(slide, cycle_code: str, page2: dict[str, Any]) -> None:
    long_text_shapes = []
    dashboard_label = f"WW{cycle_code[-2:]}'{cycle_code[:4]}"
    for shape in _text_shapes(slide):
        text = (shape.text or "").strip()
        if not text:
            continue
        if re.search(r"(?i)platform\s+dashboard", text):
            _replace_week_tokens_for_shape(shape, dashboard_label)
        elif len(text) > 80:
            long_text_shapes.append(shape)

    if not long_text_shapes:
        raise ValueError("PPT template slide 2 has no summary text area")
    summary = _paragraphs(page2.get("executive_summary"), count=2)
    _set_sections(long_text_shapes[0], [{"title": "Executive Summary", "paragraphs": summary}])

    details = page2.get("detail_sections")
    if isinstance(details, list):
        detail_shape = (
            long_text_shapes[1]
            if len(long_text_shapes) > 1
            else slide.shapes.add_textbox(
                PAGE2_DETAIL_TEXTBOX_LEFT,
                PAGE2_DETAIL_TEXTBOX_TOP,
                PAGE2_DETAIL_TEXTBOX_WIDTH,
                PAGE2_DETAIL_TEXTBOX_HEIGHT,
            )
        )
        _set_sections(detail_shape, details[:2])


def _replace_week_tokens_for_shape(shape, label: str) -> None:
    _set_text_preserving_font_size(
        shape,
        re.sub(
            r"(?i)WW\s*\d{1,2}(?:\s*[‘’']?\s*\d{2,4})?",
            label,
            shape.text,
        ),
    )


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

    dashboard_label = f"WW{cycle_code[-2:]}'{cycle_code[:4]}"
    _replace_week_tokens(presentation.slides[0], dashboard_label)
    _update_page2(presentation.slides[1], cycle_code, page2)
    _replace_week_tokens(presentation.slides[2], dashboard_label)

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
    output_dir = WORKSPACE_ROOT / cycle_code / "ppt"
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = []
    for source in sources:
        excel_path = WORKSPACE_ROOT / source.relative_path
        template_path = _template_path_for(source.file_name)
        if not template_path.is_file():
            raise FileNotFoundError(f"PPT template does not exist: {template_path}")
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
        output_path = output_dir / f"{excel_path.stem}_AI_generated.pptx"
        _update_presentation(template_path, output_path, cycle_code, page2, page3)
        generated.append(register_ppt(cycle_code, output_path, source.file_name))
    return generated