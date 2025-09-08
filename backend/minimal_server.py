"""
Minimal FastAPI server for HighPal - Immediate functionality
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import json
from datetime import datetime

app = FastAPI(title="HighPal Minimal Server")

# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store uploaded files in memory (for demo)
uploaded_docs = []

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/documents")
async def get_documents():
    return {
        "documents": uploaded_docs,
        "count": len(uploaded_docs)
    }

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read file content
        content = await file.read()
        
        # Create document entry
        doc_entry = {
            "id": len(uploaded_docs) + 1,
            "filename": file.filename,
            "file_size": len(content),
            "file_type": file.content_type,
            "upload_time": datetime.now().isoformat(),
            "content_preview": str(content[:200]) if content else "No content"
        }
        
        uploaded_docs.append(doc_entry)
        
        return {
            "success": True,
            "message": f"File {file.filename} uploaded successfully",
            "file_id": doc_entry["id"],
            "doc_id": doc_entry["id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/ask_question")
@app.post("/ask_question")
async def ask_question(question: str = None):
    if not question:
        return {"error": "No question provided"}
    
    # Simple demo responses
    demo_responses = {
        "hello": "Hello! I'm Pal, your AI learning assistant. How can I help you today?",
        "help": "I can help you with your uploaded documents. Try uploading a PDF and asking questions about it!",
        "test": "The system is working perfectly! Upload some documents and I'll help you understand them.",
        "default": f"That's an interesting question about '{question}'. I'd need some uploaded documents to give you specific answers, but I'm here to help with your learning!"
    }
    
    # Simple keyword matching
    q_lower = question.lower()
    if any(word in q_lower for word in ["hello", "hi", "hey"]):
        response = demo_responses["hello"]
    elif any(word in q_lower for word in ["help", "what can you do"]):
        response = demo_responses["help"]
    elif "test" in q_lower:
        response = demo_responses["test"]
    else:
        response = demo_responses["default"]
    
    return {
        "answer": response,
        "question": question,
        "timestamp": datetime.now().isoformat(),
        "source": "Pal AI Assistant"
    }

@app.get("/search")
async def search_documents(q: str = "", limit: int = 5):
    if not q:
        return {"results": [], "query": q}
    
    # Return demo search results
    demo_results = [
        {
            "content": f"This is a demo result for your search: '{q}'",
            "score": 0.85,
            "source": "Demo Document",
            "metadata": {"page": 1, "type": "demo"}
        }
    ]
    
    return {
        "results": demo_results,
        "query": q,
        "total_results": len(demo_results)
    }

if __name__ == "__main__":
    print("🚀 Starting HighPal Minimal Server on port 8003...")
    print("📋 Available endpoints:")
    print("   GET  /health - Health check")
    print("   GET  /documents - List uploaded documents") 
    print("   POST /upload - Upload files")
    print("   GET  /ask_question - Ask questions")
    print("   GET  /search - Search documents")
    print("🌐 Frontend should connect to: http://localhost:8003")
    
    uvicorn.run(
        "minimal_server:app",
        host="0.0.0.0",
        port=8003,
        reload=False
    )
