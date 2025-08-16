from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HighPal Admin", description="Training Data Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Admin authentication
ADMIN_KEY = os.getenv("ADMIN_KEY", "your_secure_admin_key_2025!")

def verify_admin_key(admin_key: str):
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

@app.get("/health")
async def health_check():
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "message": "HighPal Admin API is running",
        "elasticsearch": "not configured",
        "haystack": "not configured"
    }

@app.get("/")
async def root():
    return {"message": "HighPal Admin API is running"}

@app.get("/admin/training_data/")
async def list_training_data(admin_key: str):
    """List all training data"""
    verify_admin_key(admin_key)
    
    return {
        "total_training_docs": 0,
        "categories": {},
        "training_documents": [],
        "message": "No training data yet - this is a simplified admin interface"
    }

@app.post("/admin/upload_training_pdf/")
async def admin_upload_training_pdf(
    file: UploadFile = File(...),
    category: str = Form(...),
    admin_key: str = Form(...)
):
    """Upload PDF for training data (simplified version)"""
    verify_admin_key(admin_key)
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    content = await file.read()
    
    return {
        "message": "PDF uploaded successfully (test mode)",
        "filename": file.filename,
        "category": category,
        "character_count": len(content),
        "status": "This is a test version - full functionality requires Haystack setup"
    }

@app.post("/admin/add_training_url/")
async def admin_add_training_url(
    url: str = Form(...),
    category: str = Form(...),
    admin_key: str = Form(...)
):
    """Add URL for training data (simplified version)"""
    verify_admin_key(admin_key)
    
    return {
        "message": "URL processed successfully (test mode)",
        "url": url,
        "category": category,
        "character_count": 500,  # Mock value
        "status": "This is a test version - full functionality requires Haystack setup"
    }

@app.delete("/admin/clear_training_data/")
async def admin_clear_training_data(admin_key: str):
    """Clear all training data (simplified version)"""
    verify_admin_key(admin_key)
    
    return {
        "message": "Training data cleared successfully (test mode)",
        "status": "This is a test version - no actual data to clear"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
