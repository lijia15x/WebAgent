import argparse
from pathlib import Path
from typing import Any, Sequence

import yaml


TOP_LEVEL_KEYS = ("version", "boards", "elements", "connections")


class ArchitectureDumper(yaml.SafeDumper):
    def ignore_aliases(self, data: Any) -> bool:
        return True

    def increase_indent(
        self,
        flow: bool = False,
        indentless: bool = False,
    ) -> None:
        return super().increase_indent(flow, False)


def format_architecture_document(document: dict[str, Any]) -> str:
    dumped = yaml.dump(
        document,
        Dumper=ArchitectureDumper,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        indent=2,
        width=120,
    ).strip()

    top_level_prefixes = tuple(f"{key}:" for key in TOP_LEVEL_KEYS[1:])
    lines: list[str] = []
    for line in dumped.splitlines():
        if line.startswith(top_level_prefixes) and lines and lines[-1] != "":
            lines.append("")
        lines.append(line)
    return "\n".join(lines)


def format_architecture_yaml(content: str) -> str:
    document = yaml.safe_load(content)
    if not isinstance(document, dict):
        raise ValueError("The YAML root must be a mapping")
    return format_architecture_document(document)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Format architecture YAML using two-space block indentation."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    arguments = parser.parse_args(argv)

    formatted = format_architecture_yaml(
        arguments.input.read_text(encoding="utf-8")
    )
    destination = arguments.output or arguments.input
    destination.write_text(f"{formatted}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
