@echo off
echo ========================================
echo HighPal Educational AI Assistant Startup
echo ========================================

echo.
echo [1/4] Setting up environment...
cd /d "c:\Users\eddyu\Documents\Projects\highpal"

echo [2/4] Starting Backend Server...
start "HighPal Backend" cmd /k "cd /d c:\Users\eddyu\Documents\Projects\highpal\backend && .\venv\Scripts\Activate.ps1 && python training_server.py"

echo [3/4] Waiting for backend to initialize...
timeout /t 10 /nobreak >nul

echo [4/4] Starting Frontend Server...
start "HighPal Frontend" cmd /k "cd /d c:\Users\eddyu\Documents\Projects\highpal && npm run dev"

echo.
echo ========================================
echo HighPal Application Starting...
echo ========================================
echo Frontend:     http://localhost:5173
echo Backend API:  http://localhost:8003  
echo API Docs:     http://localhost:8003/docs
echo Health Check: http://localhost:8003/health
echo ========================================
echo.
echo Both servers are starting in separate windows.
echo Close those windows to stop the servers.
echo.
pause
