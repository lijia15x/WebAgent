"""Deterministic I2C/SMBus protocol decoder.

This decoder must always follow Datasheet/SLVA704.pdf ("Understanding
the I2C Bus", TI SLVA704-June 2015) as the authoritative protocol
reference. Every rule below cites the SLVA704 section it implements, and
any change to this module must be checked against that datasheet first:

- START: SDA falls while SCL is high (SLVA704 Section 2.1.1, Figure 5).
- STOP: SDA rises while SCL is high (SLVA704 Section 2.1.1, Figure 5).
- Repeated START: a START that occurs before a STOP (the bus was already
  "active"); electrically identical to a plain START (SLVA704 Section
  2.1.2).
- Data bits are sampled once per SCL clock pulse and must be stable while
  SCL is high, so any SDA transition while SCL is high is unambiguously a
  START/STOP control symbol, never a data bit (SLVA704 Section 2.2).
- Each byte is 8 data bits (MSB first) followed by a 9th ACK/NACK bit;
  ACK = SDA low, NACK = SDA high (SLVA704 Section 2.3, Figures 6-7). Per
  SLVA704 Figure 7, the ACK/NACK clock period (period 9) is immediately
  followed by the STOP condition -- the datasheet's model has no
  additional clock pulse between the ACK/NACK bit and STOP.
- The first byte after a START/repeated-START is the address byte: bits
  [7:1] are the 7-bit address, bit [0] is R/W (0 = write, 1 = read)
  (SLVA704 Section 3, Figures 8-9).

This module only decodes the protocol; it does not judge whether the
address/data/sequence is "correct" for a given device or use case. That
is Task 2 (validation), which will consume this decoder's output plus a
reviewed device/test profile (see Requirements 7-8 and Roadmap Phase 2).
"""

from __future__ import annotations

from dataclasses import dataclass

from .csv_reader import RawCapture
from .digitize import DigitizeConfig, to_logic_levels
from .models import CaptureInfo, DecodedByte, DecodeResult, Transaction

DATASHEET_REFERENCE = "TI SLVA704 (Understanding the I2C Bus), Datasheet/SLVA704.pdf"


@dataclass
class DecoderConfig:
    """Decoder settings. Thresholds default to auto (min/max midpoint)."""

    scl_threshold: float | None = None
    sda_threshold: float | None = None
    hysteresis_fraction: float = 0.05


def decode_capture(raw: RawCapture, config: DecoderConfig | None = None) -> DecodeResult:
    """Digitize and decode a :class:`RawCapture` into I2C/SMBus transactions."""
    config = config or DecoderConfig()

    scl_levels, scl_threshold = to_logic_levels(
        raw.scl,
        DigitizeConfig(threshold=config.scl_threshold, hysteresis_fraction=config.hysteresis_fraction),
    )
    sda_levels, sda_threshold = to_logic_levels(
        raw.sda,
        DigitizeConfig(threshold=config.sda_threshold, hysteresis_fraction=config.hysteresis_fraction),
    )

    capture_info = _build_capture_info(raw, scl_threshold, sda_threshold)
    transactions = _decode_transactions(raw.time, scl_levels, sda_levels)
    _estimate_clock_timing(raw.time, scl_levels, capture_info)

    return DecodeResult(capture=capture_info, transactions=transactions, decoder_version=_decoder_version())


def _decoder_version() -> str:
    from . import __version__

    return __version__


