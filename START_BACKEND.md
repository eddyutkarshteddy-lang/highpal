# 🚀 Start Backend Server

## Quick Start

The backend server needs to be running for the AI to respond. Currently seeing:
```
POST http://localhost:8003/ask_question/ net::ERR_CONNECTION_REFUSED
```

### **Option 1: PowerShell (Recommended)**
```powershell
cd backend
python training_server.py
```

### **Option 2: Use Existing Batch File**
```cmd
.\restart-backend.bat
```

### **Option 3: Python Virtual Environment**
```powershell
cd backend
.\venv\Scripts\Activate.ps1
python training_server.py
```

## Expected Output

When backend starts successfully, you should see:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8003
```

## Common Issues

### 1. **Port Already in Use**
```powershell
# Kill process on port 8003
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8003).OwningProcess -Force
```

### 2. **Missing Dependencies**
```powershell
cd backend
pip install -r requirements.txt
```

### 3. **Virtual Environment Not Activated**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Test Backend is Running

```powershell
curl http://localhost:8003/health
# OR
Invoke-WebRequest -Uri http://localhost:8003/health
```

## Current Issue

The VAD system initialized successfully:
```
✅ 🎤 Initializing VAD detector...
✅ VAD detector initialized successfully
```

But backend is not responding, causing generic fallback responses:
```
"I'd love to continue our conversation. What else would you like to discuss?"
```

**Start the backend server to fix this!** 🎯
