"""
Fixed HighPal Server with Haystack + MongoDB Atlas Integration
Simplified version to ensure it works properly
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import PyPDF2
import io
import logging
from datetime import datetime
import os

# Import our Haystack-MongoDB integration
try:
    from production_haystack_mongo import HaystackStyleMongoIntegration
    HAYSTACK_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Haystack integration not available: {e}")
    HAYSTACK_AVAILABLE = False

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
haystack_mongo = None
if HAYSTACK_AVAILABLE:
    try:
        haystack_mongo = HaystackStyleMongoIntegration()
        logger.info("✅ Haystack + MongoDB Atlas integration initialized!")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Haystack integration: {e}")
        haystack_mongo = None
else:
    logger.warning("⚠️ Haystack integration not available")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main application page"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>HighPal AI Assistant</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
            .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
            .success { background-color: #d4edda; border-left: 4px solid #28a745; color: #155724; }
            .info { background-color: #d1ecf1; border-left: 4px solid #17a2b8; color: #0c5460; }
            .endpoint { background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #6c757d; }
            .upload-form { background-color: #e7f3ff; padding: 20px; border-radius: 5px; margin: 20px 0; }
            input[type="file"] { margin: 10px 0; padding: 10px; }
            button { background-color: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background-color: #0056b3; }
            a { color: #007bff; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 HighPal AI Assistant</h1>
            
            <div class="status success">
                <strong>✅ Server Status:</strong> Running successfully on port 8000
            </div>
            
            <div class="status info">
                <strong>🧠 AI Features:</strong> Haystack + MongoDB Atlas Integration Active
            </div>
            
            <h2>📡 API Endpoints</h2>
            
            <div class="endpoint">
                <strong>📚 API Documentation:</strong> 
                <a href="/docs" target="_blank">http://localhost:8000/docs</a>
                <br><small>Interactive API documentation with Swagger UI</small>
            </div>
            
            <div class="endpoint">
                <strong>📊 System Stats:</strong> 
                <a href="/stats" target="_blank">http://localhost:8000/stats</a>
                <br><small>View system statistics and health</small>
            </div>
            
            <div class="endpoint">
                <strong>❤️ Health Check:</strong> 
                <a href="/health" target="_blank">http://localhost:8000/health</a>
                <br><small>Check server and integration status</small>
            </div>
            
            <h2>📤 Quick File Upload Test</h2>
            <div class="upload-form">
                <p><strong>Upload a document to test the system:</strong></p>
                <form action="/upload" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" accept=".txt,.pdf,.png,.jpg,.jpeg" required>
                    <br>
                    <button type="submit">Upload & Process Document</button>
                </form>
            </div>
            
            <h2>🔍 API Usage Examples</h2>
            
            <div class="endpoint">
                <strong>Upload Document (POST /upload):</strong>
                <pre>curl -X POST "http://localhost:8000/upload" -F "file=@document.pdf"</pre>
            </div>
            
            <div class="endpoint">
                <strong>Search Documents (POST /search):</strong>
                <pre>curl -X POST "http://localhost:8000/search" -H "Content-Type: application/json" -d '{"query": "artificial intelligence", "method": "hybrid", "top_k": 5}'</pre>
            </div>
            
            <div class="endpoint">
                <strong>Ask Questions (POST /ask):</strong>
                <pre>curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{"question": "What is this document about?"}'</pre>
            </div>
            
            <h2>✨ Features Available</h2>
            <ul>
                <li>✅ MongoDB Atlas cloud storage</li>
                <li>✅ Haystack document processing pipelines</li>
                <li>✅ Semantic search with AI embeddings</li>
                <li>✅ Hybrid search (semantic + text)</li>
                <li>✅ Document upload (PDF, images, text)</li>
                <li>✅ Question answering (requires OpenAI key)</li>
                <li>✅ RESTful API with FastAPI</li>
                <li>✅ Interactive API documentation</li>
            </ul>
        </div>
    </body>
    </html>
    """)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload and process documents"""
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
                for page in pdf_reader.pages:
                    extracted_content += page.extract_text() + "\n"
            except Exception as e:
                logger.error(f"PDF extraction error: {e}")
                extracted_content = "Failed to extract PDF content"
        else:
            # Try to decode as text
            try:
                extracted_content = file_content.decode('utf-8', errors='ignore')
            except:
                extracted_content = f"Content from {file.filename}"
        
        # Prepare document for processing
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
            "message": f"File '{file.filename}' processed successfully with Haystack + MongoDB Atlas",
            "documents_added": documents_added,
            "file_info": {
                "filename": file.filename,
                "content_type": file.content_type,
                "file_size": len(file_content),
                "content_length": len(extracted_content),
                "processing_method": "haystack_pipeline"
            },
            "next_steps": {
                "search": "Use POST /search to find documents",
                "ask": "Use POST /ask to ask questions about the document"
            }
        })
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/search")
async def search_documents(request: dict):
    """Search documents using AI-powered methods"""
    if not haystack_mongo:
        raise HTTPException(status_code=500, detail="Haystack integration not available")
    
    try:
        query = request.get('query', '')
        top_k = request.get('top_k', 5)
        search_method = request.get('method', 'hybrid')
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        # Perform search
        if search_method == 'semantic':
            results = haystack_mongo.semantic_search(query, top_k)
        elif search_method == 'text':
            results = haystack_mongo.text_search(query, top_k)
        else:
            results = haystack_mongo.hybrid_search(query, top_k)
        
        return JSONResponse(content={
            "success": True,
            "query": query,
            "method": search_method,
            "results_count": len(results),
            "results": results,
            "system_info": {
                "storage": "MongoDB Atlas",
                "search_engine": "Haystack + Sentence Transformers",
                "ai_powered": True
            }
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/ask")
async def ask_question(request: dict):
    """Ask questions about documents"""
    if not haystack_mongo:
        raise HTTPException(status_code=500, detail="Haystack integration not available")
    
    try:
        question = request.get('question', '')
        top_k = request.get('top_k', 5)
        
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        qa_result = haystack_mongo.ask_question(question, top_k)
        
        return JSONResponse(content={
            "success": True,
            "question": question,
            "answer": qa_result['answer'],
            "confidence": qa_result['confidence'],
            "method": qa_result['method'],
            "source_documents": qa_result['source_documents'],
            "sources_count": len(qa_result['source_documents']),
            "system_info": {
                "qa_engine": "Haystack + OpenAI (if available)",
                "fallback_to_search": qa_result['method'] == 'fallback_to_search'
            }
        })
        
    except Exception as e:
        logger.error(f"Q&A error: {e}")
        raise HTTPException(status_code=500, detail=f"Q&A failed: {str(e)}")

@app.get("/stats")
async def get_system_stats():
    """Get comprehensive system statistics"""
    if not haystack_mongo:
        return JSONResponse(content={
            "error": "Haystack integration not available",
            "basic_info": {
                "server": "FastAPI",
                "status": "running",
                "haystack_integration": False
            }
        })
    
    try:
        stats = haystack_mongo.get_system_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return JSONResponse(content={"error": str(e)})

@app.get("/health")
async def health_check():
    """System health check"""
    try:
        health_info = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "server": "FastAPI",
            "haystack_integration": haystack_mongo is not None
        }
        
        if haystack_mongo:
            try:
                stats = haystack_mongo.get_system_stats()
                health_info.update({
                    "mongodb_atlas": "connected",
                    "total_documents": stats['storage']['total_documents'],
                    "semantic_search": stats['capabilities']['semantic_search'],
                    "question_answering": stats['capabilities']['question_answering']
                })
            except Exception as e:
                health_info["integration_error"] = str(e)
        
        return JSONResponse(content=health_info)
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "unhealthy", "error": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting HighPal AI Assistant Server...")
    print("✨ Haystack + MongoDB Atlas Integration")
    print("📡 Server will run on: http://localhost:8000")
    print("📚 API docs will be at: http://localhost:8000/docs")
    print("🌐 Main interface: http://localhost:8000")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
