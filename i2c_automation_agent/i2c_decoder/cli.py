"""Command-line entry point: decode a CSV capture into text/JSON/CSV reports.

Writes 3 files per input by default: <stem>.decoded.json and
<stem>.decoded.txt (the full, complete decoded data) plus
<stem>.summary.csv (one row per transaction, for a quick view of which
address/bytes were sent).

Example (matching the project's Input/Output folder convention)::

    py -m i2c_decoder --input Input/FAN_CONTROL_SMB_DEBUG.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .csv_reader import CsvFormatError, read_capture
from .decoder import DecoderConfig, decode_capture
from .export import to_text, write_json, write_summary_csv, write_text


def _default_output_dir(input_path: Path) -> Path:
    """Default to a sibling "Output" folder, matching the project layout."""
    if input_path.parent.name.lower() == "input":
        return input_path.parent.parent / "Output"
    return input_path.parent / "Output"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="i2c_decoder",
        description=(
            "Decode an oscilloscope CSV capture (timestamp, SCL, SDA) into "
            "I2C/SMBus transactions. Protocol decoding only; no electrical/"
            "signal-integrity diagnosis."
        ),
    )
    parser.add_argument("--input", "-i", required=True, help="Path to the CSV capture file.")
    parser.add_argument(
        "--output-dir",
        "-o",
        default=None,
        help="Directory to write reports into (default: sibling 'Output' folder).",
    )
    parser.add_argument("--time-col", default=None, help="Time column name (default: first column).")
    parser.add_argument("--scl-col", default=None, help="SCL column name (default: auto-detect, contains 'scl').")
    parser.add_argument("--sda-col", default=None, help="SDA column name (default: auto-detect, contains 'sda').")
    parser.add_argument(
        "--scl-threshold", type=float, default=None, help="Explicit SCL logic threshold in volts (default: auto)."
    )
    parser.add_argument(
        "--sda-threshold", type=float, default=None, help="Explicit SDA logic threshold in volts (default: auto)."
    )
    parser.add_argument("--no-json", action="store_true", help="Skip writing the full decoded JSON report.")
    parser.add_argument("--no-text", action="store_true", help="Skip writing the full decoded text report.")
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Skip writing the flattened per-transaction summary table (.summary.csv).",
    )
    parser.add_argument(
        "--print", dest="print_report", action="store_true", help="Also print the text report to stdout."
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    try:
        raw = read_capture(input_path, time_col=args.time_col, scl_col=args.scl_col, sda_col=args.sda_col)
    except (FileNotFoundError, CsvFormatError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    config = DecoderConfig(scl_threshold=args.scl_threshold, sda_threshold=args.sda_threshold)
    result = decode_capture(raw, config)

    output_dir = Path(args.output_dir) if args.output_dir else _default_output_dir(input_path)
    stem = input_path.stem

    if not args.no_json:
        write_json(result, output_dir / f"{stem}.decoded.json")
    if not args.no_text:
        write_text(result, output_dir / f"{stem}.decoded.txt")
    if not args.no_summary:
        write_summary_csv(result, output_dir / f"{stem}.summary.csv")

    if args.print_report or (args.no_json and args.no_text):
        print(to_text(result))

    print(
        f"Decoded {len(result.transactions)} transaction(s) from {input_path} -> {output_dir}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
