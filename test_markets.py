import asyncio
import logging
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.api.client import O1Client

async def test_fetch():
    logging.basicConfig(level=logging.INFO)
    client = O1Client("https://zo-mainnet.n1.xyz")
    try:
        print("Fetching markets...")
        markets = await client.get_markets()
        print(f"Found {len(markets)} markets.")
        for sym in list(markets.keys())[:5]:
            print(f" - {sym}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(test_fetch())
