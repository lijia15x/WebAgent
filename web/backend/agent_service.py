import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from log_analysis_agent.agent.graph import create_agent_graph
from log_analysis_agent.main import create_model
from log_analysis_agent.tools.executor import execute_command


logger = logging.getLogger(__name__)


class AgentBusyError(RuntimeError):
    pass


@dataclass
class AgentRun:
    run_id: str
    events: asyncio.Queue[dict[str, Any]]
    task: asyncio.Task | None = None
    sequence: int = 0


class AgentService:
    agent_id = "jenkins-log-analyst"

    def __init__(self) -> None:
        self._guard = asyncio.Lock()
        self._current_run: AgentRun | None = None
        self._status = "idle"

    @property
    def status(self) -> str:
        return self._status

    async def submit(self, content: str) -> str:
        async with self._guard:
            if self._current_run and self._current_run.task:
                if not self._current_run.task.done():
                    raise AgentBusyError("Agent is currently running another task")

            run = AgentRun(run_id=uuid4().hex, events=asyncio.Queue())
            self._current_run = run
            self._status = "running"
            run.task = asyncio.create_task(self._run(run, content))
            return run.run_id

    def get_run(self, run_id: str) -> AgentRun | None:
        run = self._current_run
        return run if run and run.run_id == run_id else None

    def _event(self, run: AgentRun, event: dict[str, Any]) -> dict[str, Any]:
        run.sequence += 1
        return {
            "sequence": run.sequence,
            "timestamp": datetime.now(UTC).isoformat(),
            **event,
        }

    async def _run(self, run: AgentRun, content: str) -> None:
        loop = asyncio.get_running_loop()

        def emit(event: dict[str, Any]) -> None:
            safe_event = dict(event)
            if safe_event.get("type") == "error":
                safe_event = {
                    "type": "error",
                    "message": "Copilot execution failed. Check the server log.",
                }
            payload = self._event(run, safe_event)
            loop.call_soon_threadsafe(run.events.put_nowait, payload)

        def command_runner(command: str):
            return execute_command(command, on_event=emit)

        try:
            graph = create_agent_graph(
                create_model(),
                command_runner=command_runner,
                on_event=emit,
            )
            result = await asyncio.to_thread(
                graph.invoke,
                {"original_question": content},
            )
            await run.events.put(
                self._event(
                    run,
                    {
                        "type": "completed",
                        "answer": result.get(
                            "final_answer",
                            "The agent completed without an answer.",
                        ),
                    },
                )
            )
        except Exception:
            logger.exception("Agent run %s failed", run.run_id)
            await run.events.put(
                self._event(
                    run,
                    {
                        "type": "error",
                        "message": "Agent execution failed. Check the server log.",
                    },
                )
            )
        finally:
            self._status = "idle"


agent_service = AgentService()