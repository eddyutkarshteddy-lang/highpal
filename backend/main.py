from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
import logging
import hashlib
from PIL import Image
import pytesseract
import cv2
import numpy as np
import os

# Configure Tesseract path for Windows
if os.name == 'nt':  # Windows
    # Try common installation paths
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
document_store = None
indexing_pipeline = None
retrieval_pipeline = None
stored_documents = {}  # Fallback storage

if HAYSTACK_AVAILABLE:
    try:
        # Initialize Elasticsearch Document Store
        document_store = ElasticsearchDocumentStore(
            hosts=["http://localhost:9200"],
            index="highpal_documents"
        )
        logger.info("✅ Elasticsearch document store initialized")
        
        # Initialize embedder
        embedder = SentenceTransformersDocumentEmbedder(model="all-MiniLM-L6-v2")
        text_embedder = SentenceTransformersTextEmbedder(model="all-MiniLM-L6-v2")
        
        # Create indexing pipeline
        indexing_pipeline = Pipeline()
        indexing_pipeline.add_component("embedder", embedder)
        indexing_pipeline.add_component("writer", DocumentWriter(document_store=document_store))
        indexing_pipeline.connect("embedder.documents", "writer.documents")
        
        # Create retrieval pipeline  
        retrieval_pipeline = Pipeline()
        retrieval_pipeline.add_component("retriever", ElasticsearchBM25Retriever(document_store=document_store))
        retrieval_pipeline.add_component("text_embedder", text_embedder)
        retrieval_pipeline.connect("text_embedder", "retriever")
        
        logger.info("✅ Haystack pipelines initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Haystack components: {e}")
        document_store = None
        indexing_pipeline = None
        retrieval_pipeline = None
else:
    logger.info("🔄 Running in fallback mode - Haystack components not available")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    elasticsearch_status = "connected" if document_store else "disconnected"
    haystack_status = "available" if HAYSTACK_AVAILABLE else "not_available"
    
    return JSONResponse({
        "status": "healthy",
        "elasticsearch": elasticsearch_status,
        "haystack": haystack_status,
        "features": {
            "document_indexing": indexing_pipeline is not None,
            "document_retrieval": retrieval_pipeline is not None,
            "basic_storage": True
        }
    })

