import json
import re
import shlex
import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable

from ..agent.contracts import CommandResult


class CommandExecutionError(RuntimeError):
    pass


ALLOWED_SKILL_MODULES = frozenset(
    {
        "common.skills.jenkins_api.get_job_status",
        "common.skills.jenkins_api.get_console_log",
        "common.skills.copilot_sdk.run_copilot",
    }
)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMMAND_TIMEOUT_SECONDS = 330


def parse_command(command: str) -> list[str]:
    try:
        arguments = shlex.split(command)
    except ValueError as exc:
        raise CommandExecutionError(f"Invalid command format: {exc}") from exc
    if len(arguments) < 3 or arguments[0] not in {"python", "python.exe"}:
        raise CommandExecutionError("The command must start with python -m")
    if arguments[1] != "-m" or arguments[2] not in ALLOWED_SKILL_MODULES:
        raise CommandExecutionError(
            "The Python module is not allowed for the Jenkins log analysis agent"
        )
    return [sys.executable, *arguments[1:]]


def validate_command(command: str) -> None:
    parse_command(command)


def _execute_streaming_command(
    arguments: list[str],
    on_event: Callable[[dict], None] | None,
) -> subprocess.CompletedProcess:
    process = subprocess.Popen(
        arguments,
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    stderr_lines: list[str] = []

    def read_events() -> None:
        if process.stderr is None:
            return
        for line in process.stderr:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                stderr_lines.append(line)
                continue
            if isinstance(event, dict) and on_event is not None:
                on_event(event)

    reader = threading.Thread(target=read_events, daemon=True)
    reader.start()
    try:
        process.wait(timeout=COMMAND_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise CommandExecutionError(
            f"Command timed out after {COMMAND_TIMEOUT_SECONDS} seconds"
        )
    finally:
        reader.join(timeout=2)

    stdout = process.stdout.read() if process.stdout is not None else ""
    return subprocess.CompletedProcess(
        arguments,
        process.returncode,
        stdout,
        "\n".join(stderr_lines),
    )


def execute_command(
    command: str,
    on_event: Callable[[dict], None] | None = None,
) -> CommandResult:
    try:
        arguments = parse_command(command)
        stream_copilot = (
            arguments[2]
            == "common.skills.copilot_sdk.run_copilot"
        )
        if stream_copilot:
            completed = _execute_streaming_command(arguments, on_event)
        else:
            completed = subprocess.run(
                arguments,
                cwd=PROJECT_ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=COMMAND_TIMEOUT_SECONDS,
                check=False,
            )
        if completed.returncode != 0:
            error = (
                completed.stderr.strip()
                if completed.stderr
                else f"Command exit code: {completed.returncode}"
            )
            return CommandResult(command=command, success=False, error=error)
        output = json.loads(completed.stdout)
        if not isinstance(output, dict):
            raise CommandExecutionError("Script output must be a JSON object")
        return CommandResult(command=command, success=True, output=output)
    except Exception as exc:
        return CommandResult(command=command, success=False, error=str(exc))