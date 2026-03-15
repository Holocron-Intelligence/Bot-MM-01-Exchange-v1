# 🔒 Security & Privacy

We believe that **Your Keys = Your Crypto**. ZeroOne is built with a "Privacy First" architecture.

---

## 🏠 100% Local Execution
Unlike many "Web-Based" bots, ZeroOne does not store your keys on a server. 
*   **The code runs on YOUR machine.**
*   **Your private keys never leave your device.**
*   **Your trading data is never uploaded to a cloud.**

## 📑 Open Signing Process
The bot uses the standard Solana Ed25519 signing algorithm. It prepares transactions locally and sends the signed payload directly to the 01 Exchange RPC. 

## 🛡️ Anti-DRM Transparency
The "Exchange ID" verification is a simple check against a public list. No sensitive account data is transmitted during the activation process.

## 🕵️ Data Anonymity
ZeroOne does not require your name, email, or any personal identification. It identifies your account only by your Public Key (Solana Address) to interact with the exchange.

---

### Security Best Practices:
*   **Use a Dedicated Wallet**: We recommend using a sub-wallet with only the funds you intend to trade.
*   **Keep Software Updated**: Always use the latest version to ensure security patches and exchange compatibility.
*   **Monitor Logs**: Regularly check the `logs/` folder to see exactly what transactions the bot is signing.
