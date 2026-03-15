"""
Data fetcher script — downloads historical klines from Binance Futures
for all target 01 Exchange altcoins.

Usage:
    python scripts/fetch_history.py [--days 30] [--timeframes 1m,3m,5m]
"""

from __future__ import annotations

import argparse
import sys
import time

# Add project root to path
sys.path.insert(0, str(__file__).rsplit("scripts", 1)[0])

from src.config import load_config
from src.data.binance import BinanceDataClient, o1_to_binance
from src.data.storage import save_candles


def p(msg: str):
    """Print with immediate flush (no buffering)."""
    print(msg, flush=True)


def main():
    parser = argparse.ArgumentParser(description="Fetch historical data from Binance Futures")
    parser.add_argument("--days", type=int, default=30, help="Days of history")
    parser.add_argument("--timeframes", default="1m,3m,5m", help="Comma-separated timeframes")
    parser.add_argument("--symbols", default=None, help="Specific symbols (comma-separated 01 symbols)")
    args = parser.parse_args()

    cfg = load_config()
    timeframes = args.timeframes.split(",")
    symbols = args.symbols.split(",") if args.symbols else cfg.active_symbols

    client = BinanceDataClient()

    p(f"\n{'='*60}")
    p(f"  NUOVOBOT — Binance Historical Data Fetcher")
    p(f"{'='*60}")
    p(f"  Days:       {args.days}")
    p(f"  Timeframes: {', '.join(timeframes)}")
    p(f"  Symbols:    {len(symbols)} altcoins")
    p(f"{'='*60}\n")

    success = []
    failed = []
    skipped = []

    total_tasks = len(symbols) * len(timeframes)
    done = 0

    for o1_sym in symbols:
        binance_sym = o1_to_binance(o1_sym)
        if not binance_sym:
            p(f"  ⚠ [{o1_sym}] Nessun mapping Binance — SKIP")
            skipped.append(o1_sym)
            done += len(timeframes)
            continue

        for tf in timeframes:
            done += 1
            progress = f"[{done}/{total_tasks}]"

            p(f"  {progress} {o1_sym} ({binance_sym}) {tf} ... ", )

            try:
                t0 = time.time()
                df = client.fetch_full_history(
                    symbol=binance_sym,
                    interval=tf,
                    days=args.days,
                )

                if df.empty:
                    p(f"       ❌ NESSUN DATO")
                    failed.append(f"{o1_sym}/{tf}")
                    continue

                save_candles(df, binance_sym, tf)
                elapsed = time.time() - t0
                p(f"       ✅ {len(df)} candele ({elapsed:.0f}s)")
                success.append(f"{o1_sym}/{tf}")

            except Exception as e:
                p(f"       ❌ ERRORE: {e}")
                failed.append(f"{o1_sym}/{tf}")

    # Summary
    p(f"\n{'='*60}")
    p(f"  RISULTATI")
    p(f"{'='*60}")
    p(f"  ✅ Completati: {len(success)}")
    p(f"  ❌ Falliti:    {len(failed)}")
    p(f"  ⚠ Skippati:   {len(skipped)}")

    if failed:
        p(f"\n  Falliti:")
        for f_item in failed:
            p(f"    - {f_item}")

    if skipped:
        p(f"\n  Skippati (no Binance mapping):")
        for s_item in skipped:
            p(f"    - {s_item}")

    p(f"\n{'='*60}")
    p(f"  Dati salvati in: data/*.parquet")
    p(f"{'='*60}\n")


if __name__ == "__main__":
    main()
