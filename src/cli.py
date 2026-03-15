"""CLI entry point for NuovoBot."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import load_config, LOG_DIR
from src.live.trader import LiveTrader
from src.dashboard.app import run_dashboard

# Setup logging
log_file = LOG_DIR / "paper_trading.log"
file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
# Clear existing handlers to avoid conflicts with launcher
for h in root_logger.handlers[:]:
    root_logger.removeHandler(h)
root_logger.addHandler(logging.StreamHandler())
root_logger.addHandler(file_handler)

logger = logging.getLogger("NuovoBot")

async def run_bot_only():
    """Runs the LiveTrader only."""
    cfg = load_config()
    trader = LiveTrader(cfg)
    
    mode_str = "PAPER" if cfg.paper_mode else "REAL"
    logger.info(f"Bot starting in {mode_str} Trading mode...")
    
    # Start the trader and await it
    await trader.start()

async def run_bot_with_dashboard():
    """Runs both bot and dashboard, dashboard first for responsiveness."""
    cfg = load_config()
    trader = LiveTrader(cfg)
    
    mode_str = "PAPER" if cfg.paper_mode else "REAL"
    print(f"CLI_AUDIT: Bot starting. Capital=${cfg.capital}, Mode={mode_str}, Symbols={cfg.active_symbols}")
    logger.info(f"Bot starting in {mode_str} Trading mode with Dashboard...")
    
    # CRITICAL: Start Dashboard FIRST so the UI appears immediately
    # while the bot engine loads market info / candles in the background.
    dashboard_task = asyncio.create_task(run_dashboard(cfg))
    
    # Wait a tiny bit to let uvicorn bind the port
    await asyncio.sleep(2)
    
    try:
        # Run both concurrently so they don't block each other
        await asyncio.gather(
            trader.start(),
            dashboard_task
        )
    except Exception as e:
        logger.error(f"Bot engine crashed: {e}", exc_info=True)

def main():
    """Main CLI entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--dashboard":
        asyncio.run(run_bot_with_dashboard())
    else:
        asyncio.run(run_bot_only())

if __name__ == "__main__":
    main()
