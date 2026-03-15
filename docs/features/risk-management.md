# 📉 Risk Management

Trading at high frequency involves managing risk in milliseconds. ZeroOne includes several "Fail-Safe" systems to protected your capital.

---

## 🛑 Daily Drawdown Breaker
The bot monitors your P&L in real-time. If your losses for the day exceed a specific percentage (defined in `risk.max_daily_drawdown_pct`), the bot will:
1.  **Cancel all open orders.**
2.  **Close all active positions.**
3.  **Enter `HALTED` mode** and stop trading until the next day.

## 🌪️ Volatility Filter
The engine tracks price velocity. During extreme market "crashes" or "pumps", the bot briefly pauses new order placement to avoid being caught on the wrong side of a massive trend.

## ⏳ Stale Position Cleanup
The "Market Maker" strategy works best when neutral. If the bot is stuck in a position for too long (e.g., 20 minutes), it will automatically close it at market price. This ensures your capital isn't "locked" in a losing trade while other coins are profitable.

## 🧊 Margin Health Monitor
ZeroOne calculates your **Account Health** constantly. If your margin becomes too thin, the bot will stop opening new positions and focus only on **Closing** existing ones to protect you from liquidation.

---

### Remember:
> "The best trade is sometimes the one you don't make."
> 
> ZeroOne is designed to prioritize **Survival** over "Moonshots".
