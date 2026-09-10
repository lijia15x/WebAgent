import argparse
import json
import sys

from .client import JenkinsClient, JenkinsError


def main() -> int:
    parser = argparse.ArgumentParser(description="Get Jenkins job or build status")
    parser.add_argument("--url", required=True)
    arguments = parser.parse_args()
    try:
        result = JenkinsClient().get_build_status(arguments.url)
    except JenkinsError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())