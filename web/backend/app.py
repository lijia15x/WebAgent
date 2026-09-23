import asyncio
import json
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from mrc_automation_agent.artifact_store import resolve_artifact

from .agent_service import AgentBusyError, agent_service
from .mrc_service import MrcBusyError, mrc_service


class MessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class MrcScanRequest(BaseModel):
    cycle_code: str = Field(pattern=r"^\d{4}WW(?:0[1-9]|[1-4]\d|5[0-3])$")
    reminder_type: Literal["reminder", "lastreminder"] = "reminder"


class MrcMailRequest(BaseModel):
    include_all: bool = False


class MrcTestMailRequest(BaseModel):
    recipient_email: str = Field(
        min_length=3,
        max_length=320,
        pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$",
    )


class AutomationRequest(BaseModel):
    enabled: bool


app = FastAPI(title="Agent Desk", version="0.1.0")


@app.middleware("http")
async def disable_frontend_cache(request: Request, call_next):
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.endswith(
        (".html", ".js", ".css")
    ):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/agents")
async def list_agents() -> list[dict]:
    return [
        {
            "id": agent_service.agent_id,
            "name": "Jenkins Log Analyst",
            "description": "Analyze Jenkins failures with logs and workspace code.",
            "status": agent_service.status,
        },
        {
            "id": mrc_service.agent_id,
            "name": "MRC Automation",
            "description": "Scan MRC workbooks and prepare individual email drafts.",
            "status": mrc_service.status,
        },
    ]


@app.post("/api/agents/{agent_id}/messages", status_code=status.HTTP_202_ACCEPTED)
async def submit_message(agent_id: str, request: MessageRequest) -> dict:
    if agent_id != agent_service.agent_id:
        raise HTTPException(status_code=404, detail="Agent not found")
    try:
        run_id = await agent_service.submit(request.content.strip())
    except AgentBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"run_id": run_id, "status": "running"}


@app.post("/api/agents/mrc-automation/scans", status_code=status.HTTP_202_ACCEPTED)
async def submit_mrc_scan(request: MrcScanRequest) -> dict:
    try:
        run_id = await mrc_service.submit_scan(
            request.cycle_code, request.reminder_type
        )
    except MrcBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"run_id": run_id, "status": "running"}


@app.post("/api/agents/mrc-automation/cycles/{cycle_code}/ppt", status_code=status.HTTP_202_ACCEPTED)
async def generate_mrc_ppt(cycle_code: str) -> dict:
    try:
        run_id = await mrc_service.submit_ppt(cycle_code)
    except MrcBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"run_id": run_id, "status": "running"}


@app.post(
    "/api/agents/mrc-automation/cycles/{cycle_code}/ppt/upload",
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_mrc_ppt(cycle_code: str) -> dict:
    try:
        run_id = await mrc_service.submit_ppt_upload(cycle_code)
    except MrcBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"run_id": run_id, "status": "running"}


@app.post("/api/agents/mrc-automation/cycles/{cycle_code}/mail", status_code=status.HTTP_202_ACCEPTED)
async def send_mrc_mail(cycle_code: str, request: MrcMailRequest) -> dict:
    try:
        run_id = await mrc_service.submit_mail(cycle_code, request.include_all)
    except MrcBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"run_id": run_id, "status": "running"}


@app.post(
    "/api/agents/mrc-automation/cycles/{cycle_code}/test-mail",
    status_code=status.HTTP_202_ACCEPTED,
)
async def send_mrc_test_mail(cycle_code: str, request: MrcTestMailRequest) -> dict:
    try:
        run_id = await mrc_service.submit_test_mail(
            cycle_code, request.recipient_email
        )
    except MrcBusyError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"run_id": run_id, "status": "running"}


@app.get("/api/agents/mrc-automation/cycles/{cycle_code}/latest")
async def get_latest_mrc_scan(cycle_code: str) -> dict:
    scan = await mrc_service.get_latest_scan(cycle_code)
    if scan is None:
        raise HTTPException(status_code=404, detail="No completed scan for this cycle")
    return scan


@app.get(
    "/api/agents/mrc-automation/cycles/{cycle_code}/artifacts/{kind}/{file_name}"
)
async def download_mrc_artifact(
    cycle_code: str, kind: str, file_name: str
) -> FileResponse:
    try:
        file_path = resolve_artifact(cycle_code, kind, file_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Artifact not found") from exc
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Artifact not found")
    media_types = {
        "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ppt": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    return FileResponse(file_path, media_type=media_types[kind], filename=file_path.name)


@app.get("/api/agents/mrc-automation/automation")
async def get_mrc_automation() -> dict:
    return {"enabled": await mrc_service.get_automation_enabled()}


@app.put("/api/agents/mrc-automation/automation")
async def set_mrc_automation(request: AutomationRequest) -> dict:
    await mrc_service.set_automation_enabled(request.enabled)
    return {"enabled": request.enabled}


@app.get("/api/runs/{run_id}/events")
async def stream_events(run_id: str, request: Request) -> StreamingResponse:
    run = agent_service.get_run(run_id) or mrc_service.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")

    async def event_stream():
        while True:
            if await request.is_disconnected():
                break
            try:
                event = await asyncio.wait_for(run.events.get(), timeout=15)
            except TimeoutError:
                yield ": keep-alive\n\n"
                continue
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if event.get("type") in {"completed", "error"}:
                break

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")