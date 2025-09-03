"""
Enhanced Haystack FastAPI Server with MongoDB Atlas Support
Provides REST API endpoints with cloud storage capabilities
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
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
import uvicorn
from bs4 import BeautifulSoup
import urllib.parse

from cloud_haystack_manager import get_cloud_haystack_manager
from mongodb_config import mongodb_config
from pdf_extractor import AdvancedPDFExtractor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HighPal Enhanced API with MongoDB Atlas",
    description="Advanced document management with MongoDB Atlas cloud storage",
    version="3.0.0"
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
    method: str = "simple"
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
    storage_type: str
    connection_status: str

# Initialize the advanced PDF extractor
advanced_pdf_extractor = AdvancedPDFExtractor()

# Initialize document manager with MongoDB if available
if mongodb_config.is_configured():
    logger.info("🚀 MongoDB Atlas connection configured - using cloud storage")
    document_manager = get_cloud_haystack_manager("mongodb", mongodb_config.connection_string)
else:
    logger.info("📁 MongoDB not configured - using local storage")
    document_manager = get_cloud_haystack_manager("local")

# Advanced PDF extraction function (using the AdvancedPDFExtractor)
def extract_pdf_content(pdf_content: bytes) -> dict:
    """Advanced PDF extraction using multiple methods"""
    try:
        logger.info("🚀 Starting advanced PDF extraction...")
        result = advanced_pdf_extractor.extract_text_from_pdf(pdf_content)
        logger.info(f"✅ Advanced extraction complete: {result['extraction_info']['total_length']} characters using {result['extraction_info']['final_method']}")
        return result
    except Exception as e:
        logger.error(f"❌ Advanced extraction failed: {str(e)}")
        # Fallback to simple extraction
        return simple_pdf_extract_fallback(pdf_content)

def simple_pdf_extract_fallback(pdf_content: bytes) -> dict:
    """Simple PDF extraction fallback"""
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
                'methods': ['pypdf2_fallback'],
                'total_length': len(text.strip()),
                'pages': pages,
                'final_method': 'pypdf2_fallback',
                'all_results': {
                    'pypdf2_fallback': {'length': len(text.strip()), 'pages': pages}
                }
            }
        }
    except Exception as e:
        # Ultimate fallback
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
    storage_info = "MongoDB Atlas" if mongodb_config.is_configured() else "Local Storage"
    return {
        "message": f"HighPal Enhanced API v3.0 - {storage_info}",
        "version": "3.0.0",
        "storage": document_manager.storage_type,
        "features": [
            "MongoDB Atlas cloud storage", 
            "Advanced PDF extraction with 6 methods", 
            "Table detection and extraction",
            "Quality scoring and best result selection",
            "URL content extraction", 
            "Document search", 
            "Cloud backup"
        ],
        "endpoints": {
            "health": "/health",
            "search": "/search",
            "documents": "/documents",
            "upload": "/upload",
            "upload_pdf": "/upload_pdf",
            "url": "/url",
            "admin": "/admin",
            "statistics": "/statistics",
            "setup": "/setup"
        }
    }

@app.get("/setup")
async def setup_instructions():
    """Get MongoDB Atlas setup instructions"""
    if mongodb_config.is_configured():
        return {
            "status": "✅ MongoDB Atlas is configured",
            "connection": "Active",
            "storage_type": document_manager.storage_type
        }
    else:
        return JSONResponse(
            content={
                "status": "⚠️ MongoDB Atlas not configured",
                "instructions": mongodb_config.get_setup_instructions(),
                "current_storage": "Local files only"
            },
            media_type="application/json"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        stats = document_manager.get_statistics()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "document_count": stats.get("total_documents", 0),
            "storage_type": stats.get("storage_type", "local"),
            "connection_status": stats.get("connection_status", "local"),
            "mongodb_configured": mongodb_config.is_configured()
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
        
        results = document_manager.search_documents(
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
    method: str = Query("simple", description="Search method"),
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
            "source": "api",
            "storage": document_manager.storage_type
        }
        
        doc_id = document_manager.add_document(request.content, metadata)
        
        return {
            "document_id": doc_id,
            "message": f"Document added successfully to {document_manager.storage_type}",
            "characters": len(request.content),
            "storage": document_manager.storage_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add document error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add document: {str(e)}")

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: str = Form("general")
):
    """Simple file upload endpoint"""
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        pdf_content = await file.read()
        if not pdf_content:
            raise HTTPException(status_code=400, detail="Empty file")
        
        # Use advanced PDF extraction
        from pdf_extractor import extract_pdf_text_advanced
        extraction_result = extract_pdf_text_advanced(pdf_content)
        
        metadata = {
            "filename": file.filename,
            "title": title or file.filename,
            "category": category,
            "upload_date": datetime.now().isoformat(),
            "size": len(pdf_content),
            "source": "file_upload",
            "storage": document_manager.storage_type,
            "extraction_method": extraction_result.get('method', 'unknown'),
            "extraction_score": extraction_result.get('score', 0)
        }
        
        doc_id = document_manager.add_document(extraction_result['content'], metadata)
        
        return {
            "document_id": doc_id,
            "filename": file.filename,
            "characters": len(extraction_result['content']),
            "extraction_method": extraction_result.get('method', 'unknown'),
            "extraction_score": extraction_result.get('score', 0),
            "storage_type": document_manager.storage_type,
            "message": f"File uploaded successfully to {document_manager.storage_type}"
        }
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/upload_pdf")
async def upload_pdf_enhanced(
    file: UploadFile = File(...),
    category: str = Form("academic"),
    title: Optional[str] = Form(None)
):
    """Enhanced PDF upload endpoint with cloud storage"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No PDF file selected")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read PDF content
        pdf_content = await file.read()
        
        logger.info(f"🚀 Enhanced PDF upload: {file.filename} ({len(pdf_content)} bytes) to {document_manager.storage_type}")
        
        # Extract text from PDF using advanced extraction
        extraction_result = extract_pdf_content(pdf_content)
        extracted_text = extraction_result['best_text']
        extraction_info = extraction_result['extraction_info']
        
        logger.info(f"📊 PDF Extraction Complete: {len(extracted_text)} characters")
        
        # Create comprehensive metadata
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
            "storage": document_manager.storage_type
        }
        
        # Add document to storage (MongoDB Atlas or local)
        doc_id = document_manager.add_document(extracted_text, metadata)
        
        logger.info(f"✅ Document stored with ID: {doc_id} in {document_manager.storage_type}")
        
        # Response with storage info
        response = {
            "message": f"Enhanced PDF upload successful to {document_manager.storage_type}!",
            "filename": file.filename,
            "size": len(pdf_content),
            "file_id": doc_id,
            "category": category,
            "extracted_text_length": len(extracted_text),
            "storage_type": document_manager.storage_type,
            "cloud_backup": mongodb_config.is_configured(),
            "extraction_info": {
                "pages": extraction_info['pages'],
                "final_method": extraction_info['final_method'],
                "methods_tried": extraction_info['methods']
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Enhanced PDF upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced PDF upload failed: {str(e)}")

@app.post("/url", response_model=Dict[str, str])
async def add_url_content(request: URLRequest):
    """Extract content from URL and add as document to cloud storage"""
    try:
        if not request.url.strip():
            raise HTTPException(status_code=400, detail="URL cannot be empty")
        
        # Validate URL
        if not request.url.startswith(('http://', 'https://')):
            request.url = 'https://' + request.url
        
        # Fetch content from URL
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
        
        # Clean up text
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = ' '.join(chunk for chunk in chunks if chunk)
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="No text content found at URL")
        
        # Extract title
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
            "domain": urllib.parse.urlparse(request.url).netloc,
            "storage": document_manager.storage_type
        }
        
        doc_id = document_manager.add_document(text_content, metadata)
        
        return {
            "document_id": doc_id,
            "url": request.url,
            "title": title,
            "characters": len(text_content),
            "storage_type": document_manager.storage_type,
            "message": f"URL content extracted and saved to {document_manager.storage_type}"
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"URL fetch error: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process URL: {str(e)}")

