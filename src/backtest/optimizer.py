"""
Multi-config batch backtester ? runs parameter sweeps
across timeframes, grid settings, and risk parameters.
"""

from __future__ import annotations

import copy
import itertools
import logging
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from src.backtest.engine import BacktestEngine, BacktestResult
from src.config import Config, load_config
from src.data.storage import load_candles

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Result from batch optimization."""
    results: list[BacktestResult]
    best_by_sharpe: BacktestResult | None = None
    best_by_return: BacktestResult | None = None
    best_by_calmar: BacktestResult | None = None
    total_configs: int = 0
    elapsed_seconds: float = 0.0

    def summary_df(self) -> pd.DataFrame:
        """Create summary DataFrame sorted by Sharpe ratio."""
        rows = []
        for r in self.results:
            rows.append({
                "symbol": r.symbol,
                "timeframe": r.timeframe,
                "return_pct": r.total_return_pct,
                "sharpe": r.sharpe_ratio,
                "max_dd_pct": r.max_drawdown_pct,
                "win_rate": r.win_rate,
                "profit_factor": r.profit_factor,
                "total_trades": r.total_trades,
                "calmar": r.calmar_ratio,
                "sortino": r.sortino_ratio,
                "total_fees": r.total_fees,
                **r.config_params,
            })
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("sharpe", ascending=False)
        return df


def _run_single_backtest(args: tuple) -> BacktestResult | None:
    """Worker function for parallel backtest execution."""
    config_dict, symbol, binance_symbol, timeframe, indicators = args

    try:
        cfg = load_config()
        # Override with parameter combo
        cfg.timeframe = timeframe
        for key, val in config_dict.items():
            parts = key.split(".")
            obj = cfg
            for p in parts[:-1]:
                obj = getattr(obj, p)
            setattr(obj, parts[-1], val)

        # Load cached data
        df = load_candles(binance_symbol, timeframe)
        if df.empty or len(df) < 100:
            logger.warning("Insufficient data for %s %s", symbol, timeframe)
            return None

        engine = BacktestEngine(cfg)
        result = engine.run(df, symbol=symbol, indicators=indicators)

        # Tag with config params
        result.config_params = {
            "timeframe": timeframe,
            **config_dict,
        }
        return result
    except Exception as e:
        logger.error("Backtest failed for %s: %s", symbol, e)
        return None


class BatchOptimizer:
    """
    Runs parameter sweeps across multiple configurations.

    Default parameter grid:
    - Timeframes: 1m, 3m, 5m
    - Grid levels: 3, 5, 7
    - ATR spacing mult: 0.3, 0.5, 0.7, 1.0
    - Stop ATR mult (range): 1.0, 1.5, 2.0
    - Risk per trade: 0.5%, 1.0%, 1.5%, 2.0%
    """

    DEFAULT_GRID = {
        "grid.levels": [5, 8],
        "grid.spacing_atr_mult": [0.5],
        "risk.risk_per_trade_pct": [1.0],
        "market_maker.fixed_tp_bps": [15],
        "market_maker.tp_atr_mult": [1.5],
        "indicators.adx_trend_threshold": [25],
        "market_maker.stale_candles": [20, 60],
    }

    def __init__(
        self,
        timeframes: list[str] | None = None,
        param_grid: dict[str, list] | None = None,
        max_workers: int = 4,
        max_dd_filter: float = 30.0,
    ):
        self.timeframes = timeframes or ["1m", "3m", "5m"]
        self.param_grid = param_grid or self.DEFAULT_GRID
        self.max_workers = max_workers
        self.max_dd_filter = max_dd_filter

    def generate_configs(self) -> list[dict[str, Any]]:
        """Generate all parameter combinations."""
        keys = list(self.param_grid.keys())
        values = list(self.param_grid.values())
        combos = list(itertools.product(*values))

        configs = []
        for combo in combos:
            cfg = dict(zip(keys, combo))
            configs.append(cfg)

        logger.info("Generated %d parameter combinations", len(configs))
        return configs

    def run(
        self,
        symbols: list[tuple[str, str]],  # [(o1_symbol, binance_symbol), ...]
        verbose: bool = True,
    ) -> OptimizationResult:
        """
        Run batch optimization across all symbols, timeframes, and configs.

        Args:
            symbols: List of (o1_symbol, bybit_symbol) tuples
            verbose: Print progress

        Returns:
            OptimizationResult with all results
        """
        configs = self.generate_configs()
        total = len(configs) * len(symbols) * len(self.timeframes)

        if verbose:
            logger.info(
                "Starting batch: %d configs ? %d symbols ? %d timeframes = %d runs",
                len(configs), len(symbols), len(self.timeframes), total,
            )

        # Build task list with indicator caching
        t0 = time.time()
        tasks = []
        symbol_cache = {}  # (symbol, timeframe) -> indicators df

        for o1_sym, binance_sym in symbols:
            for tf in self.timeframes:
                # Pre-calculate indicators once per symbol/timeframe
                # (Assuming indicator parameters are constant across this batch)
                df = load_candles(binance_sym, tf)
                if df.empty:
                    continue
                
                # Check if we should cache (no indicator params in grid)
                has_indicator_sweep = any(k.startswith("indicators.") for k in self.param_grid.keys())
                
                inds = None
                if not has_indicator_sweep:
                    cfg = load_config()
                    from src.indicators.core import compute_all
                    inds = compute_all(
                        df,
                        rsi_period=cfg.indicators.rsi_period,
                        adx_period=cfg.indicators.adx_period,
                        atr_period=cfg.indicators.atr_period,
                        momentum_period=cfg.indicators.momentum_period,
                        vwap_session_hours=cfg.indicators.vwap_session_hours,
                    )
                
                for cfg_dict in configs:
                    tasks.append((cfg_dict, o1_sym, binance_sym, tf, inds))

        # Run in parallel or sequential
        results: list[BacktestResult] = []
        completed = 0

        if self.max_workers <= 1:
            logger.info("Running sequentially (max_workers <= 1)")
            for t in tasks:
                completed += 1
                result = _run_single_backtest(t)
                if result is not None:
                    if result.max_drawdown_pct <= self.max_dd_filter:
                        results.append(result)
                if verbose and (completed % 5 == 0 or total < 20):
                    logger.info("Progress: %d / %d", completed, total)
        else:
            with ProcessPoolExecutor(max_workers=self.max_workers) as pool:
                futures = {pool.submit(_run_single_backtest, t): t for t in tasks}

                for future in as_completed(futures):
                    completed += 1
                    try:
                        result = future.result()
                        if result is not None:
                            if result.max_drawdown_pct <= self.max_dd_filter:
                                results.append(result)
                    except Exception as e:
                        logger.error("Worker failed: %s", e)

                    if verbose and (completed % 10 == 0 or total < 50):
                        logger.info("Progress: %d / %d", completed, total)

        elapsed = time.time() - t0

        # Find bests
        best_sharpe = max(results, key=lambda r: r.sharpe_ratio) if results else None
        best_return = max(results, key=lambda r: r.total_return_pct) if results else None
        best_calmar = max(results, key=lambda r: r.calmar_ratio) if results else None

        return OptimizationResult(
            results=results,
            best_by_sharpe=best_sharpe,
            best_by_return=best_return,
            best_by_calmar=best_calmar,
            total_configs=total,
            elapsed_seconds=round(elapsed, 1),
        )
