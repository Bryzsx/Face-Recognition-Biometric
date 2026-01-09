# Building Standalone Application

This guide explains how to convert the Face Biometric System into a standalone executable application.

## Option 1: Quick Start (Using Batch File)

1. **Double-click `run_app.bat`**
   - This will automatically start the application and open your browser
   - No installation needed if Python is already installed

## Option 2: Create Standalone Executable (.exe)

### Prerequisites

1. Install Python 3.8 or higher
2. Install required packages:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

### Building the Executable

#### Method 1: Using the Build Script (Recommended)

1. Run the build script:
   ```bash
   python build_exe.py
   ```

2. The executable will be created in the `dist` folder:
   - `dist/FaceBiometricSystem.exe`

3. Copy the entire `dist` folder to distribute the application

#### Method 2: Manual PyInstaller Command

```bash
pyinstaller --name=FaceBiometricSystem ^
    --onefile ^
    --windowed ^
    --add-data="templates;templates" ^
    --add-data="static;static" ^
    --add-data="encodings;encodings" ^
    --add-data="faces;faces" ^
    --hidden-import=flask ^
    --hidden-import=face_recognition ^
    --hidden-import=dlib ^
    --hidden-import=PIL ^
    --collect-all=flask ^
    --collect-all=face_recognition ^
    launcher.py
```

### Distribution

After building, you can distribute:
- The `FaceBiometricSystem.exe` file
- The `dist` folder (contains all dependencies)

**Note:** The first run may be slower as files are extracted. Subsequent runs will be faster.

## Option 3: Create Windows Service (Auto-start on Boot)

### Using NSSM (Non-Sucking Service Manager)

1. Download NSSM from: https://nssm.cc/download

2. Install as service:
   ```bash
   nssm install FaceBiometricSystem
   ```
   - Path: `C:\path\to\python.exe`
   - Arguments: `C:\path\to\launcher.py`
   - Startup: Automatic

### Using Task Scheduler (Built-in Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: "When the computer starts"
4. Action: Start a program
   - Program: `python.exe`
   - Arguments: `launcher.py`
   - Start in: `C:\path\to\project\folder`

## Option 4: Create Desktop Shortcut

1. Right-click on `run_app.bat`
2. Create shortcut
3. Right-click shortcut → Properties
4. Change icon if desired
5. Pin to taskbar or desktop

## Troubleshooting

### "Python not found" error
- Install Python from python.org
- Make sure Python is added to PATH during installation

### "Module not found" errors
- Activate virtual environment: `venv\Scripts\activate`
- Install requirements: `pip install -r requirements.txt`

### Executable is large
- This is normal - it includes Python and all dependencies
- First run extracts files to temp folder
- Consider using `--onedir` instead of `--onefile` for faster startup

### Browser doesn't open automatically
- Manually navigate to: http://127.0.0.1:5000
- Check firewall settings

## File Structure After Building

```
Face_Biometric_System/
├── dist/
│   └── FaceBiometricSystem.exe  (Standalone executable)
├── build/                        (Build files - can be deleted)
├── launcher.py                   (Launcher script)
├── run_app.bat                   (Quick start batch file)
├── build_exe.py                  (Build script)
└── ... (other project files)
```

## Notes

- The database (`biometric.db`) will be created automatically on first run
- Photos and encodings are stored in the same directory as the executable
- For production, consider using a proper web server (nginx + gunicorn)
- The application runs on localhost (127.0.0.1) by default for security
