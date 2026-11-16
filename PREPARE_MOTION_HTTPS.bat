@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Run START_WINDOWS.bat once, then close NONA before using this setup.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r requirements-https.txt
if errorlevel 1 goto failed
".venv\Scripts\python.exe" local_tls.py
if errorlevel 1 goto failed
echo.
echo Certificates were created, not installed. Read docs\MOTION_TEST.md next.
echo Never share ca-key.pem or server-key.pem.
pause
exit /b 0
:failed
echo HTTPS preparation failed. Read the error above.
pause
exit /b 1
