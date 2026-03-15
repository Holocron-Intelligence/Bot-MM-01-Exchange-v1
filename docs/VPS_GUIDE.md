# ☁️ AWS Tokyo VPS Guide

For high-frequency trading on 01 Exchange, latency is king. We recommend hosting your bot in **AWS Tokyo (ap-northeast-1)**.

## Why Tokyo?
01 Exchange's infrastructure is optimized for Asian markets. Running the bot in Tokyo reduces network round-trip time, giving you a competitive edge in getting orders filled.

## Setup Steps

### 1. Launch Instance
- **Region**: Tokyo (ap-northeast-1)
- **AMI**: Ubuntu 22.04 LTS (Recommended)
- **Instance Type**: `t3.small` (Minimum) or `c5.large` (Optimal)
- **Storage**: 20GB gp3

### 2. Environment Setup
Connect via SSH and run:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv git -y
```

### 3. Deploy Bot
- Transfer your project files via SCP/SFTP or Git.
- Follow the `README.md` installation steps.

### 4. Keeping it Alive
Use `screen` or `tmux` to keep the bot running after you disconnect:
```bash
screen -S mmbot
python -m src.cli --dashboard
# Press Ctrl+A then D to detach
```

> [!TIP]
> Use Reserved Instances or Spot Instances on AWS to save up to 60-90% on monthly costs.
