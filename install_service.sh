#!/bin/bash

echo "=== Installing Telegram Username Monitor Bot as systemd service ==="
echo ""

CURRENT_DIR=$(pwd)
CURRENT_USER=$(whoami)

if [ ! -f "username-monitor.service" ]; then
    echo "Error: username-monitor.service file not found!"
    exit 1
fi

echo "Creating service file..."
sudo cp username-monitor.service /etc/systemd/system/

echo "Updating service file with current paths..."
sudo sed -i "s|YOUR_USERNAME|$CURRENT_USER|g" /etc/systemd/system/username-monitor.service
sudo sed -i "s|/path/to/username_cheker|$CURRENT_DIR|g" /etc/systemd/system/username-monitor.service

echo "Reloading systemd..."
sudo systemctl daemon-reload

echo "Enabling service..."
sudo systemctl enable username-monitor.service

echo ""
echo "=== Service installed successfully! ==="
echo ""
echo "Available commands:"
echo "  Start:   sudo systemctl start username-monitor"
echo "  Stop:    sudo systemctl stop username-monitor"
echo "  Status:  sudo systemctl status username-monitor"
echo "  Logs:    sudo journalctl -u username-monitor -f"
echo "  Restart: sudo systemctl restart username-monitor"
echo ""
