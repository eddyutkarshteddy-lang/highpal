"""
Ultra Simple FastAPI Server for Testing
Minimal version without complex dependencies
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HighPal AI Assistant - Test Server",
    description="Simple document processing API",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HighPal AI Assistant API - Test Server",
        "version": "0.1.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "server": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return {
        "test": "success",
        "message": "Server is working correctly!",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Test Server...")
    print("📡 Server will run on http://localhost:8002")
    print("📖 API docs: http://localhost:8002/docs")
    print("🔄 Interactive docs: http://localhost:8002/redoc")
    
    uvicorn.run(
        "test_server:app",
        host="127.0.0.1", 
        port=8002, 
        reload=False,
        log_level="info"
    )
