"""
Launcher script for Face Biometric System
This script starts the Flask server and automatically opens the browser
"""
import webbrowser
import threading
import time
import sys
import os
import socket

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def open_browser():
    """Open browser after a short delay"""
    time.sleep(1.5)  # Wait for server to start
    try:
        webbrowser.open('http://127.0.0.1:5000')
    except Exception as e:
        print(f"Could not open browser automatically: {e}")
        print("Please manually open: http://127.0.0.1:5000")

def main():
    """Main function to start the application"""
    # Check if port is already in use
    if is_port_in_use(5000):
        print("=" * 50)
        print("WARNING: Port 5000 is already in use!")
        print("=" * 50)
        print("Another instance might be running.")
        print("Please close it first or change the port.")
        print()
        response = input("Open browser to existing instance? (y/n): ")
        if response.lower() == 'y':
            open_browser()
        sys.exit(1)
    
    # Start browser in a separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Import and run the Flask app
    try:
        from app import app
        print("=" * 50)
        print("Face Biometric System")
        print("=" * 50)
        print("Server starting at http://127.0.0.1:5000")
        print("Browser will open automatically...")
        print("Press Ctrl+C to stop the server")
        print("=" * 50)
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
        sys.exit(0)
    except OSError as e:
        if "Address already in use" in str(e):
            print("\n\nERROR: Port 5000 is already in use!")
            print("Please close the other instance first.")
        else:
            print(f"\nError: {e}")
        input("Press Enter to exit...")
        sys.exit(1)
    except Exception as e:
        print(f"\nError starting server: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
