# Binance Real-time Market Data Collector

A production-ready Python application that connects to the Binance WebSocket API and records 1-minute timeframe market data with detailed trade execution metrics.

## 🚀 Features

- **Real-time Data Collection**: Streams 1-minute OHLC candles and trade data from Binance WebSocket API
- **Advanced Trade Metrics**: Computes buyer/seller ratios, power position, and peak activity per second
- **Multiple Storage Formats**: Supports CSV, JSON, and SQLite database storage
- **Robust Error Handling**: Automatic reconnection with exponential backoff
- **Production Ready**: Includes systemd service configuration for continuous operation
- **Cloud Deployment**: Ready for AWS EC2, DigitalOcean, or any Linux server
- **Comprehensive Monitoring**: Health checks and data analysis tools
- **Organized Structure**: Clean, maintainable codebase with proper separation of concerns

## 📊 Collected Data Points

For each completed 1-minute candle:

- **OHLC Data**: Open, High, Low, Close prices
- **Volume**: Trading volume for the period  
- **Trade Counts**: Number of buyer-initiated vs seller-initiated trades
- **Power Position**: +1 (buyers dominant), -1 (sellers dominant), 0 (neutral)
- **Peak Activity**: Highest number of buyers/sellers in any single second
- **Timestamps**: Unix timestamp and ISO datetime

## 📁 Project Structure

```
binance-data-collector/
├── src/                          # Source code
│   ├── __init__.py              # Package initialization
│   ├── binance_data_collector.py # Main application
│   └── config.py                # Configuration settings
├── scripts/                      # Utility scripts
│   ├── deploy.sh               # Automated deployment
│   ├── health_check.py         # Health monitoring
│   └── analyze_data.py         # Data analysis
├── config/                      # Configuration files
│   └── binance-collector.service # Systemd service
├── data/                        # Data storage (created at runtime)
├── examples/                    # Example files
│   └── sample_output.csv       # Sample data output
├── docs/                        # Documentation (future)
├── requirements.txt             # Python dependencies
├── setup.py                    # Package setup
└── README.md                   # This file
```

## 📋 Requirements

- Python 3.8+
- Linux server (Ubuntu 20.04+ recommended)
- 500MB+ free disk space (for data storage)
- Internet connection

## 🛠 Quick Start

### Option 1: One-Click Deployment (Recommended)

1. **Download and extract** the project:
   ```bash
   wget https://github.com/your-repo/binance-data-collector/releases/latest/download/binance-data-collector.zip
   unzip binance-data-collector.zip
   cd binance-data-collector
   ```

2. **Run automated deployment**:
   ```bash
   sudo ./scripts/deploy.sh
   ```

The deployment script will:
- Install system dependencies
- Create dedicated user account
- Set up Python virtual environment
- Configure systemd service
- Start data collection automatically

### Option 2: Manual Installation

1. **Install system dependencies**:
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv git -y
   ```

2. **Set up the application**:
   ```bash
   sudo mkdir -p /opt/binance-data-collector
   sudo cp -r * /opt/binance-data-collector/
   cd /opt/binance-data-collector

   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure and start service**:
   ```bash
   sudo cp config/binance-collector.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable binance-collector
   sudo systemctl start binance-collector
   ```

## ⚙️ Configuration

Edit `src/config.py` to customize settings:

```python
# Trading Configuration
SYMBOL = 'BTCUSDT'  # Change to any Binance trading pair

# Storage Configuration  
OUTPUT_FORMAT = 'csv'  # Options: 'csv', 'json', 'sqlite'
DATA_DIR = 'data'  # Directory for output files

# Performance Settings
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
```

### Environment Variables

Configure via environment variables:

```bash
export BINANCE_SYMBOL=ETHUSDT
export OUTPUT_FORMAT=sqlite
export LOG_LEVEL=DEBUG
export DATA_DIR=/custom/data/path
```

## 🌐 Cloud Deployment

### AWS EC2

1. **Launch Instance**: Ubuntu 20.04 LTS, t2.micro
2. **Upload and deploy**:
   ```bash
   scp -i your-key.pem binance-data-collector.zip ubuntu@your-ec2-ip:
   ssh -i your-key.pem ubuntu@your-ec2-ip
   unzip binance-data-collector.zip
   cd binance-data-collector
   sudo ./scripts/deploy.sh
   ```

