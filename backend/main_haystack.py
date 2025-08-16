from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
import logging
import hashlib
import os
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Haystack imports with proper error handling
try:
    from haystack import Document, Pipeline
    from haystack.components.writers import DocumentWriter
    from haystack.components.embedders import SentenceTransformersDocumentEmbedder, SentenceTransformersTextEmbedder
    from haystack.components.retrievers import ElasticsearchBM25Retriever
    from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
    HAYSTACK_AVAILABLE = True
    logger.info("✅ Haystack components loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Haystack not available: {e}")
    HAYSTACK_AVAILABLE = False

app = FastAPI(title="HighPal Document Assistant", description="AI-powered document processing with Haystack + Elasticsearch")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Elasticsearch and Haystack components
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
        
        # Create retrieval pipeline (BM25 for text search)
        retrieval_pipeline = Pipeline()
        retriever = ElasticsearchBM25Retriever(document_store=document_store)
        retrieval_pipeline.add_component("retriever", retriever)
        
        logger.info("✅ Haystack pipelines initialized successfully")
        
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize Elasticsearch/Haystack: {e}")
        document_store = None
        indexing_pipeline = None
        retrieval_pipeline = None

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
