@echo off
setlocal
cd /d "%~dp0"
echo NONA optional Xbox output package
echo This installs the Python adapter only. It does not install a Windows driver.
echo Read docs\GAMEPAD_SETUP.md for the separate optional driver setup and its status.
if not exist ".venv\Scripts\python.exe" (
    echo Run START_WINDOWS.bat once, then close NONA and run this file again.
    pause
    exit /b 1
)
set "VGAMEPAD_SKIP_VIGEMBUS_INSTALL=true"
".venv\Scripts\python.exe" -m pip install -r requirements-gamepad.txt
if errorlevel 1 (
    echo Adapter installation failed. Read the error above.
    pause
    exit /b 1
)
echo Adapter installed. See docs\GAMEPAD_SETUP.md before connecting Xbox output.
pause
