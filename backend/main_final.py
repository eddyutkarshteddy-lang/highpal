from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
import logging
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="HighPal Document Assistant", description="Document processing and Q&A system")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage for documents
stored_documents = {}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "features": {
            "document_processing": True,
            "document_storage": True,
            "basic_qa": True
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
    """Simple Q&A using text matching and basic responses"""
    try:
        question_original = question
        question = question.strip().lower()
        
        # Handle greetings
        greetings = ["hi", "hello", "hey", "greetings"]
        if question in greetings:
            return JSONResponse({
                "answer": "Hello! I'm HighPal, your document assistant. I can help you process PDFs, fetch web content, and answer questions about uploaded documents.",
                "method": "greeting_response",
                "question": question_original
            })
        
        # If text is provided directly
        if text and text.strip():
            # Simple keyword-based response
            answer = f"I found information in the provided text. Here's a summary of the content:\n\n{text[:300]}..."
            if len(text) > 300:
                answer += f"\n\n(Showing first 300 characters of {len(text)} total characters)"
            
            return JSONResponse({
                "answer": answer,
                "method": "direct_text_analysis",
                "question": question_original,
                "context_length": len(text)
            })
        
        # Search through stored documents
        elif stored_documents:
            question_words = set(question.split())
            relevant_docs = []
            
            for doc_id, doc_data in stored_documents.items():
                content_words = set(doc_data["content"].lower().split())
                # Simple word overlap scoring
                overlap = len(question_words.intersection(content_words))
                if overlap > 0:
                    relevant_docs.append((doc_data, overlap))
            
            if relevant_docs:
                # Sort by relevance and take top document
                relevant_docs.sort(key=lambda x: x[1], reverse=True)
                top_doc = relevant_docs[0][0]
                
                # Find relevant excerpt
                content = top_doc["content"]
                # Simple approach: find sentences containing question words
                sentences = content.split('.')
                relevant_sentences = []
                
                for sentence in sentences[:10]:  # Check first 10 sentences
                    sentence_words = set(sentence.lower().split())
                    if question_words.intersection(sentence_words):
                        relevant_sentences.append(sentence.strip())
                
                if relevant_sentences:
                    answer = f"Based on the document '{top_doc.get('filename', top_doc.get('url', 'Unknown'))}', here's what I found:\n\n"
                    answer += ". ".join(relevant_sentences[:3]) + "."
                else:
                    answer = f"I found the document '{top_doc.get('filename', top_doc.get('url', 'Unknown'))}' but couldn't find specific information about your question. Here's a preview:\n\n{content[:200]}..."
                
                return JSONResponse({
                    "answer": answer,
                    "method": "document_search",
                    "question": question_original,
                    "found_docs": len(relevant_docs),
                    "source": top_doc.get("filename", top_doc.get("url", "Unknown"))
                })
            else:
                return JSONResponse({
                    "answer": f"I have {len(stored_documents)} document(s) stored, but I couldn't find information related to your question. Try uploading more relevant documents or asking about the content you've already uploaded.",
                    "method": "no_relevant_docs",
                    "question": question_original,
                    "stored_docs": len(stored_documents)
                })
        
        # No documents and no text provided
        else:
            return JSONResponse({
                "answer": "Hi! I can help you with document analysis. Please:\n1. Upload a PDF document, or\n2. Fetch content from a URL, or\n3. Provide text with your question\n\nThen ask me questions about the content!",
                "method": "no_content_available",
                "question": question_original,
                "suggestions": [
                    "Upload a PDF document",
                    "Fetch content from a URL",
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
