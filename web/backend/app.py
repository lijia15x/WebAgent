import asyncio
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .agent_service import AgentBusyError, agent_service


class MessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


app = FastAPI(title="Agent Desk", version="0.1.0")


@app.get("/api/agents")
async def list_agents() -> list[dict]:
    return [
        {
            "id": agent_service.agent_id,
            "name": "Jenkins Log Analyst",
            "description": "Analyze Jenkins failures with logs and workspace code.",
            "status": agent_service.status,
        }
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


@app.get("/api/runs/{run_id}/events")
async def stream_events(run_id: str, request: Request) -> StreamingResponse:
    run = agent_service.get_run(run_id)
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