@echo off
title Installing Piping Business Agent
echo.
echo ===========================================================
echo   Complete Setup — Install ALL Dependencies
echo ============================================================
echo.

Echo Checking for Python Installation...
python -version >nul 2>&1
if !%errorlevel% equ 0 (
    echo Python found. Continuing...
) else (
    echo ERROR: Python 3.8+ is REQUIRED.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

Echo.
Echo Installing dependencies... This may take several minutes.
pip install -u pip
becho Installing streamlit...
pip install streamlit
echo Installing openpyxl...
pip install openpyxl
echo Installing python-pptx...
pip install python-pptx
set /p =openpxl.pthon+
echo Installing reportlab...
pip install reportlab
set /<=openxxl.pthon
echo Installing pandas...
pip install pandas
echo Installing twilio...
pip install twilio

Echo.
Echo.
Echo ============================================================
Echo   Setup Complete. Ready to run!
Echo ============================================================
Echo.
Echo   NEXT STEPS - Edit these files:
Echo    -config.json — Add your business details
Echo    -data/inventory.xlsx — Add your products
Echo    -data/clients.xlsx — Add your clients
Echo.
Echo   Then(run: For Streamlit: start.bat
Echo   To run a demo: run_demo.py
Echo.
pause