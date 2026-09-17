import importlib
import json
import os
import re
from pathlib import Path
from typing import Callable, Optional, Sequence, Union


PROCESS_PHASES = frozenset({"analysis", "reasoning"})
ANSWER_PHASES = frozenset({"answer", "final", "response"})


def _message_is_process(phase: str | None, has_tool_requests: bool) -> bool:
    return (phase or "").lower() in PROCESS_PHASES or has_tool_requests


def _format_tool_start(tool_name: str, arguments, working_directory: str | None) -> str:
    message = f"Started tool: {tool_name}"
    if tool_name not in {"glob", "rg", "view"} or arguments is None:
        return message

    def sanitize(value):
        if isinstance(value, str) and working_directory:
            value = re.sub(
                re.escape(working_directory),
                "<workspace>",
                value,
                flags=re.IGNORECASE,
            )
            return re.sub(
                re.escape(working_directory.replace("\\", "/")),
                "<workspace>",
                value,
                flags=re.IGNORECASE,
            )
        if isinstance(value, dict):
            return {key: sanitize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [sanitize(item) for item in value]
        return value

    safe_arguments = sanitize(arguments)
    if isinstance(safe_arguments, dict):
        details = ", ".join(
            f"{key}={json.dumps(value, ensure_ascii=False, default=str)}"
            for key, value in safe_arguments.items()
        )
    else:
        details = json.dumps(safe_arguments, ensure_ascii=False, default=str)

    if len(details) > 500:
        details = f"{details[:497]}..."
    return f"{message} ({details})"


async def ask_copilot(
    prompt: str,
    model: str = "auto",
    files: Optional[Sequence[Union[str, Path]]] = None,
    workspace: Optional[Union[str, Path]] = None,
    timeout: float = 300.0,
    on_delta: Optional[Callable[[str], None]] = None,
    on_process_delta: Optional[Callable[[str], None]] = None,
    on_activity: Optional[Callable[[str], None]] = None,
) -> str:
    try:
        copilot_module = importlib.import_module("copilot")
        session_module = importlib.import_module("copilot.session")
        events_module = importlib.import_module("copilot.session_events")
    except ImportError as error:
        raise RuntimeError(
            "Copilot SDK is not installed. Install it with: "
            "pip install github-copilot-sdk"
        ) from error

    attachments = []
    for file_path in files or []:
        resolved_path = Path(file_path).resolve()
        if not resolved_path.exists():
            raise FileNotFoundError(f"Attachment file does not exist: {resolved_path}")
        if not resolved_path.is_file():
            raise ValueError(f"Attachment path is not a file: {resolved_path}")
        attachments.append(
            {
                "type": "file",
                "path": str(resolved_path),
                "displayName": resolved_path.name,
            }
        )

    if workspace is None:
        workspace = os.getenv("COPILOT_WORKSPACE_ROOT")
    working_directory = None
    if workspace:
        resolved_workspace = Path(workspace).resolve()
        if not resolved_workspace.exists():
            raise FileNotFoundError(
                f"Copilot workspace does not exist: {resolved_workspace}"
            )
        if not resolved_workspace.is_dir():
            raise ValueError(
                f"Copilot workspace is not a directory: {resolved_workspace}"
            )
        working_directory = str(resolved_workspace)

    effective_prompt = prompt
    if working_directory:
        effective_prompt = (
            f"{prompt}\n\n"
            "Before answering, use targeted text searches for test names, stack "
            "trace symbols, and component names from the attached log, then read "
            "only the most relevant workspace files. Do not scan or index the "
            "entire workspace. Use the code as evidence, cite relevant file paths, "
            "and do not modify any workspace files."
        )

    client = copilot_module.CopilotClient()
    await client.start()
    try:
        session = await client.create_session(
            on_permission_request=session_module.PermissionHandler.approve_all,
            model=model,
            streaming=on_delta is not None,
            working_directory=working_directory,
        )
        unsubscribe = None
        if on_delta is not None or on_process_delta is not None or on_activity is not None:
            active_tools: dict[str, str] = {}
            message_phases: dict[str, str] = {}
            pending_messages: dict[str, list[str]] = {}
            streamed_messages: set[str] = set()

            def emit_process(content: str) -> None:
                if content and on_process_delta is not None:
                    on_process_delta(content)

            def emit_answer(content: str) -> None:
                if content and on_delta is not None:
                    on_delta(content)

            def handle_event(event) -> None:
                data = event.data
                if isinstance(data, events_module.AssistantMessageStartData):
                    message_phases[data.message_id] = (data.phase or "").lower()
                elif isinstance(data, events_module.AssistantIntentData):
                    emit_process(f"{data.intent}\n")
                elif isinstance(
                    data, events_module.AssistantReasoningDeltaData
                ):
                    emit_process(data.delta_content)
                elif isinstance(
                    data, events_module.AssistantMessageDeltaData
                ):
                    phase = message_phases.get(data.message_id, "")
                    if phase in PROCESS_PHASES:
                        streamed_messages.add(data.message_id)
                        emit_process(data.delta_content)
                    elif phase in ANSWER_PHASES:
                        streamed_messages.add(data.message_id)
                        emit_answer(data.delta_content)
                    else:
                        pending_messages.setdefault(data.message_id, []).append(
                            data.delta_content
                        )
                elif isinstance(data, events_module.AssistantMessageData):
                    message_id = data.message_id
                    phase = data.phase or message_phases.get(message_id, "")
                    buffered = "".join(pending_messages.pop(message_id, []))
                    if message_id not in streamed_messages:
                        content = buffered or data.content
                        if _message_is_process(phase, bool(data.tool_requests)):
                            emit_process(content)
                        else:
                            emit_answer(content)
                    message_phases.pop(message_id, None)
                    streamed_messages.discard(message_id)
                elif on_activity is not None and isinstance(
                    data, events_module.ToolExecutionStartData
                ):
                    active_tools[data.tool_call_id] = data.tool_name
                    on_activity(
                        _format_tool_start(
                            data.tool_name,
                            data.arguments,
                            working_directory,
                        )
                    )
                elif on_activity is not None and isinstance(
                    data, events_module.ToolExecutionProgressData
                ):
                    on_activity(data.progress_message)
                elif on_activity is not None and isinstance(
                    data, events_module.ToolExecutionCompleteData
                ):
                    tool_name = active_tools.pop(data.tool_call_id, "unknown")
                    status = "completed" if data.success else "failed"
                    on_activity(f"Tool {status}: {tool_name}")

            unsubscribe = session.on(handle_event)
        try:
            response = await session.send_and_wait(
                effective_prompt,
                attachments=attachments or None,
                timeout=timeout,
            )
        finally:
            if unsubscribe is not None:
                unsubscribe()
        content = getattr(getattr(response, "data", None), "content", None)
        if not content:
            raise RuntimeError("Copilot SDK returned an empty response.")
        if on_delta is not None or on_process_delta is not None:
            for chunks in pending_messages.values():
                buffered = "".join(chunks)
                if buffered == content:
                    emit_answer(buffered)
                else:
                    emit_process(buffered)
        return content
    finally:
        await client.stop()