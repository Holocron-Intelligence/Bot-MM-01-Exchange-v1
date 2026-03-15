"""
Adaptive grid generator ? creates price levels scaled by volatility
and biased by liquidity heatmap.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class GridLevel:
    """A single grid level."""
    price: float
    side: str            # "BUY" or "SELL"
    size: float          # Position size in base asset
    order_id: int | None = None   # Filled once order is placed
    is_filled: bool = False
    fill_price: float = 0.0
    stop_loss: float = 0.0


@dataclass
class GridState:
    """Current state of the adaptive grid."""
    levels: list[GridLevel] = field(default_factory=list)
    mid_price: float = 0.0
    spacing: float = 0.0
    regime: str = "range"  # "range" or "trend"
    bias_score: float = 0.0
    timestamp: float = 0.0

    @property
    def buy_levels(self) -> list[GridLevel]:
        return [l for l in self.levels if l.side == "BUY"]

    @property
    def sell_levels(self) -> list[GridLevel]:
        return [l for l in self.levels if l.side == "SELL"]

    @property
    def open_orders(self) -> list[GridLevel]:
        return [l for l in self.levels if l.order_id and not l.is_filled]

    @property
    def filled_orders(self) -> list[GridLevel]:
        return [l for l in self.levels if l.is_filled]


class AdaptiveGrid:
    """
    Generates grid levels that adapt to:
    1. Volatility (ATR) ? wider grid in volatile markets
    2. Liquidity bias ? asymmetric weighting toward liquidity concentration
    3. Regime ? trend vs range mode changes grid behavior
    """

    def __init__(
        self,
        num_levels: int = 5,
        spacing_atr_mult: float = 0.5,
        rebalance_threshold: float = 0.3,
    ):
        self.num_levels = num_levels
        self.spacing_atr_mult = spacing_atr_mult
        self.rebalance_threshold = rebalance_threshold
        self._current_grid: GridState | None = None

    def generate(
        self,
        mid_price: float,
        atr_value: float,
        bias_score: float = 0.0,
        regime: str = "range",
        base_size: float = 1.0,
        stop_atr_mult: float = 1.5,
        timestamp: float = 0.0,
    ) -> GridState:
        """
        Generate a new grid centered on mid_price.

        Args:
            mid_price: Current mid price
            atr_value: Current ATR value
            bias_score: Heatmap bias [-1, +1]. Positive = bias long
            regime: "range" or "trend"
            base_size: Base position size per level
            stop_atr_mult: Stop-loss distance in ATR multiples
            timestamp: Current timestamp

        Returns:
            GridState with all computed levels
        """
        spacing = atr_value * self.spacing_atr_mult

        if spacing <= 0:
            spacing = mid_price * 0.001  # Fallback: 0.1% of price

        levels: list[GridLevel] = []

        for i in range(1, self.num_levels + 1):
            # ? Buy levels (below mid) ?
            buy_price = mid_price - (spacing * i)
            buy_size = self._compute_size(
                base_size, bias_score, side="BUY",
                level_idx=i, regime=regime,
            )
            buy_stop = buy_price - (atr_value * stop_atr_mult)

            levels.append(GridLevel(
                price=round(buy_price, 8),
                side="BUY",
                size=round(buy_size, 8),
                stop_loss=round(buy_stop, 8),
            ))

            # ? Sell levels (above mid) ?
            sell_price = mid_price + (spacing * i)
            sell_size = self._compute_size(
                base_size, bias_score, side="SELL",
                level_idx=i, regime=regime,
            )
            sell_stop = sell_price + (atr_value * stop_atr_mult)

            levels.append(GridLevel(
                price=round(sell_price, 8),
                side="SELL",
                size=round(sell_size, 8),
                stop_loss=round(sell_stop, 8),
            ))

        # Sort buy levels descending (closest to mid first)
        # Sort sell levels ascending (closest to mid first)
        levels.sort(key=lambda l: l.price)

        state = GridState(
            levels=levels,
            mid_price=mid_price,
            spacing=spacing,
            regime=regime,
            bias_score=bias_score,
            timestamp=timestamp,
        )
        self._current_grid = state
        return state

    def _compute_size(
        self,
        base_size: float,
        bias_score: float,
        side: str,
        level_idx: int,
        regime: str,
    ) -> float:
        """
        Compute size for a grid level with asymmetric bias weighting.

        - If bias > 0 (liquidity above ? expect price to go up):
          ? Increase BUY sizes, decrease SELL sizes
        - If bias < 0 (liquidity below ? expect price to go down):
          ? Increase SELL sizes, decrease BUY sizes

        In trend mode, bias effect is amplified.
        """
        # Bias multiplier: 0.5 to 1.5
        if side == "BUY":
            bias_mult = 1.0 + (bias_score * 0.5)  # Positive bias ? more buys
        else:
            bias_mult = 1.0 - (bias_score * 0.5)  # Positive bias ? fewer sells

        # Clamp
        bias_mult = max(0.2, min(2.0, bias_mult))

        # In trend mode, amplify bias effect
        if regime == "trend":
            bias_mult = 1.0 + (bias_mult - 1.0) * 1.5

        # Reduce size for farther levels (1st level = 100%, Nth = 60%)
        distance_decay = 1.0 - (level_idx - 1) * 0.1
        distance_decay = max(0.6, distance_decay)

        return base_size * bias_mult * distance_decay

    def needs_rebalance(self, current_price: float) -> bool:
        """Check if grid needs rebalancing based on price movement."""
        if not self._current_grid:
            return True

        distance = abs(current_price - self._current_grid.mid_price)
        threshold = self._current_grid.spacing * self.rebalance_threshold
        return distance > threshold

    @property
    def current_grid(self) -> GridState | None:
        return self._current_grid
