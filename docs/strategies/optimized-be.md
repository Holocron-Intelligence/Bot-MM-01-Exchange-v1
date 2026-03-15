# 🛡️ Optimized BE (Break-Even)

The **Optimized BE** variant is the "Shield" of the ZeroOne suite. It is specifically designed for users who prioritize **safety** while farming volume.

---

## 🛡️ The Philosophy: "Do No Harm"

The primary goal of Optimized BE is to ensure that at the end of the day, your wallet balance is as close to your starting balance as possible (or slightly higher), having generated thousands of dollars in volume.

### Key Logic Improvements:

### 1. Adaptive ATR Spreads
The bot uses a sophisticated **Average True Range (ATR)** calculation to determine the "noise" level of the market. It places orders just outside this noise to avoid being "picked off" by minor fluctuations.

### 2. Aggressive Exit Skew
In this version, if the bot accumulates a position, it will prioritize **exiting** that position at break-even over trying to squeeze out extra profit. This ensures capital is always liquid and ready for the next "clean" volume trade.

### 3. Capital Awareness
The engine constantly syncs with your wallet. If available margin drops, the bot automatically reduces order sizes to prevent "Margin Lock" or rejections.

---

## 📈 Ideal Use Case
*   **Low to Medium Volatility**: Perfect for stable trending or ranging markets.
*   **Balance Protection**: Best for users who cannot afford significant drawdowns during farming.
*   **Points Accumulation**: Generates consistent points with minimal "slippage" costs.

---

### Configuration Recommendation:
*   **Order Size**: 30%
*   **Timeframe**: 1m or 5m
*   **Markets**: 4-6 coins for every $100 of capital.
