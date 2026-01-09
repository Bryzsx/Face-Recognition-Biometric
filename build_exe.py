"""
Script to build standalone executable using PyInstaller
Run this script to create a distributable .exe file
"""
import PyInstaller.__main__
import os
import sys

def build_executable():
    """Build the executable"""
    print("=" * 60)
    print("Building Face Biometric System Executable")
    print("=" * 60)
    print()
    
    # PyInstaller arguments
    args = [
        'launcher.py',                    # Main script
        '--name=FaceBiometricSystem',     # Executable name
        '--onefile',                      # Single executable file
        '--windowed',                     # No console window (use --noconsole for console)
        '--icon=NONE',                    # Add icon path if you have one
        '--add-data=templates;templates', # Include templates folder
        '--add-data=static;static',       # Include static folder
        '--add-data=encodings;encodings', # Include encodings folder
        '--add-data=faces;faces',         # Include faces folder
        '--hidden-import=flask',          # Ensure Flask is included
        '--hidden-import=face_recognition', # Ensure face_recognition is included
        '--hidden-import=dlib',           # Ensure dlib is included
        '--hidden-import=PIL',            # Ensure PIL is included
        '--hidden-import=sqlite3',        # Ensure sqlite3 is included
        '--collect-all=flask',            # Collect all Flask files
        '--collect-all=face_recognition', # Collect all face_recognition files
        '--noconfirm',                    # Overwrite output without asking
    ]
    
    try:
        PyInstaller.__main__.run(args)
        print()
        print("=" * 60)
        print("Build completed successfully!")
        print("=" * 60)
        print()
        print("Executable location: dist/FaceBiometricSystem.exe")
        print()
        print("Note: The first time you run the .exe, it may take")
        print("a moment to extract files. Subsequent runs will be faster.")
        print()
    except Exception as e:
        print(f"Error building executable: {e}")
        print()
        print("Make sure PyInstaller is installed:")
        print("  pip install pyinstaller")
        return False
    
    return True

if __name__ == "__main__":
    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller is not installed.")
        print("Installing PyInstaller...")
        os.system("pip install pyinstaller")
        print()
    
    build_executable()
    input("Press Enter to exit...")
