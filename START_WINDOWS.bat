@echo off
setlocal
cd /d "%~dp0"
title NONA
if exist ".venv\Scripts\python.exe" goto ready
py -3 -c "import sys; assert sys.version_info >= (3, 10)" >nul 2>&1
if not errorlevel 1 (
    py -3 -m venv .venv
) else (
    python -c "import sys; assert sys.version_info >= (3, 10)" >nul 2>&1
    if errorlevel 1 goto missingpython
    python -m venv .venv
)
if errorlevel 1 goto failed
:ready
if exist ".venv\nona-installed-v2" goto launch
echo Installing NONA packages. Internet is needed for this first setup.
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
type nul > ".venv\nona-installed-v2"
:launch
".venv\Scripts\python.exe" run.py
if errorlevel 1 goto failed
exit /b 0
:missingpython
echo.
echo Install Python 3.10 or newer from https://www.python.org/downloads/windows/
echo Choose "Add python.exe to PATH", then reopen this file.
pause
exit /b 1
:failed
echo.
echo NONA could not start. Read the error above before closing this window.
echo If the port is in use, close the other NONA window and try again.
pause
exit /b 1
