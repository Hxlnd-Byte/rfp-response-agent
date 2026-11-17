@echo off
rem Double-click this file to start the RFP Response Agent. It opens in your browser.
cd /d "%~dp0"
python --version >nul 2>&1
if errorlevel 1 (
  echo Python is not installed. Install Python 3.12 from python.org and tick "Add python.exe to PATH".
  pause
  exit /b 1
)
start "" http://localhost:8765
python app.py
pause