def _build_capture_info(raw: RawCapture, scl_threshold: float, sda_threshold: float) -> CaptureInfo:
    times = raw.time
    sample_count = len(times)

    sample_interval: float | None = None
    sample_rate_hz: float | None = None
    if sample_count > 1:
        # Median step is robust to any single irregular sample.
        steps = sorted(times[i + 1] - times[i] for i in range(sample_count - 1))
        sample_interval = steps[len(steps) // 2]
        if sample_interval > 0:
            sample_rate_hz = 1.0 / sample_interval

    warnings: list[str] = list(raw.warnings)
    if sample_count < 2:
        warnings.append("Capture has fewer than 2 samples; decode will be empty.")

    return CaptureInfo(
        source_file=raw.source_file,
        sample_count=sample_count,
        time_start=times[0],
        time_end=times[-1],
        sample_interval=sample_interval,
        sample_rate_hz=sample_rate_hz,
        scl_min=min(raw.scl),
        scl_max=max(raw.scl),
        sda_min=min(raw.sda),
        sda_max=max(raw.sda),
        scl_threshold=scl_threshold,
        sda_threshold=sda_threshold,
        estimated_scl_frequency_hz=None,
        estimated_samples_per_bit=None,
        warnings=warnings,
    )


def _estimate_clock_timing(times: list[float], scl_levels: list[int], capture_info: CaptureInfo) -> None:
    """Fill in an informational SCL clock-rate estimate (not a pass/fail check)."""
    rising_edge_times = [
        times[i] for i in range(1, len(times)) if scl_levels[i - 1] == 0 and scl_levels[i] == 1
    ]
    if len(rising_edge_times) < 2:
        return
    periods = sorted(
        rising_edge_times[i + 1] - rising_edge_times[i] for i in range(len(rising_edge_times) - 1)
    )
    median_period = periods[len(periods) // 2]
    if median_period <= 0:
        return
    capture_info.estimated_scl_frequency_hz = 1.0 / median_period
    if capture_info.sample_interval:
        capture_info.estimated_samples_per_bit = median_period / capture_info.sample_interval


def _decode_transactions(times: list[float], scl: list[int], sda: list[int]) -> list[Transaction]:
    transactions: list[Transaction] = []
    current: Transaction | None = None
    bus_active = False
    bit_buffer: list[int] = []
    byte_start_time: float | None = None
    sequence_id = 0

    def close_current(end_time: float, completed: bool, note: str | None) -> None:
        nonlocal current, bit_buffer, byte_start_time
        assert current is not None
        current.end_time = end_time
        current.complete = completed
        if note:
            current.warnings.append(note)
        transactions.append(current)
        current = None
        bit_buffer = []
        byte_start_time = None

    for i in range(1, len(times)):
        scl_prev, scl_cur = scl[i - 1], scl[i]
        sda_prev, sda_cur = sda[i - 1], sda[i]

        is_start = scl_cur == 1 and sda_prev == 1 and sda_cur == 0
        is_stop = scl_cur == 1 and sda_prev == 0 and sda_cur == 1 and bus_active

        if is_start:
            repeated = bus_active
            if current is not None and not current.complete:
                pending = len(bit_buffer)
                note = (
                    f"Interrupted by a repeated START before a STOP; {pending} bit(s) "
                    "pending were discarded"
                    if pending
                    else "Interrupted by a repeated START before a STOP"
                )
                close_current(times[i], False, note)

            if not repeated:
                sequence_id += 1

            current = Transaction(
                index=len(transactions),
                sequence_id=sequence_id,
                start_time=times[i],
                end_time=None,
                repeated_start=repeated,
            )
            bus_active = True
            bit_buffer = []
            byte_start_time = None
            continue

        if is_stop:
            note = None
            if len(bit_buffer) == 1:
                # Per SLVA704 Figure 7, STOP follows immediately after the
                # ACK/NACK clock period (period 9) with no additional
                # clock pulse in between. One extra bit sampled here is
                # therefore a deviation from that documented 9-clock byte
                # structure, not something SLVA704 defines or explains;
                # report it factually rather than asserting it is benign.
                note = (
                    "1 extra bus clock observed immediately before STOP, beyond the "
                    "9-clock byte structure defined in SLVA704 Figure 7 (ACK/NACK "
                    "immediately followed by STOP); flagged for review, not assumed benign"
                )
            elif bit_buffer:
                note = f"STOP occurred mid-byte; {len(bit_buffer)} bit(s) discarded"
            close_current(times[i], True, note)
            bus_active = False
            continue

        # Sample a data/ACK bit on the SCL rising edge, only while a
        # transaction is open. Activity before the first observed START in
        # the capture is intentionally not decoded (see module docstring).
        if bus_active and current is not None and scl_prev == 0 and scl_cur == 1:
            if not bit_buffer:
                byte_start_time = times[i]
            bit_buffer.append(sda_cur)

            if len(bit_buffer) == 9:
                value = 0
                for bit in bit_buffer[:8]:
                    value = (value << 1) | bit
                ack = bit_buffer[8] == 0
                byte_index = len(current.bytes)
                current.bytes.append(
                    DecodedByte(
                        index=byte_index,
                        value=value,
                        ack=ack,
                        start_time=byte_start_time if byte_start_time is not None else times[i],
                        end_time=times[i],
                    )
                )

                if byte_index == 0:
                    current.address_7bit = value >> 1
                    current.direction = "read" if (value & 0x01) else "write"
                    current.address_ack = ack

                bit_buffer = []
                byte_start_time = None

    if current is not None:
        note = (
            f"Capture ended mid-byte with {len(bit_buffer)}/9 bit(s) sampled (truncated)"
            if bit_buffer
            else "Capture ended without a STOP condition (truncated)"
        )
        close_current(times[-1], False, note)

    return transactions
