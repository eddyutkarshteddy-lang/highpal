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
        question = question.strip().lower()
        
        # Handle greetings
        greetings = ["hi", "hello", "hey", "greetings"]
        if question in greetings:
            return JSONResponse({
                "answer": "Hello! I'm HighPal, your document assistant. I can help you process PDFs, fetch web content, and answer questions about uploaded documents.",
                "method": "greeting_response",
                "question": question
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
                "question": question,
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
                    "question": question,
                    "found_docs": len(relevant_docs),
                    "source": top_doc.get("filename", top_doc.get("url", "Unknown"))
                })
            else:
                return JSONResponse({
                    "answer": f"I have {len(stored_documents)} document(s) stored, but I couldn't find information related to your question. Try uploading more relevant documents or asking about the content you've already uploaded.",
                    "method": "no_relevant_docs",
                    "question": question,
                    "stored_docs": len(stored_documents)
                })
        
        # No documents and no text provided
        else:
            return JSONResponse({
                "answer": "Hi! I can help you with document analysis. Please:\n1. Upload a PDF document, or\n2. Fetch content from a URL, or\n3. Provide text with your question\n\nThen ask me questions about the content!",
                "method": "no_content_available",
                "question": question,
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Elasticsearch Document Store
elasticsearch_host = os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200")
elasticsearch_index = os.getenv("ELASTICSEARCH_INDEX", "highpal_documents")

try:
    document_store = ElasticsearchDocumentStore(
        hosts=[elasticsearch_host],
        index=elasticsearch_index
    )
    logger.info("✅ Connected to Elasticsearch")
except Exception as e:
    logger.warning(f"⚠️ Could not connect to Elasticsearch: {e}")
    document_store = None

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

# Initialize Haystack components
embedder = SentenceTransformersDocumentEmbedder(model="all-MiniLM-L6-v2")
text_embedder = SentenceTransformersTextEmbedder(model="all-MiniLM-L6-v2")

# Initialize pipelines
indexing_pipeline = None
rag_pipeline = None

if document_store and ELASTICSEARCH_RETRIEVER_AVAILABLE:
    # Document indexing pipeline
    indexing_pipeline = Pipeline()
    indexing_pipeline.add_component("embedder", embedder)
    indexing_pipeline.add_component("writer", DocumentWriter(document_store=document_store))
    indexing_pipeline.connect("embedder.documents", "writer.documents")

    # RAG pipeline for Q&A
    try:
        retriever = ElasticsearchEmbeddingRetriever(document_store=document_store)
        prompt_builder = PromptBuilder(
            template="""
            Given the following context, please answer the question.
            
            Context:
            {% for document in documents %}
                {{ document.content }}
            {% endfor %}
            
            Question: {{ question }}
            
            Answer:
            """
        )
        
        rag_pipeline = Pipeline()
        rag_pipeline.add_component("text_embedder", text_embedder)
        rag_pipeline.add_component("retriever", retriever)
        rag_pipeline.add_component("prompt_builder", prompt_builder)
        
        rag_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
        rag_pipeline.connect("retriever.documents", "prompt_builder.documents")
        
        logger.info("✅ RAG pipeline initialized successfully")
    except Exception as e:
        logger.warning(f"⚠️ Failed to initialize RAG pipeline: {e}")
        rag_pipeline = None
else:
    indexing_pipeline = None
    rag_pipeline = None
    if not document_store:
        logger.info("ℹ️ Elasticsearch not available - document indexing disabled")
    if not ELASTICSEARCH_RETRIEVER_AVAILABLE:
        logger.info("ℹ️ Elasticsearch retriever not available - RAG disabled")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    elasticsearch_status = "connected" if document_store else "disconnected"
    openai_status = "configured" if openai_client else "not_configured"
    
    return JSONResponse({
        "status": "healthy",
        "elasticsearch": elasticsearch_status,
        "openai": openai_status,
        "haystack_ready": indexing_pipeline is not None and rag_pipeline is not None,
        "features": {
            "document_indexing": document_store is not None,
            "rag_qa": indexing_pipeline is not None and rag_pipeline is not None,
            "general_qa": openai_client is not None
        }
    })

@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload PDF and extract text, optionally index to Elasticsearch"""
    try:
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        
        # Create document ID from file content hash
        doc_id = hashlib.md5(content).hexdigest()
        
        # Index document if Elasticsearch is available
        if indexing_pipeline and text.strip():
            document = Document(
                content=text,
                meta={
                    "filename": file.filename,
                    "doc_id": doc_id,
                    "source": "pdf_upload"
                }
            )
            
            try:
                indexing_pipeline.run({"embedder": {"documents": [document]}})
                logger.info(f"Indexed document: {file.filename}")
                indexed = True
            except Exception as e:
                logger.error(f"Failed to index document: {e}")
                indexed = False
        else:
            indexed = False
        
        return JSONResponse({
            "text": text,
            "doc_id": doc_id,
            "filename": file.filename,
            "indexed": indexed,
            "character_count": len(text)
        })
    
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@app.post("/fetch_url/")
async def fetch_url(url: str = Form(...)):
    """Fetch content from URL and optionally index to Elasticsearch"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(strip=True, separator=' ')
        
        # Create document ID from URL
        doc_id = hashlib.md5(url.encode()).hexdigest()
        
        # Index document if Elasticsearch is available
        if indexing_pipeline and text.strip():
            document = Document(
                content=text,
                meta={
                    "url": url,
                    "doc_id": doc_id,
                    "source": "web_scraping",
                    "title": soup.title.string if soup.title else "No title"
                }
            )
            
            try:
                indexing_pipeline.run({"embedder": {"documents": [document]}})
                logger.info(f"Indexed web content from: {url}")
                indexed = True
            except Exception as e:
                logger.error(f"Failed to index web content: {e}")
                indexed = False
        else:
            indexed = False
        
        return JSONResponse({
            "text": text,
            "doc_id": doc_id,
            "url": url,
            "indexed": indexed,
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
    """Enhanced Q&A using OpenAI, RAG, or direct text analysis"""
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
                # Fallback if OpenAI not available
                answer = f"Based on the provided text: {text[:200]}... \nRegarding '{question}': Please configure OpenAI for better analysis."
                return JSONResponse({
                    "answer": answer,
                    "method": "direct_text_fallback",
                    "question": question
                })
        
        # Priority 2: Check if we have indexed documents and if this seems document-specific
        elif rag_pipeline and document_store and not is_general_question(question):
            try:
                # First try RAG retrieval
                result = rag_pipeline.run({
                    "text_embedder": {"text": question},
                    "prompt_builder": {"question": question}
                })
                
                documents = result.get("retriever", {}).get("documents", [])
                
                if documents:
                    # Use OpenAI with retrieved context for better answers
                    context = "\n\n".join([doc.content[:500] for doc in documents[:3]])
                    
                    if openai_client:
                        answer = await get_openai_response(question, context=context)
                        method = "rag_with_openai"
                    else:
                        answer = f"Based on the indexed documents:\n\n{context[:300]}..."
                        method = "rag_only"
                    
                    return JSONResponse({
                        "answer": answer,
                        "method": method,
                        "question": question,
                        "retrieved_docs": len(documents),
                        "sources": [doc.meta.get("filename", doc.meta.get("url", "Unknown")) for doc in documents[:3]]
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
                            "answer": "I couldn't find relevant information in the indexed documents, and OpenAI is not configured for general questions.",
                            "method": "no_results",
                            "question": question,
                            "retrieved_docs": 0
                        })
            
            except Exception as e:
                logger.error(f"RAG pipeline error: {e}")
                # Fall back to OpenAI if RAG fails
                if openai_client:
                    answer = await get_openai_response(question)
                    return JSONResponse({
                        "answer": answer,
                        "method": "openai_rag_fallback",
                        "question": question,
                        "note": "Document search failed, using general knowledge"
                    })
                else:
                    raise HTTPException(status_code=500, detail=f"Error in RAG pipeline: {str(e)}")
        
        # Priority 3: General questions or when RAG isn't available - use OpenAI
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
    """Get the count of indexed documents"""
    if document_store:
        try:
            count = document_store.count_documents()
            return JSONResponse({"document_count": count})
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return JSONResponse({"document_count": 0, "error": str(e)})
    else:
        return JSONResponse({"document_count": 0, "error": "Elasticsearch not connected"})

@app.delete("/documents/clear")
async def clear_documents():
    """Clear all indexed documents"""
    if document_store:
        try:
            document_store.delete_documents()
            return JSONResponse({"message": "All documents cleared successfully"})
        except Exception as e:
            logger.error(f"Error clearing documents: {e}")
            raise HTTPException(status_code=500, detail=f"Error clearing documents: {str(e)}")
    else:
        raise HTTPException(status_code=503, detail="Elasticsearch not connected")
