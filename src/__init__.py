"""
Binance Data Collector Package
"""

__version__ = '1.0.0'
__author__ = 'AI Assistant'

from .binance_data_collector import BinanceDataCollector
from .config import CONFIG

__all__ = ['BinanceDataCollector', 'CONFIG']
