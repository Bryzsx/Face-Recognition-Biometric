#!/bin/bash
# Script to quickly set up HTTPS for the Face Recognition Attendance System

echo "=========================================="
echo "HTTPS Setup for Face Recognition System"
echo "=========================================="
echo ""

# Check if certs directory exists
CERTS_DIR="certs"
if [ ! -d "$CERTS_DIR" ]; then
    echo "Creating certificates directory..."
    mkdir -p "$CERTS_DIR"
fi

# Check if certificates already exist
if [ -f "$CERTS_DIR/server.crt" ] && [ -f "$CERTS_DIR/server.key" ]; then
    echo "⚠️  Certificates already exist!"
    read -p "Do you want to regenerate them? (y/n): " regenerate
    if [ "$regenerate" != "y" ] && [ "$regenerate" != "Y" ]; then
        echo "Using existing certificates."
        exit 0
    fi
fi

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    SERVER_IP=$(ip route get 8.8.8.8 2>/dev/null | awk '{print $7; exit}')
fi

if [ -z "$SERVER_IP" ]; then
    echo "❌ Could not determine server IP. Please enter it manually:"
    read -p "Server IP address: " SERVER_IP
fi

echo ""
echo "Generating self-signed certificate for: $SERVER_IP"
echo ""

# Check if openssl is installed
if ! command -v openssl &> /dev/null; then
    echo "❌ OpenSSL is not installed. Installing..."
    sudo apt-get update
    sudo apt-get install -y openssl
fi

# Generate private key
echo "Generating private key..."
openssl genrsa -out "$CERTS_DIR/server.key" 2048

# Generate certificate
echo "Generating certificate (valid for 365 days)..."
openssl req -new -x509 -key "$CERTS_DIR/server.key" -out "$CERTS_DIR/server.crt" -days 365 \
    -subj "/C=PH/ST=State/L=City/O=Organization/CN=$SERVER_IP"

# Set permissions
chmod 600 "$CERTS_DIR/server.key"
chmod 644 "$CERTS_DIR/server.crt"

echo ""
echo "✅ Certificates generated successfully!"
echo ""
echo "Certificate location:"
echo "  - Private Key: $CERTS_DIR/server.key"
echo "  - Certificate: $CERTS_DIR/server.crt"
echo ""
echo "📝 Next steps:"
echo "   1. Update app.py to use HTTPS (see HTTPS_SETUP.md)"
echo "   2. Restart the Flask app"
echo "   3. Access via: https://$SERVER_IP:5000/attendance"
echo ""
echo "⚠️  Note: Browsers will show a security warning for self-signed certificates."
echo "   Employees need to click 'Advanced' → 'Proceed' to continue."
echo ""
