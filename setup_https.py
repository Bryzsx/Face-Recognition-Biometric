"""
Script to generate SSL certificates for HTTPS setup (Windows compatible)
"""
import os
import sys
from pathlib import Path

# Add the current directory to the path to import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from werkzeug.serving import make_ssl_devcert
    from config import SSL_CERT_PATH, SSL_KEY_PATH
    BASE_DIR = Path(__file__).parent.absolute()
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("\nPlease ensure Flask/Werkzeug is installed:")
    print("  pip install Flask")
    sys.exit(1)

def get_server_ip():
    """Get the server's IP address"""
    import socket
    try:
        # Connect to a remote server to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        # Fallback to localhost
        return "localhost"

def main():
    print("=" * 50)
    print("HTTPS Setup for Face Recognition System")
    print("=" * 50)
    print()
    
    # Check if certs directory exists
    certs_dir = os.path.join(BASE_DIR, 'certs')
    if not os.path.exists(certs_dir):
        print("Creating certificates directory...")
        os.makedirs(certs_dir, exist_ok=True)
    
    # Check if certificates already exist
    cert_exists = os.path.exists(SSL_CERT_PATH)
    key_exists = os.path.exists(SSL_KEY_PATH)
    
    if cert_exists and key_exists:
        print("[WARNING] Certificates already exist!")
        response = input("Do you want to regenerate them? (y/n): ").strip().lower()
        if response != 'y':
            print("Using existing certificates.")
            return
    
    # Get server IP for certificate CN
    server_ip = get_server_ip()
    print(f"\nDetected server IP: {server_ip}")
    print(f"Generating self-signed certificate for: {server_ip}")
    print()
    
    try:
        # Use Werkzeug's make_ssl_devcert to generate matching certificate and key
        # This ensures the certificate and key are properly matched
        base_path = os.path.join(certs_dir, 'server')
        
        print("Generating private key and certificate...")
        cert_file, key_file = make_ssl_devcert(base_path, host=server_ip)
        
        print()
        print("[OK] Certificates generated successfully!")
        print()
        print("Certificate location:")
        print(f"  - Private Key: {key_file}")
        print(f"  - Certificate: {cert_file}")
        print()
        print("Next steps:")
        print(f"   1. Restart the Flask app")
        print(f"   2. Access via: https://{server_ip}:5000")
        print()
        print("Note: Browsers will show a security warning for self-signed certificates.")
        print("   Employees need to click 'Advanced' -> 'Proceed' to continue.")
        print()
        
    except ImportError:
        print("[ERROR] The 'cryptography' library is required to generate certificates.")
        print("Please install it with:")
        print("  pip install cryptography")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error generating certificates: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
