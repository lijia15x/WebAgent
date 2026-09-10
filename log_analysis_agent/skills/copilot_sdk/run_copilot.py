import argparse
import asyncio
import json
import sys

from .copilot_sdk_client import ask_copilot


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Send a prompt and file attachments to GitHub Copilot SDK"
    )
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--workspace")
    parser.add_argument("--model", default="auto")
    parser.add_argument("--timeout", type=float, default=300.0)
    arguments = parser.parse_args()

    stream_started = False

    def stream_delta(delta: str) -> None:
        nonlocal stream_started
        if not delta:
            return
        if not stream_started:
            print("Assistant: ", end="", file=sys.stderr, flush=True)
            stream_started = True
        print(delta, end="", file=sys.stderr, flush=True)

    def stream_activity(activity: str) -> None:
        print(f"\n[Copilot] {activity}", file=sys.stderr, flush=True)

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
        print(str(exc), file=sys.stderr)
        return 1

    if stream_started:
        print(file=sys.stderr, flush=True)
    else:
        print(f"Assistant: {response}", file=sys.stderr, flush=True)
    print(json.dumps({"response": response, "streamed": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())