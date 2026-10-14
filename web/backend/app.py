import asyncio
import json
import re
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Literal
from urllib.parse import quote
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from mrc_automation_agent.artifact_store import resolve_artifact
from pdf_to_yaml_agent import YamlGenerationError, generate_architecture_yaml
from pdf_to_yaml_agent.pdf_filter import (
    ArchitectureFigureNotFoundError,
    extract_architecture_pages,
)
from pdf_to_yaml_agent.reference_store import (
    InvalidReferenceFile,
    delete_reference,
    ensure_reference_workspace,
    list_reference_paths,
    list_references,
    normalize_reference_name,
    resolve_reference,
)

from .agent_service import AgentBusyError, agent_service
from .mrc_service import MrcBusyError, mrc_service
from .i2c_service import I2cBusyError, I2cDecodeOptions, i2c_service


MAX_PDF_BYTES = 100 * 1024 * 1024
MAX_REFERENCE_BYTES = 20 * 1024 * 1024
MAX_REFERENCE_FILES = 10
MAX_I2C_CAPTURE_BYTES = 100 * 1024 * 1024
DEFAULT_AUTHORING_GUIDE = (
    Path(__file__).resolve().parents[2]
    / ".temp"
    / "yml"
    / "I2C_architecture_YAML_authoring_guide.md"
)


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
        {
            "id": "pdf-yaml",
            "name": "PDF-to-YAML Architecture",
            "description": "Convert I2C/I3C architecture PDFs into validated YAML.",
            "status": "ready",
        },
        {
            "id": i2c_service.agent_id,
            "name": "I2C Automation",
            "description": "Decode oscilloscope CSV captures into I2C/SMBus transactions.",
            "status": i2c_service.status,
        },
    ]


def _safe_upload_name(file_name: str | None, fallback: str) -> str:
    base_name = (file_name or fallback).replace("\\", "/").rsplit("/", 1)[-1]
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", base_name).strip("._")
    return safe_name or fallback


async def _save_upload(upload: UploadFile, destination: Path, max_bytes: int) -> None:
    size = 0
    with destination.open("wb") as output:
        while chunk := await upload.read(1024 * 1024):
            size += len(chunk)
            if size > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail=f"{upload.filename or 'Upload'} exceeds the size limit",
                )
            output.write(chunk)


@app.get("/api/agents/pdf-yaml/references")
async def get_pdf_yaml_references() -> dict:
    return {"files": list_references()}


@app.post("/api/agents/pdf-yaml/references")
async def upload_pdf_yaml_references(files: list[UploadFile] = File(...)) -> dict:
    if not files or len(files) > MAX_REFERENCE_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"Upload between 1 and {MAX_REFERENCE_FILES} reference files",
        )
    try:
        names = [normalize_reference_name(upload.filename) for upload in files]
    except InvalidReferenceFile as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    existing_names = {path.name.casefold() for path in list_reference_paths()}
    resulting_names = existing_names | {name.casefold() for name in names}
    if len(resulting_names) > MAX_REFERENCE_FILES:
        raise HTTPException(
            status_code=400,
            detail=f"The workspace can contain at most {MAX_REFERENCE_FILES} reference files",
        )

    workspace = ensure_reference_workspace()
    for upload, name in zip(files, names):
        destination = resolve_reference(name)
        temporary_path = workspace / f".{uuid4().hex}.upload"
        try:
            await _save_upload(upload, temporary_path, MAX_REFERENCE_BYTES)
            temporary_path.replace(destination)
        finally:
            temporary_path.unlink(missing_ok=True)
    return {"files": list_references()}


@app.get("/api/agents/pdf-yaml/references/{file_name}")
async def download_pdf_yaml_reference(file_name: str) -> FileResponse:
    try:
        file_path = resolve_reference(file_name)
    except InvalidReferenceFile as exc:
        raise HTTPException(status_code=404, detail="Reference file not found") from exc
    if not file_path.is_file() or file_path.is_symlink():
        raise HTTPException(status_code=404, detail="Reference file not found")
    media_types = {
        ".md": "text/markdown",
        ".pdf": "application/pdf",
        ".txt": "text/plain",
        ".yaml": "application/yaml",
        ".yml": "application/yaml",
    }
    media_type = media_types[file_path.suffix.lower()]
    return FileResponse(file_path, media_type=media_type, filename=file_path.name)


