"""Import oscilloscope CSV captures for I2C/SMBus decoding.

Expected input shape (matches the supplied FAN_CONTROL_SMB_DEBUG.csv):

    x-axis,smbus_fanctrl_scl,smbus_fanctrl_sda,hz
    second,Volt,Volt,Volt
    -157.5000E-06,+3.2437236831E+00,+3.3269874081E+00,+4.7848809479E+00
    ...

Row 1 is the column header. Row 2 is an optional units row (kept as
metadata, not decoded). All other columns besides the selected time/SCL/SDA
columns are ignored by the decoder (e.g. the auxiliary "hz" channel in the
sample capture, whose real meaning is undocumented — see the development
plan's Requirements sheet).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RawCapture:
    source_file: str
    header: list[str]
    units: dict[str, str]
    time: list[float]
    scl: list[float]
    sda: list[float]
    warnings: list[str] = field(default_factory=list)


class CsvFormatError(ValueError):
    """Raised when the CSV does not contain usable timestamp/SCL/SDA data."""


def _find_column(header: list[str], explicit: str | None, contains: str | None, role: str) -> str:
    if explicit is not None:
        for name in header:
            if name.strip().lower() == explicit.strip().lower():
                return name
        raise CsvFormatError(
            f"Requested {role} column '{explicit}' not found. Available columns: {header}"
        )
    if contains is not None:
        matches = [name for name in header if contains.lower() in name.strip().lower()]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise CsvFormatError(
                f"Could not auto-detect a unique {role} column (candidates {matches}); "
                f"pass an explicit column name."
            )
    raise CsvFormatError(
        f"Could not auto-detect the {role} column. Available columns: {header}"
    )


def read_capture(
    path: str | Path,
    time_col: str | None = None,
    scl_col: str | None = None,
    sda_col: str | None = None,
) -> RawCapture:
    """Read a scope-exported CSV into parallel time/SCL/SDA float lists.

    If ``time_col``/``scl_col``/``sda_col`` are omitted, columns are
    auto-detected: the first column is used for time, and the SCL/SDA
    columns are matched by looking for "scl"/"sda" (case-insensitive)
    in the header names.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"CSV capture not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise CsvFormatError(f"CSV file is empty: {path}") from exc
        header = [name.strip() for name in header]

        resolved_time = header[0] if time_col is None else _find_column(header, time_col, None, "time")
        resolved_scl = _find_column(header, scl_col, None if scl_col else "scl", "SCL")
        resolved_sda = _find_column(header, sda_col, None if sda_col else "sda", "SDA")

        time_idx = header.index(resolved_time)
        scl_idx = header.index(resolved_scl)
        sda_idx = header.index(resolved_sda)

        rows = list(reader)

    if not rows:
        raise CsvFormatError(f"CSV file has a header but no data rows: {path}")

    units: dict[str, str] = {}
    first_data_row = 0
    candidate = rows[0]
    is_units_row = False
    if len(candidate) > time_idx:
        try:
            float(candidate[time_idx])
        except ValueError:
            is_units_row = True
    if is_units_row:
        for name, value in zip(header, candidate):
            units[name] = value.strip()
        first_data_row = 1

    times: list[float] = []
    scl: list[float] = []
    sda: list[float] = []
    warnings: list[str] = []

    for row_number, row in enumerate(rows[first_data_row:], start=first_data_row + 2):
        if not row or all(not cell.strip() for cell in row):
            continue
        try:
            t = float(row[time_idx])
            scl_v = float(row[scl_idx])
            sda_v = float(row[sda_idx])
        except (IndexError, ValueError):
            warnings.append(f"Row {row_number}: skipped, could not parse time/SCL/SDA values")
            continue
        times.append(t)
        scl.append(scl_v)
        sda.append(sda_v)

    if not times:
        raise CsvFormatError(
            f"No usable data rows found in {path} for columns "
            f"time='{resolved_time}', scl='{resolved_scl}', sda='{resolved_sda}'"
        )

    return RawCapture(
        source_file=str(path),
        header=header,
        units=units,
        time=times,
        scl=scl,
        sda=sda,
        warnings=warnings,
    )
