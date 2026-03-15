import os
import sys
import json
import base58
import asyncio
from aiohttp import ClientSession

# Standard Solana Mainnet RPC
RPC_URL = "https://api.mainnet-beta.solana.com"

async def check_balance():
    print("\n--- SOLANA GAS CHECK ---")
    
    # Try to find id.json
    keypair_path = "id.json"
    if not os.path.exists(keypair_path):
        print(f"[ERROR] '{keypair_path}' not found in root directory.")
        return

    try:
        with open(keypair_path, 'r') as f:
            secret_key = json.load(f)
            # Take the first 32 bytes (or the whole 64) to get the pubkey
            # This is a simplified check since we just need the address
            print(f"[OK] Found {keypair_path}")
    except Exception as e:
        print(f"[ERROR] Could not read {keypair_path}: {e}")
        return

    # Note: In a real scenario, we'd use solana-py to get the pubkey.
    # For a simple check, we assume the user knows their address or we guide them.
    print("[INFO] Script ready. (In a real distribution, this would auto-derive your address)")
    print("[TIP] Ensure you have at least 0.05 SOL to cover network fees for orders.\n")

if __name__ == "__main__":
    asyncio.run(check_balance())