@app.delete("/api/agents/pdf-yaml/references/{file_name}")
async def remove_pdf_yaml_reference(file_name: str) -> dict:
    try:
        deleted = delete_reference(file_name)
    except InvalidReferenceFile as exc:
        raise HTTPException(status_code=404, detail="Reference file not found") from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Reference file not found")
    return {"files": list_references()}


@app.post("/api/agents/pdf-yaml/prepare")
async def prepare_pdf_yaml_source(pdf: UploadFile = File(...)) -> Response:
    pdf_name = _safe_upload_name(pdf.filename, "architecture.pdf")
    if not pdf_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Architecture source must be a PDF")

    with TemporaryDirectory(prefix="pdf-yaml-prepare-") as directory:
        request_directory = Path(directory)
        source_path = request_directory / pdf_name
        prepared_name = f"{Path(pdf_name).stem}_smbus_figures.pdf"
        prepared_path = request_directory / prepared_name
        await _save_upload(pdf, source_path, MAX_PDF_BYTES)
        try:
            selection = extract_architecture_pages(source_path, prepared_path)
        except ArchitectureFigureNotFoundError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        content = prepared_path.read_bytes()

    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{prepared_name}"',
            "X-Prepared-Name": quote(prepared_name),
            "X-Architecture-Product": quote(selection.product_name),
            "X-Architecture-Target": quote(selection.target.caption),
            "X-Architecture-Pages": ",".join(
                str(figure.page_number) for figure in selection.figures
            ),
        },
    )


@app.post("/api/agents/pdf-yaml/generate")
async def generate_pdf_yaml(pdf: UploadFile = File(...)) -> dict:
    pdf_name = _safe_upload_name(pdf.filename, "architecture.pdf")
    if not pdf_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Architecture source must be a PDF")
    with TemporaryDirectory(prefix="pdf-yaml-") as directory:
        request_directory = Path(directory)
        pdf_path = request_directory / pdf_name
        await _save_upload(pdf, pdf_path, MAX_PDF_BYTES)

        reference_paths = list_reference_paths()
        if not reference_paths:
            if not DEFAULT_AUTHORING_GUIDE.is_file():
                raise HTTPException(
                    status_code=500,
                    detail="Default YAML authoring guide is unavailable",
                )
            reference_paths = [DEFAULT_AUTHORING_GUIDE]

        try:
            content, validation = await generate_architecture_yaml(
                pdf_path, reference_paths
            )
        except YamlGenerationError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except (RuntimeError, TimeoutError) as exc:
            raise HTTPException(
                status_code=502, detail=f"Copilot generation failed: {exc}"
            ) from exc

    output_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(pdf_name).stem).strip("_")
    return {
        "yaml": content,
        "file_name": f"{output_stem or 'architecture'}.yml",
        "source_file": pdf_name,
        "validation": validation,
    }


