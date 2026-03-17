
<p align="center">
  <img src="assets/agency_logo.jpg" alt="Holocron" width="120" />
</p>

<h1 align="center">ZeroOne</h1>
<p align="center">
  <strong>Professional Market Maker for <a href="https://01.xyz">01 Exchange</a></strong><br/>
  <em>by Holocron — AI Software Agency</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/exchange-01.xyz-00FF66?style=flat-square" />
  <img src="https://img.shields.io/badge/strategy-Break--Even-cyan?style=flat-square" />
  <img src="https://img.shields.io/badge/license-MIT-lightgrey?style=flat-square" />
</p>

---

> **🎯 Core Philosophy** — ZeroOne is designed to **generate the highest possible trading volume** while keeping your wallet at **Break-Even**. Farm rebates and rewards by producing massive volume, without losing capital.

> [!NOTE]
> **Ready out-of-the-box** — ZeroOne works immediately with its default configuration, no changes needed. However, we recommend customizing the parameters in `config/default.toml` to match your personal risk tolerance, capital, and farming goals.

> [!IMPORTANT]
> For **optimal performance**, run ZeroOne on an **AWS Tokyo (ap-northeast-1)** VPS. See the [VPS Setup Guide](docs/VPS_GUIDE.md).

---

> [!TIP]
> **Support the Project!**
> If you find this bot useful and want to support its continued development and improvement, please consider using our referral link when signing up for 01 Exchange:
> **[Register on 01 Exchange (Ref: 019c2e4e)](https://01.xyz/ref/019c2e4e-3be0-74e8-ab72-22e2ffb15398)**
>
> Your support helps us maintain the bot and add new professional features!

---

## ⚡ Quick Start

### Step 1 — Install dependencies

```bash
# Clone the repository
git clone https://github.com/YOUR_USER/zeroone.git && cd zeroone

# Run the one-click Windows installer
setup.bat
```

---

### Step 2 — Add your Private Key 🔑

> [!CAUTION]
> **This step is mandatory.** The bot cannot sign transactions without your private key.
> Never share this file with anyone, and never commit it to Git.

A template file **`id.json.example`** is already included in the project.

**Steps:**
1. Copy `id.json.example` → rename the copy to **`id.json`**
2. Open `id.json` and replace the placeholder with your **Base58 private key**
3. Save. Done ✅

```json
{
  "PRIVATE_KEY": "5Jkm3xyzABCDEFGHIJKLMN..."
}
```

Place **`id.json`** in the root folder of the project (same folder as `setup.bat`):

```
zeroone/
├── id.json       ← ✅ HERE
├── setup.bat
├── config/
└── src/
```

**How to get your Base58 private key:**

| Wallet | Steps |
| :--- | :--- |
| **Phantom** | Settings → Security & Privacy → **Export Private Key** → copy the string |
| **Solflare** | Settings → Export Wallet → **Private Key** → copy the string |
| **01 Exchange** | Use the private key of the keypair linked to your account |

> [!TIP]
> Use a **dedicated trading wallet** with only the capital you intend to use — not your main wallet.

---

### Step 3 — Launch the bot

Simply run the **Desktop Launcher GUI**:

```bash
python launcher.py
```

*(If you received the compiled version, simply double-click `ZeroOne.exe` or `Launcher.exe`).*

1. Paste your **Private Key** (Mandatory for Real Trading — you can skip this *only* if you already created `id.json`)
2. Select the coins you want to trade (minimum 1, limited by your capital)
3. Click **START BOT** and monitor your profit from the **LIVE MONITOR** tab!

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────┐
│                   ZeroOne Bot                   │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │Indicators│  │ Heatmap  │  │  Risk Engine  │  │
│  │RSI · ADX │  │ CVD · OI │  │ Stop · Sizing │  │
│  └────┬─────┘  └────┬─────┘  └──────┬───────┘  │
│       └──────┬───────┘               │          │
│         ┌────▼─────┐          ┌──────▼───────┐  │
│         │  Smart   │          │   Position   │  │
│         │  Score   │          │   Manager    │  │
│         └────┬─────┘          └──────┬───────┘  │
│              └──────────┬────────────┘          │
│                   ┌─────▼──────┐                │
│                   │  Grid MM   │                │
│                   │  Engine    │                │
│                   └─────┬──────┘                │
└─────────────────────────┼───────────────────────┘
                          │
                    ┌─────▼──────┐
                    │ 01 Exchange│
                    │    API     │
                    └────────────┘
```

### How It Works

1. **Indicators** (RSI, ADX, ATR, VWAP) generate a **Smart Score**
2. The **Grid Engine** places buy/sell orders around the fair price
3. Orders get filled → bot captures the spread → stays at **Break-Even**
4. The **Risk Engine** enforces stop-losses and position limits

```
|------- spread -------|------- spread -------|
     Buy Orders         Fair Price        Sell Orders
     $99,920            $100,000          $100,080
```

---

## ⚙️ Configuration

All settings live in **`config/default.toml`**:

### Strategy Presets

| Preset | `spread_bps` | `fixed_tp_bps` | Best For |
| :--- | :---: | :---: | :--- |
| 🛡️ **Safe Growth** | `15` | `5` | Capital growth & steady profit |
| 🚀 **Standard Farming** | `8` | `3` | Maximum volume & rebates |

### Key Parameters

```toml
[general]
capital = 100.0           # USD starting capital
paper_mode = true         # Set to false for real trading

[market_maker]
spread_bps = 8            # Distance from mid-price (basis points)
fixed_tp_bps = 3          # Take-profit target per trade
order_size_pct = 10.0     # % of capital per order
stop_loss_bps = 35        # Hard stop distance

[risk]
max_daily_drawdown_pct = 5.0   # Bot halts if daily loss > 5%
```

---

## 🪙 Coin Selection

Edit the `symbols` list in `config/default.toml`:

```toml
[markets]
symbols = ["HYPEUSD", "SUIUSD", "BERAUSD"]
```

Or select coins from the **Launcher GUI** — no file editing needed.

| Capital | Coins | Examples |
| :--- | :---: | :--- |
| **$50 – $200** | 2 – 4 | HYPE, SUI, BERA |
| **$200 – $1K** | 5 – 8 | + APT, AAVE, XRP |
| **$1K+** | 10+ | Full coverage |ntinua

> [!TIP]
> Fewer coins = bigger orders per pair = better fill rate.

---

## 📁 Project Structure

```
zeroone/
├── launcher.py            # GUI Launcher (CustomTkinter)
├── setup.bat              # One-click Windows installer
├── requirements.txt       # Python dependencies
├── config/
│   └── default.toml       # All bot parameters
├── src/
│   ├── api/               # 01 Exchange SDK & WebSocket
│   ├── live/
│   │   └── trader.py      # Core trading engine
│   ├── strategy/          # Grid MM logic
│   ├── indicators/        # RSI, ADX, ATR, VWAP
│   ├── heatmap/           # Orderbook analysis (CVD, OI)
│   ├── risk/              # Position sizing & stop-loss
│   ├── dashboard/         # FastAPI real-time dashboard
│   ├── backtest/          # Historical testing engine
│   └── cli.py             # CLI entry point
├── docs/                  # Guides & FAQ
└── scripts/               # Utilities (PnL, build)
```

---

## 💎 Features

| Feature | Description |
| :--- | :--- |
| **Dynamic Sizing** | Auto-adjusts order size based on wallet balance |
| **Inventory Skew** | Shifts quotes to flatten position bias |
| **Grid Trading** | Multi-level orders for deeper liquidity |
| **Drawdown Breaker** | Emergency halt on excessive daily loss |
| **Volatility Pause** | Stops quoting during price spikes |
| **Stale Position Mgmt** | Auto-closes old positions to free capital |
| **Live GUI Monitor** | Real-time desktop metrics and controls |
| **Paper Trading** | Full simulation before going live |

---

## 🖥️ Commands

```bash
# Launch the Graphical Desktop GUI (Recommended)
python launcher.py

# Launch CLI only (Advanced)
python -m src.cli


# Check SOL balance for gas
python scripts/check_sol.py
```

---

## 🛠️ Manual Setup (Linux / Mac)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env, then place id.json in root
python launcher.py
```

---

## 📚 Documentation

- [VPS Setup Guide](docs/VPS_GUIDE.md) — Deploy on AWS Tokyo
- [FAQ](docs/faq.md) — Common questions
- [Introduction](docs/introduction.md) — How the bot works
- [Disclaimer](docs/disclaimer.md) — Legal notice

---

## ⚖️ Disclaimer

This software is provided "as is", without warranty of any kind. Cryptocurrency trading involves significant risk and can result in the loss of your capital. **The author assumes no responsibility** for any financial loss resulting from the use of this bot. Use at your own risk.

---

## 📄 License

MIT — see [LICENSE](LICENSE) for details.

<p align="center">
  <sub>Built with ❤️ by <strong>Holocron</strong> — AI Software Agency</sub>
</p>
