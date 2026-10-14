"""Convert analog voltage samples to digital logic levels.

Uses a Schmitt-trigger style threshold with hysteresis so that noise
sitting close to the logic threshold does not cause spurious toggles.
This is purely for reliable *protocol* decoding — it does not attempt to
grade signal quality (that would be electrical/signal-integrity analysis,
which is out of scope for this decoder; see Requirement 1).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class DigitizeConfig:
    """Digitization settings.

    ``threshold``: explicit logic threshold in volts. If ``None``, the
    threshold is computed automatically as the midpoint between the
    observed minimum and maximum voltage on that signal.

    ``hysteresis_fraction``: fraction of the observed voltage span
    (max - min) used as the total hysteresis band width around the
    threshold, to avoid chatter from noise near the threshold.
    """

    threshold: float | None = None
    hysteresis_fraction: float = 0.05


def to_logic_levels(values: list[float], config: DigitizeConfig | None = None) -> tuple[list[int], float]:
    """Convert a list of voltage samples to a list of 0/1 logic levels.

    Returns ``(levels, threshold_used)``.
    """
    if not values:
        raise ValueError("Cannot digitize an empty list of samples")

    config = config or DigitizeConfig()
    v_min = min(values)
    v_max = max(values)
    threshold = config.threshold if config.threshold is not None else (v_min + v_max) / 2.0
    band = config.hysteresis_fraction * (v_max - v_min)
    high_enter = threshold + band / 2.0
    low_enter = threshold - band / 2.0

    levels: list[int] = []
    state = 1 if values[0] >= threshold else 0
    levels.append(state)
    for value in values[1:]:
        if state == 0 and value >= high_enter:
            state = 1
        elif state == 1 and value <= low_enter:
            state = 0
        levels.append(state)

    return levels, threshold