@app.post("/api/agents/pdf-yaml/generate-stream")
async def generate_pdf_yaml_stream(pdf: UploadFile = File(...)) -> StreamingResponse:
    pdf_name = _safe_upload_name(pdf.filename, "architecture.pdf")
    if not pdf_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Architecture source must be a PDF")

    temporary_directory = TemporaryDirectory(prefix="pdf-yaml-stream-")
    request_directory = Path(temporary_directory.name)
    pdf_path = request_directory / pdf_name
    try:
        await _save_upload(pdf, pdf_path, MAX_PDF_BYTES)
    except Exception:
        temporary_directory.cleanup()
        raise

    reference_paths = list_reference_paths()
    if not reference_paths:
        if not DEFAULT_AUTHORING_GUIDE.is_file():
            temporary_directory.cleanup()
            raise HTTPException(
                status_code=500,
                detail="Default YAML authoring guide is unavailable",
            )
        reference_paths = [DEFAULT_AUTHORING_GUIDE]

    output_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(pdf_name).stem).strip("_")

    async def event_stream():
        events: asyncio.Queue[dict | None] = asyncio.Queue()

        async def report_progress(stage: str, percent: int) -> None:
            await events.put(
                {"type": "progress", "stage": stage, "percent": percent}
            )

        async def report_activity(activity: str) -> None:
            await events.put({"type": "activity", "activity": activity})

        async def report_process(message: str) -> None:
            await events.put({"type": "process", "message": message})

        async def report_process_delta(content: str) -> None:
            await events.put({"type": "process_delta", "content": content})

        async def report_output_delta(content: str) -> None:
            await events.put({"type": "output_delta", "content": content})

        async def report_copilot_activity(message: str) -> None:
            await events.put({"type": "copilot_activity", "message": message})

        async def run_generation() -> None:
            try:
                await report_progress("starting", 5)
                content, validation = await generate_architecture_yaml(
                    pdf_path,
                    reference_paths,
                    progress_callback=report_progress,
                    activity_callback=report_activity,
                    process_callback=report_process,
                    process_delta_callback=report_process_delta,
                    output_delta_callback=report_output_delta,
                    copilot_activity_callback=report_copilot_activity,
                )
                await events.put(
                    {
                        "type": "result",
                        "yaml": content,
                        "file_name": f"{output_stem or 'architecture'}.yml",
                        "source_file": pdf_name,
                        "validation": validation,
                    }
                )
            except YamlGenerationError as exc:
                await events.put({"type": "error", "detail": str(exc)})
            except (RuntimeError, TimeoutError) as exc:
                await events.put(
                    {"type": "error", "detail": f"Copilot generation failed: {exc}"}
                )
            finally:
                await events.put(None)

        generation_task = asyncio.create_task(run_generation())
        try:
            while True:
                event = await events.get()
                if event is None:
                    break
                yield json.dumps(event, ensure_ascii=False) + "\n"
        finally:
            if not generation_task.done():
                generation_task.cancel()
                try:
                    await generation_task
                except asyncio.CancelledError:
                    pass
            temporary_directory.cleanup()

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/agents/i2c-automation/decodes", status_code=status.HTTP_202_ACCEPTED)
async def submit_i2c_decode(
    capture: UploadFile = File(...),
    time_col: str | None = Form(default=None),
    scl_col: str | None = Form(default=None),
    sda_col: str | None = Form(default=None),
    scl_threshold: float | None = Form(default=None),
    sda_threshold: float | None = Form(default=None),
    hysteresis_fraction: float = Form(default=0.05),
) -> dict:
    if capture.filename and not capture.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="I2C capture must be a CSV file")
    if hysteresis_fraction < 0 or hysteresis_fraction > 0.5:
        raise HTTPException(
            status_code=400,
            detail="hysteresis_fraction must be between 0 and 0.5",
        )

    source_name, upload_path = i2c_service.prepare_upload_path(capture.filename)
    await _save_upload(capture, upload_path, MAX_I2C_CAPTURE_BYTES)
    try:
        run_id = await i2c_service.submit(
            upload_path,
            source_name,
            I2cDecodeOptions(
                time_col=time_col,
                scl_col=scl_col,
                sda_col=sda_col,
                scl_threshold=scl_threshold,
                sda_threshold=sda_threshold,
                hysteresis_fraction=hysteresis_fraction,
            ),
        )
    except I2cBusyError as exc:
        upload_path.unlink(missing_ok=True)
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"run_id": run_id, "status": "running"}


@app.get("/api/agents/i2c-automation/runs/{run_id}/artifacts/{file_name}")
async def download_i2c_artifact(run_id: str, file_name: str) -> FileResponse:
    try:
        file_path = i2c_service.resolve_artifact(run_id, file_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Artifact not found") from exc
    media_types = {
        ".csv": "text/csv",
        ".json": "application/json",
        ".txt": "text/plain",
    }
    return FileResponse(
        file_path,
        media_type=media_types.get(file_path.suffix.lower(), "application/octet-stream"),
        filename=file_path.name,
    )


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
    run = agent_service.get_run(run_id) or mrc_service.get_run(run_id) or i2c_service.get_run(run_id)
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