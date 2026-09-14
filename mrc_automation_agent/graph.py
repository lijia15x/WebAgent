import re
from collections.abc import Callable
from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from .config import MrcConfig
from .email_renderer import render_drafts
from .excel_parser import parse_workbook
from .models import EmailDraft, ProjectRecord, WorkbookFile


ReminderType = Literal["tuesday", "thursday", "monday", "manual"]


class MrcState(TypedDict, total=False):
    cycle_code: str
    reminder_type: ReminderType
    triggered_by: Literal["manual", "scheduler"]
    scan_run_id: int
    workbooks: list[WorkbookFile]
    records: list[ProjectRecord]
    eligible_records: list[ProjectRecord]
    drafts: list[EmailDraft]
    files_found: int
    error: str


def create_mrc_graph(
    config: MrcConfig,
    database: Any,
    sharepoint_client: Any,
    on_event: Callable[[dict[str, Any]], None] | None = None,
    workbook_parser: Callable[[WorkbookFile, int], list[ProjectRecord]] = parse_workbook,
    draft_renderer: Callable[
        [str, int, list[ProjectRecord], str], list[EmailDraft]
    ] = render_drafts,
):
    def emit(stage: str, message: str) -> None:
        if on_event is not None:
            on_event({"type": "progress", "stage": stage, "message": message})

    def prepare_cycle(state: MrcState) -> dict[str, Any]:
        cycle_code = state.get("cycle_code", "").strip().upper()
        reminder_type = state.get("reminder_type", "manual")
        if not re.fullmatch(r"\d{4}WW(?:0[1-9]|[1-4]\d|5[0-3])", cycle_code):
            return {"error": "cycle_code must use the format YYYYWW01-YYYYWW53"}
        if reminder_type not in {"tuesday", "thursday", "monday", "manual"}:
            return {"error": "Unsupported reminder type"}
        emit("prepare_cycle", f"Preparing reporting cycle {cycle_code}")
        return {
            "cycle_code": cycle_code,
            "reminder_type": reminder_type,
            "triggered_by": state.get("triggered_by", "manual"),
            "error": "",
        }

    def create_scan(state: MrcState) -> dict[str, Any]:
        if state.get("error"):
            return {}
        try:
            emit("create_scan", "Creating the scan record")
            return {
                "scan_run_id": database.create_scan(
                    state["cycle_code"], state["triggered_by"]
                )
            }
        except Exception as exc:
            return {"error": f"Could not create scan record: {exc}"}

    def fetch_sharepoint(state: MrcState) -> dict[str, Any]:
        if state.get("error"):
            return {}
        try:
            emit("fetch_sharepoint", "Downloading Excel workbooks from SharePoint")
            workbooks = sharepoint_client.fetch_workbooks(state["cycle_code"])
            if not workbooks:
                raise RuntimeError("No .xlsx workbooks were found for this cycle")
            return {"workbooks": workbooks, "files_found": len(workbooks)}
        except Exception as exc:
            return {"error": f"SharePoint scan failed: {exc}"}

    def parse_workbooks(state: MrcState) -> dict[str, Any]:
        if state.get("error"):
            return {}
        try:
            emit("parse_workbooks", "Parsing workbook rows by header name")
            parsed_records = [
                record
                for workbook in state.get("workbooks", [])
                for record in workbook_parser(workbook, config.header_search_rows)
            ]
            unique_records: dict[tuple[str, str, str], ProjectRecord] = {}
            for record in parsed_records:
                key = (
                    record.owner_email.casefold(),
                    record.function_team.casefold(),
                    record.project_name.casefold(),
                )
                existing = unique_records.get(key)
                if existing is None or (
                    existing.is_missing_update and not record.is_missing_update
                ):
                    unique_records[key] = record
            records = list(unique_records.values())
            return {"records": records}
        except Exception as exc:
            return {"error": f"Workbook parsing failed: {exc}"}

    def select_recipients(state: MrcState) -> dict[str, Any]:
        if state.get("error"):
            return {}
        emit("select_recipients", "Selecting one recipient per owner email")
        records = state.get("records", [])
        if state["reminder_type"] == "monday":
            missing_owners = {
                record.owner_email
                for record in records
                if record.owner_email and record.is_missing_update
            }
            records = [record for record in records if record.owner_email in missing_owners]
        return {"eligible_records": records}

    def build_drafts(state: MrcState) -> dict[str, Any]:
        if state.get("error"):
            return {}
        try:
            emit("build_drafts", "Generating individual email drafts")
            drafts = draft_renderer(
                state["cycle_code"],
                state["scan_run_id"],
                state.get("eligible_records", []),
                state["reminder_type"],
            )
            return {"drafts": drafts}
        except Exception as exc:
            return {"error": f"Draft generation failed: {exc}"}

    def persist_snapshot(state: MrcState) -> dict[str, Any]:
        if state.get("error"):
            return {}
        try:
            emit("persist_snapshot", "Saving the completed snapshot and drafts")
            database.complete_scan(
                state["scan_run_id"],
                state["cycle_code"],
                state.get("records", []),
                state.get("drafts", []),
                state.get("files_found", 0),
                state["reminder_type"],
            )
            return {}
        except Exception as exc:
            return {"error": f"Could not persist scan snapshot: {exc}"}

    def fail_scan(state: MrcState) -> dict[str, Any]:
        error = state.get("error", "MRC scan failed")
        scan_run_id = state.get("scan_run_id")
        if scan_run_id is not None:
            try:
                database.fail_scan(scan_run_id, error)
            except Exception:
                pass
        return {"error": error}

    def route(state: MrcState) -> str:
        return "fail_scan" if state.get("error") else "continue"

    graph = StateGraph(MrcState)
    graph.add_node("prepare_cycle", prepare_cycle)
    graph.add_node("create_scan", create_scan)
    graph.add_node("fetch_sharepoint", fetch_sharepoint)
    graph.add_node("parse_workbooks", parse_workbooks)
    graph.add_node("select_recipients", select_recipients)
    graph.add_node("build_drafts", build_drafts)
    graph.add_node("persist_snapshot", persist_snapshot)
    graph.add_node("fail_scan", fail_scan)
    graph.add_edge(START, "prepare_cycle")

    ordered_nodes = [
        "prepare_cycle",
        "create_scan",
        "fetch_sharepoint",
        "parse_workbooks",
        "select_recipients",
        "build_drafts",
    ]
    next_nodes = [
        "create_scan",
        "fetch_sharepoint",
        "parse_workbooks",
        "select_recipients",
        "build_drafts",
        "persist_snapshot",
    ]
    for node, next_node in zip(ordered_nodes, next_nodes):
        graph.add_conditional_edges(
            node,
            route,
            {"continue": next_node, "fail_scan": "fail_scan"},
        )
    graph.add_conditional_edges(
        "persist_snapshot",
        route,
        {"continue": END, "fail_scan": "fail_scan"},
    )
    graph.add_edge("fail_scan", END)
    return graph.compile()