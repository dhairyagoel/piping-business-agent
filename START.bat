@echo off
title Piping Business Agent
echo.
echo ============================================================
echo   PIPING BUSINESS AGENT - Starting...
echo   This will open in your browser automatically.
echo   Keep this window open. Press Ctrl+C to stop.
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Install dependencies if streamlit not found
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo First-time setup: Installing required packages...
    echo This will take 2-3 minutes. Please wait...
    pip install streamlit openpyxl python-pptx reportlab twilio pandas
    echo.
    echo Setup complete!
    echo.
)

REM Get local IP for mobile/tablet access
echo ============================================================
echo   ACCESS FROM OTHER DEVICES:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| find "IPv4"') do (
    echo   Phone/Tablet: http://%%a:8501
)
echo   This PC:      http://localhost:8501
echo ============================================================
echo.

REM Start the app
streamlit run app.py --server.address 0.0.0.0 -server.port 8501 -browser.gatherUsageStats false
