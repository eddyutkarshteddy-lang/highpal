# HighPal Complete Application Startup Script
# This script starts both backend and frontend servers with proper configuration

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

# Function to wait for server to start
function Wait-ForServer {
    param([int]$Port, [string]$ServerName, [int]$MaxAttempts = 30)
    
    Write-Host "Waiting for $ServerName to start on port $Port..." -ForegroundColor Yellow
    
    for ($i = 0; $i -lt $MaxAttempts; $i++) {
        if (Test-Port $Port) {
            Write-Host "SUCCESS: $ServerName is running on port $Port!" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 2
        Write-Host "." -NoNewline -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "ERROR: $ServerName failed to start on port $Port" -ForegroundColor Red
    return $false
}

# Check if ports are already in use
if (Test-Port 8003) {
    Write-Host "WARNING: Port 8003 is already in use. Attempting to continue..." -ForegroundColor Yellow
}

if (Test-Port 5173) {
    Write-Host "WARNING: Port 5173 is already in use. Frontend will use alternate port..." -ForegroundColor Yellow
}

# Navigate to project directory
$ProjectRoot = "c:\Users\eddyu\Documents\Projects\highpal"
$BackendPath = "$ProjectRoot\backend"

Write-Host "Project Root: $ProjectRoot" -ForegroundColor Blue
Write-Host "Backend Path: $BackendPath" -ForegroundColor Blue

# Check if directories exist
if (-not (Test-Path $ProjectRoot)) {
    Write-Host "ERROR: Project directory not found: $ProjectRoot" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $BackendPath)) {
    Write-Host "ERROR: Backend directory not found: $BackendPath" -ForegroundColor Red
    exit 1
}

# Start Backend Server
Write-Host "Starting Backend Server..." -ForegroundColor Blue
$backendJob = Start-Job -ScriptBlock {
    param($BackendPath)
    
    Set-Location $BackendPath
    
    # Activate virtual environment
    & ".\venv\Scripts\Activate.ps1"
    
    # Start the training server
    python training_server.py
    
} -ArgumentList $BackendPath

# Wait for backend to start
if (-not (Wait-ForServer -Port 8003 -ServerName "Backend")) {
    Write-Host "Stopping backend job..." -ForegroundColor Yellow
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
    exit 1
}

# Test backend health
Write-Host "Testing backend health..." -ForegroundColor Blue
try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:8003/health" -UseBasicParsing -TimeoutSec 10
    $healthData = $healthResponse.Content | ConvertFrom-Json
    
    Write-Host "Backend Health Status:" -ForegroundColor Green
    Write-Host "  MongoDB: $($healthData.mongodb)" -ForegroundColor White
    Write-Host "  OpenAI: $($healthData.openai)" -ForegroundColor White
    Write-Host "  Training Ready: $($healthData.training_ready)" -ForegroundColor White
    
} catch {
    Write-Host "WARNING: Could not verify backend health, but continuing..." -ForegroundColor Yellow
}

# Start Frontend Server
Write-Host "Starting Frontend Server..." -ForegroundColor Blue
$frontendJob = Start-Job -ScriptBlock {
    param($ProjectRoot)
    
    Set-Location $ProjectRoot
    
    # Install dependencies if needed
    if (-not (Test-Path "node_modules")) {
        Write-Host "Installing dependencies..."
        npm install
    }
    
    # Start the development server
    npm run dev
    
} -ArgumentList $ProjectRoot

# Wait for frontend to start (it might use port 5174 if 5173 is busy)
$frontendPort = 5173
if (-not (Wait-ForServer -Port $frontendPort -ServerName "Frontend" -MaxAttempts 15)) {
    # Try alternate port
    $frontendPort = 5174
    if (-not (Wait-ForServer -Port $frontendPort -ServerName "Frontend" -MaxAttempts 10)) {
        Write-Host "Frontend may still be starting. Check manually at http://localhost:5173 or http://localhost:5174" -ForegroundColor Yellow
    }
}

# Display success information
Write-Host ""
Write-Host "SUCCESS: HighPal Application Started!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Frontend:     http://localhost:$frontendPort" -ForegroundColor White
Write-Host "Backend API:  http://localhost:8003" -ForegroundColor White
Write-Host "API Docs:     http://localhost:8003/docs" -ForegroundColor White
Write-Host "Health Check: http://localhost:8003/health" -ForegroundColor White
Write-Host ""
Write-Host "Your HighPal Educational AI Assistant is ready!" -ForegroundColor Yellow
Write-Host "Features Available:" -ForegroundColor Cyan
Write-Host "  - GPT-4o powered chat assistance" -ForegroundColor White
Write-Host "  - MongoDB Atlas document storage" -ForegroundColor White
Write-Host "  - PDF document processing" -ForegroundColor White
Write-Host "  - Semantic search capabilities" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop both servers..." -ForegroundColor Gray

# Keep the script running and monitor the jobs
try {
    while ($true) {
        # Check if both jobs are still running
        if ($backendJob.State -eq "Failed" -or $backendJob.State -eq "Stopped") {
            Write-Host "ERROR: Backend server stopped unexpectedly" -ForegroundColor Red
            Write-Host "Backend Job State: $($backendJob.State)" -ForegroundColor Red
            
            # Get job output for debugging
            $jobOutput = Receive-Job $backendJob -ErrorAction SilentlyContinue
            if ($jobOutput) {
                Write-Host "Backend Output:" -ForegroundColor Yellow
                Write-Host $jobOutput -ForegroundColor Gray
            }
            break
        }
        
        if ($frontendJob.State -eq "Failed" -or $frontendJob.State -eq "Stopped") {
            Write-Host "ERROR: Frontend server stopped unexpectedly" -ForegroundColor Red
            Write-Host "Frontend Job State: $($frontendJob.State)" -ForegroundColor Red
            
            # Get job output for debugging
            $jobOutput = Receive-Job $frontendJob -ErrorAction SilentlyContinue
            if ($jobOutput) {
                Write-Host "Frontend Output:" -ForegroundColor Yellow
                Write-Host $jobOutput -ForegroundColor Gray
            }
            break
        }
        
        Start-Sleep -Seconds 5
    }
} catch {
    Write-Host "Shutting down servers..." -ForegroundColor Yellow
} finally {
    # Clean up jobs
    Write-Host "Stopping all servers..." -ForegroundColor Yellow
    
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -ErrorAction SilentlyContinue
    
    Stop-Job $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $frontendJob -ErrorAction SilentlyContinue
    
    Write-Host "SUCCESS: All servers stopped successfully!" -ForegroundColor Green
}
