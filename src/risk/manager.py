"""
Risk management ? position sizing, stop-loss, and drawdown control.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ? Position Sizing ?

@dataclass
class SizeResult:
    size_usd: float       # Dollar size
    size_base: float      # Base asset size
    risk_usd: float       # Dollar amount at risk
    leverage_used: float  # Effective leverage


def compute_position_size(
    capital: float,
    risk_per_trade_pct: float,
    atr_value: float,
    stop_atr_mult: float,
    current_price: float,
    max_position_pct: float = 20.0,
    max_leverage: float = 20.0,
) -> SizeResult:
    """
    ATR-based dynamic position sizing.

    Logic: size = (risk_budget) / (stop_distance)
    Where risk_budget = capital * risk_per_trade_pct / 100
    And stop_distance = atr * stop_atr_mult

    This ensures we risk the same $ amount per trade regardless
    of volatility ? more volatile ? smaller position.

    Args:
        capital: Current total capital (USD)
        risk_per_trade_pct: % of capital to risk per trade
        atr_value: Current ATR value
        stop_atr_mult: Stop-loss distance in ATR multiples
        current_price: Current market price
        max_position_pct: Max % of capital in one position
        max_leverage: Max leverage allowed by exchange
    """
    if atr_value <= 0 or current_price <= 0:
        return SizeResult(size_usd=0, size_base=0, risk_usd=0, leverage_used=0)

    # Risk budget in USD
    risk_usd = capital * (risk_per_trade_pct / 100.0)

    # Stop distance in USD
    stop_distance = atr_value * stop_atr_mult

    # Size in base asset units
    size_base = risk_usd / stop_distance

    # Size in USD
    size_usd = size_base * current_price

    # Cap at max position % of capital
    max_usd = capital * (max_position_pct / 100.0)
    if size_usd > max_usd:
        size_usd = max_usd
        size_base = size_usd / current_price

    # Cap at max leverage
    max_leveraged = capital * max_leverage
    if size_usd > max_leveraged:
        size_usd = max_leveraged
        size_base = size_usd / current_price

    leverage_used = size_usd / capital if capital > 0 else 0

    return SizeResult(
        size_usd=round(float(size_usd), 4),
        size_base=round(float(size_base), 8),
        risk_usd=round(float(risk_usd), 4),
        leverage_used=round(float(leverage_used), 2),
    )


# ? Adaptive Stop-Loss ?

def compute_stop_loss(
    entry_price: float,
    side: str,
    atr_value: float,
    stop_mult_range: float = 1.5,
    stop_mult_trend: float = 2.5,
    regime: str = "range",
) -> float:
    """
    Compute adaptive stop-loss price.

    Range mode: tighter stop (less ATR multiples)
    Trend mode: wider stop (more room to breathe)

    Args:
        entry_price: Fill price
        side: "BUY" or "SELL"
        atr_value: Current ATR
        stop_mult_range: ATR multiplier for range regime
        stop_mult_trend: ATR multiplier for trend regime
        regime: "range" or "trend"

    Returns:
        Stop-loss price
    """
    mult = stop_mult_trend if regime == "trend" else stop_mult_range
    distance = atr_value * mult

    if side == "BUY":
        return entry_price - distance
    else:
        return entry_price + distance


# ? Drawdown Monitor ?

@dataclass
class DrawdownState:
    """Daily drawdown tracking state."""
    day_start_capital: float = 0.0
    current_capital: float = 0.0
    peak_capital: float = 0.0
    max_drawdown_pct: float = 0.0
    current_drawdown_pct: float = 0.0
    is_halted: bool = False
    halt_reason: str = ""
    day_start_time: float = 0.0
    trades_today: int = 0
    pnl_today: float = 0.0

    @property
    def is_profitable_today(self) -> bool:
        return self.pnl_today > 0


class DrawdownMonitor:
    """
    Monitors daily P&L and halts trading if drawdown exceeds threshold.
    Resets at the start of each new day.
    """

    def __init__(self, max_daily_drawdown_pct: float = 5.0):
        self.max_dd_pct = max_daily_drawdown_pct
        self._state = DrawdownState()

    def initialize(self, capital: float, timestamp: float | None = None) -> None:
        """Initialize with starting capital for the day."""
        ts = timestamp or time.time()
        self._state = DrawdownState(
            day_start_capital=capital,
            current_capital=capital,
            peak_capital=capital,
            day_start_time=ts,
        )

    def update(self, current_capital: float, timestamp: float | None = None) -> DrawdownState:
        """
        Update with current capital and check drawdown.

        Returns:
            DrawdownState (check .is_halted)
        """
        if self._state.is_halted:
            return self._state

        # Check for new day (24h reset)
        ts = timestamp or time.time()
        if ts - self._state.day_start_time >= 86400:
            logger.info("New day ? resetting drawdown monitor")
            self.initialize(current_capital, ts)

        self._state.current_capital = current_capital
        self._state.peak_capital = max(self._state.peak_capital, current_capital)

        # P&L today
        self._state.pnl_today = current_capital - self._state.day_start_capital

        # Current drawdown from day start
        if self._state.day_start_capital > 0:
            dd = (self._state.day_start_capital - current_capital) / self._state.day_start_capital * 100
            self._state.current_drawdown_pct = max(0.0, float(dd))
            self._state.max_drawdown_pct = max(
                self._state.max_drawdown_pct,
                self._state.current_drawdown_pct,
            )

        # Check halt condition
        if self._state.current_drawdown_pct >= self.max_dd_pct:
            self._state.is_halted = True
            self._state.halt_reason = (
                f"Daily drawdown {self._state.current_drawdown_pct:.2f}% "
                f"exceeded max {self.max_dd_pct:.1f}%"
            )
            logger.critical("? %s", self._state.halt_reason)

        return self._state

    def record_trade(self, pnl: float) -> None:
        """Record a trade P&L."""
        self._state.trades_today += 1

    def force_halt(self, reason: str) -> None:
        """Manually halt trading."""
        self._state.is_halted = True
        self._state.halt_reason = reason
        logger.warning("Forced halt: %s", reason)

    def reset_halt(self, new_capital: float | None = None) -> None:
        """Reset halt state (e.g., manual override)."""
        self._state.is_halted = False
        self._state.halt_reason = ""
        if new_capital:
            self.initialize(new_capital)

    @property
    def state(self) -> DrawdownState:
        return self._state
