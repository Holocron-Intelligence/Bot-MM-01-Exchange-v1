""" 01 Exchange WebSocket client for real-time market data. """

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional

import websockets
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

logger = logging.getLogger(__name__)

class O1WebSocketClient:
    """
    WebSocket client for 01 Exchange (Zo Mainnet).
    Handles real-time trades and orderbook snapshots.
    """

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/") + "/"
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._subscriptions: List[str] = [] # list of stream names like 'trades@HYPEUSD'
        self._callbacks: Dict[str, List[Callable]] = {
            "trades": [],
            "orderbook": [],
        }
        self._running = False
        self._reconnect_delay = 1.0

    def on_trade(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for trade events."""
        self._callbacks["trades"].append(callback)

    def on_orderbook(self, callback: Callable[[Dict[str, Any]], None]):
        """Register a callback for orderbook events."""
        self._callbacks["orderbook"].append(callback)

    def add_subscription(self, stream_type: str, market: str):
        """Add a stream to the multiplexed connection (e.g., 'trades', 'HYPEUSD')."""
        if stream_type == "orderbook":
            stream_type = "deltas" # 01 use 'deltas' for L2 updates
        
        stream = f"{stream_type}@{market.upper()}"
        if stream not in self._subscriptions:
            self._subscriptions.append(stream)

    async def start(self):
        """Start the WebSocket connection and message loop."""
        if not self._subscriptions:
            logger.warning("No streams to subscribe to.")
            return

        # Build multiplexed URL: base/stream1&stream2&...
        streams_query = "&".join(self._subscriptions)
        full_url = f"{self.base_url}{streams_query}"
        
        self._running = True
        while self._running:
            try:
                # Disable native ping/pong as 01 Exchange may not respond to them (causes 30s timeout)
                async with websockets.connect(full_url, ping_interval=None) as ws:
                    self.ws = ws
                    logger.info("Connected to 01 Multiplexed WebSocket: %s", full_url)
                    
                    self._reconnect_delay = 1.0
                    
                    while self._running:
                        try:
                            msg = await ws.recv()
                            data = json.loads(msg)
                            await self._handle_message(data)
                        except (ConnectionClosedError, ConnectionClosedOK):
                            logger.warning("WebSocket connection closed. Reconnecting...")
                            break
                        except Exception as e:
                            logger.error("Error processing WebSocket message: %s", e)
                            
            except Exception as e:
                if self._running:
                    logger.error("WebSocket connection failed (%s): %s. Retrying in %.1fs...", full_url, e, self._reconnect_delay)
                    await asyncio.sleep(self._reconnect_delay)
                    self._reconnect_delay = min(self._reconnect_delay * 2, 60.0)

    async def stop(self):
        """Stop the WebSocket client."""
        self._running = False
        ws = self.ws
        if ws is not None:
            self.ws = None
            await ws.close()

    async def _handle_message(self, data: Dict[str, Any]):
        """Dispatch message to registered callbacks."""
        channel = data.get("channel")
        if not channel:
            return

        # 01 uses 'trades' and 'deltas' as channels
        if channel == "trades":
            for cb in self._callbacks["trades"]:
                if asyncio.iscoroutinefunction(cb):
                    await cb(data)
                else:
                    cb(data)
        elif channel == "deltas":
            # Map 'deltas' to 'orderbook' callback for internal consistency
            for cb in self._callbacks["orderbook"]:
                if asyncio.iscoroutinefunction(cb):
                    await cb(data)
                else:
                    cb(data)
        else:
            logger.debug("Received unknown channel message: %s", channel)

async def main_test():
    """Simple test for the WebSocket client."""
    logging.basicConfig(level=logging.INFO)
    url = "wss://zo-mainnet.n1.xyz/ws"
    client = O1WebSocketClient(url)
    
    def handle_trade(data):
        print(f"Trade: {data}")

    client.on_trade(handle_trade)
    client.add_subscription("trades", "HYPEUSD")
    
    try:
        await client.start()
    except KeyboardInterrupt:
        await client.stop()

if __name__ == "__main__":
    asyncio.run(main_test())
