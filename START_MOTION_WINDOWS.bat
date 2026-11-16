@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run START_WINDOWS.bat once, then PREPARE_MOTION_HTTPS.bat.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" run.py --https
if errorlevel 1 (
    echo Motion HTTPS could not start. See docs\MOTION_TEST.md and the error above.
    pause
    exit /b 1
)
