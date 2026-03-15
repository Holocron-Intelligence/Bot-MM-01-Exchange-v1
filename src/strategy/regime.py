"""
Regime detector ? determines if market is in range or trend mode.
Uses ADX with hysteresis to avoid frequent flipping.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RegimeState:
    """Current market regime."""
    regime: str        # "range" or "trend"
    adx: float         # Current ADX value
    plus_di: float     # +DI
    minus_di: float    # -DI
    trend_direction: str  # "UP", "DOWN", or "NONE"
    confidence: float  # 0-1 confidence in current regime

    @property
    def is_trend(self) -> bool:
        return self.regime == "trend"

    @property
    def is_uptrend(self) -> bool:
        return self.regime == "trend" and self.trend_direction == "UP"

    @property
    def is_downtrend(self) -> bool:
        return self.regime == "trend" and self.trend_direction == "DOWN"


class RegimeDetector:
    """
    Determines market regime using ADX with hysteresis band
    to prevent frequent regime switches.

    ADX > upper_threshold ? TREND mode
    ADX < lower_threshold ? RANGE mode
    ADX between thresholds ? keep current regime (hysteresis)
    """

    def __init__(
        self,
        trend_threshold: float = 25.0,
        hysteresis_band: float = 3.0,
    ):
        self.upper_threshold = trend_threshold
        self.lower_threshold = trend_threshold - hysteresis_band
        self._current_regime = "range"

    def detect(
        self,
        adx_value: float,
        plus_di: float = 0.0,
        minus_di: float = 0.0,
    ) -> RegimeState:
        """
        Detect current regime from ADX and DI values.

        Args:
            adx_value: Current ADX value
            plus_di: +DI value
            minus_di: -DI value

        Returns:
            RegimeState with current classification
        """
        # Hysteresis logic
        if adx_value >= self.upper_threshold:
            self._current_regime = "trend"
        elif adx_value <= self.lower_threshold:
            self._current_regime = "range"
        # else: keep current regime (in hysteresis band)

        # Trend direction from DI
        if plus_di > minus_di:
            direction = "UP"
        elif minus_di > plus_di:
            direction = "DOWN"
        else:
            direction = "NONE"

        # Confidence: how far ADX is from threshold
        if self._current_regime == "trend":
            confidence = min(1.0, (adx_value - self.upper_threshold) / 20.0 + 0.5)
        else:
            confidence = min(1.0, (self.lower_threshold - adx_value) / 20.0 + 0.5)
        confidence = max(0.0, confidence)

        return RegimeState(
            regime=self._current_regime,
            adx=adx_value,
            plus_di=plus_di,
            minus_di=minus_di,
            trend_direction=direction if self._current_regime == "trend" else "NONE",
            confidence=confidence,
        )

    def reset(self) -> None:
        self._current_regime = "range"
