"""
Simple MongoDB Atlas Server - Direct Cloud Storage
No Haystack - Pure MongoDB Atlas integration
"""
import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn

from simple_mongodb_client import SimpleMongoClient
from pdf_extractor import extract_pdf_text_advanced

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="HighPal Direct MongoDB Atlas API",
    description="Simple document storage directly to MongoDB Atlas cloud",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize MongoDB client
mongo_client = SimpleMongoClient()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HighPal Direct MongoDB Atlas Server",
        "storage": "MongoDB Atlas (Direct)",
        "endpoints": {
            "docs": "/docs",
            "admin": "/admin",
            "upload": "/upload_pdf",
            "documents": "/documents",
            "statistics": "/statistics"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        stats = mongo_client.get_statistics()
        return {
            "status": "healthy",
            "storage": "mongodb_atlas_direct",
            "connection": "connected" if "error" not in stats else "failed",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/upload_pdf")
async def upload_pdf_direct(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    category: str = Form("general")
):
    """Upload PDF directly to MongoDB Atlas"""
    try:
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file content
        pdf_content = await file.read()
        if not pdf_content:
            raise HTTPException(status_code=400, detail="Empty file")
        
        logger.info(f"📄 Processing PDF: {file.filename} ({len(pdf_content)} bytes)")
        
        # Extract text using advanced PDF extractor
        extraction_result = extract_pdf_text_advanced(pdf_content)
        
        if not extraction_result['content'].strip():
            raise HTTPException(status_code=400, detail="No text content extracted from PDF")
        
        # Create metadata
        metadata = {
            "filename": file.filename,
            "title": title or file.filename,
            "category": category,
            "size": len(pdf_content),
            "source": "pdf_upload_direct",
            "extraction_method": extraction_result.get('method', 'unknown'),
            "extraction_score": extraction_result.get('score', 0),
            "pages": extraction_result.get('pages', 0),
            "upload_timestamp": datetime.now().isoformat()
        }
        
        # Save directly to MongoDB Atlas
        doc_id = mongo_client.save_document(extraction_result['content'], metadata)
        
        logger.info(f"✅ Document saved to MongoDB Atlas: {doc_id}")
        
        return {
            "document_id": doc_id,
            "filename": file.filename,
            "title": metadata["title"],
            "characters": len(extraction_result['content']),
            "extraction_method": extraction_result.get('method'),
            "extraction_score": extraction_result.get('score'),
            "storage_type": "mongodb_atlas_direct",
            "message": "PDF uploaded successfully to MongoDB Atlas!"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/documents")
async def get_all_documents():
    """Get all documents from MongoDB Atlas"""
    try:
        documents = mongo_client.get_all_documents()
        return {
            "documents": documents,
            "total": len(documents),
            "storage_type": "mongodb_atlas_direct",
            "message": f"Found {len(documents)} documents in MongoDB Atlas"
        }
    except Exception as e:
        logger.error(f"❌ Get documents error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")

@app.get("/statistics")
async def get_statistics():
    """Get MongoDB Atlas statistics"""
    try:
        stats = mongo_client.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"❌ Statistics error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete document from MongoDB Atlas"""
    try:
        success = mongo_client.delete_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        return {
            "message": f"Document {doc_id} deleted from MongoDB Atlas",
            "storage": "mongodb_atlas_direct"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Delete error: {e}")
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@app.get("/admin")
async def admin_interface():
    """Simple admin interface"""
    try:
        stats = mongo_client.get_statistics()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>HighPal - Direct MongoDB Atlas Storage</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .header {{ background: linear-gradient(135deg, #28a745, #20c997); color: white; padding: 25px; border-radius: 8px; }}
                .stats {{ margin: 20px 0; display: flex; flex-wrap: wrap; }}
                .stat-item {{ background: linear-gradient(135deg, #007bff, #0056b3); color: white; margin: 10px; padding: 15px; border-radius: 8px; min-width: 200px; }}
                .upload-form {{ background-color: #ffffff; padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px dashed #28a745; }}
                .upload-form input, .upload-form button {{ margin: 10px 0; padding: 10px; border: 1px solid #ccc; border-radius: 4px; }}
                .upload-form button {{ background-color: #28a745; color: white; border: none; cursor: pointer; font-weight: bold; }}
                .status {{ margin-top: 15px; padding: 10px; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>☁️ HighPal - Direct MongoDB Atlas Storage</h1>
                <p>Documents saved directly to MongoDB Atlas cloud (no Haystack)</p>
                <p><strong>Status: {"✅ Connected" if "error" not in stats else "❌ Connection Failed"}</strong></p>
            </div>
            
            <div class="stats">
                <div class="stat-item">
                    <h4>📊 Total Documents</h4>
                    <p>{stats.get('total_documents', 0)}</p>
                </div>
                <div class="stat-item">
                    <h4>📝 Total Characters</h4>
                    <p>{stats.get('total_characters', 0):,}</p>
                </div>
                <div class="stat-item">
                    <h4>📏 Average Length</h4>
                    <p>{stats.get('average_length', 0)} chars</p>
                </div>
                <div class="stat-item">
                    <h4>💾 Storage Type</h4>
                    <p>MongoDB Atlas Direct</p>
                </div>
            </div>
            
            <div class="upload-form">
                <h3>📤 Upload PDF to MongoDB Atlas</h3>
                <form id="uploadForm" enctype="multipart/form-data">
                    <div>
                        <label>Select PDF File:</label><br>
                        <input type="file" id="pdfFile" name="file" accept=".pdf" required style="width: 300px;">
                    </div>
                    <div>
                        <label>Title (optional):</label><br>
                        <input type="text" id="title" name="title" placeholder="Document title" style="width: 300px;">
                    </div>
                    <div>
                        <label>Category:</label><br>
                        <input type="text" id="category" name="category" value="general" style="width: 300px;">
                    </div>
                    <button type="submit">🚀 Upload to MongoDB Atlas</button>
                </form>
                <div id="uploadStatus"></div>
            </div>
            
            <div style="margin: 20px 0;">
                <h3>🔗 Quick Links</h3>
                <p><a href="/docs" target="_blank">📖 API Documentation</a></p>
                <p><a href="/documents" target="_blank">📋 View All Documents</a></p>
                <p><a href="/statistics" target="_blank">📊 Database Statistics</a></p>
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
                    formData.append('category', categoryInput.value);
                    
                    statusDiv.innerHTML = '<div style="color: blue;">☁️ Uploading to MongoDB Atlas...</div>';
                    
                    try {{
                        const response = await fetch('/upload_pdf', {{
                            method: 'POST',
                            body: formData
                        }});
                        
                        const result = await response.json();
                        
                        if (response.ok) {{
                            statusDiv.innerHTML = `
                                <div style="color: green; background-color: #d4edda; padding: 10px; border-radius: 4px;">
                                    ✅ Successfully uploaded to MongoDB Atlas!<br>
                                    🆔 Document ID: ${{result.document_id}}<br>
                                    📊 Characters: ${{result.characters.toLocaleString()}}<br>
                                    🔧 Extraction Method: ${{result.extraction_method}}<br>
                                    ☁️ Storage: MongoDB Atlas Direct
                                </div>
                            `;
                            // Reset form
                            fileInput.value = '';
                            titleInput.value = '';
                            // Refresh page after 3 seconds
                            setTimeout(() => window.location.reload(), 3000);
                        }} else {{
                            statusDiv.innerHTML = `<div style="color: red;">❌ Upload failed: ${{result.detail}}</div>`;
                        }}
                    }} catch (error) {{
                        statusDiv.innerHTML = `<div style="color: red;">❌ Upload error: ${{error.message}}</div>`;
                    }}
                }});
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"❌ Admin interface error: {e}")
        raise HTTPException(status_code=500, detail=f"Admin interface failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting HighPal Direct MongoDB Atlas Server...")
    print("=" * 60)
    print("☁️  Storage: MongoDB Atlas (Direct - No Haystack)")
    print("🌐 Server: http://localhost:8003")
    print("📖 API Docs: http://localhost:8003/docs")
    print("👨‍💼 Admin: http://localhost:8003/admin")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
