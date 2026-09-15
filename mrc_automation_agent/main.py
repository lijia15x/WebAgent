import argparse

from .config import MrcConfig
from .database import MrcDatabase
from .graph import create_mrc_graph
from .sharepoint_client import SharePointClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the fixed MRC Automation workflow")
    parser.add_argument("--cycle", required=True, help="Reporting cycle, for example 2026WW38")
    parser.add_argument(
        "--reminder-type",
        choices=("manual", "tuesday", "thursday", "monday"),
        default="manual",
    )
    arguments = parser.parse_args()

    config = MrcConfig.from_env()
    graph = create_mrc_graph(
        config=config,
        database=MrcDatabase(),
        sharepoint_client=SharePointClient(config),
        on_event=lambda event: print(f"[{event['stage']}] {event['message']}", flush=True),
    )
    result = graph.invoke(
        {
            "cycle_code": arguments.cycle,
            "reminder_type": arguments.reminder_type,
            "triggered_by": "manual",
        }
    )
    if result.get("error"):
        raise SystemExit(result["error"])
    print(
        f"Scan {result['scan_run_id']} completed: "
        f"{result.get('files_found', 0)} workbook(s), "
        f"{len(result.get('drafts', []))} draft(s)",
        flush=True,
    )


if __name__ == "__main__":
    main()