@app.get("/admin")
async def admin_interface():
    """Enhanced admin interface with MongoDB Atlas info"""
    try:
        stats = document_manager.get_statistics()
        storage_status = "✅ MongoDB Atlas" if mongodb_config.is_configured() else "📁 Local Storage"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>HighPal Enhanced Admin - Cloud Storage</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 8px; }}
                .storage-info {{ background-color: #e8f5e8; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 5px solid #27ae60; }}
                .stats {{ margin: 20px 0; display: flex; flex-wrap: wrap; }}
                .stat-item {{ background: linear-gradient(135deg, #3498db, #2980b9); color: white; margin: 10px; padding: 15px; border-radius: 8px; min-width: 200px; }}
                .feature {{ background-color: #2c3e50; color: white; padding: 12px; margin: 5px 0; border-radius: 5px; }}
                .endpoint {{ background-color: #e74c3c; color: white; padding: 10px; margin: 3px 0; border-radius: 5px; }}
                .setup-box {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚀 HighPal Enhanced Admin - Cloud Storage Ready</h1>
                <p>Advanced document management with MongoDB Atlas integration</p>
                <p><strong>Storage: {storage_status}</strong></p>
            </div>
            
            <div class="storage-info">
                <h3>☁️ Storage Information</h3>
                <p><strong>Current Storage:</strong> {stats.get('storage_type', 'local').title()}</p>
                <p><strong>Connection Status:</strong> {stats.get('connection_status', 'local').title()}</p>
                <p><strong>MongoDB Configured:</strong> {'Yes' if mongodb_config.is_configured() else 'No'}</p>
            </div>
            
            <div class="stats">
                <div class="stat-item">
                    <h4>📊 Documents</h4>
                    <p>{stats.get('total_documents', 0)} total</p>
                </div>
                <div class="stat-item">
                    <h4>📝 Characters</h4>
                    <p>{stats.get('total_characters', 0):,} total</p>
                </div>
                <div class="stat-item">
                    <h4>📏 Average Length</h4>
                    <p>{stats.get('average_document_length', 0):.0f} chars</p>
                </div>
            </div>
            
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px dashed #6c757d;">
                <h3>📤 Upload PDF Document</h3>
                <form id="uploadForm" enctype="multipart/form-data" style="margin: 15px 0;">
                    <div style="margin: 10px 0;">
                        <label for="pdfFile" style="display: block; margin-bottom: 5px; font-weight: bold;">Select PDF File:</label>
                        <input type="file" id="pdfFile" name="file" accept=".pdf" style="padding: 8px; border: 1px solid #ccc; border-radius: 4px; width: 300px;" required>
                    </div>
                    <div style="margin: 10px 0;">
                        <label for="title" style="display: block; margin-bottom: 5px; font-weight: bold;">Title (optional):</label>
                        <input type="text" id="title" name="title" placeholder="Document title" style="padding: 8px; border: 1px solid #ccc; border-radius: 4px; width: 300px;">
                    </div>
                    <div style="margin: 10px 0;">
                        <label for="category" style="display: block; margin-bottom: 5px; font-weight: bold;">Category (optional):</label>
                        <input type="text" id="category" name="category" placeholder="academic, business, legal, etc." style="padding: 8px; border: 1px solid #ccc; border-radius: 4px; width: 300px;">
                    </div>
                    <button type="submit" style="background-color: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">🚀 Upload PDF</button>
                </form>
                <div id="uploadStatus" style="margin-top: 15px;"></div>
            </div>
            
            <script>
                document.getElementById('uploadForm').addEventListener('submit', async function(e) {{
                    e.preventDefault();
                    
                    const formData = new FormData();
                    const fileInput = document.getElementById('pdfFile');
                    const titleInput = document.getElementById('title');
                    const categoryInput = document.getElementById('category');
                    const statusDiv = document.getElementById('uploadStatus');
                    
                    if (!fileInput.files[0]) {{
                        statusDiv.innerHTML = '<div style="color: red;">Please select a PDF file</div>';
                        return;
                    }}
                    
                    formData.append('file', fileInput.files[0]);
                    if (titleInput.value) formData.append('title', titleInput.value);
                    if (categoryInput.value) formData.append('category', categoryInput.value);
                    
                    statusDiv.innerHTML = '<div style="color: blue;">📤 Uploading...</div>';
                    
                    try {{
                        const response = await fetch('/upload_pdf', {{
                            method: 'POST',
                            body: formData
                        }});
                        
                        const result = await response.json();
                        
                        if (response.ok) {{
                            statusDiv.innerHTML = `
                                <div style="color: green; padding: 10px; background-color: #d4edda; border-radius: 4px;">
                                    ✅ Upload successful!<br>
                                    📄 Document ID: ${{result.document_id}}<br>
                                    📊 Characters extracted: ${{result.characters.toLocaleString()}}<br>
                                    💾 Storage: ${{result.storage_type}}
                                </div>
                            `;
                            // Reset form
                            fileInput.value = '';
                            titleInput.value = '';
                            categoryInput.value = '';
                            // Refresh page after 2 seconds to update stats
                            setTimeout(() => window.location.reload(), 2000);
                        }} else {{
                            statusDiv.innerHTML = `<div style="color: red;">❌ Upload failed: ${{result.detail}}</div>`;
                        }}
                    }} catch (error) {{
                        statusDiv.innerHTML = `<div style="color: red;">❌ Upload error: ${{error.message}}</div>`;
                    }}
                }});
            </script>
            </div>
        """
        
        if not mongodb_config.is_configured():
            html_content += f"""
            <div class="setup-box">
                <h3>⚠️ MongoDB Atlas Setup Required</h3>
                <p>To enable cloud storage, set up MongoDB Atlas:</p>
                <ol>
                    <li>Go to <a href="https://cloud.mongodb.com" target="_blank">MongoDB Atlas</a></li>
                    <li>Create a free account and cluster</li>
                    <li>Get your connection string</li>
                    <li>Set environment variable: <code>MONGODB_URI=your_connection_string</code></li>
                    <li>Restart the server</li>
                </ol>
                <p><a href="/setup" target="_blank">📋 View detailed setup instructions</a></p>
            </div>
            """
        
        html_content += f"""
            <div>
                <h2>📂 Document Categories</h2>
                <ul>
        """
        
        for category, count in stats.get('categories', {}).items():
            html_content += f"<li><strong>{category}:</strong> {count} documents</li>"
        
        html_content += f"""
                </ul>
            </div>
            
            <div>
                <h2>✨ Enhanced Features</h2>
                <div class="feature">☁️ MongoDB Atlas cloud storage</div>
                <div class="feature">🔄 Automatic local backup fallback</div>
                <div class="feature">📑 Advanced PDF extraction</div>
                <div class="feature">🌐 URL content extraction</div>
                <div class="feature">🔍 Document search capabilities</div>
                <div class="feature">📊 Real-time statistics</div>
            </div>
            
            <div>
                <h2>🔧 API Endpoints</h2>
                <div class="endpoint"><a href="/docs" target="_blank" style="color: white;">📖 API Documentation</a></div>
                <div class="endpoint"><a href="/health" target="_blank" style="color: white;">❤️ Health Check</a></div>
                <div class="endpoint"><a href="/setup" target="_blank" style="color: white;">⚙️ Setup Instructions</a></div>
                <div class="endpoint"><a href="/statistics" target="_blank" style="color: white;">📊 Statistics</a></div>
                <div class="endpoint">📤 /upload_pdf - Enhanced PDF upload</div>
                <div class="endpoint">🌐 /url - URL content extraction</div>
            </div>
        </body>
        </html>
        """
        
        return JSONResponse(content=html_content, media_type="text/html")
        
    except Exception as e:
        logger.error(f"Admin interface error: {e}")
        raise HTTPException(status_code=500, detail=f"Admin interface failed: {str(e)}")

@app.get("/documents")
async def get_all_documents():
    """Get all documents with storage info"""
    try:
        documents = document_manager.get_all_documents()
        return {
            "documents": documents,
            "total": len(documents),
            "storage_type": document_manager.storage_type,
            "mongodb_configured": mongodb_config.is_configured()
        }
    except Exception as e:
        logger.error(f"Get documents error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")

@app.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Get enhanced document store statistics"""
    try:
        stats = document_manager.get_statistics()
        return StatisticsResponse(**stats)
    except Exception as e:
        logger.error(f"Statistics error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from cloud or local storage"""
    try:
        success = document_manager.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {
            "message": f"Document {doc_id} deleted successfully from {document_manager.storage_type}",
            "storage": document_manager.storage_type
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

if __name__ == "__main__":
    # Print startup information
    print("\n" + "="*60)
    print("🚀 HighPal Enhanced Server Starting...")
    print("="*60)
    if mongodb_config.is_configured():
        print("✅ MongoDB Atlas: CONFIGURED")
        print("☁️ Storage: Cloud (MongoDB Atlas)")
    else:
        print("⚠️ MongoDB Atlas: NOT CONFIGURED")
        print("📁 Storage: Local files only")
        print("\n💡 To enable MongoDB Atlas:")
        print("   Set environment variable: MONGODB_URI=your_connection_string")
        print("   Or visit /setup endpoint for detailed instructions")
    
    print("="*60)
    print("🌐 Server will be available at: http://localhost:8002")
    print("📖 API Documentation: http://localhost:8002/docs")
    print("👨‍💼 Admin Interface: http://localhost:8002/admin")
    print("="*60 + "\n")
    
    # Run the enhanced server
    uvicorn.run(
        "mongodb_server:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
