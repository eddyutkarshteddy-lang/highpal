# Firebase Configuration Setup Script for HighPal
# This script helps you configure Firebase for the admin panel

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Firebase Configuration Setup for HighPal" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if .env file exists
$envFile = ".env"
$envContent = ""

if (Test-Path $envFile) {
    $envContent = Get-Content $envFile -Raw
    Write-Host "✓ Found existing .env file" -ForegroundColor Green
} else {
    Write-Host "× .env file not found, creating new one..." -ForegroundColor Yellow
    $envContent = Get-Content ".env.example" -Raw
}

Write-Host ""
Write-Host "Please enter your Firebase configuration values:" -ForegroundColor Yellow
Write-Host "(Get these from: https://console.firebase.google.com/)" -ForegroundColor Gray
Write-Host "Project Settings > General > Your apps > SDK setup and configuration" -ForegroundColor Gray
Write-Host ""

# Prompt for Firebase values
$apiKey = Read-Host "Firebase API Key"
$authDomain = Read-Host "Firebase Auth Domain (e.g., your-app.firebaseapp.com)"
$projectId = Read-Host "Firebase Project ID"
$storageBucket = Read-Host "Firebase Storage Bucket (e.g., your-app.appspot.com)"
$messagingSenderId = Read-Host "Firebase Messaging Sender ID"
$appId = Read-Host "Firebase App ID"

Write-Host ""
Write-Host "Updating .env file..." -ForegroundColor Yellow

# Update or add Firebase config
$firebaseConfig = @"

# Firebase Configuration (for Admin Authentication)
VITE_FIREBASE_API_KEY=$apiKey
VITE_FIREBASE_AUTH_DOMAIN=$authDomain
VITE_FIREBASE_PROJECT_ID=$projectId
VITE_FIREBASE_STORAGE_BUCKET=$storageBucket
VITE_FIREBASE_MESSAGING_SENDER_ID=$messagingSenderId
VITE_FIREBASE_APP_ID=$appId
"@

# Remove old Firebase config if exists
$envContent = $envContent -replace '(?ms)# Firebase Configuration.*?VITE_FIREBASE_APP_ID=.*?\r?\n', ''

# Add new Firebase config
$envContent = $envContent.TrimEnd() + "`n" + $firebaseConfig

# Save to .env
$envContent | Out-File -FilePath $envFile -Encoding UTF8 -NoNewline

Write-Host "✓ Firebase configuration saved to .env" -ForegroundColor Green
Write-Host ""

# Ask about admin emails
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Admin Email Whitelist Configuration" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Current whitelisted admin emails:" -ForegroundColor Yellow
Write-Host "  - admin@highpal.com" -ForegroundColor White
Write-Host "  - eddyutkarsh@gmail.com" -ForegroundColor White
Write-Host ""
$addEmails = Read-Host "Do you want to add more admin emails? (y/n)"

if ($addEmails -eq 'y' -or $addEmails -eq 'Y') {
    Write-Host ""
    Write-Host "Enter admin emails (one per line, empty line to finish):" -ForegroundColor Yellow
    $adminEmails = @('admin@highpal.com', 'eddyutkarsh@gmail.com')
    
    while ($true) {
        $email = Read-Host "Admin email"
        if ([string]::IsNullOrWhiteSpace($email)) {
            break
        }
        $adminEmails += "'$email'"
    }
    
    Write-Host ""
    Write-Host "Admin emails to add:" -ForegroundColor Yellow
    $adminEmails | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }
    Write-Host ""
    
    # Create backup of firebase.js
    $firebaseJs = "src\config\firebase.js"
    $backupFile = "src\config\firebase.js.backup"
    Copy-Item $firebaseJs $backupFile -Force
    Write-Host "✓ Created backup: $backupFile" -ForegroundColor Green
    
    # Read firebase.js
    $firebaseContent = Get-Content $firebaseJs -Raw
    
    # Update admin emails array
    $emailList = $adminEmails -join ",`n  "
    $newEmailSection = @"
const AUTHORIZED_ADMINS = [
  $emailList,
  // Add more admin emails
];
"@
    
    $firebaseContent = $firebaseContent -replace '(?ms)const AUTHORIZED_ADMINS = \[.*?\];', $newEmailSection
    
    # Save updated file
    $firebaseContent | Out-File -FilePath $firebaseJs -Encoding UTF8 -NoNewline
    Write-Host "✓ Updated admin whitelist in firebase.js" -ForegroundColor Green
}

Write-Host ""
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart your dev server: npm run dev" -ForegroundColor White
Write-Host "2. Go to: http://localhost:5173/admin/login" -ForegroundColor White
Write-Host "3. Click 'Sign in with Google' to test" -ForegroundColor White
Write-Host ""
Write-Host "Important Notes:" -ForegroundColor Yellow
Write-Host "- Make sure you enabled Google Sign-In in Firebase Console" -ForegroundColor White
Write-Host "- Add your domain to Firebase authorized domains (localhost is pre-approved)" -ForegroundColor White
Write-Host "- Only whitelisted emails can access the admin panel" -ForegroundColor White
Write-Host ""
Write-Host "Firebase Console: https://console.firebase.google.com/project/$projectId/overview" -ForegroundColor Cyan
Write-Host ""
