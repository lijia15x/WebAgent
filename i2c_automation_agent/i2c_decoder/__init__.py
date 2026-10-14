"""Deterministic I2C/SMBus waveform decoder (HWV Task 1).

This package converts an oscilloscope CSV capture of an I2C/SMBus bus
(timestamp, SCL voltage, SDA voltage) into structured, timestamped
transactions: START/repeated-START/STOP boundaries, 7-bit address,
read/write direction, command/data bytes, byte length, and ACK/NACK.

Scope note (per 06 Aug 2026 HWV meeting): this package performs protocol
decoding only. It does not perform electrical/signal-integrity diagnosis
(voltage-level pass/fail, rise-time, glitches, etc.). See
I2C_SMBus_HWV_Development_Plan.xlsx, "Requirements - WIP", requirement 1.
"""

from .models import CaptureInfo, DecodedByte, DecodeResult, Transaction
from .csv_reader import RawCapture, read_capture
from .digitize import DigitizeConfig, to_logic_levels
from .decoder import DecoderConfig, decode_capture

__version__ = "0.1.0"

__all__ = [
    "CaptureInfo",
    "DecodedByte",
    "DecodeResult",
    "Transaction",
    "RawCapture",
    "read_capture",
    "DigitizeConfig",
    "to_logic_levels",
    "DecoderConfig",
    "decode_capture",
    "__version__",
]
