import argparse
import asyncio
import json
import os
import sys

from .copilot_sdk_client import ask_copilot


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Send a prompt and file attachments to GitHub Copilot SDK"
    )
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--workspace")
    parser.add_argument(
        "--model", default=os.getenv("LOG_ANALYSIS_MODEL", "gpt-5.5")
    )
    parser.add_argument("--timeout", type=float, default=300.0)
    arguments = parser.parse_args()

    stream_started = False

    def emit_event(event: dict) -> None:
        print(json.dumps(event), file=sys.stderr, flush=True)

    def stream_delta(delta: str) -> None:
        nonlocal stream_started
        if not delta:
            return
        stream_started = True
        emit_event({"type": "answer_delta", "content": delta})

    def stream_activity(activity: str) -> None:
        emit_event({"type": "copilot_activity", "message": activity})

    try:
        response = asyncio.run(
            ask_copilot(
                prompt=arguments.prompt,
                model=arguments.model,
                files=arguments.file,
                workspace=arguments.workspace,
                timeout=arguments.timeout,
                on_delta=stream_delta,
                on_activity=stream_activity,
            )
        )
    except Exception as exc:
        emit_event({"type": "error", "message": str(exc)})
        return 1

    if not stream_started:
        emit_event({"type": "answer_delta", "content": response})
    emit_event({"type": "answer_complete"})
    print(json.dumps({"response": response, "streamed": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())