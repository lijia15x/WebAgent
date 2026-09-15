import argparse
import json
import sys
import tempfile
from pathlib import Path

from .client import JenkinsClient, JenkinsError
from .log_sanitizer import sanitize_log


def main() -> int:
    parser = argparse.ArgumentParser(description="Get a sanitized Jenkins console log")
    parser.add_argument("--build-url", required=True)
    arguments = parser.parse_args()
    try:
        log = JenkinsClient().get_console_log(arguments.build_url)
    except JenkinsError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    sanitized_log = sanitize_log(log)
    artifacts_dir = Path(__file__).resolve().parents[3] / "log_analysis_agent" / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".log",
        prefix="jenkins-",
        dir=artifacts_dir,
        delete=False,
    ) as attachment:
        attachment.write(sanitized_log)
    print(
        json.dumps(
            {
                "attachment_path": str(Path(attachment.name).resolve()),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())