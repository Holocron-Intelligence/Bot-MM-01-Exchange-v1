"""
Backtest HTML report generator.
Creates interactive report with Plotly charts.
"""

from __future__ import annotations

import logging
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.backtest.engine import BacktestResult

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def generate_html_report(result: BacktestResult, output_path: Path | None = None) -> Path:
    """
    Generate an interactive HTML report for a backtest result.

    Args:
        result: BacktestResult from engine
        output_path: Optional custom output path

    Returns:
        Path to generated HTML file
    """
    if output_path is None:
        output_path = REPORTS_DIR / f"{result.symbol}_{result.timeframe}_report.html"

    # Create subplot figure
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=["Equity Curve", "Drawdown", "Trade P&L"],
    )

    _add_equity_curve(fig, result)

    _add_drawdown_curve(fig, result)

    _add_trade_pnl(fig, result)

    _apply_layout(fig, result)

    fig.write_html(str(output_path), include_plotlyjs="cdn")
    logger.info("Report generated: %s", output_path)
    return output_path


def _add_equity_curve(fig: go.Figure, result: BacktestResult) -> None:
    """Add equity curve and initial capital line to the figure."""
    # Equity curve
    fig.add_trace(
        go.Scatter(
            x=result.equity_curve.index,
            y=result.equity_curve.values,
            mode="lines",
            name="Equity",
            line={"color": "#00d4aa", "width": 2},
            fill="tozeroy",
            fillcolor="rgba(0, 212, 170, 0.1)",
        ),
        row=1, col=1,
    )

    # Initial capital line
    fig.add_hline(
        y=result.initial_capital, row=1, col=1,
        line_dash="dash", line_color="rgba(255,255,255,0.3)",
        annotation_text=f"Initial: ${result.initial_capital}",
    )


def _add_drawdown_curve(fig: go.Figure, result: BacktestResult) -> None:
    """Add drawdown curve to the figure."""
    fig.add_trace(
        go.Scatter(
            x=result.drawdown_curve.index,
            y=-result.drawdown_curve.values,
            mode="lines",
            name="Drawdown %",
            line={"color": "#ff4757", "width": 1.5},
            fill="tozeroy",
            fillcolor="rgba(255, 71, 87, 0.15)",
        ),
        row=2, col=1,
    )


def _add_trade_pnl(fig: go.Figure, result: BacktestResult) -> None:
    """Add trade P&L bar chart to the figure."""
    # Trade P&L scatter
    trade_data = [t for t in result.trades if t.pnl != 0]
    if trade_data:
        fig.add_trace(
            go.Bar(
                x=[t.timestamp for t in trade_data],
                y=[t.pnl for t in trade_data],
                name="Trade P&L",
                marker_color=[
                    "#00d4aa" if t.pnl > 0 else "#ff4757"
                    for t in trade_data
                ],
                opacity=0.7,
            ),
            row=3, col=1,
        )


def _apply_layout(fig: go.Figure, result: BacktestResult) -> None:
    """Apply layout and add metrics annotation to the figure."""
    # Layout
    fig.update_layout(
        template="plotly_dark",
        title={
            "text": (
                f"<b>{result.symbol}</b> | {result.timeframe} | "
                f"Sharpe: {result.sharpe_ratio:.2f} | "
                f"Return: {result.total_return_pct:+.1f}% | "
                f"Max DD: {result.max_drawdown_pct:.1f}%"
            ),
            "font": {"size": 16},
        },
        font={"family": "Inter, sans-serif"},
        showlegend=False,
        height=900,
        paper_bgcolor="#0a0a0a",
        plot_bgcolor="#111111",
    )

    # Add metrics annotation
    metrics_text = (
        f"<b>Summary</b><br>"
        f"Capital: ${result.initial_capital} ? ${result.final_capital}<br>"
        f"Trades: {result.total_trades} | Win Rate: {result.win_rate}%<br>"
        f"Profit Factor: {result.profit_factor:.2f}<br>"
        f"Sharpe: {result.sharpe_ratio:.2f} | Sortino: {result.sortino_ratio:.2f}<br>"
        f"Calmar: {result.calmar_ratio:.2f}<br>"
        f"Fees: ${result.total_fees:.2f}"
    )
    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        text=metrics_text,
        showarrow=False,
        font={"size": 11, "color": "#aaa"},
        align="left",
        bgcolor="rgba(0,0,0,0.6)",
        bordercolor="#333",
        borderwidth=1,
    )
