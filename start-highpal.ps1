# HighPal Application Startup Script
# This script starts both backend and frontend servers simultaneously

Write-Host "🚀 Starting HighPal Educational AI Assistant..." -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Cyan

# Check if Node.js is available
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js detected: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js not found. Please install Node.js first." -ForegroundColor Red
    exit 1
}

# Check if Python is available in backend venv
$backendPath = "c:\Users\eddyu\Documents\Projects\highpal\backend"
$pythonPath = "$backendPath\venv\Scripts\python.exe"

if (Test-Path $pythonPath) {
    Write-Host "✅ Python virtual environment found" -ForegroundColor Green
} else {
    Write-Host "❌ Python virtual environment not found at $pythonPath" -ForegroundColor Red
    exit 1
}

# Function to start backend server
function Start-Backend {
    Write-Host "🔧 Starting Backend Server (FastAPI + MongoDB + GPT-5)..." -ForegroundColor Yellow
    
    # Navigate to backend and start server
    Set-Location $backendPath
    
    # Start backend in a new PowerShell window
    $backendScript = @"
Set-Location '$backendPath'
Write-Host '🔧 Activating Python Environment...' -ForegroundColor Yellow
& '.\venv\Scripts\Activate.ps1'
Write-Host '🚀 Starting HighPal Backend Server...' -ForegroundColor Green
& '.\venv\Scripts\python.exe' training_server.py
pause
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript
    
    # Wait for backend to initialize
    Write-Host "⏳ Waiting for backend to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 8
    
    # Test backend health
    try {
        $healthCheck = Invoke-WebRequest -Uri "http://localhost:8003/health" -UseBasicParsing -TimeoutSec 5
        $healthData = $healthCheck.Content | ConvertFrom-Json
        
        if ($healthData.status -eq "healthy") {
            Write-Host "✅ Backend Server Running: http://localhost:8003" -ForegroundColor Green
            Write-Host "✅ MongoDB: $($healthData.mongodb)" -ForegroundColor Green
            Write-Host "✅ OpenAI GPT-5: $($healthData.openai)" -ForegroundColor Green
            return $true
        }
    } catch {
        Write-Host "⚠️  Backend health check failed, but continuing..." -ForegroundColor Yellow
        return $false
    }
}

# Function to start frontend server
function Start-Frontend {
    Write-Host "🎨 Starting Frontend Server (React + Vite)..." -ForegroundColor Yellow
    
    # Navigate to project root
    Set-Location "c:\Users\eddyu\Documents\Projects\highpal"
    
    # Check if node_modules exists
    if (-not (Test-Path "node_modules")) {
        Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Yellow
        npm install
    }
    
    # Start frontend in a new PowerShell window
    $frontendScript = @"
Set-Location 'c:\Users\eddyu\Documents\Projects\highpal'
Write-Host '🎨 Starting HighPal Frontend...' -ForegroundColor Green
npm run dev
pause
"@
    
    Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript
    
    Write-Host "⏳ Waiting for frontend to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    Write-Host "✅ Frontend Server Starting: http://localhost:5173" -ForegroundColor Green
}

# Main execution
try {
    Write-Host ""
    Write-Host "Step 1: Starting Backend Server..." -ForegroundColor Cyan
    $backendSuccess = Start-Backend
    
    Write-Host ""
    Write-Host "Step 2: Starting Frontend Server..." -ForegroundColor Cyan
    Start-Frontend
    
    Write-Host ""
    Write-Host "🎉 HighPal Application Started Successfully!" -ForegroundColor Green
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host "📡 Backend API: http://localhost:8003" -ForegroundColor White
    Write-Host "📖 API Docs: http://localhost:8003/docs" -ForegroundColor White
    Write-Host "🎨 Frontend App: http://localhost:5173" -ForegroundColor White
    Write-Host "🏥 Health Check: http://localhost:8003/health" -ForegroundColor White
    Write-Host ""
    Write-Host "💡 Both servers are running in separate windows." -ForegroundColor Yellow
    Write-Host "💡 Close those windows to stop the servers." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to open the application in your browser..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    
    # Open browser
    Start-Process "http://localhost:5173"
    
} catch {
    Write-Host "❌ Error starting HighPal: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Please check the error messages above and try again." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Script completed. Check the server windows for any errors." -ForegroundColor Cyan
