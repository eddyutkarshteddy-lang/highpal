"""
Simple FastAPI Server with MongoDB Atlas Integration
Minimal version for testing and deployment
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from datetime import datetime
import hashlib
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HighPal AI Assistant",
    description="Document processing with MongoDB Atlas",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable for database connection
mongo_integration = None

def get_mongo_integration():
    """Lazy initialization of MongoDB integration"""
    global mongo_integration
    if mongo_integration is None:
        try:
            from production_haystack_mongo import HaystackStyleMongoIntegration
            mongo_integration = HaystackStyleMongoIntegration()
            logger.info("✅ MongoDB integration initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MongoDB integration: {e}")
            mongo_integration = None
    return mongo_integration

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HighPal AI Assistant API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "upload": "/upload",
            "search": "/search",
            "documents": "/documents"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    mongo = get_mongo_integration()
    mongo_status = "connected" if mongo else "disconnected"
    
    return {
        "status": "healthy",
        "mongodb": mongo_status,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(None)
):
    """Upload a document"""
    try:
        mongo = get_mongo_integration()
        if not mongo:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Read file content
        content = await file.read()
        
        # Process based on file type
        text_content = ""
        if file.content_type == "text/plain":
            text_content = content.decode('utf-8')
        elif file.content_type == "application/pdf":
            # Simple PDF processing
            text_content = f"PDF file: {file.filename}"
        else:
            text_content = f"File: {file.filename} ({file.content_type})"
        
        # Create document metadata
        doc_id = hashlib.md5(content).hexdigest()
        document = {
            "id": doc_id,
            "title": title or file.filename,
            "filename": file.filename,
            "content_type": file.content_type,
            "content": text_content,
            "size": len(content),
            "uploaded_at": datetime.now().isoformat()
        }
        
        # Store in MongoDB
        result = mongo.add_document(
            text_content,
            metadata=document
        )
        
        return {
            "success": True,
            "document_id": doc_id,
            "filename": file.filename,
            "size": len(content),
            "message": "Document uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search_documents(q: str, limit: int = 10):
    """Search documents"""
    try:
        mongo = get_mongo_integration()
        if not mongo:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Perform semantic search
        results = mongo.semantic_search(q, top_k=limit)
        
        return {
            "query": q,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents(limit: int = 20):
    """List all documents"""
    try:
        mongo = get_mongo_integration()
        if not mongo:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Get recent documents from MongoDB
        documents = mongo.get_all_documents(limit=limit)
        
        return {
            "documents": documents,
            "count": len(documents)
        }
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting HighPal AI Assistant Server...")
    print("📡 Server starting on http://localhost:8001")
    print("📖 API docs available at http://localhost:8001/docs")
    
    uvicorn.run(
        "simple_fastapi_server:app",
        host="0.0.0.0", 
        port=8003, 
        reload=False,  # Disable reload to prevent initialization issues
        log_level="info"
    )