@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload PDF and extract text, with Elasticsearch indexing"""
    try:
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        
        # Create document ID from file content hash
        doc_id = hashlib.md5(content).hexdigest()
        
        # Store in fallback storage
        stored_documents[doc_id] = {
            "filename": file.filename,
            "content": text,
            "source": "pdf_upload"
        }
        
        indexed = False
        
        # Index with Haystack if available
        if indexing_pipeline and text.strip():
            try:
                document = Document(
                    content=text,
                    meta={
                        "filename": file.filename,
                        "doc_id": doc_id,
                        "source": "pdf_upload"
                    }
                )
                
                indexing_pipeline.run({"embedder": {"documents": [document]}})
                indexed = True
                logger.info(f"✅ Indexed document: {file.filename}")
                
            except Exception as e:
                logger.error(f"❌ Failed to index document: {e}")
        
        logger.info(f"📁 Stored document: {file.filename}")
        
        return JSONResponse({
            "text": text,
            "doc_id": doc_id,
            "filename": file.filename,
            "indexed": indexed,
            "stored": True,
            "character_count": len(text)
        })
    
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/fetch_url/")
async def fetch_url(url: str = Form(...)):
    """Fetch content from URL and index with Elasticsearch"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(strip=True, separator=' ')
        
        # Create document ID from URL
        doc_id = hashlib.md5(url.encode()).hexdigest()
        
        # Store in fallback storage
        stored_documents[doc_id] = {
            "url": url,
            "content": text,
            "source": "web_scraping",
            "title": soup.title.string if soup.title else "No title"
        }
        
        indexed = False
        
        # Index with Haystack if available
        if indexing_pipeline and text.strip():
            try:
                document = Document(
                    content=text,
                    meta={
                        "url": url,
                        "doc_id": doc_id,
                        "source": "web_scraping",
                        "title": soup.title.string if soup.title else "No title"
                    }
                )
                
                indexing_pipeline.run({"embedder": {"documents": [document]}})
                indexed = True
                logger.info(f"✅ Indexed web content from: {url}")
                
            except Exception as e:
                logger.error(f"❌ Failed to index web content: {e}")
        
        logger.info(f"🌐 Stored web content from: {url}")
        
        return JSONResponse({
            "text": text,
            "doc_id": doc_id,
            "url": url,
            "indexed": indexed,
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
    """Enhanced Q&A using Haystack retrieval or fallback methods"""
    try:
        question_original = question
        question_lower = question.strip().lower()
        
        # Handle greetings
        greetings = ["hi", "hello", "hey", "greetings"]
        if question_lower in greetings:
            return JSONResponse({
                "answer": "Hello! I'm HighPal, your advanced document assistant powered by Haystack and Elasticsearch. I can help you process PDFs, fetch web content, and find information using semantic search.",
                "method": "greeting_response",
                "question": question_original
            })
        
        # If text is provided directly
        if text and text.strip():
            # Extract relevant information
            sentences = text.split('.')[:5]  # First 5 sentences
            summary = '. '.join(sentences) + '.'
            
            answer = f"Based on the provided text, here's what I found:\n\n{summary}"
            if len(text) > len(summary):
                answer += f"\n\n(This is a summary of {len(text)} characters of text)"
            
            return JSONResponse({
                "answer": answer,
                "method": "direct_text_analysis",
                "question": question_original,
                "context_length": len(text)
            })
        
        # Try Haystack retrieval first
        if retrieval_pipeline and document_store:
            try:
                # Use BM25 retrieval
                result = retrieval_pipeline.run({
                    "retriever": {"query": question_original, "top_k": 3}
                })
                
                documents = result.get("retriever", {}).get("documents", [])
                
                if documents:
                    # Combine content from retrieved documents
                    contexts = []
                    sources = []
                    
                    for doc in documents:
                        contexts.append(doc.content[:300])  # First 300 chars
                        source = doc.meta.get("filename", doc.meta.get("url", "Unknown"))
                        sources.append(source)
                    
                    combined_context = "\n\n---\n\n".join(contexts)
                    answer = f"Based on the indexed documents, here's what I found:\n\n{combined_context}"
                    
                    if len(combined_context) < 100:  # If very short, add more context
                        answer += f"\n\n(Found {len(documents)} relevant document(s) but content is limited)"
                    
                    return JSONResponse({
                        "answer": answer,
                        "method": "haystack_retrieval",
                        "question": question_original,
                        "retrieved_docs": len(documents),
                        "sources": sources
                    })
                
            except Exception as e:
                logger.error(f"Haystack retrieval error: {e}")
        
        # Fallback to simple search through stored documents
        if stored_documents:
            question_words = set(question_lower.split())
            relevant_docs = []
            
            for doc_id, doc_data in stored_documents.items():
                content_words = set(doc_data["content"].lower().split())
                overlap = len(question_words.intersection(content_words))
                if overlap > 0:
                    relevant_docs.append((doc_data, overlap))
            
            if relevant_docs:
                relevant_docs.sort(key=lambda x: x[1], reverse=True)
                top_doc = relevant_docs[0][0]
                
                # Extract relevant sentences
                content = top_doc["content"]
                sentences = content.split('.')
                relevant_sentences = []
                
                for sentence in sentences[:10]:
                    sentence_words = set(sentence.lower().split())
                    if question_words.intersection(sentence_words):
                        relevant_sentences.append(sentence.strip())
                
                if relevant_sentences:
                    answer = f"Based on the document '{top_doc.get('filename', top_doc.get('url', 'Unknown'))}', here's what I found:\n\n"
                    answer += ". ".join(relevant_sentences[:3]) + "."
                else:
                    answer = f"I found the document '{top_doc.get('filename', top_doc.get('url', 'Unknown'))}' but couldn't find specific information. Here's a preview:\n\n{content[:200]}..."
                
                return JSONResponse({
                    "answer": answer,
                    "method": "fallback_search",
                    "question": question_original,
                    "found_docs": len(relevant_docs),
                    "source": top_doc.get("filename", top_doc.get("url", "Unknown"))
                })
            else:
                return JSONResponse({
                    "answer": f"I have {len(stored_documents)} document(s) stored, but couldn't find information related to your question. Try uploading more relevant documents or rephrasing your question.",
                    "method": "no_relevant_docs",
                    "question": question_original,
                    "stored_docs": len(stored_documents)
                })
        
        # No content available
        return JSONResponse({
            "answer": "Hi! I'm ready to help with document analysis using Haystack and Elasticsearch. Please:\n\n1. Upload a PDF document\n2. Fetch content from a URL\n3. Provide text with your question\n\nThen ask me questions and I'll use advanced search to find answers!",
            "method": "no_content_available",
            "question": question_original,
            "features": [
                "Semantic search with Elasticsearch",
                "Document embedding and retrieval",
                "BM25 text search",
                "Fallback keyword search"
            ]
        })
    
    except Exception as e:
        logger.error(f"Error in ask_question: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/documents/count")
async def get_document_count():
    """Get the count of documents in both Elasticsearch and fallback storage"""
    elasticsearch_count = 0
    if document_store:
        try:
            elasticsearch_count = document_store.count_documents()
        except Exception as e:
            logger.error(f"Error getting Elasticsearch count: {e}")
    
    return JSONResponse({
        "elasticsearch_count": elasticsearch_count,
        "fallback_count": len(stored_documents),
        "total_documents": max(elasticsearch_count, len(stored_documents))
    })

@app.delete("/documents/clear")
async def clear_documents():
    """Clear all documents from both Elasticsearch and fallback storage"""
    global stored_documents
    
    # Clear fallback storage
    stored_documents = {}
    
    # Clear Elasticsearch
    elasticsearch_cleared = False
    if document_store:
        try:
            document_store.delete_documents()
            elasticsearch_cleared = True
            logger.info("✅ Cleared Elasticsearch documents")
        except Exception as e:
            logger.error(f"Error clearing Elasticsearch: {e}")
    
    return JSONResponse({
        "message": "Documents cleared successfully",
        "elasticsearch_cleared": elasticsearch_cleared,
        "fallback_cleared": True
    })

@app.get("/documents/list")
async def list_documents():
    """List documents from both sources"""
    docs = []
    
    # From fallback storage
    for doc_id, doc_data in stored_documents.items():
        docs.append({
            "doc_id": doc_id,
            "filename": doc_data.get("filename"),
            "url": doc_data.get("url"),
            "source": doc_data.get("source"),
            "content_length": len(doc_data.get("content", "")),
            "title": doc_data.get("title"),
            "storage": "fallback"
        })
    
    # From Elasticsearch (if available)
    if document_store:
        try:
            es_docs = document_store.filter_documents()
            for doc in es_docs:
                docs.append({
                    "doc_id": doc.meta.get("doc_id"),
                    "filename": doc.meta.get("filename"),
                    "url": doc.meta.get("url"),
                    "source": doc.meta.get("source"),
                    "content_length": len(doc.content),
                    "title": doc.meta.get("title"),
                    "storage": "elasticsearch"
                })
        except Exception as e:
            logger.error(f"Error listing Elasticsearch documents: {e}")
    
    return JSONResponse({"documents": docs})

# Admin endpoints for training data management
ADMIN_KEY = os.getenv("ADMIN_KEY", "admin123")  # Change this in production!

@app.post("/admin/upload_training_pdf/")
async def admin_upload_training_pdf(
    file: UploadFile = File(...), 
    category: str = Form(...),
    admin_key: str = Form(...)
):
    """Admin endpoint to upload PDF as training data"""
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        
        # Create document ID from file content hash
        doc_id = hashlib.md5(content).hexdigest()
        
        # Store in fallback storage with training data marker
        stored_documents[doc_id] = {
            "filename": file.filename,
            "content": text,
            "source": "training_data",
            "category": category,
            "admin_added": True
        }
        
        indexed = False
        
        # Index with Haystack if available
        if indexing_pipeline and text.strip():
            try:
                document = Document(
                    content=text,
                    meta={
                        "filename": file.filename,
                        "doc_id": doc_id,
                        "source": "training_data",
                        "category": category,
                        "type": "knowledge_base",
                        "admin_added": True
                    }
                )
                
                indexing_pipeline.run({"embedder": {"documents": [document]}})
                indexed = True
                logger.info(f"✅ Indexed training document: {file.filename} in category: {category}")
                
            except Exception as e:
                logger.error(f"❌ Failed to index training document: {e}")
        
        return JSONResponse({
            "message": f"Training document uploaded successfully",
            "filename": file.filename,
            "category": category,
            "indexed": indexed,
            "character_count": len(text),
            "doc_id": doc_id
        })
    
    except Exception as e:
        logger.error(f"Error processing training PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing training PDF: {str(e)}")

@app.post("/admin/add_training_url/")
async def admin_add_training_url(
    url: str = Form(...),
    category: str = Form(...),
    admin_key: str = Form(...)
):
    """Admin endpoint to fetch URL as training data"""
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(strip=True, separator=' ')
        
        # Create document ID from URL
        doc_id = hashlib.md5(url.encode()).hexdigest()
        
        # Store in fallback storage with training data marker
        stored_documents[doc_id] = {
            "url": url,
            "content": text,
            "source": "training_data",
            "category": category,
            "title": soup.title.string if soup.title else "No title",
            "admin_added": True
        }
        
        indexed = False
        
        # Index with Haystack if available
        if indexing_pipeline and text.strip():
            try:
                document = Document(
                    content=text,
                    meta={
                        "url": url,
                        "doc_id": doc_id,
                        "source": "training_data",
                        "category": category,
                        "type": "knowledge_base",
                        "title": soup.title.string if soup.title else "No title",
                        "admin_added": True
                    }
                )
                
                indexing_pipeline.run({"embedder": {"documents": [document]}})
                indexed = True
                logger.info(f"✅ Indexed training URL: {url} in category: {category}")
                
            except Exception as e:
                logger.error(f"❌ Failed to index training URL: {e}")
        
        return JSONResponse({
            "message": "Training URL processed successfully",
            "url": url,
            "category": category,
            "indexed": indexed,
            "character_count": len(text),
            "title": soup.title.string if soup.title else "No title",
            "doc_id": doc_id
        })
    
    except requests.RequestException as e:
        logger.error(f"Error fetching training URL {url}: {e}")
        raise HTTPException(status_code=400, detail=f"Error fetching training URL: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing training URL content: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing training content: {str(e)}")

@app.get("/admin/training_data/")
async def admin_list_training_data(admin_key: str):
    """Admin endpoint to list all training data"""
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    training_docs = []
    categories = {}
    
    # From fallback storage
    for doc_id, doc_data in stored_documents.items():
        if doc_data.get("source") == "training_data":
            category = doc_data.get("category", "unknown")
            categories[category] = categories.get(category, 0) + 1
            
            training_docs.append({
                "doc_id": doc_id,
                "filename": doc_data.get("filename"),
                "url": doc_data.get("url"),
                "category": category,
                "content_length": len(doc_data.get("content", "")),
                "title": doc_data.get("title"),
                "storage": "fallback"
            })
    
    # From Elasticsearch (if available)
    if document_store:
        try:
            es_docs = document_store.filter_documents(filters={"source": "training_data"})
            for doc in es_docs:
                category = doc.meta.get("category", "unknown")
                categories[category] = categories.get(category, 0) + 1
                
                training_docs.append({
                    "doc_id": doc.meta.get("doc_id"),
                    "filename": doc.meta.get("filename"),
                    "url": doc.meta.get("url"),
                    "category": category,
                    "content_length": len(doc.content),
                    "title": doc.meta.get("title"),
                    "storage": "elasticsearch"
                })
        except Exception as e:
            logger.error(f"Error listing Elasticsearch training data: {e}")
    
    return JSONResponse({
        "training_documents": training_docs,
        "categories": categories,
        "total_training_docs": len(training_docs)
    })

@app.delete("/admin/clear_training_data/")
async def admin_clear_training_data(admin_key: str):
    """Admin endpoint to clear only training data (keeps user documents)"""
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    global stored_documents
    
    # Clear training data from fallback storage
    stored_documents = {k: v for k, v in stored_documents.items() 
                      if v.get("source") != "training_data"}
    
    # Clear training data from Elasticsearch
    elasticsearch_cleared = False
    if document_store:
        try:
            document_store.delete_documents(filters={"source": "training_data"})
            elasticsearch_cleared = True
            logger.info("✅ Cleared training data from Elasticsearch")
        except Exception as e:
            logger.error(f"Error clearing training data from Elasticsearch: {e}")
    
    return JSONResponse({
        "message": "Training data cleared successfully",
        "elasticsearch_cleared": elasticsearch_cleared,
        "fallback_cleared": True
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
