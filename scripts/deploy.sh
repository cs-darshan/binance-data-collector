#!/bin/bash

# Binance Data Collector Deployment Script
# This script sets up the application on a fresh Linux server

set -e

echo "🚀 Starting Binance Data Collector deployment..."

# Configuration
APP_DIR="/opt/binance-data-collector"
SERVICE_NAME="binance-collector"
PYTHON_VERSION="python3"
USER_NAME="binance"

# Create application directory
echo "📁 Creating application directory..."
sudo mkdir -p $APP_DIR
sudo useradd -r -s /bin/false $USER_NAME || true
sudo chown $USER_NAME:$USER_NAME $APP_DIR

# Update system packages
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install Python and required system packages
echo "🐍 Installing Python and dependencies..."
sudo apt install -y python3 python3-pip python3-venv git htop nano curl

# Copy application files
echo "📋 Copying application files..."
sudo cp -r . $APP_DIR/
sudo chown -R $USER_NAME:$USER_NAME $APP_DIR

# Create Python virtual environment
echo "🔧 Setting up Python virtual environment..."
cd $APP_DIR
sudo -u $USER_NAME python3 -m venv venv
sudo -u $USER_NAME $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u $USER_NAME $APP_DIR/venv/bin/pip install -r requirements.txt

# Set up data directory
echo "📊 Setting up data directory..."
sudo -u $USER_NAME mkdir -p $APP_DIR/data
sudo chmod 755 $APP_DIR/data

# Update service file with correct paths
echo "⚙️ Updating service configuration..."
sudo sed -i "s|/home/ubuntu/binance-collector|$APP_DIR|g" $APP_DIR/config/binance-collector.service
sudo sed -i "s|User=ubuntu|User=$USER_NAME|g" $APP_DIR/config/binance-collector.service

# Copy service file and enable systemd service
sudo cp $APP_DIR/config/binance-collector.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# Create log rotation configuration
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/binance-collector > /dev/null <<EOF
$APP_DIR/data/app.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER_NAME $USER_NAME
    postrotate
        systemctl reload binance-collector || true
    endscript
}
EOF

# Set final permissions
echo "🔐 Setting final permissions..."
sudo chown -R $USER_NAME:$USER_NAME $APP_DIR
sudo chmod +x $APP_DIR/src/binance_data_collector.py
sudo chmod +x $APP_DIR/scripts/*.py

# Start the service
echo "🎬 Starting the service..."
sudo systemctl start $SERVICE_NAME

# Wait a moment for startup
sleep 3

# Show status
echo "📊 Service status:"
sudo systemctl status $SERVICE_NAME --no-pager -l

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Useful commands:"
echo "  • Check status: sudo systemctl status $SERVICE_NAME"
echo "  • View logs: sudo journalctl -u $SERVICE_NAME -f"
echo "  • View app logs: sudo tail -f $APP_DIR/data/app.log"
echo "  • Stop service: sudo systemctl stop $SERVICE_NAME"
echo "  • Start service: sudo systemctl start $SERVICE_NAME"
echo "  • Restart service: sudo systemctl restart $SERVICE_NAME"
echo "  • Health check: sudo -u $USER_NAME $APP_DIR/scripts/health_check.py $APP_DIR/data"
echo ""
echo "📁 Data files will be saved in: $APP_DIR/data/"
echo "📈 Run analysis: sudo -u $USER_NAME $APP_DIR/scripts/analyze_data.py --data-dir $APP_DIR/data"
echo ""
