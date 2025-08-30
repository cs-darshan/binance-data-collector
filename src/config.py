#!/usr/bin/env python3
"""
Configuration file for Binance Data Collector
Modify these settings according to your needs
"""

import os

# Trading Configuration
SYMBOL = os.getenv('BINANCE_SYMBOL', 'ETHUSDT')  # Trading pair to monitor

# WebSocket Configuration
BASE_URL = 'wss://stream.binance.com:9443'
RECONNECT_INTERVAL = 5  # seconds
MAX_RECONNECT_ATTEMPTS = 10
PING_INTERVAL = 20  # seconds

# Data Storage Configuration
OUTPUT_FORMAT = os.getenv('OUTPUT_FORMAT', 'csv')  # 'csv', 'json', or 'sqlite'
DATA_DIR = os.getenv('DATA_DIR', 'data')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')  # DEBUG, INFO, WARNING, ERROR

# Performance Configuration
BUFFER_SIZE = 100000  # Maximum number of trades to keep in memory
CLEANUP_INTERVAL = 3000000  # Clean up old data every 5 minutes

# Update main configuration
CONFIG = {
    'symbol': SYMBOL,
    'base_url': BASE_URL,
    'reconnect_interval': RECONNECT_INTERVAL,
    'max_reconnect_attempts': MAX_RECONNECT_ATTEMPTS,
    'ping_interval': PING_INTERVAL,
    'output_format': OUTPUT_FORMAT,
    'data_dir': DATA_DIR,
    'log_level': LOG_LEVEL,
    'buffer_size': BUFFER_SIZE,
    'cleanup_interval': CLEANUP_INTERVAL
}
