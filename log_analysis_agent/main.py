import os
import sys
from pathlib import Path

from langchain_ollama import ChatOllama
from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

if __package__:
    from .agent.graph import create_agent_graph
    from .tools.executor import execute_command
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from log_analysis_agent.agent.graph import create_agent_graph
    from log_analysis_agent.tools.executor import execute_command


def create_model():
    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://10.112.230.27:11434"),
        temperature=0,
    )


def main() -> None:
    stream_started = False

    def print_event(event: dict) -> None:
        nonlocal stream_started
        event_type = event.get("type")
        if event_type == "answer_delta":
            if not stream_started:
                print("Assistant: ", end="", flush=True)
                stream_started = True
            print(event.get("content", ""), end="", flush=True)
        elif event_type == "answer_complete" and stream_started:
            print(flush=True)
            stream_started = False
        elif event_type == "copilot_activity":
            print(f"\n[Copilot] {event.get('message', '')}", flush=True)

    agent = create_agent_graph(
        create_model(),
        command_runner=lambda command: execute_command(
            command,
            on_event=print_event,
        ),
    )
    print("Hi, I am jenkins log analyzer. Please input Jenkins job/build link, or input exit/quit to exit.")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue

        result = agent.invoke({"original_question": user_input})
        if not result.get("answer_streamed"):
            print(f"Assistant: {result['final_answer']}")


if __name__ == "__main__":
    main()