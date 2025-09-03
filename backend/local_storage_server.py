#!/usr/bin/env python3
"""
HighPal Local Storage Server
=========================
A FastAPI server that stores documents locally while MongoDB Atlas credentials are being fixed.
This is a working solution that saves documents to local files immediately.

Features:
- PDF upload and processing
- Local file storage with timestamps
- Admin interface with upload forms
- Statistics tracking
- 6-method PDF extraction with quality scoring

Run: python local_storage_server.py
Admin Interface: http://localhost:8004/admin
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from pdf_extractor import extract_pdf_text_advanced

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LocalStorageManager:
    """Manages local file storage for documents"""
    
    def __init__(self, storage_dir: str = "local_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.docs_dir = self.storage_dir / "documents"
        self.metadata_dir = self.storage_dir / "metadata"
        self.docs_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)
        
        # Statistics file
        self.stats_file = self.storage_dir / "statistics.json"
        
        logger.info(f"📁 Local storage initialized at: {self.storage_dir.absolute()}")
    
    def save_document(self, filename: str, content: bytes, metadata: Dict[str, Any]) -> str:
        """Save document and metadata locally"""
        try:
            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = Path(filename).stem
            extension = Path(filename).suffix
            unique_filename = f"{base_name}_{timestamp}{extension}"
            
            # Save file
            file_path = self.docs_dir / unique_filename
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Save metadata
            metadata_filename = f"{base_name}_{timestamp}_metadata.json"
            metadata_path = self.metadata_dir / metadata_filename
            
            full_metadata = {
                "filename": filename,
                "stored_filename": unique_filename,
                "upload_timestamp": datetime.now().isoformat(),
                "file_size": len(content),
                "file_path": str(file_path),
                **metadata
            }
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(full_metadata, f, indent=2, ensure_ascii=False)
            
            # Update statistics
            self._update_statistics(full_metadata)
            
            logger.info(f"✅ Document saved: {unique_filename} ({len(content)} bytes)")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"❌ Error saving document: {str(e)}")
            raise
    
    def _update_statistics(self, metadata: Dict[str, Any]) -> None:
        """Update storage statistics"""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    stats = json.load(f)
            else:
                stats = {
                    "total_documents": 0,
                    "total_size_bytes": 0,
                    "documents_by_type": {},
                    "last_updated": None
                }
            
            # Update statistics
            stats["total_documents"] += 1
            stats["total_size_bytes"] += metadata.get("file_size", 0)
            
            # Track by file type
            file_type = Path(metadata["filename"]).suffix.lower()
            if file_type not in stats["documents_by_type"]:
                stats["documents_by_type"][file_type] = 0
            stats["documents_by_type"][file_type] += 1
            
            stats["last_updated"] = datetime.now().isoformat()
            
            # Save updated statistics
            with open(self.stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Error updating statistics: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics"""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
            else:
                return {
                    "total_documents": 0,
                    "total_size_bytes": 0,
                    "documents_by_type": {},
                    "last_updated": None
                }
        except Exception as e:
            logger.error(f"❌ Error getting statistics: {str(e)}")
            return {"error": str(e)}

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 HighPal Local Storage Server Starting...")
    logger.info(f"📁 Storage Directory: {storage_manager.storage_dir.absolute()}")
    logger.info("🌐 Admin Interface: http://localhost:8004/admin")
    yield
    # Shutdown (if needed)
    logger.info("👋 HighPal Local Storage Server Shutting Down...")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="HighPal Local Storage Server",
    description="Document storage server with local file storage",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize storage manager
storage_manager = LocalStorageManager()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HighPal Local Storage Server",
        "version": "1.0.0",
        "storage": "Local Files",
        "admin": "http://localhost:8004/admin",
        "endpoints": {
            "upload": "/upload",
            "statistics": "/statistics",
            "admin": "/admin"
        }
    }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    try:
        logger.info(f"📄 Processing upload: {file.filename}")
        
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read file content
        content = await file.read()
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Extract text from PDF
        logger.info("🔍 Extracting text from PDF...")
        extraction_result = extract_pdf_text_advanced(content)
        
        if not extraction_result or not extraction_result.get('best_text'):
            raise HTTPException(status_code=400, detail="Failed to extract text from PDF")
        
        # Prepare metadata
        metadata = {
            "extraction_result": extraction_result,
            "content_type": file.content_type,
            "processing_timestamp": datetime.now().isoformat()
        }
        
        # Save to local storage
        file_path = storage_manager.save_document(file.filename, content, metadata)
        
        # Return success response
        response = {
            "success": True,
            "message": f"Document '{file.filename}' processed successfully",
            "file_path": file_path,
            "extraction_info": extraction_result.get('extraction_info', {}),
            "text_length": len(extraction_result.get('best_text', '')),
            "storage": "Local Files"
        }
        
        logger.info(f"✅ Upload completed: {file.filename}")
        return JSONResponse(content=response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

@app.get("/statistics")
async def get_statistics():
    """Get storage statistics"""
    try:
        stats = storage_manager.get_statistics()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"❌ Statistics error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin", response_class=HTMLResponse)
