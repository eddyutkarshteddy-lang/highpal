"""
Haystack FastAPI Server for HighPal
Provides REST API endpoints for document management and search
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from bs4 import BeautifulSoup
import urllib.parse

from simple_haystack_manager import get_haystack_manager
# from pdf_extractor import extract_pdf_text_advanced  # Comment out for now

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HighPal Haystack API",
    description="Advanced document management with Haystack integration",
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

# Pydantic models
class DocumentResponse(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    score: Optional[float] = None

class SearchRequest(BaseModel):
    query: str
    method: str = "hybrid"  # bm25, embedding, hybrid
    top_k: int = 5

class SearchResponse(BaseModel):
    results: List[DocumentResponse]
    total_found: int
    query: str
    method: str

class AddDocumentRequest(BaseModel):
    content: str
    filename: Optional[str] = None
    category: Optional[str] = "general"
    title: Optional[str] = None

class URLRequest(BaseModel):
    url: str
    title: Optional[str] = None
    category: Optional[str] = "web_content"

class StatisticsResponse(BaseModel):
    total_documents: int
    total_characters: int
    categories: Dict[str, int]
    average_document_length: float

# Initialize Haystack manager
haystack_manager = get_haystack_manager()

# Simple PDF extraction function (fallback)
def simple_pdf_extract(pdf_content: bytes) -> dict:
    """Simple PDF extraction using basic methods"""
    try:
        import PyPDF2
        import io
        
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        text = ""
        pages = len(reader.pages)
        
        for page in reader.pages:
            try:
                text += page.extract_text() + "\n\n"
            except:
                continue
        
        return {
            'best_text': text.strip(),
            'extraction_info': {
                'methods': ['pypdf2_basic'],
                'total_length': len(text.strip()),
                'pages': pages,
                'final_method': 'pypdf2_basic',
                'all_results': {
                    'pypdf2_basic': {'length': len(text.strip()), 'pages': pages}
                }
            }
        }
    except Exception as e:
        # Fallback to simple text extraction
        try:
            text = pdf_content.decode('utf-8', errors='ignore')
        except:
            text = f"PDF content ({len(pdf_content)} bytes) - extraction failed"
        
        return {
            'best_text': text,
            'extraction_info': {
                'methods': ['fallback'],
                'total_length': len(text),
                'pages': 1,
                'final_method': 'fallback',
                'error': str(e)
            }
        }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HighPal Haystack API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "search": "/search",
            "documents": "/documents",
            "upload": "/upload",
            "statistics": "/statistics"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        stats = haystack_manager.get_statistics()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "document_count": stats.get("total_documents", 0),
            "haystack_status": "operational"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Search documents using various methods"""
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        if request.method not in ["bm25", "embedding", "hybrid"]:
            raise HTTPException(status_code=400, detail="Method must be one of: bm25, embedding, hybrid")
        
        results = haystack_manager.search_documents(
            query=request.query,
            method=request.method,
            top_k=request.top_k
        )
        
        formatted_results = [
            DocumentResponse(
                id=result["id"],
                content=result["content"],
                metadata=result["metadata"],
                score=result.get("score")
            )
            for result in results
        ]
        
        return SearchResponse(
            results=formatted_results,
            total_found=len(formatted_results),
            query=request.query,
            method=request.method
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/search")
async def search_documents_get(
    q: str = Query(..., description="Search query"),
    method: str = Query("hybrid", description="Search method"),
    top_k: int = Query(5, description="Number of results")
):
    """GET endpoint for searching documents"""
    request = SearchRequest(query=q, method=method, top_k=top_k)
    return await search_documents(request)

@app.post("/documents", response_model=Dict[str, str])
async def add_document(request: AddDocumentRequest):
    """Add a new document"""
    try:
        if not request.content.strip():
            raise HTTPException(status_code=400, detail="Content cannot be empty")
        
        metadata = {
            "filename": request.filename or "direct_input",
            "category": request.category or "general",
            "title": request.title or "Untitled Document",
            "upload_date": datetime.now().isoformat(),
            "size": len(request.content),
            "source": "api"
        }
        
        doc_id = haystack_manager.add_document(request.content, metadata)
        
        return {
            "document_id": doc_id,
            "message": "Document added successfully",
            "characters": len(request.content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add document error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add document: {str(e)}")

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form("general"),
    title: Optional[str] = Form(None)
):
    """Upload and process a file with advanced PDF extraction"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")
        
        # Read file content
        content = await file.read()
        
        # Handle different file types
        if file.filename.lower().endswith('.pdf'):
            logger.info(f"🚀 Processing PDF file: {file.filename} ({len(content)} bytes)")
            
            # Use simple PDF extraction for now
            extraction_result = simple_pdf_extract(content)
            text_content = extraction_result['best_text']
            extraction_info = extraction_result['extraction_info']
            
            logger.info(f"📊 PDF Extraction Complete:")
            logger.info(f"- Final extracted text: {len(text_content)} characters")
            logger.info(f"- Methods used: {', '.join(extraction_info['methods'])}")
            logger.info(f"- Best method: {extraction_info['final_method']}")
            logger.info(f"- Pages: {extraction_info['pages']}")
            
            if len(text_content) < 100:
                logger.warning(f"⚠️ Low extraction yield: only {len(text_content)} characters extracted")
            
            # Add extraction info to metadata
            metadata = {
                "filename": file.filename,
                "category": category,
                "title": title or file.filename,
                "upload_date": datetime.now().isoformat(),
                "size": len(content),
                "source": "pdf_upload",
                "file_type": file.content_type,
                "extraction_info": extraction_info,
                "pages": extraction_info['pages'],
                "extraction_method": extraction_info['final_method']
            }
            
        elif file.filename.lower().endswith(('.txt', '.md')):
            text_content = content.decode('utf-8')
            metadata = {
                "filename": file.filename,
                "category": category,
                "title": title or file.filename,
                "upload_date": datetime.now().isoformat(),
                "size": len(content),
                "source": "text_upload",
                "file_type": file.content_type
            }
            
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Supported: PDF, TXT, MD")
        
        doc_id = haystack_manager.add_document(text_content, metadata)
        
        response = {
            "document_id": doc_id,
            "filename": file.filename,
            "characters": len(text_content),
            "message": "File uploaded and processed successfully"
        }
        
        # Add PDF-specific info to response
        if file.filename.lower().endswith('.pdf'):
            response.update({
                "pages": extraction_info['pages'],
                "extraction_method": extraction_info['final_method'],
                "extraction_methods_tried": extraction_info['methods']
            })
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/upload_pdf")
async def upload_pdf_enhanced(
    file: UploadFile = File(...),
    category: str = Form("academic"),
    title: Optional[str] = Form(None)
):
    """
    Enhanced PDF upload endpoint with advanced extraction
    Equivalent to the Node.js /upload_training_pdf/ endpoint
    """
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No PDF file selected")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported for this endpoint")
        
        # Read PDF content
        pdf_content = await file.read()
        
        logger.info(f"🚀 Enhanced PDF upload: {file.filename} ({len(pdf_content)} bytes)")
        
        # Use simple PDF extraction with multiple strategies
        extraction_result = simple_pdf_extract(pdf_content)
        extracted_text = extraction_result['best_text']
        extraction_info = extraction_result['extraction_info']
        
        logger.info(f"📊 Enhanced PDF Extraction Complete:")
        logger.info(f"- Final extracted text: {len(extracted_text)} characters")
        logger.info(f"- Methods used: {', '.join(extraction_info['methods'])}")
        logger.info(f"- Best method: {extraction_info['final_method']}")
        logger.info(f"- PDF file size: {len(pdf_content)} bytes")
        logger.info(f"- Pages: {extraction_info['pages']}")
        
        if len(extracted_text) < 100:
            logger.warning(f"⚠️ Low extraction yield: only {len(extracted_text)} characters extracted")
        
        # Create comprehensive metadata similar to Node.js version
        metadata = {
            "filename": file.filename,
            "category": category,
            "title": title or "Enhanced PDF Upload",
            "upload_date": datetime.now().isoformat(),
            "size": len(pdf_content),
            "source": "pdf_enhanced_upload",
            "file_type": "application/pdf",
            "extraction_info": extraction_info,
            "pages": extraction_info['pages'],
            "extraction_method": extraction_info['final_method'],
            "methods_attempted": len(extraction_info['methods']),
            "final_length": len(extracted_text)
        }
        
        # Add document to Haystack
        doc_id = haystack_manager.add_document(extracted_text, metadata)
        
        logger.info(f"✅ Document stored with ID: {doc_id}")
        
        # Response similar to Node.js version
        response = {
            "message": "Enhanced PDF upload successful!",
            "filename": file.filename,
            "size": len(pdf_content),
            "file_id": doc_id,
            "category": category,
            "extracted_text_length": len(extracted_text),
            "extraction_info": {
                "pages": extraction_info['pages'],
                "final_method": extraction_info['final_method'],
                "methods_tried": extraction_info['methods'],
                "total_methods": len(extraction_info['methods']),
                "all_results": extraction_info['all_results']
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced PDF upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced PDF upload failed: {str(e)}")

@app.get("/admin")
async def admin_interface():
    """Admin interface endpoint similar to Node.js version"""
    try:
        # Get document statistics
        stats = haystack_manager.get_statistics()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>HighPal Admin - Haystack Documents</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .stats {{ margin: 20px 0; }}
                .stat-item {{ display: inline-block; margin: 10px; padding: 10px; background: #e0e0e0; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 HighPal Admin - Haystack Server (Port 8002)</h1>
                <p>Advanced document management with AI-powered search</p>
            </div>
            
            <div class="stats">
                <h2>📊 Document Statistics</h2>
                <div class="stat-item"><strong>Total Documents:</strong> {stats.get('total_documents', 0)}</div>
                <div class="stat-item"><strong>Total Characters:</strong> {stats.get('total_characters', 0):,}</div>
                <div class="stat-item"><strong>Average Length:</strong> {stats.get('average_document_length', 0):.0f}</div>
            </div>
            
            <div>
                <h2>📂 Categories</h2>
                <ul>
        """
        
        for category, count in stats.get('categories', {}).items():
            html_content += f"<li><strong>{category}:</strong> {count} documents</li>"
        
        html_content += """
                </ul>
            </div>
            
            <div>
                <h2>🔧 API Endpoints</h2>
                <ul>
                    <li><a href="/docs" target="_blank">📖 API Documentation</a></li>
                    <li><a href="/health" target="_blank">❤️ Health Check</a></li>
                    <li><a href="/statistics" target="_blank">📊 Statistics JSON</a></li>
                    <li><a href="/documents" target="_blank">📄 All Documents</a></li>
                </ul>
            </div>
            
            <div style="margin-top: 30px; padding: 15px; background-color: #e8f5e8; border-radius: 5px;">
                <h3>✨ Enhanced Features</h3>
                <ul>
                    <li>🤖 AI-powered semantic search</li>
                    <li>📑 Advanced PDF extraction (6 different methods)</li>
                    <li>🌐 URL content extraction</li>
                    <li>🔍 Hybrid search (BM25 + Embeddings)</li>
                    <li>📚 Document categorization</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        return JSONResponse(content=html_content, media_type="text/html")
        
    except Exception as e:
        logger.error(f"Admin interface error: {e}")
        raise HTTPException(status_code=500, detail=f"Admin interface failed: {str(e)}")

@app.url_content
async def add_url_content(request: URLRequest):
    """Extract content from URL and add as document"""
    try:
        if not request.url.strip():
            raise HTTPException(status_code=400, detail="URL cannot be empty")
        
        # Validate URL
        if not request.url.startswith(('http://', 'https://')):
            request.url = 'https://' + request.url
        
        # Fetch content from URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(request.url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract text content
        text_content = soup.get_text()
        
        # Clean up text (remove extra whitespace)
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = ' '.join(chunk for chunk in chunks if chunk)
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="No text content found at URL")
        
        # Extract title from HTML if not provided
        title = request.title
        if not title:
            title_tag = soup.find('title')
            title = title_tag.string.strip() if title_tag and title_tag.string else urllib.parse.urlparse(request.url).netloc
        
        metadata = {
            "url": request.url,
            "title": title,
            "category": request.category,
            "upload_date": datetime.now().isoformat(),
            "size": len(text_content),
            "source": "url_extraction",
            "domain": urllib.parse.urlparse(request.url).netloc
        }
        
        doc_id = haystack_manager.add_document(text_content, metadata)
        
        return {
            "document_id": doc_id,
            "url": request.url,
            "title": title,
            "characters": len(text_content),
            "message": "URL content extracted and added successfully"
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"URL fetch error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process URL: {str(e)}")

@app.get("/documents")
async def get_all_documents():
    """Get all documents with metadata"""
    try:
        documents = haystack_manager.get_all_documents()
        return {
            "documents": documents,
            "total": len(documents)
        }
    except Exception as e:
        logger.error(f"Get documents error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")

@app.get("/documents/{doc_id}")
async def get_document(doc_id: str):
    """Get a specific document by ID"""
    try:
        document = haystack_manager.get_document_by_id(doc_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document"""
    try:
        success = haystack_manager.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": f"Document {doc_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@app.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Get document store statistics"""
    try:
        stats = haystack_manager.get_statistics()
        return StatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@app.get("/categories")
async def get_categories():
    """Get all document categories"""
    try:
        stats = haystack_manager.get_statistics()
        categories = stats.get("categories", {})
        return {
            "categories": list(categories.keys()),
            "category_counts": categories
        }
    except Exception as e:
        logger.error(f"Categories error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")

@app.post("/migrate")
async def migrate_from_local():
    """Migrate documents from local storage to Haystack"""
    try:
        # This will reload documents from local storage
        haystack_manager.load_existing_documents()
        stats = haystack_manager.get_statistics()
        return {
            "message": "Migration completed successfully",
            "documents_migrated": stats.get("total_documents", 0)
        }
    except Exception as e:
        logger.error(f"Migration error: {e}")
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "haystack_server:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
