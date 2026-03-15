"""
Pure Market Maker backtest engine.

Goal: MAXIMIZE VOLUME while keeping P&L at break-even or slightly positive.

Mechanism:
- Place a BUY order at (price - half_spread) and SELL at (price + half_spread)
- When BUY fills ? immediately set a SELL target at (fill + spread) to capture profit
- When SELL fills ? immediately set a BUY target at (fill - spread) to capture profit
- Inventory management: reduce size when position grows too large
- Stale position timeout: close at market after N candles if not matched
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from src.indicators.core import compute_all

logger = logging.getLogger(__name__)


@dataclass
class MMTrade:
    """Record of a market maker fill."""
    timestamp: pd.Timestamp
    side: str
    price: float
    size: float
    fee: float
    pnl: float = 0.0


@dataclass
class MMResult:
    """Market maker backtest result."""
    symbol: str
    timeframe: str
    initial_capital: float
    final_capital: float
    total_return_pct: float
    total_volume: float
    weekly_volume: float
    total_trades: int
    total_fees: float
    win_rate: float
    avg_pnl_per_trade: float
    max_drawdown_pct: float
    trades: list[MMTrade] = field(default_factory=list)


class MarketMakerEngine:
    """
    Pure market maker backtester.

    Strategy: continuously place tight bid/ask orders around
    the current price. Profit = spread - fees.
    """

    def __init__(
        self,
        initial_capital: float = 50.0,
        spread_bps: float = 15.0,       # Half-spread in basis points (each side)
        order_size_pct: float = 10.0,    # % of capital per order
        max_inventory_pct: float = 30.0, # Max % of capital in inventory
        stale_candles: int = 10,         # Close stale positions after N candles
        maker_fee_pct: float = 0.02,     # 2 bps maker
        taker_fee_pct: float = 0.05,     # 5 bps taker
        slippage_bps: float = 3.0,
        use_atr_spread: bool = True,     # Use ATR for dynamic spread
        atr_spread_mult: float = 0.3,    # Spread = ATR * this
        min_spread_bps: float = 8.0,     # Minimum spread floor
    ):
        self.initial_capital = initial_capital
        self.spread_bps = spread_bps
        self.order_size_pct = order_size_pct
        self.max_inventory_pct = max_inventory_pct
        self.stale_candles = stale_candles
        self.maker_fee = maker_fee_pct / 100
        self.taker_fee = taker_fee_pct / 100
        self.slippage_bps = slippage_bps
        self.use_atr_spread = use_atr_spread
        self.atr_spread_mult = atr_spread_mult
        self.min_spread_bps = min_spread_bps

    def run(self, df: pd.DataFrame, symbol: str = "UNKNOWN") -> MMResult:
        """Run market maker backtest on OHLCV data."""
        capital = self.initial_capital
        peak_capital = capital

        # Compute ATR for dynamic spread
        inds = compute_all(df, atr_period=14, rsi_period=14, adx_period=14,
                          momentum_period=10, vwap_session_hours=24)

        warmup = 20
        trades: list[MMTrade] = []
        equity: list[float] = []
        total_volume = 0.0
        total_fees = 0.0

        # Position tracking
        inventory = 0.0        # Net base asset (positive = long, negative = short)
        avg_entry = 0.0        # Weighted average entry price
        candles_in_position = 0

        for i in range(len(inds)):
            row = inds.iloc[i]
            ts = inds.index[i]

            if i < warmup:
                equity.append(capital)
                continue

            close = row["close"]
            high = row["high"]
            low = row["low"]
            atr_val = row.get("atr", 0)

            if atr_val <= 0 or np.isnan(atr_val) or close <= 0:
                equity.append(capital)
                continue

            # Calculate dynamic spread
            if self.use_atr_spread and atr_val > 0:
                atr_spread = (atr_val / close) * 10000  # ATR as bps of price
                spread_bps = max(atr_spread * self.atr_spread_mult, self.min_spread_bps)
            else:
                spread_bps = self.spread_bps

            half_spread = close * (spread_bps / 10000)

            # Order size based on available capital
            inventory_value = abs(inventory * close)
            max_inv = capital * (self.max_inventory_pct / 100)
            available = max(0, max_inv - inventory_value)

            order_usd = min(
                capital * (self.order_size_pct / 100),
                available if available > 0 else capital * (self.order_size_pct / 100) * 0.5
            )
            order_size = order_usd / close if close > 0 else 0

            if order_size <= 0:
                equity.append(capital + inventory * (close - avg_entry) if inventory != 0 else capital)
                continue

            # ? BUY side: bid at (close - half_spread) ?
            bid_price = close - half_spread
            if low <= bid_price:
                fill_price = bid_price * (1 + self.slippage_bps / 10000)
                fee = order_size * fill_price * self.maker_fee
                total_fees += fee
                capital -= fee

                # If we have short inventory, this closes part of it (realize P&L)
                if inventory < 0:
                    close_size = min(order_size, abs(inventory))
                    pnl = (avg_entry - fill_price) * close_size
                    capital += pnl
                    remaining = order_size - close_size

                    if close_size >= abs(inventory):
                        # Fully closed short, may go long
                        inventory = remaining
                        avg_entry = fill_price if remaining > 0 else 0
                    else:
                        inventory += order_size
                        # avg_entry stays the same for remaining short

                    trades.append(MMTrade(ts, "BUY", fill_price, order_size, fee, pnl))
                else:
                    # Adding to long or opening new long
                    if inventory > 0:
                        total_inv = inventory + order_size
                        avg_entry = (avg_entry * inventory + fill_price * order_size) / total_inv
                        inventory = total_inv
                    else:
                        inventory = order_size
                        avg_entry = fill_price
                    trades.append(MMTrade(ts, "BUY", fill_price, order_size, fee, 0))

                total_volume += order_size * fill_price
                candles_in_position = 0

            # ? SELL side: ask at (close + half_spread) ?
            ask_price = close + half_spread
            if high >= ask_price:
                fill_price = ask_price * (1 - self.slippage_bps / 10000)
                fee = order_size * fill_price * self.maker_fee
                total_fees += fee
                capital -= fee

                # If we have long inventory, this closes part of it
                if inventory > 0:
                    close_size = min(order_size, inventory)
                    pnl = (fill_price - avg_entry) * close_size
                    capital += pnl
                    remaining = order_size - close_size

                    if close_size >= inventory:
                        inventory = -remaining
                        avg_entry = fill_price if remaining > 0 else 0
                    else:
                        inventory -= order_size

                    trades.append(MMTrade(ts, "SELL", fill_price, order_size, fee, pnl))
                else:
                    # Adding to short or opening new short
                    if inventory < 0:
                        total_inv = abs(inventory) + order_size
                        avg_entry = (avg_entry * abs(inventory) + fill_price * order_size) / total_inv
                        inventory = -total_inv
                    else:
                        inventory = -order_size
                        avg_entry = fill_price
                    trades.append(MMTrade(ts, "SELL", fill_price, order_size, fee, 0))

                total_volume += order_size * fill_price
                candles_in_position = 0

            # ? Stale position timeout ?
            if abs(inventory) > 0:
                candles_in_position += 1
                if candles_in_position >= self.stale_candles:
                    # Close at market
                    if inventory > 0:
                        pnl = (close - avg_entry) * inventory
                        fee = abs(inventory * close) * self.taker_fee
                    else:
                        pnl = (avg_entry - close) * abs(inventory)
                        fee = abs(inventory * close) * self.taker_fee

                    capital += pnl - fee
                    total_fees += fee
                    total_volume += abs(inventory * close)
                    trades.append(MMTrade(ts, "CLOSE", close, abs(inventory), fee, pnl))
                    inventory = 0
                    avg_entry = 0
                    candles_in_position = 0

            # Update equity
            unrealized = 0
            if inventory > 0:
                unrealized = (close - avg_entry) * inventory
            elif inventory < 0:
                unrealized = (avg_entry - close) * abs(inventory)

            total_value = capital + unrealized
            equity.append(total_value)
            peak_capital = max(peak_capital, total_value)

        # Close remaining inventory at end
        if abs(inventory) > 0 and len(inds) > 0:
            close_price = inds.iloc[-1]["close"]
            if inventory > 0:
                pnl = (close_price - avg_entry) * inventory
            else:
                pnl = (avg_entry - close_price) * abs(inventory)
            fee = abs(inventory * close_price) * self.taker_fee
            capital += pnl - fee
            total_fees += fee
            total_volume += abs(inventory * close_price)

        # Compute metrics
        final_capital = capital
        total_return = (final_capital - self.initial_capital) / self.initial_capital * 100

        eq_series = pd.Series(equity)
        peak = eq_series.cummax()
        dd = ((peak - eq_series) / peak * 100)
        max_dd = dd.max() if len(dd) > 0 else 0

        closed = [t for t in trades if t.pnl != 0]
        winners = [t for t in closed if t.pnl > 0]
        win_rate = len(winners) / len(closed) * 100 if closed else 0
        avg_pnl = sum(t.pnl for t in closed) / len(closed) if closed else 0

        days = (inds.index[-1] - inds.index[0]).days if len(inds) > 1 else 1
        weeks = max(days / 7, 1)
        weekly_vol = total_volume / weeks

        return MMResult(
            symbol=symbol,
            timeframe="5m",
            initial_capital=self.initial_capital,
            final_capital=round(final_capital, 2),
            total_return_pct=round(total_return, 2),
            total_volume=round(total_volume, 2),
            weekly_volume=round(weekly_vol, 2),
            total_trades=len(trades),
            total_fees=round(total_fees, 4),
            win_rate=round(win_rate, 1),
            avg_pnl_per_trade=round(avg_pnl, 6),
            max_drawdown_pct=round(max_dd, 2),
            trades=trades,
        )
