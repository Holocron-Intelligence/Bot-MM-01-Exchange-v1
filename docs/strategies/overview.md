# Strategy Overview

ZeroOne Bot offers two distinct Market Making strategies, each optimized for different risk/reward profiles. Both strategies leverage high-frequency quoting and real-time inventory management.

## 1. Optimized BE (Safety First)
Designed for capital preservation and maximizing rebate accumulation with minimal downside risk.

*   **Logic**: Wide spreads and tight inventory control.
*   **Behavior**: Quickly skews quotes to flatten balance and minimize delta exposure.
*   **Best for**: Long-term stability and farming points with low volatility.

## 2. Safe Volume (Aggressive Balance)
Designed for high volume generation while maintaining strict P&L protection.

*   **Logic**: Tighter spreads for higher fill frequency and slightly larger position scaling.
*   **Behavior**: Aggressive quoting to capture every market move, but with protective stops to prevent significant drawdowns.
*   **Best for**: Climbing volume leaderboards while keeping the account healthy.

---

## Technical Indicators Used
Regardless of the profile chosen, the bot utilizes a sophisticated signal pipeline:

*   **CVD & RSI Divergence**: Filters entries to avoid trading into "toxic" momentum.
*   **Open Interest (OI) Analysis**: Detects predatory flow and large positioning shifts.
*   **Smart Indicators**: Dynamically skews prices based on market imbalance.
*   **Heatmap Bias**: Real-time orderbook depth analysis for trend detection.

## Risk Management Features
*   **Drawdown Breaker**: Automatically halts all trading if a daily loss threshold is hit.
*   **Volatility Pause**: Stops placing orders during extreme ATR spikes to avoid "catching knives."
*   **Stale Position Auto-Close**: Closes trades that haven't reached target Profit/Loss within a defined timeframe.