### DigitalOcean

1. **Create Droplet**: Ubuntu 20.04, Basic $5/month
2. **Deploy**:
   ```bash
   scp binance-data-collector.zip root@your-droplet-ip:
   ssh root@your-droplet-ip
   unzip binance-data-collector.zip
   cd binance-data-collector
   sudo ./scripts/deploy.sh
   ```

## 📱 Management & Monitoring

### Service Management

```bash
# Check service status
sudo systemctl status binance-collector

# Start/Stop/Restart service
sudo systemctl start binance-collector
sudo systemctl stop binance-collector  
sudo systemctl restart binance-collector

# View real-time logs
sudo journalctl -u binance-collector -f
```

### Health Monitoring

```bash
# Run health check
sudo /opt/binance-data-collector/scripts/health_check.py

# Check with custom data directory
sudo /opt/binance-data-collector/scripts/health_check.py /custom/data/path
```

### Data Analysis

```bash
# Generate analysis report
sudo /opt/binance-data-collector/scripts/analyze_data.py

# Save analysis to file
sudo /opt/binance-data-collector/scripts/analyze_data.py --save analysis.json --format json

# Analyze custom data directory
sudo /opt/binance-data-collector/scripts/analyze_data.py --data-dir /custom/path
```

## 📄 Output Format

### CSV Output
```csv
timestamp,datetime,open,high,low,close,volume,num_buyers,num_sellers,power_position,max_buyers_per_second,max_sellers_per_second
1725348060000,2025-08-23T07:41:00+00:00,43501.14,43503.37,43496.51,43507.04,1.609305,64,67,-1,8,2
```

### JSON Output
```json
{
  "timestamp": 1725348060000,
  "open_price": 43501.14,
  "high_price": 43503.37,
  "low_price": 43496.51,
  "close_price": 43507.04,
  "volume": 1.609305,
  "num_buyers": 64,
  "num_sellers": 67,
  "power_position": -1,
  "max_buyers_per_second": 8,
  "max_sellers_per_second": 2,
  "datetime": "2025-08-23T07:41:00+00:00"
}
```

## 🔧 Troubleshooting

### Common Issues

1. **Service fails to start**:
   ```bash
   # Check service logs
   sudo journalctl -u binance-collector --since "10 minutes ago"

   # Check file permissions
   sudo chown -R binance:binance /opt/binance-data-collector
   ```

2. **No data being collected**:
   ```bash
   # Test network connectivity
   ping stream.binance.com

   # Check application logs
   sudo tail -f /opt/binance-data-collector/data/app.log
   ```

3. **Permission errors**:
   ```bash
   # Fix permissions
   sudo chown -R binance:binance /opt/binance-data-collector
   sudo chmod +x /opt/binance-data-collector/scripts/*.py
   ```

### Performance Optimization

For high-volume pairs, adjust `src/config.py`:
```python
BUFFER_SIZE = 500  # Reduce memory usage
LOG_LEVEL = 'WARNING'  # Reduce log verbosity
```

## 📈 Data Analysis Example

```python
import pandas as pd

# Load collected data
df = pd.read_csv('/opt/binance-data-collector/data/binance_data_20250823.csv')
df['datetime'] = pd.to_datetime(df['datetime'])

# Calculate additional metrics
df['price_change'] = df['close'] - df['open']
df['buyer_dominance'] = df['num_buyers'] / (df['num_buyers'] + df['num_sellers'])

# Generate insights
print(f"Average price change: {df['price_change'].mean():.4f}")
print(f"Buyer dominance: {df['buyer_dominance'].mean():.2%}")
```

## 🔒 Security Features

- **Non-root execution**: Runs as dedicated `binance` user
- **Systemd hardening**: NoNewPrivileges, PrivateTmp, ProtectSystem
- **Minimal permissions**: Read-only filesystem except data directory
- **Secure logging**: Structured logging with rotation

## 📞 Support

1. **Check logs**: `/opt/binance-data-collector/data/app.log`
2. **Run health check**: `sudo /opt/binance-data-collector/scripts/health_check.py`
3. **Service status**: `sudo systemctl status binance-collector`

## 📝 License

This project is provided as-is for educational and research purposes.

## ⚠️ Disclaimer

This application collects market data only and does not place trades or access your Binance account. Always comply with Binance's API terms of service.
# Binance-Data-Collector
