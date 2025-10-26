# Firebase Setup Verification Script
# Tests if Firebase is configured correctly

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Firebase Configuration Verification" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[X] .env file not found!" -ForegroundColor Red
    Write-Host "  Run: ./setup-firebase.ps1 to configure Firebase" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] .env file exists" -ForegroundColor Green

# Read .env and check for Firebase variables
$envContent = Get-Content ".env" -Raw

$requiredVars = @(
    "VITE_FIREBASE_API_KEY",
    "VITE_FIREBASE_AUTH_DOMAIN",
    "VITE_FIREBASE_PROJECT_ID",
    "VITE_FIREBASE_STORAGE_BUCKET",
    "VITE_FIREBASE_MESSAGING_SENDER_ID",
    "VITE_FIREBASE_APP_ID"
)

Write-Host ""
Write-Host "Checking Firebase environment variables:" -ForegroundColor Yellow
$allFound = $true

foreach ($var in $requiredVars) {
    if ($envContent -match "$var=(.+)") {
        $value = $matches[1].Trim()
        if ($value -match "your-.*-here" -or $value -match "demo") {
            Write-Host "  [!] $var = $value (demo/placeholder value)" -ForegroundColor Yellow
            $allFound = $false
        } else {
            Write-Host "  [OK] $var is set" -ForegroundColor Green
        }
    } else {
        Write-Host "  [X] $var is missing" -ForegroundColor Red
        $allFound = $false
    }
}

Write-Host ""

if ($allFound) {
    Write-Host "[OK] All Firebase variables are configured!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Testing Firebase initialization..." -ForegroundColor Yellow
    
    # Check if node_modules/firebase exists
    if (Test-Path "node_modules\firebase") {
        Write-Host "  [OK] Firebase SDK is installed" -ForegroundColor Green
    } else {
        Write-Host "  [X] Firebase SDK not found" -ForegroundColor Red
        Write-Host "    Run: npm install firebase" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Configuration Status: READY [OK]" -ForegroundColor Green
    Write-Host ""
    Write-Host "You can now:" -ForegroundColor Yellow
    Write-Host "1. Start dev server: npm run dev" -ForegroundColor White
    Write-Host "2. Visit: http://localhost:5173/admin/login" -ForegroundColor White
    Write-Host "3. Test Google Sign-In or Email/Password auth" -ForegroundColor White
} else {
    Write-Host "Configuration Status: INCOMPLETE [X]" -ForegroundColor Red
    Write-Host ""
    Write-Host "Action Required:" -ForegroundColor Yellow
    Write-Host "Run: ./setup-firebase.ps1 to configure Firebase" -ForegroundColor White
    Write-Host "Or manually edit .env file with your Firebase credentials" -ForegroundColor White
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check authorized admin emails
Write-Host "Authorized Admin Emails:" -ForegroundColor Yellow
$firebaseJs = "src\config\firebase.js"
if (Test-Path $firebaseJs) {
    $content = Get-Content $firebaseJs -Raw
    if ($content -match '(?ms)AUTHORIZED_ADMINS = \[(.*?)\]') {
        $emails = $matches[1] -split '\n' | Where-Object { $_ -match "'(.+?)'" } | ForEach-Object { $matches[1] }
        foreach ($email in $emails) {
            Write-Host "  - $email" -ForegroundColor Green
        }
    }
} else {
    Write-Host "  [X] firebase.js not found" -ForegroundColor Red
}

Write-Host ""
