#!/usr/bin/env python3
"""
Setup script for Binance Data Collector
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

setup(
    name="binance-data-collector",
    version="1.0.0",
    description="Production-ready Binance market data collector with real-time WebSocket streaming",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AI Assistant",
    url="https://github.com/your-username/binance-data-collector",
    packages=find_packages(),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "websockets>=10.4",
        "requests>=2.28.0", 
        "pandas>=1.5.0",
        "numpy>=1.21.0",
        "asyncio-timeout>=4.0.2",
        "aiofiles>=0.8.0",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Financial and Insurance Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Office/Business :: Financial :: Investment",
    ],
    entry_points={
        "console_scripts": [
            "binance-collector=src.binance_data_collector:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/your-username/binance-data-collector/issues",
        "Source": "https://github.com/your-username/binance-data-collector",
    },
)
