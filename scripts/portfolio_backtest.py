"""
Portfolio backtest — runs ALL altcoins simultaneously with shared $50 capital.
Reports total volume, P&L, and per-coin breakdown.

Usage:
    python scripts/portfolio_backtest.py [--timeframe 5m] [--days 7]
"""
from __future__ import annotations

import argparse
import sys
import datetime

sys.path.insert(0, str(__file__).rsplit("scripts", 1)[0])

from src.config import load_config
from src.backtest.engine import BacktestEngine
from src.data.binance import o1_to_binance
from src.data.storage import load_candles


def main():
    parser = argparse.ArgumentParser(description="Portfolio backtest")
    parser.add_argument("--timeframe", default="5m", help="Timeframe")
    parser.add_argument("--days", type=int, default=7, help="Days to backtest")
    args = parser.parse_args()

    cfg = load_config()
    all_symbols = cfg.active_symbols
    timeframe = args.timeframe
    total_capital = cfg.backtest.initial_capital  # $50

    # Map symbols
    valid = []
    for sym in all_symbols:
        bsym = o1_to_binance(sym)
        if bsym:
            valid.append((sym, bsym))

    if not valid:
        print("No valid symbols found!")
        return

    # Allocate capital equally
    per_coin_capital = total_capital / len(valid)

    print(f"\n{'='*65}")
    print(f"  NUOVOBOT — Portfolio Backtest (Shared ${total_capital} Capital)")
    print(f"{'='*65}")
    print(f"  Timeframe:    {timeframe}")
    print(f"  Days:         {args.days}")
    print(f"  Coins:        {len(valid)}")
    print(f"  Capital/coin: ${per_coin_capital:.2f}")
    print(f"{'='*65}\n")

    total_volume = 0.0
    total_pnl = 0.0
    total_fees = 0.0
    total_trades = 0
    coin_results = []
    skipped = []

    for o1_sym, bsym in valid:
        try:
            df = load_candles(bsym, timeframe)
            if df.empty or len(df) < 100:
                skipped.append(o1_sym)
                continue

            # Filter to requested days
            last_ts = df.index[-1]
            start_ts = last_ts - datetime.timedelta(days=args.days)
            df = df[df.index >= start_ts]

            if len(df) < 50:
                skipped.append(o1_sym)
                continue

            # Override capital for this coin's slice
            coin_cfg = load_config()
            coin_cfg.timeframe = timeframe
            coin_cfg.backtest.initial_capital = per_coin_capital

            engine = BacktestEngine(coin_cfg)
            result = engine.run(df, symbol=o1_sym)

            vol = sum(t.price * t.size for t in result.trades)
            pnl = result.final_capital - per_coin_capital
            
            total_volume += vol
            total_pnl += pnl
            total_fees += result.total_fees
            total_trades += len(result.trades)

            coin_results.append({
                'symbol': o1_sym,
                'trades': len(result.trades),
                'volume': vol,
                'pnl': pnl,
                'return_pct': result.total_return_pct,
                'win_rate': result.win_rate,
                'max_dd': result.max_drawdown_pct,
                'fees': result.total_fees,
            })

        except Exception as e:
            skipped.append(f"{o1_sym} ({e})")
            continue

    # Sort by volume descending
    coin_results.sort(key=lambda x: x['volume'], reverse=True)

    # Print results
    print(f"{'Symbol':<12} {'Trades':>7} {'Volume':>12} {'P&L':>9} {'Ret%':>7} {'WR%':>6} {'DD%':>6} {'Fees':>7}")
    print("-" * 72)

    for r in coin_results:
        color = "+" if r['pnl'] >= 0 else ""
        print(
            f"{r['symbol']:<12} {r['trades']:>7} "
            f"${r['volume']:>10,.0f} "
            f"${r['pnl']:>+8.2f} "
            f"{r['return_pct']:>+6.1f}% "
            f"{r['win_rate']:>5.1f} "
            f"{r['max_dd']:>5.1f} "
            f"${r['fees']:>6.2f}"
        )

    # Summary
    days = args.days
    weeks = max(days / 7, 1)
    weekly_vol = total_volume / weeks
    final_capital = total_capital + total_pnl
    total_return = (total_pnl / total_capital) * 100

    print(f"\n{'='*65}")
    print(f"  PORTFOLIO SUMMARY ({days} days = {weeks:.1f} weeks)")
    print(f"{'='*65}")
    print(f"  Starting Capital:   ${total_capital:.2f}")
    print(f"  Final Capital:      ${final_capital:.2f}")
    print(f"  Total P&L:          ${total_pnl:+.2f} ({total_return:+.1f}%)")
    print(f"  Total Fees:         ${total_fees:.2f}")
    print(f"  Total Trades:       {total_trades:,}")
    print(f"  Active Coins:       {len(coin_results)}")
    print(f"  Skipped Coins:      {len(skipped)}")
    print(f"{'='*65}")
    print(f"  📊 TOTAL VOLUME:        ${total_volume:>12,.2f}")
    print(f"  📊 WEEKLY VOLUME:       ${weekly_vol:>12,.2f}")
    print(f"{'='*65}")

    # Profitable vs losing coins
    winners = [r for r in coin_results if r['pnl'] >= 0]
    losers = [r for r in coin_results if r['pnl'] < 0]
    print(f"\n  🟢 Profitable coins: {len(winners)}")
    print(f"  🔴 Losing coins:     {len(losers)}")

    if losers:
        print(f"\n  Coins to consider excluding:")
        for r in sorted(losers, key=lambda x: x['pnl']):
            print(f"    ✗ {r['symbol']} → ${r['pnl']:+.2f} ({r['return_pct']:+.1f}%)")

    if skipped:
        print(f"\n  Skipped (no data):")
        for s in skipped:
            print(f"    ⚠ {s}")

    print(f"\n{'='*65}\n")


if __name__ == "__main__":
    main()
