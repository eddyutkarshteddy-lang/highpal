@echo off
echo ========================================
echo Restarting HighPal Backend Server
echo ========================================

echo [1/3] Stopping any running backend processes...
taskkill /F /FI "WINDOWTITLE eq HighPal Backend*" >nul 2>&1
timeout /t 2 /nobreak >nul

echo [2/3] Starting updated backend server...
start "HighPal Backend" cmd /k "cd /d c:\Users\eddyu\Documents\Projects\highpal\backend && .\venv\Scripts\Activate.ps1 && python training_server.py"

echo [3/3] Waiting for server to initialize...
timeout /t 8 /nobreak >nul

echo ========================================
echo Backend server restarted with updates!
echo ========================================
echo Testing connection...
curl -s "http://localhost:8003/health" || echo "Server starting..."
echo.
echo Backend API: http://localhost:8003
echo API Docs: http://localhost:8003/docs
echo ========================================
pause
