"""Data models for decoded I2C/SMBus captures.

These are plain dataclasses so results can be serialized with
``dataclasses.asdict`` (see :mod:`i2c_decoder.export`) without any extra
dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DecodedByte:
    """One decoded 8-bit byte plus its ACK/NACK bit.

    ``index`` is 0 for the address byte and 1, 2, 3, ... for each
    subsequent command/data byte in the same transaction.
    """

    index: int
    value: int
    ack: bool | None
    start_time: float
    end_time: float

    @property
    def is_address_byte(self) -> bool:
        return self.index == 0


@dataclass
class Transaction:
    """One I2C/SMBus transaction: START (or repeated START) through STOP.

    ``sequence_id`` groups transactions that are chained by repeated START
    conditions (no intervening STOP), e.g. a write-then-read register
    access or a mux-select-then-target-access sequence. Task 2 validation
    can use ``sequence_id`` to check multi-command paths as a single unit
    (see Requirement 8).
    """

    index: int
    sequence_id: int
    start_time: float
    end_time: float | None
    repeated_start: bool
    address_7bit: int | None = None
    direction: str | None = None  # "write" | "read" | None
    address_ack: bool | None = None
    bytes: list[DecodedByte] = field(default_factory=list)
    complete: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def address_byte_raw(self) -> int | None:
        if not self.bytes:
            return None
        return self.bytes[0].value

    @property
    def data_bytes(self) -> list[DecodedByte]:
        return self.bytes[1:] if len(self.bytes) > 1 else []

    @property
    def byte_count(self) -> int:
        return len(self.bytes)


@dataclass
class CaptureInfo:
    """Descriptive summary of the imported waveform capture.

    This is informational context for the decode (sample rate, observed
    voltage range, estimated samples-per-bit), not an electrical
    pass/fail verdict. Electrical/signal-integrity diagnosis is out of
    scope for this decoder (Requirement 1).
    """

    source_file: str
    sample_count: int
    time_start: float
    time_end: float
    sample_interval: float | None
    sample_rate_hz: float | None
    scl_min: float
    scl_max: float
    sda_min: float
    sda_max: float
    scl_threshold: float
    sda_threshold: float
    estimated_scl_frequency_hz: float | None
    estimated_samples_per_bit: float | None
    warnings: list[str] = field(default_factory=list)


@dataclass
class DecodeResult:
    """Full decode output for one capture file."""

    capture: CaptureInfo
    transactions: list[Transaction]
    decoder_version: str
