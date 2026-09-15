import asyncio
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from mrc_automation_agent.config import MrcConfig
from mrc_automation_agent.database import MrcDatabase
from mrc_automation_agent.graph import create_mrc_graph
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

    async def submit_scan(self, cycle_code: str, reminder_type: str) -> str:
        async with self._guard:
            if self._current_run and self._current_run.task:
                if not self._current_run.task.done():
                    raise MrcBusyError("MRC Automation is currently scanning")
            run = MrcRun(run_id=uuid4().hex, events=asyncio.Queue())
            self._current_run = run
            self._status = "running"
            run.task = asyncio.create_task(
                self._run(run, cycle_code, reminder_type)
            )
            return run.run_id

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
        return await asyncio.to_thread(database.get_latest_scan, cycle_code)

    def _event(self, run: MrcRun, event: dict[str, Any]) -> dict[str, Any]:
        run.sequence += 1
        return {
            "sequence": run.sequence,
            "timestamp": datetime.now(UTC).isoformat(),
            **event,
        }

    async def _run(
        self, run: MrcRun, cycle_code: str, reminder_type: str
    ) -> None:
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
                    "reminder_type": reminder_type,
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
            drafts = [asdict(draft) for draft in result.get("drafts", [])]
            records = result.get("records", [])
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


mrc_service = MrcService()