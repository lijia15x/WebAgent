import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

from ..skills.contracts import CommandResult


class CommandExecutionError(RuntimeError):
    pass


SKILL_MODULE = re.compile(r"^log_analysis_agent\.skills\.[a-zA-Z_][\w.]*$")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
COMMAND_TIMEOUT_SECONDS = 330


def parse_command(command: str) -> list[str]:
    try:
        arguments = shlex.split(command)
    except ValueError as exc:
        raise CommandExecutionError(f"Invalid command format: {exc}") from exc
    if len(arguments) < 3 or arguments[0] not in {"python", "python.exe"}:
        raise CommandExecutionError("The command must start with python -m")
    if arguments[1] != "-m" or not SKILL_MODULE.fullmatch(arguments[2]):
        raise CommandExecutionError(
            "Only Python modules under log_analysis_agent.skills may be executed"
        )
    return [sys.executable, *arguments[1:]]


def validate_command(command: str) -> None:
    parse_command(command)


def execute_command(command: str) -> CommandResult:
    try:
        arguments = parse_command(command)
        stream_copilot = (
            arguments[2]
            == "log_analysis_agent.skills.copilot_sdk.run_copilot"
        )
        completed = subprocess.run(
            arguments,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=None if stream_copilot else subprocess.PIPE,
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