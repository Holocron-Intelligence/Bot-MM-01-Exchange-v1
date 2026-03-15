import sys
from pathlib import Path
import time
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.api.client import O1Client

def main():
    print("Connecting to 01 Exchange...")
    client = O1Client("https://zo-mainnet.n1.xyz", keypair_path="id.json")
    
    pubkey = client.user_pubkey_b58
    print(f"User Pubkey: {pubkey}")
    
    user_info = client.get_user(pubkey)
    acc_id = user_info.get("accountIds", [0])[0]
    
    acc_info = client.get_account(acc_id)
    orders = acc_info.get("orders", [])
    
    if not orders:
        print("No open orders found! Margin should be clear.")
        return
        
    print(f"Found {len(orders)} open orders taking up margin. Canceling them...")
    
    success = 0
    for order in orders:
        oid = order.get("orderId")
        try:
            client.cancel_order(oid)
            print(f"- Canceled order {oid}")
            success += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"- Failed to cancel {oid}: {e}")
            
    print(f"\nDone. Successfully canceled {success} out of {len(orders)} orders.")

if __name__ == "__main__":
    main()
