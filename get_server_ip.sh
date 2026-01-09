#!/bin/bash
# Script to get the server's IP address for accessing the attendance system

echo "=========================================="
echo "Face Recognition Attendance System"
echo "Server IP Address Information"
echo "=========================================="
echo ""

# Get the primary network interface IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')

if [ -z "$IP_ADDRESS" ]; then
    # Alternative method
    IP_ADDRESS=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}')
fi

if [ -z "$IP_ADDRESS" ]; then
    echo "❌ Could not determine IP address automatically."
    echo "Please run: ip addr show or ifconfig to find your IP address"
    exit 1
fi

echo "✅ Server IP Address: $IP_ADDRESS"
echo ""
echo "📱 Access the attendance page from employee laptops using:"
echo "   http://$IP_ADDRESS:5000/attendance"
echo ""
echo "🔧 Make sure:"
echo "   1. The Flask app is running (python app.py)"
echo "   2. Firewall allows port 5000 (see instructions below)"
echo "   3. Employee laptops are on the same network"
echo ""
echo "=========================================="
