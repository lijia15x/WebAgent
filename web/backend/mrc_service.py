import asyncio
import logging
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote
from uuid import uuid4

from mrc_automation_agent.artifact_store import list_cycle_artifacts
from mrc_automation_agent.config import MrcConfig
from mrc_automation_agent.database import MrcDatabase
from mrc_automation_agent.graph import create_mrc_graph
from mrc_automation_agent.models import EmailDraft
from mrc_automation_agent.email_sender import GraphEmailSender
from mrc_automation_agent.ppt_generator import generate_weekly_ppts
from mrc_automation_agent.sharepoint_client import SharePointClient


logger = logging.getLogger(__name__)


class MrcBusyError(RuntimeError):
    pass


@dataclass
class MrcRun:
    run_id: str
    events: asyncio.Queue[dict[str, Any]]
    task: asyncio.Task | None = None
    sequence: int = 0


class MrcService:
    agent_id = "mrc-automation"

    def __init__(self) -> None:
        self._guard = asyncio.Lock()
        self._current_run: MrcRun | None = None
        self._status = "idle"

    @property
    def status(self) -> str:
        return self._status

    async def _submit(self, operation, *arguments) -> str:
        async with self._guard:
            if self._current_run and self._current_run.task:
                if not self._current_run.task.done():
                    raise MrcBusyError("MRC Automation is currently running")
            run = MrcRun(run_id=uuid4().hex, events=asyncio.Queue())
            self._current_run = run
            self._status = "running"
            run.task = asyncio.create_task(operation(run, *arguments))
            return run.run_id

    async def submit_scan(self, cycle_code: str) -> str:
        await self._require_manual_actions()
        return await self._submit(self._run_scan, cycle_code)

    async def submit_ppt(self, cycle_code: str) -> str:
        await self._require_manual_actions()
        return await self._submit(self._run_ppt, cycle_code)

    async def submit_mail(self, cycle_code: str, include_all: bool) -> str:
        await self._require_manual_actions()
        return await self._submit(self._run_mail, cycle_code, include_all)

    async def _require_manual_actions(self) -> None:
        if await self.get_automation_enabled():
            raise MrcBusyError("Automation is enabled; manual actions are disabled")

    def get_run(self, run_id: str) -> MrcRun | None:
        run = self._current_run
        return run if run and run.run_id == run_id else None

    async def get_automation_enabled(self) -> bool:
        database = MrcDatabase()
        return await asyncio.to_thread(database.get_automation_enabled)

    async def set_automation_enabled(self, enabled: bool) -> None:
        database = MrcDatabase()
        await asyncio.to_thread(database.set_automation_enabled, enabled)

    async def get_latest_scan(self, cycle_code: str) -> dict[str, Any] | None:
        database = MrcDatabase()
        scan = await asyncio.to_thread(database.get_latest_scan, cycle_code)
        if scan is not None:
            scan["artifacts"] = self._serialize_artifacts(cycle_code)
        return scan

    @staticmethod
    def _serialize_artifacts(cycle_code: str, artifacts=None) -> list[dict[str, str]]:
        artifacts = artifacts if artifacts is not None else list_cycle_artifacts(cycle_code)
        return [
            {
                **asdict(artifact),
                "download_url": (
                    f"/api/agents/mrc-automation/cycles/{cycle_code}/artifacts/"
                    f"{artifact.kind}/{quote(artifact.file_name)}"
                ),
            }
            for artifact in artifacts
        ]

    def _event(self, run: MrcRun, event: dict[str, Any]) -> dict[str, Any]:
        run.sequence += 1
        return {
            "sequence": run.sequence,
            "timestamp": datetime.now(UTC).isoformat(),
            **event,
        }

    async def _run_scan(self, run: MrcRun, cycle_code: str) -> None:
        loop = asyncio.get_running_loop()

        def emit(event: dict[str, Any]) -> None:
            payload = self._event(run, event)
            loop.call_soon_threadsafe(run.events.put_nowait, payload)

        try:
            config = MrcConfig.from_env()
            graph = create_mrc_graph(
                config=config,
                database=MrcDatabase(),
                sharepoint_client=SharePointClient(config),
                on_event=emit,
            )
            result = await asyncio.to_thread(
                graph.invoke,
                {
                    "cycle_code": cycle_code,
                    "reminder_type": "reminder",
                    "triggered_by": "manual",
                },
            )
            if result.get("error"):
                await run.events.put(
                    self._event(
                        run,
                        {"type": "error", "message": result["error"]},
                    )
                )
                return
            records = result.get("records", [])
            missing_by_owner: dict[str, int] = {}
            for record in records:
                if record.owner_email and record.is_missing_update:
                    missing_by_owner[record.owner_email] = (
                        missing_by_owner.get(record.owner_email, 0) + 1
                    )
            drafts = [
                {
                    **asdict(draft),
                    "missing_updates": missing_by_owner.get(draft.owner_email, 0),
                }
                for draft in result.get("drafts", [])
            ]
            artifacts = self._serialize_artifacts(
                cycle_code, result.get("artifacts", [])
            )
            await run.events.put(
                self._event(
                    run,
                    {
                        "type": "completed",
                        "scan_run_id": result.get("scan_run_id"),
                        "summary": {
                            "files_found": result.get("files_found", 0),
                            "workbook_names": [
                                workbook.name for workbook in result.get("workbooks", [])
                            ],
                            "owners_found": len(
                                {record.owner_email for record in records if record.owner_email}
                            ),
                            "missing_comments": sum(
                                record.is_missing_update for record in records
                            ),
                        },
                        "drafts": drafts,
                        "artifacts": artifacts,
                    },
                )
            )
        except Exception as exc:
            logger.exception("MRC run %s failed", run.run_id)
            await run.events.put(
                self._event(
                    run,
                    {"type": "error", "message": f"MRC Automation failed: {exc}"},
                )
            )
        finally:
            self._status = "idle"

    async def _run_ppt(self, run: MrcRun, cycle_code: str) -> None:
        try:
            artifacts = list_cycle_artifacts(cycle_code)
            excel_artifacts = [item for item in artifacts if item.kind == "excel"]
            if not excel_artifacts:
                raise FileNotFoundError("Please scan SharePoint before generating PPTs")
            database = MrcDatabase()
            workbook_urls = await asyncio.to_thread(
                database.get_workbook_urls, cycle_code
            )
            missing_urls = [
                artifact.file_name
                for artifact in excel_artifacts
                if not workbook_urls.get(artifact.file_name)
            ]
            if missing_urls:
                raise FileNotFoundError(
                    "Workbook source URLs are missing; scan SharePoint again: "
                    + ", ".join(missing_urls)
                )
            excel_artifacts = [
                replace(
                    artifact,
                    source_url=workbook_urls[artifact.file_name],
                )
                for artifact in excel_artifacts
            ]
            await run.events.put(self._event(run, {"type": "progress", "stage": "generate_ppt", "message": "Generating PPTs from local Excel files"}))
            generated = await asyncio.to_thread(
                generate_weekly_ppts, MrcConfig.from_env(), cycle_code, excel_artifacts
            )
            await run.events.put(self._event(run, {"type": "completed", "operation": "ppt", "artifacts": self._serialize_artifacts(cycle_code, [*artifacts, *generated])}))
        except Exception as exc:
            await run.events.put(self._event(run, {"type": "error", "message": str(exc)}))
        finally:
            self._status = "idle"

    async def _run_mail(self, run: MrcRun, cycle_code: str, include_all: bool) -> None:
        database = MrcDatabase()
        sender = None
        try:
            rows = await asyncio.to_thread(database.get_sendable_drafts, cycle_code, include_all)
            if not rows:
                raise FileNotFoundError("No unsent recipients found; scan SharePoint first")
            sender = GraphEmailSender(MrcConfig.from_env())
            sent = 0
            failures = []
            for row in rows:
                draft = EmailDraft(
                    row.get("owner_name", ""), row["owner_email"], row["subject"],
                    row["body_html"], row.get("project_count", 0), "",
                )
                await run.events.put(self._event(run, {"type": "progress", "stage": "send_mail", "message": f"Sending reminder to {draft.owner_email}"}))
                try:
                    await asyncio.to_thread(database.update_delivery_status, row["scan_run_id"], draft.owner_email, "sending")
                    await asyncio.to_thread(sender.send, draft)
                    await asyncio.to_thread(database.update_delivery_status, row["scan_run_id"], draft.owner_email, "sent")
                    sent += 1
                except Exception as exc:
                    failures.append(draft.owner_email)
                    await asyncio.to_thread(database.update_delivery_status, row["scan_run_id"], draft.owner_email, "failed", str(exc)[:65535])
            await run.events.put(self._event(run, {"type": "completed", "operation": "mail", "sent": sent, "failed": len(failures), "failed_recipients": failures}))
        except Exception as exc:
            await run.events.put(self._event(run, {"type": "error", "message": str(exc)}))
        finally:
            if sender is not None:
                sender.close()
            self._status = "idle"


mrc_service = MrcService()