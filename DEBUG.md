# How to Debug the Face Biometric System

## 1. Run with Flask debug mode (quick way)

**From terminal (PowerShell):**
```powershell
$env:FLASK_DEBUG="true"; python app.py
```

Or set the variable and run:
```powershell
set FLASK_DEBUG=true
python app.py
```

**What you get:**
- **Auto-reload** – code changes restart the server.
- **Detailed error page** – on a crash you see the traceback in the browser.
- **Do not use in production** – turn DEBUG off when deploying.

---

## 2. Use the debugger in Cursor / VS Code (breakpoints)

1. Open the **Run and Debug** view (Ctrl+Shift+D).
2. Choose **"Flask (debug mode)"** or **"Python: app.py (debug)"** from the dropdown.
3. Set **breakpoints** by clicking in the left gutter next to a line number (e.g. in `blueprints/admin.py` or `app.py`).
4. Press **F5** (or click the green play button) to start.
5. Use the app in the browser; when a request hits a line with a breakpoint, execution will pause and you can inspect variables and step through code.

---

## 3. Check log files

- **`logs/app.log`** – general application log.
- **`logs/error.log`** – errors (if your logger is configured to write there).

Open these in the editor or tail them in a terminal:
```powershell
Get-Content logs\app.log -Tail 50 -Wait
```

---

## 4. More verbose logging

To see DEBUG-level log messages, run with:
```powershell
$env:LOG_LEVEL="DEBUG"; $env:FLASK_DEBUG="true"; python app.py
```

---

## 5. Enable debug via config (optional)

In `config.py` you can temporarily set:
```python
DEBUG = True   # instead of reading from FLASK_DEBUG env
```
Remember to revert this before deploying.
