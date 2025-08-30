#!/usr/bin/env python3

"""
Binance Real-time Market Data Collector

A production-ready Python application that connects to Binance API and records
1-minute timeframe market data and trade executions.

Author: AI Assistant
Date: August 2025
Version: 1.1
"""

import asyncio
import websockets
import json
import csv
import sqlite3
import logging
import signal
import sys
import time
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading
import queue
import os
from pathlib import Path
import ssl
import certifi

# Import configuration
try:
    from .config import CONFIG
except ImportError:
    # Fallback for direct execution
    import sys

    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import CONFIG


@dataclass
class TradeData:
    """Structure for individual trade data"""
    timestamp: int
    price: float
    quantity: float
    is_buyer_maker: bool
    trade_id: int


@dataclass
class CandleData:
    """Structure for 1-minute candle data with computed metrics"""
    timestamp: int
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float
    num_buyers: int
    num_sellers: int
    buyers_volume: float
    sellers_volume: float
    power_position: int
    max_buyers_per_second: int
    max_sellers_per_second: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class DataProcessor:
    """Processes trade data and computes candle metrics"""

    def __init__(self):
        self.trades_buffer: List[TradeData] = []
        self.second_trade_counts: Dict[int, Dict[str, int]] = defaultdict(lambda: {'buyers': 0, 'sellers': 0})
        self.current_minute_start: Optional[int] = None

    def add_trade(self, trade: TradeData):
        """Add trade to buffer and update second-level counts"""
        self.trades_buffer.append(trade)
        # Get second timestamp
        second_timestamp = trade.timestamp // 1000  # Convert to seconds
        if trade.is_buyer_maker:
            self.second_trade_counts[second_timestamp]['sellers'] += 1
        else:
            self.second_trade_counts[second_timestamp]['buyers'] += 1

    def process_minute_candle(self, kline_data: Dict) -> Optional[CandleData]:
        """Process completed 1-minute candle with trade data"""
        if not kline_data.get('x', False):  # Not closed candle
            return None
        open_time = int(kline_data['t'])
        close_time = int(kline_data['T'])

        # Filter trades for this minute
        minute_trades = [
            trade for trade in self.trades_buffer
            if open_time <= trade.timestamp <= close_time
        ]

        if not minute_trades:
            logging.warning(f"No trades found for candle {open_time}")
            num_buyers = 0
            num_sellers = 0
            buyers_volume = 0.0
            sellers_volume = 0.0
        else:
            # Calculate metrics
            num_buyers = sum(1 for trade in minute_trades if not trade.is_buyer_maker)
            num_sellers = sum(1 for trade in minute_trades if trade.is_buyer_maker)
            buyers_volume = sum(trade.quantity for trade in minute_trades if not trade.is_buyer_maker)
            sellers_volume = sum(trade.quantity for trade in minute_trades if trade.is_buyer_maker)

        # Power position
        if num_buyers > num_sellers:
            power_position = 1
        elif num_sellers > num_buyers:
            power_position = -1
        else:
            power_position = 0

        # Calculate max buyers and sellers per second
        start_second = open_time // 1000
        end_second = close_time // 1000
        max_buyers_per_second = 0
        max_sellers_per_second = 0

        for second in range(start_second, end_second + 1):
            buyers_count = self.second_trade_counts[second]['buyers']
            sellers_count = self.second_trade_counts[second]['sellers']
            max_buyers_per_second = max(max_buyers_per_second, buyers_count)
            max_sellers_per_second = max(max_sellers_per_second, sellers_count)

        # Create candle data
        candle = CandleData(
            timestamp=open_time,
            open_price=float(kline_data['o']),
            high_price=float(kline_data['h']),
            low_price=float(kline_data['l']),
            close_price=float(kline_data['c']),
            volume=float(kline_data['v']),
            num_buyers=num_buyers,
            num_sellers=num_sellers,
            buyers_volume=buyers_volume,
            sellers_volume=sellers_volume,
            power_position=power_position,
            max_buyers_per_second=max_buyers_per_second,
            max_sellers_per_second=max_sellers_per_second
        )

        # Clean up old data (keep only last 2 minutes of trades)
        cutoff_time = close_time - (2 * 60 * 1000)  # 2 minutes ago
        self.trades_buffer = [trade for trade in self.trades_buffer if trade.timestamp > cutoff_time]

        # Clean up old second counts
        cutoff_second = cutoff_time // 1000
        for second in list(self.second_trade_counts.keys()):
            if second < cutoff_second:
                del self.second_trade_counts[second]

        return candle