async def admin_interface():
    """Admin interface with upload forms"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HighPal Local Storage Admin</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                color: #333;
            }
            .container {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            h1 {
                color: #4a90e2;
                text-align: center;
                margin-bottom: 10px;
            }
            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 30px;
                font-style: italic;
            }
            .upload-section {
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
                border: 2px dashed #4a90e2;
            }
            .form-group {
                margin: 15px 0;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #333;
            }
            input[type="file"] {
                width: 100%;
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                background: white;
            }
            button {
                background: #4a90e2;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                transition: background 0.3s;
            }
            button:hover {
                background: #357abd;
            }
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }
            .status {
                margin: 15px 0;
                padding: 10px;
                border-radius: 5px;
                font-weight: 600;
                text-align: center;
            }
            .success {
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }
            .error {
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }
            .info {
                background: #d1ecf1;
                color: #0c5460;
                border: 1px solid #bee5eb;
            }
            .stats {
                background: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                margin: 20px 0;
                border-left: 4px solid #4a90e2;
            }
            .progress {
                width: 100%;
                height: 20px;
                background: #e9ecef;
                border-radius: 10px;
                overflow: hidden;
                margin: 10px 0;
                display: none;
            }
            .progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #4a90e2, #357abd);
                width: 0%;
                transition: width 0.3s;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 12px;
                font-weight: 600;
            }
            .storage-info {
                text-align: center;
                background: #e8f4f8;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                border: 1px solid #b8daff;
            }
            .icon {
                font-size: 24px;
                margin-right: 10px;
                vertical-align: middle;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1><span class="icon">📁</span>HighPal Local Storage Admin</h1>
            <div class="subtitle">Local File Storage - Working immediately!</div>
            
            <div class="storage-info">
                <strong>💾 Storage Type:</strong> Local Files<br>
                <strong>📍 Location:</strong> backend/local_storage/<br>
                <strong>⚡ Status:</strong> Ready for uploads!
            </div>
            
            <div class="upload-section">
                <h2>📄 Upload PDF Document</h2>
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="form-group">
                        <label for="file">Select PDF File:</label>
                        <input type="file" id="file" name="file" accept=".pdf" required>
                    </div>
                    <button type="submit" id="uploadBtn">
                        <span class="icon">⬆️</span>Upload Document
                    </button>
                </form>
                
                <div class="progress" id="progressContainer">
                    <div class="progress-bar" id="progressBar">0%</div>
                </div>
                
                <div id="status"></div>
            </div>
            
            <div class="stats" id="stats">
                <h3>📊 Storage Statistics</h3>
                <div id="statsContent">Loading...</div>
            </div>
        </div>

        <script>
            // Load statistics on page load
            document.addEventListener('DOMContentLoaded', loadStats);
            
            // Handle form submission
            document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const formData = new FormData();
                const fileInput = document.getElementById('file');
                const file = fileInput.files[0];
                
                if (!file) {
                    showStatus('Please select a file', 'error');
                    return;
                }
                
                if (!file.name.toLowerCase().endsWith('.pdf')) {
                    showStatus('Please select a PDF file', 'error');
                    return;
                }
                
                formData.append('file', file);
                
                const uploadBtn = document.getElementById('uploadBtn');
                const progressContainer = document.getElementById('progressContainer');
                const progressBar = document.getElementById('progressBar');
                
                uploadBtn.disabled = true;
                uploadBtn.textContent = 'Uploading...';
                progressContainer.style.display = 'block';
                
                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                        showStatus(
                            `✅ Success: ${result.message}<br>
                             📊 Quality Score: ${result.extraction_quality}<br>
                             📝 Text Length: ${result.text_length} characters<br>
                             💾 Saved to: ${result.file_path}`, 
                            'success'
                        );
                        fileInput.value = '';
                        loadStats(); // Refresh statistics
                    } else {
                        showStatus(`❌ Error: ${result.detail || 'Upload failed'}`, 'error');
                    }
                } catch (error) {
                    showStatus(`❌ Network Error: ${error.message}`, 'error');
                } finally {
                    uploadBtn.disabled = false;
                    uploadBtn.innerHTML = '<span class="icon">⬆️</span>Upload Document';
                    progressContainer.style.display = 'none';
                }
            });
            
            function showStatus(message, type) {
                const statusDiv = document.getElementById('status');
                statusDiv.innerHTML = message;
                statusDiv.className = `status ${type}`;
                
                if (type === 'success') {
                    setTimeout(() => {
                        statusDiv.innerHTML = '';
                        statusDiv.className = '';
                    }, 5000);
                }
            }
            
            async function loadStats() {
                try {
                    const response = await fetch('/statistics');
                    const stats = await response.json();
                    
                    let content = `
                        <strong>📄 Total Documents:</strong> ${stats.total_documents || 0}<br>
                        <strong>💾 Total Size:</strong> ${formatBytes(stats.total_size_bytes || 0)}<br>
                    `;
                    
                    if (stats.documents_by_type && Object.keys(stats.documents_by_type).length > 0) {
                        content += '<strong>📊 By Type:</strong><br>';
                        for (const [type, count] of Object.entries(stats.documents_by_type)) {
                            content += `&nbsp;&nbsp;&nbsp;&nbsp;${type}: ${count}<br>`;
                        }
                    }
                    
                    if (stats.last_updated) {
                        const lastUpdated = new Date(stats.last_updated).toLocaleString();
                        content += `<strong>🕒 Last Updated:</strong> ${lastUpdated}`;
                    }
                    
                    document.getElementById('statsContent').innerHTML = content;
                } catch (error) {
                    document.getElementById('statsContent').innerHTML = `❌ Error loading statistics: ${error.message}`;
                }
            }
            
            function formatBytes(bytes) {
                if (bytes === 0) return '0 Bytes';
                const k = 1024;
                const sizes = ['Bytes', 'KB', 'MB', 'GB'];
                const i = Math.floor(Math.log(bytes) / Math.log(k));
                return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    print("🚀 Starting HighPal Local Storage Server...")
    print("📁 Storage: Local Files")
    print("🌐 Admin Interface: http://localhost:8004/admin")
    print("📡 API: http://localhost:8004")
    print("\n" + "="*50)
    
    uvicorn.run(
        "local_storage_server:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
        log_level="info"
    )
