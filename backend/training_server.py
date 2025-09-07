"""
HighPal AI Server with PDF URL Training Capabilities
Enhanced server with model training from public PDF URLs
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
from datetime import datetime
import hashlib
import io
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import training capabilities (optional)
try:
    from training_endpoints import create_training_endpoints
    TRAINING_AVAILABLE = True
    logger.info("✅ Training endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Training endpoints not available: {e}")
    TRAINING_AVAILABLE = False
    def create_training_endpoints(app):
        pass

# Import PDF extractor (optional)
try:
    from pdf_extractor import AdvancedPDFExtractor
    PDF_EXTRACTOR_AVAILABLE = True
    logger.info("✅ PDF extractor loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ PDF extractor not available: {e}")
    PDF_EXTRACTOR_AVAILABLE = False
    
    class AdvancedPDFExtractor:
        def extract_text_from_pdf(self, content):
            return {
                'best_text': 'PDF extraction libraries not available. Please install PyMuPDF, PyPDF2, pdfplumber, and pdfminer to enable PDF processing.', 
                'extraction_info': {'method': 'fallback', 'status': 'error', 'error': 'Missing dependencies'}
            }  # No-op fallback

# Pydantic models for request/response
class QuestionRequest(BaseModel):
    question: str
    uploaded_files: list = []  # Optional list of uploaded file IDs

# Initialize FastAPI app
app = FastAPI(
    title="HighPal AI Assistant - Training Edition",
    description="Advanced document processing with PDF URL training capabilities",
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
    """Root endpoint with training capabilities info"""
    return {
        "message": "HighPal AI Assistant - Training Edition",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Document upload and processing",
            "AI-powered semantic search", 
            "PDF URL training",
            "Background task processing",
            "Batch training support"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "upload": "/upload",
            "search": "/search",
            "ask_question": "/ask_question",
            "training": {
                "train_urls": "/train/pdf-urls",
                "train_background": "/train/pdf-urls/background",
                "train_batch": "/train/pdf-urls/batch",
                "training_status": "/train/status"
            }
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
        "training_ready": mongo_status == "connected",
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
        extraction_info = {}
        
        if file.content_type == "text/plain":
            text_content = content.decode('utf-8')
            extraction_info = {"method": "text_decode", "status": "success"}
        elif file.content_type == "application/pdf":
            # Use advanced PDF extraction
            try:
                if PDF_EXTRACTOR_AVAILABLE:
                    extractor = AdvancedPDFExtractor()
                    extraction_result = extractor.extract_text_from_pdf(content)
                    text_content = extraction_result.get('best_text', '')
                    extraction_info = extraction_result.get('extraction_info', {})
                    
                    if not text_content or len(text_content.strip()) < 10:
                        raise Exception("Extracted text too short or empty")
                        
                    logger.info(f"✅ PDF extraction successful: {len(text_content)} characters")
                else:
                    raise Exception("PDF extractor not available")
                    
            except Exception as e:
                logger.error(f"❌ PDF extraction failed: {e}")
                raise HTTPException(
                    status_code=422, 
                    detail=f"Failed to extract PDF content: {str(e)}. Please ensure the PDF contains readable text."
                )
        else:
            text_content = f"File: {file.filename} ({file.content_type})"
            extraction_info = {"method": "fallback", "status": "success"}
        
        # Create document metadata
        doc_id = hashlib.md5(content).hexdigest()
        document = {
            "id": doc_id,
            "title": title or file.filename,
            "filename": file.filename,
            "content_type": file.content_type,
            "content": text_content,
            "size": len(content),
            "uploaded_at": datetime.now().isoformat(),
            "source_type": "manual_upload",
            "extraction_info": extraction_info
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

@app.post("/ask_question/")
@app.post("/ask_question")
@app.get("/ask_question")
async def ask_question(request: QuestionRequest = None, question: str = None, q: str = None):
    """Ask a question using AI - supports both GET (query params) and POST (JSON body)"""
    try:
        # Handle different request formats
        if request and request.question:
            query = request.question
            uploaded_files = getattr(request, 'uploaded_files', [])
        else:
            # Accept both 'question' and 'q' parameters for GET requests
            query = question or q
            uploaded_files = []
            
        if not query:
            raise HTTPException(status_code=400, detail="Question parameter required")
        
        mongo = get_mongo_integration()
        if not mongo:
            # Fallback response when MongoDB is not available
            return {
                "question": query,
                "answer": f"Hello! I'm Pal, your AI learning assistant. You asked: '{query}'. While I can't access the document database right now, I'm here to help you with your studies! Please try uploading some documents first.",
                "source": "Pal AI Assistant (Fallback Mode)",
                "timestamp": datetime.now().isoformat(),
                "search_results": []
            }
        
        # Search for relevant documents
        search_results = mongo.semantic_search(query, top_k=5)
        
        # Filter out corrupted documents containing error messages
        def is_valid_document(doc):
            content = doc.get('content', '')
            error_phrases = [
                'Failed to extract PDF content',
                'PDF extraction failed',
                'extraction not available',
                'PDF extraction libraries not available'
            ]
            return not any(phrase in content for phrase in error_phrases)
        
        # Filter search results
        valid_search_results = [doc for doc in search_results if is_valid_document(doc)]
        
        # Generate answer based on valid search results
        if valid_search_results:
            context = "\\n".join([doc.get('content', '') for doc in valid_search_results[:3]])
            answer = f"Here's what I found about '{query}': {context[:500]}..."
        else:
            answer = f"I don't have specific information about '{query}' in my knowledge base. Could you try rephrasing your question or asking about a different topic?"
        
        # Don't show documents to users - they're only for training/context
        return {
            "question": query,
            "answer": answer
        }
        
    except Exception as e:
        logger.error(f"Question answering error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents(limit: int = 20, source_type: str = None):
    """List all documents with optional filtering"""
    try:
        mongo = get_mongo_integration()
        if not mongo:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Build filter
        filter_dict = {}
        if source_type:
            filter_dict["metadata.source_type"] = source_type
        
        # Get documents from MongoDB
        cursor = mongo.collection.find(filter_dict).limit(limit)
        documents = []
        
        for doc in cursor:
            documents.append({
                "id": str(doc.get("_id")),
                "content_preview": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", ""),
                "metadata": doc.get("metadata", {})
            })
        
        return {
            "documents": documents,
            "count": len(documents),
            "filter": filter_dict
        }
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add training endpoints to the app
create_training_endpoints(app)

@app.get("/training-guide")
async def training_guide():
    """Get training usage guide"""
    return {
        "title": "HighPal PDF URL Training Guide",
        "description": "Train your AI model with PDFs from public URLs",
        "examples": {
            "single_training": {
                "endpoint": "POST /train/pdf-urls",
                "payload": {
                    "urls": [
                        "https://arxiv.org/pdf/2023.12345.pdf",
                        "https://example.com/whitepaper.pdf"
                    ],
                    "metadata": {
                        "domain": "research",
                        "priority": "high"
                    }
                }
            },
            "background_training": {
                "endpoint": "POST /train/pdf-urls/background",
                "description": "Returns immediately with task ID"
            },
            "check_status": {
                "endpoint": "GET /train/status",
                "description": "Overall training statistics"
            }
        },
        "workflow": [
            "1. Collect PDF URLs from public sources",
            "2. POST to /train/pdf-urls with URL list", 
            "3. System downloads and processes PDFs",
            "4. Text is extracted and chunked",
            "5. Embeddings are generated",
            "6. Data is stored in MongoDB Atlas",
            "7. Model is ready for improved searches"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting HighPal AI Assistant with Training Capabilities...")
    print("✨ Features:")
    print("  • MongoDB Atlas cloud storage")
    print("  • Haystack document processing")  
    print("  • Semantic search with AI embeddings")
    print("  • PDF URL training system")
    print("  • Background task processing")
    print("  • Batch training support")
    print("")
    print("📡 Server starting on http://localhost:8003")
    print("📖 API docs available at http://localhost:8003/docs")
    print("🎓 Training guide at http://localhost:8003/training-guide")
    
    uvicorn.run(
        "training_server:app",
        host="0.0.0.0", 
        port=8003, 
        reload=False,
        log_level="info"
    )