class DataStorage:
    """Handles data storage in various formats"""

    def __init__(self, output_format: str = 'csv', data_dir: str = 'data'):
        self.output_format = output_format
        # Ensure data directory is relative to project root
        if not os.path.isabs(data_dir):
            project_root = Path(__file__).parent.parent
            self.data_dir = project_root / data_dir
        else:
            self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        if output_format == 'sqlite':
            self._init_sqlite()
        elif output_format == 'csv':
            self._init_csv()

    def _init_sqlite(self):
        """Initialize SQLite database"""
        self.db_path = self.data_dir / 'binance_data.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
CREATE TABLE IF NOT EXISTS candles (
    timestamp INTEGER PRIMARY KEY,
    open_price REAL,
    high_price REAL,
    low_price REAL,
    close_price REAL,
    volume REAL,
    num_buyers INTEGER,
    num_sellers INTEGER,
    buyers_volume REAL,
    sellers_volume REAL,
    power_position INTEGER,
    max_buyers_per_second INTEGER,
    max_sellers_per_second INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')
        conn.commit()
        conn.close()

    def _init_csv(self):
        """Initialize CSV file"""
        self.csv_path = self.data_dir / f'binance_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        # Write header
        with open(self.csv_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                'timestamp', 'datetime', 'open', 'high', 'low', 'close', 'volume',
                'num_buyers', 'num_sellers', 'buyers_volume', 'sellers_volume', 'power_position',
                'max_buyers_per_second', 'max_sellers_per_second'
            ])

    def save_candle(self, candle: CandleData):
        """Save candle data to storage"""
        if self.output_format == 'csv':
            self._save_to_csv(candle)
        elif self.output_format == 'json':
            self._save_to_json(candle)
        elif self.output_format == 'sqlite':
            self._save_to_sqlite(candle)

    def _save_to_csv(self, candle: CandleData):
        """Save to CSV file"""
        datetime_str = datetime.fromtimestamp(candle.timestamp / 1000, tz=timezone.utc).isoformat()
        with open(self.csv_path, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([
                candle.timestamp, datetime_str, candle.open_price, candle.high_price,
                candle.low_price, candle.close_price, candle.volume,
                candle.num_buyers, candle.num_sellers, candle.buyers_volume, candle.sellers_volume,
                candle.power_position,
                candle.max_buyers_per_second, candle.max_sellers_per_second
            ])

    def _save_to_json(self, candle: CandleData):
        """Save to JSON file"""
        json_path = self.data_dir / f'binance_data_{datetime.now().strftime("%Y%m%d")}.jsonl'
        candle_dict = candle.to_dict()
        candle_dict['datetime'] = datetime.fromtimestamp(candle.timestamp / 1000, tz=timezone.utc).isoformat()
        with open(json_path, 'a') as file:
            json.dump(candle_dict, file)
            file.write('\n')

    def _save_to_sqlite(self, candle: CandleData):
        """Save to SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
INSERT OR REPLACE INTO candles
(timestamp, open_price, high_price, low_price, close_price, volume,
 num_buyers, num_sellers, buyers_volume, sellers_volume, power_position,
 max_buyers_per_second, max_sellers_per_second)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', (
            candle.timestamp, candle.open_price, candle.high_price, candle.low_price,
            candle.close_price, candle.volume, candle.num_buyers, candle.num_sellers,
            candle.buyers_volume, candle.sellers_volume, candle.power_position,
            candle.max_buyers_per_second, candle.max_sellers_per_second
        ))
        conn.commit()
        conn.close()


class BinanceDataCollector:
    """Main application class for collecting Binance market data"""

    def __init__(self, config: Dict):
        self.config = config
        self.symbol = config['symbol'].lower()
        self.running = False
        self.websocket = None
        self.reconnect_attempts = 0

        # Initialize components
        self.data_processor = DataProcessor()
        self.data_storage = DataStorage(
            output_format=config['output_format'],
            data_dir=config['data_dir']
        )

        # Setup logging
        self._setup_logging()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config['log_level'].upper())
        # Ensure log directory exists
        log_dir = Path(self.config['data_dir'])
        if not log_dir.is_absolute():
            project_root = Path(__file__).parent.parent
            log_dir = project_root / self.config['data_dir']
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "app.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )

        self.logger = logging.getLogger(__name__)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    async def _create_websocket_connection(self) -> websockets.WebSocketClientProtocol:
        streams = [
            f"{self.symbol}@kline_1m",
            f"{self.symbol}@trade"
        ]
        url = f"{self.config['base_url']}/stream?streams={'/'.join(streams)}"
        ssl_context = ssl.create_default_context(cafile=certifi.where())

        self.logger.info(f"Connecting to WebSocket: {url}")

        websocket = await websockets.connect(
            url,
            ping_interval=self.config['ping_interval'],
            ssl=ssl_context
        )

        return websocket

    async def _handle_message(self, message: str):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            if 'stream' not in data:
                return
            stream_name = data['stream']
            stream_data = data['data']

            if stream_name.endswith('@trade'):
                # Handle trade data
                trade = TradeData(
                    timestamp=int(stream_data['T']),
                    price=float(stream_data['p']),
                    quantity=float(stream_data['q']),
                    is_buyer_maker=stream_data['m'],
                    trade_id=int(stream_data['t'])
                )
                self.data_processor.add_trade(trade)

            elif stream_name.endswith('@kline_1m'):
                # Handle kline data
                kline_data = stream_data['k']
                if kline_data['x']:  # Candle is closed
                    candle = self.data_processor.process_minute_candle(kline_data)
                    if candle:
                        self.data_storage.save_candle(candle)
                        self.logger.info(
                            f"Saved candle: {datetime.fromtimestamp(candle.timestamp / 1000).isoformat()} "
                            f"O:{candle.open_price} H:{candle.high_price} L:{candle.low_price} C:{candle.close_price} "
                            f"Buyers:{candle.num_buyers} Sellers:{candle.num_sellers} "
                            f"BuyVol:{candle.buyers_volume:.4f} SellVol:{candle.sellers_volume:.4f} "
                            f"Power:{candle.power_position}"
                        )
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")

    async def _websocket_handler(self):
        """Main WebSocket handler with reconnection logic"""
        while self.running:
            try:
                self.websocket = await self._create_websocket_connection()
                self.reconnect_attempts = 0
                self.logger.info("WebSocket connection established")
                async for message in self.websocket:
                    if not self.running:
                        break
                    await self._handle_message(message)
            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("WebSocket connection closed")
                await self._handle_reconnection()
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")
                await self._handle_reconnection()

    async def _handle_reconnection(self):
        """Handle WebSocket reconnection with exponential backoff"""
        if not self.running:
            return
        self.reconnect_attempts += 1
        if self.reconnect_attempts > self.config['max_reconnect_attempts']:
            self.logger.error("Max reconnection attempts reached, shutting down")
            self.running = False
            return
        wait_time = min(self.config['reconnect_interval'] * (2 ** (self.reconnect_attempts - 1)), 300)
        self.logger.info(f"Reconnecting in {wait_time} seconds (attempt {self.reconnect_attempts})")
        await asyncio.sleep(wait_time)

    async def run(self):
        """Main application loop"""
        self.running = True
        self.logger.info(f"Starting Binance data collector for {self.config['symbol']}")
        try:
            await self._websocket_handler()
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        finally:
            self.running = False
            if self.websocket:
                await self.websocket.close()
            self.logger.info("Application stopped")


def main():
    """Entry point"""
    # Ensure data directory exists
    data_dir = Path(CONFIG['data_dir'])
    if not data_dir.is_absolute():
        # Make relative to project root
        project_root = Path(__file__).parent.parent
        data_dir = project_root / CONFIG['data_dir']
    data_dir.mkdir(exist_ok=True)

    # Create and run the collector
    collector = BinanceDataCollector(CONFIG)
    try:
        asyncio.run(collector.run())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
