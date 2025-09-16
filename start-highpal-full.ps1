# HighPal Full Application Startup Script
# This script starts both backend and frontend servers simultaneously

Write-Host "Starting HighPal Educational AI Assistant..." -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan

# Function to check if a port is in use
function Test-Port {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

# Check if ports are already in use
if (Test-Port 8003) {
    Write-Host "WARNING: Port 8003 is already in use. Please stop any running backend server." -ForegroundColor Yellow
    exit 1
}

if (Test-Port 5173) {
    Write-Host "WARNING: Port 5173 is already in use. Please stop any running frontend server." -ForegroundColor Yellow
    exit 1
}

# Start Backend Server in background
Write-Host "Starting Backend Server on Port 8003..." -ForegroundColor Blue
$backendJob = Start-Job -ScriptBlock {
    Set-Location "c:\Users\eddyu\Documents\Projects\highpal\backend"
    & ".\venv\Scripts\Activate.ps1"
    python training_server.py
}

# Wait a moment for backend to initialize
Start-Sleep -Seconds 3

# Check if backend started successfully
$backendStarted = $false
for ($i = 0; $i -lt 10; $i++) {
    if (Test-Port 8003) {
        Write-Host "SUCCESS: Backend Server started successfully!" -ForegroundColor Green
        $backendStarted = $true
        break
    }
    Start-Sleep -Seconds 1
}

if (-not $backendStarted) {
    Write-Host "ERROR: Failed to start Backend Server" -ForegroundColor Red
    Stop-Job $backendJob
    Remove-Job $backendJob
    exit 1
}

# Start Frontend Server in background
Write-Host "Starting Frontend Server on Port 5173..." -ForegroundColor Blue
$frontendJob = Start-Job -ScriptBlock {
    Set-Location "c:\Users\eddyu\Documents\Projects\highpal"
    npm run dev
}

# Wait for frontend to initialize
Start-Sleep -Seconds 5

# Check if frontend started successfully
$frontendStarted = $false
for ($i = 0; $i -lt 15; $i++) {
    if (Test-Port 5173) {
        Write-Host "SUCCESS: Frontend Server started successfully!" -ForegroundColor Green
        $frontendStarted = $true
        break
    }
    Start-Sleep -Seconds 1
}

if (-not $frontendStarted) {
    Write-Host "ERROR: Failed to start Frontend Server" -ForegroundColor Red
    Stop-Job $backendJob
    Remove-Job $backendJob
    Stop-Job $frontendJob
    Remove-Job $frontendJob
    exit 1
}

# Display success information
Write-Host "" -ForegroundColor White
Write-Host "SUCCESS: HighPal Application Started Successfully!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Frontend:     http://localhost:5173" -ForegroundColor White
Write-Host "Backend API:  http://localhost:8003" -ForegroundColor White
Write-Host "API Docs:     http://localhost:8003/docs" -ForegroundColor White
Write-Host "Health Check: http://localhost:8003/health" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "Your HighPal Educational AI Assistant is ready!" -ForegroundColor Yellow
Write-Host "" -ForegroundColor White
Write-Host "Press Ctrl+C to stop both servers..." -ForegroundColor Gray

# Keep the script running and monitor the jobs
try {
    while ($true) {
        # Check if both jobs are still running
        if ($backendJob.State -eq "Failed" -or $backendJob.State -eq "Stopped") {
            Write-Host "ERROR: Backend server stopped unexpectedly" -ForegroundColor Red
            break
        }
        
        if ($frontendJob.State -eq "Failed" -or $frontendJob.State -eq "Stopped") {
            Write-Host "ERROR: Frontend server stopped unexpectedly" -ForegroundColor Red
            break
        }
        
        Start-Sleep -Seconds 2
    }
} catch {
    Write-Host "Shutting down servers..." -ForegroundColor Yellow
} finally {
    # Clean up jobs
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
    Stop-Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $frontendJob -ErrorAction SilentlyContinue
    
    Write-Host "SUCCESS: All servers stopped successfully!" -ForegroundColor Green
}
