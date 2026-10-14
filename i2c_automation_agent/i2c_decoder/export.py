"""Human-readable and JSON export for decoded I2C/SMBus captures."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from .models import DecodeResult, Transaction


def to_dict(result: DecodeResult) -> dict:
    """Convert a :class:`DecodeResult` into a plain JSON-serializable dict."""
    return asdict(result)


def write_json(result: DecodeResult, path: str | Path, indent: int = 2) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(to_dict(result), handle, indent=indent)
        handle.write("\n")


def _status_label(txn: Transaction) -> str:
    if txn.complete:
        return "Complete"
    if any("truncated" in warning.lower() for warning in txn.warnings):
        return "Truncated"
    if any("repeated start" in warning.lower() for warning in txn.warnings):
        return "Interrupted by repeated START"
    return "Incomplete"


def to_summary_rows(result: DecodeResult) -> list[dict]:
    """Flatten each transaction into one simplified, human-readable
    summary row: Txn, Address, Register, Data, Status.

    Full protocol-level detail (timestamps, sequence grouping, ACK/NACK
    per byte, warnings) is intentionally NOT included here -- that detail
    remains complete in the .decoded.json/.decoded.txt reports. This
    table is meant to be quickly readable, not exhaustive.

    "Register"/"Data" assumes the common single-register I2C/SMBus write
    or read pattern described in SLVA704 Section 3 (address byte, then a
    register/command byte, then a data byte): the first payload byte
    after the address is shown as "Register" and the second as "Data".
    This is the most common I2C access pattern but is not guaranteed for
    every device or transaction shape (e.g. multi-byte block transfers);
    assigning exact, authoritative register/field meaning per device is
    Task 2's job (a reviewed device profile), not this generic decoder's.
    """
    rows: list[dict] = []
    for txn in result.transactions:
        data_bytes = txn.data_bytes
        register = f"0x{data_bytes[0].value:02X}" if len(data_bytes) >= 1 else ""
        if len(data_bytes) == 2:
            data_value = f"0x{data_bytes[1].value:02X}"
        elif len(data_bytes) > 2:
            data_value = ", ".join(f"0x{b.value:02X}" for b in data_bytes[1:])
        else:
            data_value = ""
        rows.append(
            {
                "Txn": txn.index,
                "Address": f"0x{txn.address_7bit:02X}" if txn.address_7bit is not None else "",
                "Register": register,
                "Data": data_value,
                "Status": _status_label(txn),
            }
        )
    return rows


def write_summary_json(result: DecodeResult, path: str | Path, indent: int = 2) -> None:
    """Write the flattened per-transaction table as a JSON array of
    objects (one object per row) -- the standard way JSON represents
    tabular data."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(to_summary_rows(result), handle, indent=indent)
        handle.write("\n")


def write_summary_csv(result: DecodeResult, path: str | Path) -> None:
    """Write the flattened per-transaction table as an actual CSV file,
    directly openable in Excel or any spreadsheet tool."""
    rows = to_summary_rows(result)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["Txn", "Address", "Register", "Data", "Status"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _fmt_time(seconds: float) -> str:
    return f"{seconds * 1e6:.1f} us"


def _fmt_hex(value: int | None) -> str:
    return f"0x{value:02X}" if value is not None else "?"


def _format_transaction(txn: Transaction) -> list[str]:
    lines: list[str] = []
    kind = "START (repeated)" if txn.repeated_start else "START"
    lines.append(f"--- Txn {txn.index} (sequence {txn.sequence_id}) ---")
    lines.append(f"{kind}  t={_fmt_time(txn.start_time)}")

    for byte in txn.bytes:
        ack_label = "ACK" if byte.ack else ("NACK" if byte.ack is False else "?")
        if byte.is_address_byte and txn.address_7bit is not None:
            direction_label = (txn.direction or "?").upper()
            lines.append(
                f"  Address {_fmt_hex(txn.address_7bit)} (raw {_fmt_hex(byte.value)})  "
                f"{direction_label}  {ack_label}"
            )
        else:
            lines.append(f"  Byte {byte.index}: {_fmt_hex(byte.value)}  {ack_label}")

    if txn.complete and txn.end_time is not None:
        lines.append(f"STOP   t={_fmt_time(txn.end_time)}")
        lines.append("Status: COMPLETE")
    else:
        # Use the same status logic as the summary table so the two
        # reports never disagree about *why* a transaction is not
        # complete (e.g. a genuine truncation vs. a legitimate repeated
        # START chain, which is normal per SLVA704 Section 2.1.2, not an
        # error).
        lines.append(f"Status: {_status_label(txn).upper()}")

    if txn.warnings:
        lines.append("Warnings:")
        for warning in txn.warnings:
            lines.append(f"  - {warning}")

    return lines


def to_text(result: DecodeResult) -> str:
    from .decoder import DATASHEET_REFERENCE

    capture = result.capture
    lines: list[str] = []
    lines.append("I2C/SMBus Decode Report")
    lines.append("=" * 40)
    lines.append(f"Source: {capture.source_file}")
    lines.append(f"Decoder version: {result.decoder_version}")
    lines.append(f"Protocol reference: {DATASHEET_REFERENCE}")

    span = f"{_fmt_time(capture.time_start)} to {_fmt_time(capture.time_end)}"
    if capture.sample_rate_hz:
        rate_msps = capture.sample_rate_hz / 1e6
        lines.append(
            f"Samples: {capture.sample_count}  |  Time span: {span}  |  "
            f"Sample interval: {capture.sample_interval * 1e6:.3f} us "
            f"(~{rate_msps:.2f} MS/s)"
        )
    else:
        lines.append(f"Samples: {capture.sample_count}  |  Time span: {span}")

    lines.append(
        f"SCL logic threshold: {capture.scl_threshold:.3f} V "
        f"(range {capture.scl_min:.3f} - {capture.scl_max:.3f} V)"
    )
    lines.append(
        f"SDA logic threshold: {capture.sda_threshold:.3f} V "
        f"(range {capture.sda_min:.3f} - {capture.sda_max:.3f} V)"
    )

    if capture.estimated_scl_frequency_hz:
        freq_khz = capture.estimated_scl_frequency_hz / 1e3
        spb = capture.estimated_samples_per_bit
        spb_text = f"~{spb:.1f} samples/bit" if spb else "samples/bit unknown"
        lines.append(f"Estimated SCL frequency: ~{freq_khz:.1f} kHz ({spb_text})")

    if capture.warnings:
        lines.append("Capture warnings:")
        for warning in capture.warnings:
            lines.append(f"  - {warning}")

    lines.append("")
    lines.append(f"Transactions decoded: {len(result.transactions)}")
    lines.append("")

    for txn in result.transactions:
        lines.extend(_format_transaction(txn))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_text(result: DecodeResult, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_text(result), encoding="utf-8")
