"""
Signal pipeline ? combines all indicators and heatmap bias
into entry/exit decisions for each grid level.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

from src.config import IndicatorConfig
from src.heatmap.engine import LiquidityBias
from src.strategy.regime import RegimeState

logger = logging.getLogger(__name__)


@dataclass
class Signal:
    """Composite trading signal."""
    allow_long: bool
    allow_short: bool
    long_weight: float      # 0-1: how aggressively to size longs
    short_weight: float     # 0-1: how aggressively to size shorts
    regime: str
    bias_direction: str
    reasons: list[str]      # Human-readable reasons

    @property
    def is_neutral(self) -> bool:
        return not self.allow_long and not self.allow_short


class SignalPipeline:
    """
    Combines indicator filters and heatmap bias into a composite signal.

    Filter pipeline:
    1. VWAP distance ? only enter if price is within range of VWAP
    2. RSI ? block overbought longs / oversold shorts
    3. Momentum ? confirm direction with rate of change
    4. Regime ? adapt behavior for range vs trend
    5. Heatmap bias ? weight orders asymmetrically
    6. Anomaly ? block all entries if conditions are anomalous
    """

    def __init__(self, config: IndicatorConfig | None = None):
        self.config = config or IndicatorConfig()

    def evaluate(
        self,
        indicators: pd.Series,
        bias: LiquidityBias,
        regime: RegimeState,
        include_reasons: bool = False,
    ) -> Signal:
        """
        Evaluate all filters and produce a composite signal.

        Args:
            indicators: Latest row from indicator DataFrame
            bias: Current liquidity bias
            regime: Current regime state
            include_reasons: Whether to collect diagnostic reason strings (slow)

        Returns:
            Signal with entry permissions and weights
        """
        allow_long = True
        allow_short = True
        long_weight = 1.0
        short_weight = 1.0
        reasons: list[str] = []

        # ? 0. Anomaly check ?
        if bias.is_anomalous:
            return Signal(
                allow_long=False, allow_short=False,
                long_weight=0.0, short_weight=0.0,
                regime=regime.regime,
                bias_direction="ANOMALY",
                reasons=["Market anomaly detected"] if include_reasons else [],
            )

        # ? 1. VWAP distance filter ?
        vwap_dist = indicators.get("vwap_distance", 0.0)
        max_dist = self.config.vwap_max_distance_pct

        if abs(vwap_dist) > max_dist:
            if vwap_dist > 0:
                long_weight *= 0.5
                if include_reasons: reasons.append(f"VWAP dist +{vwap_dist:.1f}%")
            else:
                short_weight *= 0.5
                if include_reasons: reasons.append(f"VWAP dist {vwap_dist:.1f}%")

        # ? 2. RSI filter ?
        rsi_val = indicators.get("rsi", 50.0)

        if rsi_val >= self.config.rsi_overbought:
            allow_long = False
            if include_reasons: reasons.append(f"RSI OB {rsi_val:.0f}")

        if rsi_val <= self.config.rsi_oversold:
            allow_short = False
            if include_reasons: reasons.append(f"RSI OS {rsi_val:.0f}")

        # ? 3. Momentum confirmation ?
        mom = indicators.get("momentum", 0.0)

        if mom > 0:
            long_weight *= 1.2
            short_weight *= 0.8
        elif mom < 0:
            long_weight *= 0.8
            short_weight *= 1.2

        if include_reasons: reasons.append(f"Mom: {mom:.2f}")

        # ? 4. Regime adaptation ?
        if regime.is_trend:
            if include_reasons: reasons.append(f"TREND {regime.regime}")
            if regime.is_uptrend:
                long_weight *= 1.3
                short_weight *= 0.5
            elif regime.is_downtrend:
                long_weight *= 0.5
                short_weight *= 1.3
        else:
            if include_reasons: reasons.append("RANGE")

        # ? 5. Heatmap bias weighting ?
        bias_score = bias.score

        if bias_score > 0.1:
            long_weight *= (1.0 + bias_score * 0.5)
            short_weight *= (1.0 - bias_score * 0.3)
            if include_reasons: reasons.append(f"Bias L {bias_score:+.2f}")
        elif bias_score < -0.1:
            short_weight *= (1.0 + abs(bias_score) * 0.5)
            long_weight *= (1.0 - abs(bias_score) * 0.3)
            if include_reasons: reasons.append(f"Bias S {bias_score:+.2f}")

        # ? Clamp weights ?
        long_weight = max(0.0, min(2.0, long_weight))
        short_weight = max(0.0, min(2.0, short_weight))

        return Signal(
            allow_long=allow_long,
            allow_short=allow_short,
            long_weight=long_weight,
            short_weight=short_weight,
            regime=regime.regime,
            bias_direction=bias.direction,
            reasons=reasons,
        )
