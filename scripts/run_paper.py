""" Entry point to run the bot in Paper Trading mode (CLI only). """

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import load_config
from src.live.trader import LiveTrader

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("paper_trading.log")
    ]
)
logger = logging.getLogger("NuovoBot")

async def run_bot_only():
    """Runs the LiveTrader only."""
    cfg = load_config()
    trader = LiveTrader(cfg)
    
    logger.info("Bot starting in Paper Trading mode (CLI Optimized)...")
    
    # Start the trader and await it
    await trader.start()

if __name__ == "__main__":
    try:
        asyncio.run(run_bot_only())
    except KeyboardInterrupt:
        logger.info("\nNuovoBot stopped by user.")
    except Exception as e:
        logger.error(f"NuovoBot crashed: {e}", exc_info=True)
