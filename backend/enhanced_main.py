"""
Enhanced Main Server with Haystack + MongoDB Atlas Integration
Production-ready FastAPI server with advanced AI capabilities
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
import logging
from PIL import Image
import pytesseract
import cv2
import numpy as np
import os
from datetime import datetime
import hashlib

# Import our Haystack-MongoDB integration
from production_haystack_mongo import HaystackStyleMongoIntegration

# Configure Tesseract path for Windows
if os.name == 'nt':  # Windows
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Users\eddyu\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
    ]
    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HighPal AI Assistant",
    description="Advanced document processing with Haystack + MongoDB Atlas",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Haystack + MongoDB integration
try:
    haystack_mongo = HaystackStyleMongoIntegration()
    logger.info("✅ Haystack + MongoDB Atlas integration ready!")
except Exception as e:
    logger.error(f"❌ Failed to initialize Haystack integration: {e}")
    haystack_mongo = None

# Serve static files
app.mount("/static", StaticFiles(directory="../public"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application page"""
    try:
        with open("../index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>HighPal AI Assistant</title>
        </head>
        <body>
            <h1>🚀 HighPal AI Assistant</h1>
            <p>✅ Haystack + MongoDB Atlas integration is running!</p>
            <h2>Available Endpoints:</h2>
            <ul>
                <li><a href="/docs">/docs</a> - API Documentation</li>
                <li><strong>POST /upload</strong> - Upload documents</li>
                <li><strong>POST /search</strong> - Semantic search</li>
                <li><strong>POST /ask</strong> - Ask questions</li>
                <li><strong>GET /stats</strong> - System statistics</li>
            </ul>
        </body>
        </html>
        """)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process documents with Haystack pipeline"""
    if not haystack_mongo:
        raise HTTPException(status_code=500, detail="Haystack integration not available")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Extract text based on file type
        extracted_content = ""
        
        if file.content_type == "text/plain":
            extracted_content = file_content.decode('utf-8')
        
        elif file.content_type == "application/pdf":
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                extracted_content = ""
                for page in pdf_reader.pages:
                    extracted_content += page.extract_text() + "\n"
            except Exception as e:
                logger.error(f"PDF extraction error: {e}")
                extracted_content = "Failed to extract PDF content"
        
        elif file.content_type.startswith('image/'):
            try:
                # OCR for images
                image = Image.open(io.BytesIO(file_content))
                image_array = np.array(image)
                extracted_content = pytesseract.image_to_string(image_array)
            except Exception as e:
                logger.error(f"OCR error: {e}")
                extracted_content = "Failed to extract image text"
        
        else:
            # Try to decode as text
            try:
                extracted_content = file_content.decode('utf-8')
            except:
                extracted_content = "Unsupported file type"
        
        # Prepare document for Haystack processing
        document_data = [{
            'content': extracted_content,
            'filename': file.filename,
            'file_type': file.content_type,
            'file_size': len(file_content),
            'upload_date': datetime.now().isoformat(),
            'user_id': 'web_user',
            'tags': ['uploaded', 'web'],
            'source': 'web_upload'
        }]
        
        # Process through Haystack pipeline
        documents_added = haystack_mongo.process_and_store_documents(document_data)
        
        return JSONResponse(content={
            "success": True,
            "message": f"File '{file.filename}' processed successfully",
            "documents_added": documents_added,
            "file_info": {
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": len(file_content),
                "content_length": len(extracted_content),
                "processing_method": "haystack_pipeline"
            }
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/search")
async def search_documents(request: dict):
    """Advanced document search with multiple methods"""
    if not haystack_mongo:
        raise HTTPException(status_code=500, detail="Haystack integration not available")
    
    try:
        query = request.get('query', '')
        top_k = request.get('top_k', 5)
        search_method = request.get('method', 'hybrid')  # semantic, text, or hybrid
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Perform search based on method
        if search_method == 'semantic':
            results = haystack_mongo.semantic_search(query, top_k)
        elif search_method == 'text':
            results = haystack_mongo.text_search(query, top_k)
        elif search_method == 'hybrid':
            results = haystack_mongo.hybrid_search(query, top_k)
        else:
            results = haystack_mongo.hybrid_search(query, top_k)  # Default to hybrid
        
        return JSONResponse(content={
            "success": True,
            "query": query,
            "method": search_method,
            "results_count": len(results),
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/ask")
async def ask_question(request: dict):
    """Ask questions about your documents using AI"""
    if not haystack_mongo:
        raise HTTPException(status_code=500, detail="Haystack integration not available")
    
    try:
        question = request.get('question', '')
        top_k = request.get('top_k', 5)
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Process question through Q&A pipeline
        qa_result = haystack_mongo.ask_question(question, top_k)
        
        return JSONResponse(content={
            "success": True,
            "question": question,
            "answer": qa_result['answer'],
            "confidence": qa_result['confidence'],
            "method": qa_result['method'],
            "source_documents": qa_result['source_documents'],
            "sources_count": len(qa_result['source_documents'])
        })
        
    except Exception as e:
        logger.error(f"Q&A error: {e}")
        raise HTTPException(status_code=500, detail=f"Q&A failed: {str(e)}")

@app.get("/stats")
async def get_system_stats():
    """Get comprehensive system statistics"""
    if not haystack_mongo:
        raise HTTPException(status_code=500, detail="Haystack integration not available")
    
    try:
        stats = haystack_mongo.get_system_stats()
        return JSONResponse(content=stats)
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")

@app.post("/search/semantic")
async def semantic_search_endpoint(request: dict):
    """Dedicated semantic search endpoint"""
    request['method'] = 'semantic'
    return await search_documents(request)

@app.post("/search/text") 
async def text_search_endpoint(request: dict):
    """Dedicated text search endpoint"""
    request['method'] = 'text'
    return await search_documents(request)

@app.post("/search/hybrid")
async def hybrid_search_endpoint(request: dict):
    """Dedicated hybrid search endpoint"""
    request['method'] = 'hybrid'
    return await search_documents(request)

@app.get("/health")
async def health_check():
    """System health check"""
    try:
        # Test Haystack integration
        if haystack_mongo:
            stats = haystack_mongo.get_system_stats()
            haystack_status = "operational"
        else:
            stats = None
            haystack_status = "unavailable"
        
        return JSONResponse(content={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "haystack_integration": haystack_status,
            "mongodb_atlas": "connected" if stats else "disconnected",
            "features": {
                "semantic_search": stats['capabilities']['semantic_search'] if stats else False,
                "text_search": stats['capabilities']['text_search'] if stats else False,
                "question_answering": stats['capabilities']['question_answering'] if stats else False,
                "document_processing": stats['capabilities']['document_processing'] if stats else False
            }
        })
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting HighPal AI Assistant Server...")
    print("✨ Features:")
    print("  • MongoDB Atlas cloud storage")
    print("  • Haystack document processing")
    print("  • Semantic search with AI embeddings")
    print("  • Hybrid search (semantic + text)")
    print("  • Question answering (with OpenAI)")
    print("  • Document upload and processing")
    print("")
    print("📡 Server starting on http://localhost:8000")
    print("📖 API docs available at http://localhost:8000/docs")
    
    uvicorn.run(
        "enhanced_main:app",
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
