from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
import logging
from typing import List, Optional
import hashlib
import os
from dotenv import load_dotenv
import openai
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI
openai_client = None
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key and openai_api_key != "your-openai-api-key-here":
    try:
        openai_client = openai.OpenAI(api_key=openai_api_key)
        logger.info("✅ OpenAI client initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize OpenAI client: {e}")
else:
    logger.info("ℹ️ OpenAI API key not set - general Q&A will be limited")

app = FastAPI(title="HighPal AI Document Assistant", description="AI-powered document processing and Q&A system")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage for documents (replace with database in production)
stored_documents = {}

# Utility functions for OpenAI
def is_general_question(question: str) -> bool:
    """Determine if a question is general (not document-specific)"""
    general_patterns = [
        r'\b(hi|hello|hey|greetings)\b',
        r'\b(what is|define|explain)\b',
        r'\b(how to|how do)\b',
        r'\b(tell me about)\b',
        r'\b(help|assistance)\b'
    ]
    
    # Simple heuristic: if question is short and matches patterns, it's likely general
    question_lower = question.lower().strip()
    
    if len(question_lower) < 10:  # Very short questions are likely greetings
        return True
    
    for pattern in general_patterns:
        if re.search(pattern, question_lower):
            return True
    
    return False

async def get_openai_response(question: str, context: str = None) -> str:
    """Get response from OpenAI API"""
    if not openai_client:
        return "I'd love to help, but OpenAI is not configured. Please set your OPENAI_API_KEY."
    
    try:
        if context:
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant. Use the provided context to answer questions accurately and concisely."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {question}"}
            ]
        else:
            messages = [
                {"role": "system", "content": "You are a helpful AI assistant. Answer questions accurately and conversationally."},
                {"role": "user", "content": question}
            ]
        
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return f"Sorry, I encountered an error while processing your question: {str(e)}"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    openai_status = "configured" if openai_client else "not_configured"
    
    return JSONResponse({
        "status": "healthy",
        "openai": openai_status,
        "features": {
            "document_processing": True,
            "general_qa": openai_client is not None,
            "document_storage": True
        }
    })

@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload PDF and extract text"""
    try:
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        
        # Create document ID from file content hash
        doc_id = hashlib.md5(content).hexdigest()
        
        # Store document in memory
        stored_documents[doc_id] = {
            "filename": file.filename,
            "content": text,
            "source": "pdf_upload"
        }
        
        logger.info(f"Stored document: {file.filename}")
        
        return JSONResponse({
            "text": text,
            "doc_id": doc_id,
            "filename": file.filename,
            "stored": True,
            "character_count": len(text)
        })
    
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/fetch_url/")
async def fetch_url(url: str = Form(...)):
    """Fetch content from URL"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(strip=True, separator=' ')
        
        # Create document ID from URL
        doc_id = hashlib.md5(url.encode()).hexdigest()
        
        # Store document in memory
        stored_documents[doc_id] = {
            "url": url,
            "content": text,
            "source": "web_scraping",
            "title": soup.title.string if soup.title else "No title"
        }
        
        logger.info(f"Stored web content from: {url}")
        
        return JSONResponse({
            "text": text,
            "doc_id": doc_id,
            "url": url,
            "stored": True,
            "character_count": len(text)
        })
    
    except requests.RequestException as e:
        logger.error(f"Error fetching URL {url}: {e}")
        raise HTTPException(status_code=400, detail=f"Error fetching URL: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing URL content: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing content: {str(e)}")

@app.post("/ask_question/")
async def ask_question(question: str = Form(...), text: str = Form(None)):
    """Enhanced Q&A using OpenAI with optional context"""
    try:
        question = question.strip()
        
        # Priority 1: If text is provided, use OpenAI with that context
        if text and text.strip():
            if openai_client:
                answer = await get_openai_response(question, context=text[:2000])  # Limit context size
                return JSONResponse({
                    "answer": answer,
                    "method": "openai_with_context",
                    "question": question,
                    "context_length": len(text)
                })
            else:
                answer = f"Based on the provided text, I can see content about: {text[:200]}...\n\nRegarding '{question}': Please configure OpenAI for better analysis."
                return JSONResponse({
                    "answer": answer,
                    "method": "direct_text_fallback",
                    "question": question
                })
        
        # Priority 2: Check if we have stored documents and if this seems document-specific
        elif stored_documents and not is_general_question(question):
            # Simple search through stored documents
            relevant_docs = []
            question_words = set(question.lower().split())
            
            for doc_id, doc_data in stored_documents.items():
                content_words = set(doc_data["content"].lower().split())
                # Simple word overlap scoring
                overlap = len(question_words.intersection(content_words))
                if overlap > 0:
                    relevant_docs.append((doc_data, overlap))
            
            if relevant_docs:
                # Sort by relevance and take top documents
                relevant_docs.sort(key=lambda x: x[1], reverse=True)
                top_docs = relevant_docs[:3]
                
                # Combine context from relevant documents
                context = "\n\n".join([doc[0]["content"][:500] for doc in top_docs])
                
                if openai_client:
                    answer = await get_openai_response(question, context=context)
                    method = "document_search_with_openai"
                else:
                    answer = f"Based on the stored documents:\n\n{context[:300]}..."
                    method = "document_search_only"
                
                return JSONResponse({
                    "answer": answer,
                    "method": method,
                    "question": question,
                    "found_docs": len(top_docs),
                    "sources": [doc[0].get("filename", doc[0].get("url", "Unknown")) for doc in top_docs]
                })
            else:
                # No relevant documents found, fall back to general OpenAI
                if openai_client:
                    answer = await get_openai_response(question)
                    return JSONResponse({
                        "answer": answer,
                        "method": "openai_general_fallback",
                        "question": question,
                        "note": "No relevant documents found, using general knowledge"
                    })
                else:
                    return JSONResponse({
                        "answer": "I couldn't find relevant information in the stored documents, and OpenAI is not configured for general questions.",
                        "method": "no_results",
                        "question": question,
                        "found_docs": 0
                    })
        
        # Priority 3: General questions - use OpenAI
        elif openai_client:
            answer = await get_openai_response(question)
            return JSONResponse({
                "answer": answer,
                "method": "openai_general",
                "question": question
            })
        
        # Priority 4: Fallback when nothing is available
        else:
            return JSONResponse({
                "answer": "Hello! I'd love to help you, but I need either:\n1. OpenAI API key for general questions\n2. Uploaded documents for document-specific questions\n3. Text provided with your question\n\nPlease configure OpenAI or upload some documents first!",
                "method": "no_capabilities",
                "question": question,
                "suggestions": [
                    "Set OPENAI_API_KEY environment variable",
                    "Upload PDF documents",
                    "Provide text with your question"
                ]
            })
    
    except Exception as e:
        logger.error(f"Error in ask_question: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/documents/count")
async def get_document_count():
    """Get the count of stored documents"""
    return JSONResponse({"document_count": len(stored_documents)})

@app.delete("/documents/clear")
async def clear_documents():
    """Clear all stored documents"""
    global stored_documents
    stored_documents = {}
    return JSONResponse({"message": "All documents cleared successfully"})

@app.get("/documents/list")
async def list_documents():
    """List all stored documents"""
    docs = []
    for doc_id, doc_data in stored_documents.items():
        docs.append({
            "doc_id": doc_id,
            "filename": doc_data.get("filename"),
            "url": doc_data.get("url"),
            "source": doc_data.get("source"),
            "content_length": len(doc_data.get("content", "")),
            "title": doc_data.get("title")
        })
    return JSONResponse({"documents": docs})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
