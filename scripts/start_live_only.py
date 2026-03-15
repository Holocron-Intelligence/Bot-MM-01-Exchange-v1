""" Start only the LiveTrader. """

import asyncio
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.config import load_config
from src.live.trader import LiveTrader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LiveTrader")

async def main():
    cfg = load_config()
    trader = LiveTrader(cfg)
    await trader.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
