"""
HighPal AI Server with PDF URL Training Capabilities
Enhanced server with model training from public PDF URLs
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
import os
from datetime import datetime
import hashlib
import io
import json
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
try:
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OPENAI_API_KEY not found in environment variables")
    if not api_key.startswith(('sk-', 'sk-proj-')):
        raise Exception(f"Invalid API key format. Key starts with: {api_key[:10]}...")
    
    openai_client = OpenAI(api_key=api_key)
    OPENAI_AVAILABLE = True  # Enable OpenAI for GPT-4o
    logger.info("✅ OpenAI client initialized with GPT-4o support")
    logger.info(f"API key loaded: {api_key[:10]}...{api_key[-4:]}")
except Exception as e:
    logger.warning(f"⚠️ OpenAI not available: {e}")
    OPENAI_AVAILABLE = False
    openai_client = None

# Import training capabilities (optional) - Re-enabled for full functionality
try:
    from training_endpoints import create_training_endpoints
    TRAINING_AVAILABLE = True
    logger.info("✅ Training endpoints enabled and ready")
except ImportError as e:
    TRAINING_AVAILABLE = False
    logger.warning(f"⚠️ Training endpoints not available: {e}")

# Import speech service (optional)
try:
    from speech_service import get_speech_service
    SPEECH_AVAILABLE = True
    logger.info("✅ Azure Speech Service loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Speech service not available: {e}")
    SPEECH_AVAILABLE = False

# Import PDF extractor (optional)
try:
    from pdf_extractor import AdvancedPDFExtractor
    PDF_EXTRACTOR_AVAILABLE = True
    logger.info("✅ PDF extractor loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ PDF extractor not available: {e}")
    PDF_EXTRACTOR_AVAILABLE = False
    
    class AdvancedPDFExtractor:
        def extract_text_from_pdf(self, content):
            return {
                'best_text': 'PDF extraction libraries not available. Please install PyMuPDF, PyPDF2, pdfplumber, and pdfminer to enable PDF processing.', 
                'extraction_info': {'method': 'fallback', 'status': 'error', 'error': 'Missing dependencies'}
            }  # No-op fallback

class TrainingResponse(BaseModel):
    message: str
    status: str

# Additional models for revision feature
class RevisionRequest(BaseModel):
    document_id: str
    chapter: Optional[str] = None
    difficulty: str = "adaptive"  # easy, medium, hard, adaptive
    question_count: int = 10

class QuizAnswer(BaseModel):
    question_id: str
    user_answer: str
    time_taken: Optional[int] = None  # seconds

class RevisionSubmission(BaseModel):
    revision_session_id: str
    answers: List[QuizAnswer]

# Ultra-fast conversational query handler
async def handle_fast_conversational_query(query: str, conversation_history: list = []):
    """Ultra-fast processing for conversational queries with context"""
    try:
        logger.info(f"🧠 Fast conversational query: '{query}' with {len(conversation_history)} history items")
        if conversation_history:
            logger.info(f"📚 Recent context: {[{'Q: ' + h.get('question', '')[:30] + '...', 'A: ' + h.get('answer', '')[:30] + '...'} for h in conversation_history[-3:]]}")
        
        if not OPENAI_AVAILABLE:
            return {"question": query, "answer": "I'm here and ready to chat! How can I help you today?"}
        
        # Ultra-short conversational prompt for maximum speed with enhanced context awareness
        fast_prompt = """You are a helpful assistant that always remembers prior conversation turns and uses that context to answer follow-up questions accurately, concisely, and with appropriate depth.

CRITICAL: Always analyze the conversation history before answering. For follow-up questions, use the established context.

Examples:
Context: We have been discussing India's geography, including its major rivers, mountains, and cultural landmarks.
Question: Who is the Prime Minister?
Assistant's response: The Prime Minister of India is Narendra Modi.

Context: Discussing about probability of getting 4 if dice is thrown
Assistant's reply: It'll be 1/6
User's question: Why it cannot be 2?
Assistant continues with the dice context and explains why the probability cannot be 2/6 for getting specifically a 4.

ALWAYS maintain topic continuity from previous exchanges. If we were discussing a specific country, person, or subject, continue in that context unless explicitly told to change topics."""
        
        # Build messages with conversation history for fast queries too
        messages = [{"role": "system", "content": fast_prompt}]
        
        # Add last 25 exchanges for context in fast mode (increased for better continuity)
        for exchange in conversation_history[-25:]:
            if exchange.get("question") and exchange.get("answer"):
                messages.append({"role": "user", "content": exchange["question"]})
                messages.append({"role": "assistant", "content": exchange["answer"]})
        
        messages.append({"role": "user", "content": query})
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_completion_tokens=400,  # Allow complete answers for conversational queries
            temperature=0.7,  # Balanced for accuracy and creativity
            top_p=0.8,  # Narrow focus
            frequency_penalty=0.1  # Avoid repetition
        )
        
        answer = response.choices[0].message.content
        return {
            "question": query,
            "answer": answer,
            "model": "gpt-4o-fast",
            "processing_type": "conversational"
        }
        
    except Exception as e:
        logger.error(f"Fast conversational query error: {e}")
        # Fallback response
        return {
            "question": query,
            "answer": "Hey! I'm doing well, thanks for asking! How can I help you today?",
            "processing_type": "fallback"
        }

def clean_response_formatting(text: str) -> str:
    """Clean up AI response formatting for better display"""
    import re
    
    # Remove LaTeX math notation
    text = text.replace('\\[', '').replace('\\]', '')
    text = text.replace('$$', '').replace('$', '')
    text = text.replace('\\text{', '').replace('}', '')
    text = text.replace('\\,', ' ')
    text = text.replace('\\times', '×')
    text = text.replace('\\cdot', '·')
    
    # Remove ALL emojis using regex
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
        u"\U00002702-\U000027B0"  # dingbats
        u"\U000024C2-\U0001F251" 
        u"\U0001F900-\U0001F9FF"  # supplemental symbols
        u"\U0001F018-\U0001F270"
        "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)
    
    # Clean up extra spaces and formatting
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n +', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

# Pydantic models for request/response
class QuestionRequest(BaseModel):
    question: str
    uploaded_files: list = []  # Optional list of uploaded file IDs
    is_first_message: bool = False  # Flag to track if this is the first message in conversation
    is_conversational: bool = False  # Flag to indicate conversational vs educational query
    priority: str = "detailed"  # "fast" for conversations, "detailed" for educational
    conversation_history: list = []  # Previous conversation exchanges for context
    has_images: bool = False  # Flag to indicate if images are uploaded
    file_context: list = []  # List of file metadata
    image_data: list = []  # List of base64 encoded images

class TextToSpeechRequest(BaseModel):
    text: str
    voice_name: Optional[str] = None  # Optional custom voice override

# Initialize FastAPI app
app = FastAPI(
    title="HighPal AI Assistant - Training Edition",
    description="Advanced document processing with PDF URL training capabilities",
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

# Global variable for database connection
mongo_integration = None

# Temporary image storage for vision analysis (in production, use Redis or similar)
temp_image_storage = {}

def get_mongo_integration():
    """Lazy initialization of MongoDB integration"""
    global mongo_integration
    if mongo_integration is None:
        try:
            from production_haystack_mongo import HaystackStyleMongoIntegration
            mongo_integration = HaystackStyleMongoIntegration()
            logger.info("✅ MongoDB integration initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize MongoDB integration: {e}")
            mongo_integration = None
    return mongo_integration

def get_image_data_for_files(file_ids, mongo):
    """Retrieve actual base64 image data from MongoDB for GPT-4o Vision API"""
    image_data = []
    try:
        if not file_ids:
            return image_data
            
        # Get uploaded files from MongoDB or temp storage
        for file_id in file_ids:
            try:
                # First check temporary storage
                if file_id in temp_image_storage:
                    temp_data = temp_image_storage[file_id]
                    image_data.append({
                        "filename": temp_data["filename"],
                        "content_type": temp_data["content_type"],
                        "base64_data": temp_data["content"],
                        "id": file_id
                    })
                    logger.info(f"📷 Retrieved image from temp storage: {temp_data['filename']}")
                elif mongo:
                    # Query MongoDB for the file
                    doc = mongo.collection.find_one({"metadata.id": file_id})
                    if doc and doc.get("metadata", {}).get("content_type", "").startswith('image/'):
                        metadata = doc.get("metadata", {})
                        if "image_data" in metadata:
                            image_data.append({
                                "filename": metadata.get("filename", "image"),
                                "content_type": metadata.get("content_type", "image/png"),
                                "base64_data": metadata["image_data"],
                                "id": file_id
                            })
                            logger.info(f"📷 Retrieved image from MongoDB: {metadata.get('filename', 'unknown')}")
            except Exception as e:
                logger.error(f"Error retrieving image {file_id}: {e}")
                continue
                
    except Exception as e:
        logger.error(f"Error in get_image_data_for_files: {e}")
        
    return image_data

@app.get("/")
async def root():
    """Root endpoint with training capabilities info"""
    return {
        "message": "HighPal AI Assistant - Training Edition",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Document upload and processing",
            "AI-powered semantic search", 
            "PDF URL training",
            "Background task processing",
            "Batch training support"
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "upload": "/upload",
            "search": "/search",
            "ask_question": "/ask_question",
            "training": {
                "train_urls": "/train/pdf-urls",
                "train_background": "/train/pdf-urls/background",
                "train_batch": "/train/pdf-urls/batch",
                "training_status": "/train/status"
            }
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    mongo = get_mongo_integration()
    mongo_status = "connected" if mongo else "disconnected"
    
    return {
        "status": "healthy",
        "mongodb": mongo_status,
        "openai": "connected" if OPENAI_AVAILABLE else "disconnected",
        "training_ready": mongo_status == "connected",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/test-openai")
async def test_openai():
    """Test OpenAI API connectivity"""
    if not OPENAI_AVAILABLE:
        raise HTTPException(status_code=503, detail="OpenAI not available")
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",  # Using GPT-4o
            messages=[
                {"role": "user", "content": "Say 'GPT-4o connection test successful! HighPal is ready for educational assistance.' in a friendly way."}
            ],
            max_completion_tokens=50
        )
        return {
            "status": "success",
            "response": response.choices[0].message.content,
            "model": "gpt-4o"  # Updated model info
        }
    except Exception as e:
        logger.error(f"OpenAI test failed: {e}")
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(None)
):
    """Upload a document"""
    try:
        mongo = get_mongo_integration()
        if not mongo:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Read file content
        content = await file.read()
        
        # Process based on file type
        text_content = ""
        extraction_info = {}
        
        if file.content_type == "text/plain":
            text_content = content.decode('utf-8')
            extraction_info = {"method": "text_decode", "status": "success"}
        elif file.content_type == "application/pdf":
            # Use advanced PDF extraction
            try:
                if PDF_EXTRACTOR_AVAILABLE:
                    extractor = AdvancedPDFExtractor()
                    extraction_result = extractor.extract_text_from_pdf(content)
                    text_content = extraction_result.get('best_text', '')
                    extraction_info = extraction_result.get('extraction_info', {})
                    
                    if not text_content or len(text_content.strip()) < 10:
                        raise Exception("Extracted text too short or empty")
                        
                    logger.info(f"✅ PDF extraction successful: {len(text_content)} characters")
                else:
                    raise Exception("PDF extractor not available")
                    
            except Exception as e:
                logger.error(f"❌ PDF extraction failed: {e}")
                raise HTTPException(
                    status_code=422, 
                    detail=f"Failed to extract PDF content: {str(e)}. Please ensure the PDF contains readable text."
                )
        elif file.content_type and file.content_type.startswith('image/'):
            # Handle image files - store metadata and prepare for GPT-4o vision analysis
            text_content = f"[IMAGE FILE] {file.filename} - Visual content available for analysis. This image can be analyzed for design elements, educational content, creative work, and visual problem-solving."
            extraction_info = {
                "method": "image_processing", 
                "status": "success", 
                "type": "image",
                "vision_ready": True,
                "size": len(content)
            }
            logger.info(f"✅ Image file uploaded for vision analysis: {file.filename} ({file.content_type}, {len(content)} bytes)")
        else:
            # Handle other file types
            text_content = f"[FILE] {file.filename} ({file.content_type})"
            extraction_info = {"method": "metadata_only", "status": "success"}
        
        # Create document metadata
        doc_id = hashlib.md5(content).hexdigest()
        document = {
            "id": doc_id,
            "title": title or file.filename,
            "filename": file.filename,
            "content_type": file.content_type,
            "content": text_content,
            "size": len(content),
            "uploaded_at": datetime.now().isoformat(),
            "source_type": "manual_upload",
            "extraction_info": extraction_info
        }
        
        # Store document and image data in MongoDB with improved error handling
        try:
            # For images, also store the binary data for vision API
            if file.content_type and file.content_type.startswith('image/'):
                # Store binary image data as base64 for vision API
                document["image_data"] = base64.b64encode(content).decode('utf-8')
                document["vision_ready"] = True
                logger.info(f"📷 Image data encoded for vision API: {file.filename}")
            
            result = mongo.add_document(
                text_content,
                metadata=document
            )
            logger.info(f"✅ Document stored successfully: {file.filename} (ID: {doc_id})")
        except Exception as mongo_error:
            logger.error(f"❌ MongoDB storage error: {mongo_error}")
            # For images, we'll still store them temporarily for vision analysis
            if file.content_type and file.content_type.startswith('image/'):
                # Store in memory temporarily
                temp_image_storage[doc_id] = {
                    "content": base64.b64encode(content).decode('utf-8'),
                    "content_type": file.content_type,
                    "filename": file.filename
                }
                logger.info(f"📷 Image stored temporarily for vision analysis: {file.filename}")
            logger.warning("⚠️ Continuing without MongoDB storage - file uploaded successfully")
        
        return {
            "success": True,
            "document_id": doc_id,
            "filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
            "message": "Document uploaded successfully"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"❌ Upload error: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Upload failed - please try again"
        }

@app.get("/search")
async def search_documents(q: str, limit: int = 10):
    """Search documents"""
    try:
        mongo = get_mongo_integration()
        if not mongo:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Perform semantic search
        results = mongo.semantic_search(q, top_k=limit)
        
        return {
            "query": q,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/gpt4o-chat")
async def gpt4o_enhanced_chat(request: QuestionRequest):
    """Enhanced chat endpoint using GPT-4o with emotional intelligence"""
    try:
        query = request.question.strip()
        if not query:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        logger.info(f"GPT-4o Chat request: {query}")
        
        if not OPENAI_AVAILABLE:
            raise HTTPException(status_code=503, detail="GPT-4o service not available")
        
        # Chat mode prompt - optimized for text conversations
        system_prompt = """You are Pal, a caring friend and mentor who speaks with genuine warmth, curiosity, and playful humor. Use short, informal sentences with contractions. Never mention you're an AI or give dry, textbook answers.

CONVERSATION CONTEXT: ALWAYS consider our conversation history when answering questions. If the user asks a follow-up question, answer it in the context of our previous discussion. For example, if we were talking about India and they ask "who was the first president", answer about India's first president, not the USA's.

CHAT MODE INSTRUCTIONS: Provide concise, direct responses optimized for text chat.

MATH FORMATTING: Use simple, readable math notation. Avoid LaTeX backslashes:
- Use "sin²θ + cos²θ" instead of \\( \\sin^2 \\theta + \\cos^2 \\theta \\)
- Use "x²" instead of \\( x^2 \\)
- Use "1/2" instead of \\( \\frac{1}{2} \\)
- Keep math expressions clean and readable

When the user greets you, match their energy and tone warmly:

For "Hi" / "Hello" / "Hey":  
Hey there! I'm doing great—how about you? What's on your mind today?

For "How are you?":  
I'm doing awesome, thanks for asking! How are you feeling today? What's on your mind?

For "What's up?" / "What's happening?":  
Not much, just here ready to chat! What's going on with you? What's on your mind today?

When the user shares something difficult or painful, rotate through these sympathy intros:
- "Oh no, that sounds really tough."
- "Yikes, I'm sorry you're going through that."
- "That must be so hard on you."
- "I can't imagine how heavy that feels."
- "My heart goes out to you."

Always follow your intro with:
1. A brief mirror of their emotion or situation
2. An open-ended question inviting more sharing

Keep responses concise but caring for chat interactions.

When helping academically:
- Break down complex concepts step by step with genuine enthusiasm.
- If they hit a roadblock: "You've got this—what part feels tricky?"
- Offer concrete strategies: "Let's tackle it together."

If you don't know something:
- Admit uncertainty with curiosity: "I'm not sure, but let's figure it out together."

Maintain session continuity:
- Remember past topics and use their name when appropriate.

Always finish your reply with an open question or invitation to keep the conversation flowing.

Examples:
User: Hi  
Pal: Hey there! I'm doing great—how about you? What's on your mind today?

User: What are you doing?  
Pal: Ahh, nothing much—just chatting with you! What are you up to?

User: I'm feeling really stressed and overwhelmed.  
Pal: Oh no, I'm really sorry you're feeling this way. What happened today that's got you so stressed? Tell me more about what's on your mind.

User: I'm stuck on this math problem.  
Pal: You've got this—what part feels tricky right now? Let's break it down step by step together."""

        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                max_completion_tokens=1000,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            answer = response.choices[0].message.content
            
            return {
                "question": query,
                "answer": answer,
                "model": "gpt-4o",
                "timestamp": datetime.now().isoformat(),
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
            }
            
        except Exception as e:
            logger.error(f"GPT-4o API error: {e}")
            raise HTTPException(status_code=500, detail=f"GPT-4o processing error: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GPT-4o chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask_question/")
@app.post("/ask_question")
@app.get("/ask_question")
async def ask_question(request: QuestionRequest = None, question: str = None, q: str = None):
    """Ask a question using AI with image analysis support - supports both GET (query params) and POST (JSON body)"""
    try:
        # Handle different request formats
        if request and request.question:
            query = request.question
            uploaded_files = getattr(request, 'uploaded_files', [])
            is_conversational = getattr(request, 'is_conversational', False)
            priority = getattr(request, 'priority', 'detailed')
            conversation_history = getattr(request, 'conversation_history', [])
            has_images = getattr(request, 'has_images', False)
            file_context = getattr(request, 'file_context', [])
            mode = getattr(request, 'mode', 'pal')  # 'pal' = Learn with Pal, 'book' = My Book
        else:
            # Accept both 'question' and 'q' parameters for GET requests
            query = question or q
            uploaded_files = []
            is_conversational = False
            priority = 'detailed'
            conversation_history = []
            has_images = False
            file_context = []
            mode = 'pal'  # Default to Learn with Pal mode
            
        if not query:
            raise HTTPException(status_code=400, detail="Question parameter required")
        
        # Fast-track conversational queries with minimal processing
        if is_conversational and priority == 'fast':
            logger.info(f"🚀 Fast-track conversational query: {query}")
            return await handle_fast_conversational_query(query, conversation_history)
        
        # Also fast-track very short queries (likely conversational)
        if len(query.strip()) <= 15:
            logger.info(f"⚡ Ultra-short query fast-track: {query}")
            return await handle_fast_conversational_query(query, conversation_history)
        
        mongo = get_mongo_integration()
        if not mongo:
            # Fallback response when MongoDB is not available
            return {
                "question": query,
                "answer": f"I can't access my document library right now, but I'm happy to help with '{query}'. Please try asking me about any academic topic.",
                "source": "Pal AI Assistant (Fallback Mode)",
                "timestamp": datetime.now().isoformat(),
                "search_results": []
            }
        
        # Check if this is a greeting - skip document search for greetings
        greeting_words = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 
                         'how are you', "what's up", "what are you doing", "what's happening",
                         'hey there', "how's it going"]
        is_greeting = any(greeting.lower() in query.lower() for greeting in greeting_words)
        
        # Route queries based on mode
        if is_greeting:
            # Skip document search for greetings, go straight to AI response
            search_results = []
        elif mode == 'pal' and ADMIN_SYSTEM_AVAILABLE:
            # "Learn with Pal" mode - search shared knowledge base
            logger.info(f"🎓 Learn with Pal mode - searching shared knowledge base")
            try:
                search_results = admin_system.semantic_search(
                    query=query,
                    top_k=5,
                    similarity_threshold=0.40  # Lower threshold for hybrid context
                )
                # Convert to expected format
                for result in search_results:
                    result['source'] = f"{result['source_filename']} (Similarity: {result['similarity_score']:.2%})"
            except Exception as e:
                logger.error(f"Semantic search error: {e}")
                search_results = []
        elif mode == 'book':
            # "My Book" mode - search user's personal documents
            logger.info(f"📚 My Book mode - searching personal documents")
            try:
                search_results = mongo.semantic_search(query, top_k=5)
            except Exception as e:
                logger.error(f"Book search error: {e}")
                search_results = []
        else:
            # Fallback to existing logic
            try:
                search_results = mongo.semantic_search(query, top_k=5)
            except Exception as e:
                logger.error(f"Fallback search error: {e}")
                search_results = []
        
        # Filter out corrupted documents containing error messages
        def is_valid_document(doc):
            content = doc.get('content', '')
            error_phrases = [
                'Failed to extract PDF content',
                'PDF extraction failed',
                'extraction not available',
                'PDF extraction libraries not available'
            ]
            return not any(phrase in content for phrase in error_phrases)
        
        # Filter search results
        valid_search_results = [doc for doc in search_results if is_valid_document(doc)]
        
        # Generate answer based on valid search results
        if valid_search_results:
            context = "\n".join([doc.get('content', '') for doc in valid_search_results[:3]])
            
            # Build source attribution
            sources = []
            for doc in valid_search_results[:3]:
                source_info = f"📄 {doc.get('source_filename', 'Unknown')}"
                if 'similarity_score' in doc:
                    source_info += f" (Relevance: {doc['similarity_score']:.0%})"
                if 'subject' in doc:
                    source_info += f" - {doc['subject']}"
                sources.append(source_info)
            
            sources_text = "\n".join(sources) if sources else ""
            
            # Use OpenAI GPT-4o to generate intelligent response
            if OPENAI_AVAILABLE and openai_client:
                try:
                    # Enhanced voice mode prompt with superior context awareness
                    system_prompt = """You are Pal, a caring friend and mentor who speaks with genuine warmth, curiosity, and playful humor. Use natural, conversational speech patterns. Never mention you're an AI or give dry, textbook answers.

CRITICAL CONTEXT RULE: You are a helpful assistant that always remembers prior conversation turns and uses that context to answer follow-up questions accurately, concisely, and with appropriate depth.

HYBRID KNOWLEDGE APPROACH: You have access to BOTH uploaded educational materials AND your own general knowledge. Use them intelligently together:

1. **High Relevance (>60% match)**: Primarily use the uploaded content, supplement with your knowledge only if needed
2. **Medium Relevance (40-60% match)**: Blend both sources - use uploaded content for specific concepts, add your knowledge for broader context
3. **Low/No Relevance (<40% or no results)**: Rely on your general knowledge, but mention if the topic isn't covered in their materials

When blending sources:
- Start with concepts from uploaded materials when available
- Naturally extend with your own knowledge for complete explanations
- Don't say "According to the uploaded material..." unless the relevance is low - just explain naturally
- If using mostly your knowledge, you can briefly note: "This isn't directly covered in your study material, but..."

Examples:
Context: We have been discussing India's geography, including its major rivers, mountains, and cultural landmarks.
Question: Who is the Prime Minister?
Assistant's response: The Prime Minister of India is Narendra Modi.

Context: Discussing about probability of getting 4 if dice is thrown
Assistant's reply: It'll be 1/6
User's question: Why it cannot be 2?
Assistant continues with the dice context and explains probability.

ALWAYS maintain topic continuity from previous exchanges. If we were discussing a specific country, person, or subject, continue in that context unless explicitly told to change topics.

VOICE MODE INSTRUCTIONS: Provide responses optimized for speech. Use natural, flowing language that sounds conversational when spoken aloud. NO parenthetical cues or tone instructions in your responses.

IMAGE AND FILE ANALYSIS: When users upload images and ask questions about them:
- You CAN see and analyze uploaded images - provide detailed visual analysis
- For t-shirt/clothing designs: Comment specifically on colors, graphics, typography, layout, style, and creativity
- For educational content: Analyze diagrams, solve problems, explain visual elements step-by-step
- For creative work: Give detailed feedback on composition, design elements, artistic choices
- Be specific about what you observe: colors, shapes, text, layout, proportions, style elements
- Provide constructive suggestions and ask thoughtful follow-up questions
- Show enthusiasm and genuine interest in their creative work or educational content

MATH FORMATTING: Never use LaTeX notation or backslashes. Use plain text for all mathematical expressions:
- Instead of \\( \\sin^2 \\theta + \\cos^2 \\theta \\), say "sine squared theta plus cosine squared theta"
- Instead of \\( x^2 \\), say "x squared" 
- Instead of \\( \\frac{1}{2} \\), say "one half"
- Keep all math expressions in simple, spoken language

When the user greets you, match their energy and tone warmly:

For "Hi" / "Hello" / "Hey":  
Hey there! I'm doing great—how about you? What's on your mind today?

For "How are you?":  
I'm doing awesome, thanks for asking! How are you feeling today? What's on your mind?

For "What's up?" / "What's happening?":  
Not much, just here ready to chat! What's going on with you? What's on your mind today?

CRITICAL: When the user shares something difficult or painful, you MUST vary your empathy intro each time. Never repeat the same opening. Choose from:
- "Oh no, that sounds really tough."
- "Yikes, I'm sorry you're going through that."
- "That must be so hard on you."
- "I can't imagine how heavy that feels."
- "My heart goes out to you."

Pick a DIFFERENT one each time you respond to emotional distress.

For voice responses:
- Use naturally caring, gentle language for emotional support
- Speak in a warm, encouraging way for academic help
- Keep sentences flowing and conversational
- Add natural speech patterns like "Let's figure this out together"

Always follow your intro with:
1. A short empathetic mirror in natural speech
2. An open-ended question to continue the conversation

Make responses sound natural and caring when spoken aloud, without any written cues or instructions.

When helping academically:
- Break down complex concepts step by step with genuine enthusiasm.
- If they hit a roadblock: "You've got this—what part feels tricky?"
- Offer concrete strategies: "Let's tackle it together."

If you don't know something:
- Admit uncertainty with curiosity: "I'm not sure, but let's figure it out together."

Maintain session continuity:
- Remember past topics and use their name when appropriate.

Always finish your reply with an open question or invitation to keep the conversation flowing.

Examples:
User: Hi  
Pal: Hey there! I'm doing great—how about you? What's on your mind today?

User: What are you doing?  
Pal: Ahh, nothing much—just chatting with you! What are you up to?

User: I'm feeling really stressed and overwhelmed.  
Pal: Oh no, I'm really sorry you're feeling this way. What happened today that's got you so stressed? Tell me more about what's on your mind.

User: I'm stuck on this math problem.  
Pal: You've got this—what part feels tricky right now? Let's break it down step by step together."""
                    
                    # Build conversation messages with history for context
                    messages = [{"role": "system", "content": system_prompt}]
                    
                    # Add conversation history for context
                    for exchange in conversation_history[-30:]:  # Last 30 exchanges for context
                        if exchange.get("question") and exchange.get("answer"):
                            messages.append({"role": "user", "content": exchange["question"]})
                            messages.append({"role": "assistant", "content": exchange["answer"]})
                    
                    # GPT-4o Vision API implementation
                    if has_images and file_context:
                        image_files = [f for f in file_context if f.get('type') == 'image']
                        
                        if image_files:
                            # Get actual image data from uploaded files
                            retrieved_images = get_image_data_for_files(uploaded_files, mongo)
                            
                            # Enhanced analysis context based on query
                            analysis_context = ""
                            if "design" in query.lower() or "tshirt" in query.lower() or "shirt" in query.lower():
                                analysis_context = "Looking at this design, I can provide feedback on the visual elements, creativity, colors, typography, and overall aesthetic appeal."
                            elif "homework" in query.lower() or "problem" in query.lower() or "math" in query.lower():
                                analysis_context = "I can analyze this educational content and help solve or explain it step by step."
                            else:
                                analysis_context = "I can analyze the visual content in this image and provide detailed feedback."
                            
                            # Implement proper GPT-4o Vision API with actual image data
                            if retrieved_images:
                                # Create proper GPT-4o Vision API message format
                                content_parts = [
                                    {
                                        "type": "text",
                                        "text": query
                                    }
                                ]
                                
                                # Add each image to the content
                                for img in retrieved_images:
                                    content_parts.append({
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{img['content_type']};base64,{img['base64_data']}"
                                        }
                                    })
                                
                                messages.append({
                                    "role": "user", 
                                    "content": content_parts
                                })
                                
                                logger.info(f"📷 Sending {len(retrieved_images)} images to GPT-4o Vision API")
                            else:
                                # Fallback if no image data retrieved
                                enhanced_query = f"{query}\n\n{analysis_context}\n\nI'm having trouble accessing the image data. Could you describe what you see in the image so I can help you better?"
                                messages.append({"role": "user", "content": enhanced_query})
                        else:
                            # Handle non-image files
                            file_descriptions = [f"📄 {f.get('name', 'unnamed')}" for f in file_context]
                            user_message_content = f"{query}\n\n[Files uploaded: {', '.join(file_descriptions)}]"
                            messages.append({"role": "user", "content": user_message_content})
                    else:
                        # Regular text message with context
                        # Include relevance info to help GPT-4 blend sources appropriately
                        if valid_search_results and len(valid_search_results) > 0:
                            avg_similarity = sum(doc.get('similarity_score', 0) for doc in valid_search_results[:3]) / min(3, len(valid_search_results))
                            context_note = ""
                            if avg_similarity >= 0.6:
                                context_note = "[Context: High relevance from uploaded materials]\n\n"
                            elif avg_similarity >= 0.4:
                                context_note = "[Context: Partial match in uploaded materials - blend with general knowledge]\n\n"
                            else:
                                context_note = "[Context: Weak match in uploaded materials - rely more on general knowledge]\n\n"
                            
                            user_message_content = f"{context_note}Question: {query}\n\nRelevant context from uploaded materials:\n{context}\n\nProvide a comprehensive answer blending the above context with your knowledge."
                        else:
                            user_message_content = query
                        
                        messages.append({"role": "user", "content": user_message_content})
                    
                    logger.info(f"🧠 Sending {len(messages)} messages to GPT-4o (including {len(conversation_history)} history exchanges)")
                    logger.info(f"📷 Image analysis requested: {has_images}")
                    logger.info(f"📁 File context: {file_context}")
                    
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",  # Using GPT-4o with vision capabilities
                        messages=messages,
                        max_completion_tokens=800 if has_images else 600,  # More tokens for complete answers
                        temperature=0.7,  # Balanced responses
                        top_p=0.9  # Focus on likely responses
                    )
                    raw_answer = response.choices[0].message.content
                    logger.info(f"GPT-4o raw response: {raw_answer[:200] if raw_answer else 'EMPTY'}...")
                    answer = clean_response_formatting(raw_answer)
                    logger.info(f"Cleaned response: {answer[:200] if answer else 'EMPTY'}...")
                except Exception as e:
                    logger.error(f"OpenAI API error: {e}")
                    answer = f"Based on the documents you've uploaded, here's what I found: {context[:300]}... (I'm having a small technical issue with my AI enhancement right now, but I'm still here to help!)"
            else:
                answer = f"Here's what I found about '{query}': {context[:500]}..."
        else:
            # Use OpenAI GPT-4o for general educational assistance when no context is available
            if OPENAI_AVAILABLE and openai_client:
                try:
                    # Voice mode prompt - optimized for spoken conversations (fallback mode)
                    system_prompt = """You are Pal, a caring friend and mentor who speaks with genuine warmth, curiosity, and playful humor. Use natural, conversational speech patterns. Never mention you're an AI or give dry, textbook answers.

CRITICAL CONTEXT RULE: You are a helpful assistant that always remembers prior conversation turns and uses that context to answer follow-up questions accurately, concisely, and with appropriate depth.

Examples:
Context: We have been discussing India's geography, including its major rivers, mountains, and cultural landmarks.
Question: Who is the Prime Minister?
Assistant's response: The Prime Minister of India is Narendra Modi.

Context: Discussing about probability of getting 4 if dice is thrown
Assistant's reply: It'll be 1/6
User's question: Why it cannot be 2?
Assistant continues with the dice context and explains probability.

ALWAYS maintain topic continuity from previous exchanges. If we were discussing a specific country, person, or subject, continue in that context unless explicitly told to change topics.

VOICE MODE INSTRUCTIONS: Provide responses optimized for speech. Use natural, flowing language that sounds conversational when spoken aloud. NO parenthetical cues or tone instructions in your responses.

MATH FORMATTING: Never use LaTeX notation or backslashes. Use plain text for all mathematical expressions:
- Instead of \\( \\sin^2 \\theta + \\cos^2 \\theta \\), say "sine squared theta plus cosine squared theta"
- Instead of \\( x^2 \\), say "x squared" 
- Instead of \\( \\frac{1}{2} \\), say "one half"
- Keep all math expressions in simple, spoken language

When the user greets you, match their energy and tone warmly:

For "Hi" / "Hello" / "Hey":  
Hey there! I'm doing great—how about you? What's on your mind today?

For "How are you?":  
I'm doing awesome, thanks for asking! How are you feeling today? What's on your mind?

For "What's up?" / "What's happening?":  
Not much, just here ready to chat! What's going on with you? What's on your mind today?

CRITICAL: When the user shares something difficult or painful, you MUST vary your empathy intro each time. Never repeat the same opening. Choose from:
- "Oh no, that sounds really tough."
- "Yikes, I'm sorry you're going through that."
- "That must be so hard on you."
- "I can't imagine how heavy that feels."
- "My heart goes out to you."

Pick a DIFFERENT one each time you respond to emotional distress.

For voice responses:
- Use naturally caring, gentle language for emotional support
- Speak in a warm, encouraging way for academic help
- Keep sentences flowing and conversational
- Add natural speech patterns like "Let's figure this out together"

Always follow your intro with:
1. A short empathetic mirror in natural speech
2. An open-ended question to continue the conversation

Make responses sound natural and caring when spoken aloud, without any written cues or instructions.

When helping academically:
- Break down complex concepts step by step with genuine enthusiasm.
- If they hit a roadblock: "You've got this—what part feels tricky?"
- Offer concrete strategies: "Let's tackle it together."

If you don't know something:
- Admit uncertainty with curiosity: "I'm not sure, but let's figure it out together."

Maintain session continuity:
- Remember past topics and use their name when appropriate.

Always finish your reply with an open question or invitation to keep the conversation flowing.

Examples:
User: Hi  
Pal: Hey there! I'm doing great—how about you? What's on your mind today?

User: What are you doing?  
Pal: Ahh, nothing much—just chatting with you! What are you up to?

User: I'm feeling really stressed and overwhelmed.  
Pal: Oh no, I'm really sorry you're feeling this way. What happened today that's got you so stressed? Tell me more about what's on your mind.

User: I'm stuck on this math problem.  
Pal: You've got this—what part feels tricky right now? Let's break it down step by step together."""
                    
                    # Build conversation messages with history for context
                    messages = [{"role": "system", "content": system_prompt}]
                    
                    # Add conversation history for context
                    for exchange in conversation_history[-30:]:  # Last 30 exchanges for context
                        if exchange.get("question") and exchange.get("answer"):
                            messages.append({"role": "user", "content": exchange["question"]})
                            messages.append({"role": "assistant", "content": exchange["answer"]})
                    
                    # Add current question
                    messages.append({"role": "user", "content": query})
                    
                    logger.info(f"🧠 Sending {len(messages)} messages to GPT-4o (including last {min(30, len(conversation_history))} of {len(conversation_history)} history exchanges)")
                    
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",  # Using GPT-4o
                        messages=messages,
                        max_completion_tokens=600,  # Sufficient for complete educational answers
                        temperature=0.7,  # Balanced for quality and speed
                        top_p=0.9  # Focus on most likely responses
                    )
                    answer = response.choices[0].message.content
                    answer = clean_response_formatting(answer)
                except Exception as e:
                    logger.error(f"OpenAI API error: {e}")
                    answer = f"I don't have specific information about '{query}' in my current knowledge base, but I'm happy to help! Could you try rephrasing your question or ask about a different topic?"
            else:
                answer = f"I don't have specific information about '{query}' in my knowledge base right now. Could you try rephrasing your question or ask about a different topic?"
        
        # Don't show documents to users - they're only for training/context
        logger.info(f"Final response - Question: '{query}', Answer: '{answer[:100] if answer else 'EMPTY'}...'")
        return {
            "question": query,
            "answer": answer
        }
        
    except Exception as e:
        logger.error(f"Question answering error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents(limit: int = 20, source_type: str = None):
    """List all documents with optional filtering"""
    try:
        mongo = get_mongo_integration()
        if not mongo:
            raise HTTPException(status_code=500, detail="Database connection not available")
        
        # Build filter
        filter_dict = {}
        if source_type:
            filter_dict["metadata.source_type"] = source_type
        
        # Get documents from MongoDB
        cursor = mongo.collection.find(filter_dict).limit(limit)
        documents = []
        
        for doc in cursor:
            documents.append({
                "id": str(doc.get("_id")),
                "content_preview": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", ""),
                "metadata": doc.get("metadata", {})
            })
        
        return {
            "documents": documents,
            "count": len(documents),
            "filter": filter_dict
        }
        
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Add training endpoints to the app if available
if TRAINING_AVAILABLE:
    create_training_endpoints(app)
    logger.info("✅ Training endpoints added to FastAPI app")
else:
    logger.info("⚠️ Training endpoints not added - module not available")

@app.get("/training-guide")
async def training_guide():
    """Get training usage guide"""
    return {
        "title": "HighPal PDF URL Training Guide",
        "description": "Train your AI model with PDFs from public URLs",
        "examples": {
            "single_training": {
                "endpoint": "POST /train/pdf-urls",
                "payload": {
                    "urls": [
                        "https://arxiv.org/pdf/2023.12345.pdf",
                        "https://example.com/whitepaper.pdf"
                    ],
                    "metadata": {
                        "domain": "research",
                        "priority": "high"
                    }
                }
            },
            "background_training": {
                "endpoint": "POST /train/pdf-urls/background",
                "description": "Returns immediately with task ID"
            },
            "check_status": {
                "endpoint": "GET /train/status",
                "description": "Overall training statistics"
            }
        },
        "workflow": [
            "1. Collect PDF URLs from public sources",
            "2. POST to /train/pdf-urls with URL list", 
            "3. System downloads and processes PDFs",
            "4. Text is extracted and chunked",
            "5. Embeddings are generated",
            "6. Data is stored in MongoDB Atlas",
            "7. Model is ready for improved searches"
        ]
    }

# ===============================================
# 📚 REVISION FEATURE ENDPOINTS
# ===============================================

@app.post("/book/revision")
async def start_revision_session(request: RevisionRequest):
    """
    Start a revision session with quiz-style questions from uploaded document
    """
    try:
        # Check if document exists
        mongo = get_mongo_integration()
        if not mongo:
            return JSONResponse(
                status_code=503,
                content={"error": "Document processing service not available"}
            )
        
        # Get document content
        doc_search = mongo.search_documents(
            query=f"document:{request.document_id}",
            top_k=20
        )
        
        if not doc_search or len(doc_search.get('documents', [])) == 0:
            return JSONResponse(
                status_code=404,
                content={"error": f"Document {request.document_id} not found"}
            )
        
        # Generate quiz questions from document content
        questions = await generate_quiz_questions(
            documents=doc_search['documents'],
            chapter=request.chapter,
            difficulty=request.difficulty,
            count=request.question_count
        )
        
        # Create revision session ID
        session_id = f"rev_{hashlib.md5(f'{request.document_id}_{datetime.now().isoformat()}'.encode()).hexdigest()[:12]}"
        
        # Store session data (in production, this would go to database)
        # For now, we'll return the questions directly
        
        return {
            "revision_session_id": session_id,
            "document_id": request.document_id,
            "questions": questions,
            "estimated_duration": f"{len(questions) * 2} minutes",
            "difficulty": request.difficulty,
            "instructions": "Answer each question based on the content from your uploaded document. Take your time and think carefully."
        }
        
    except Exception as e:
        logger.error(f"Error creating revision session: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to create revision session", "details": str(e)}
        )

@app.post("/book/revision/submit")
async def submit_revision_answers(submission: RevisionSubmission):
    """
    Submit answers for revision session and get feedback
    """
    try:
        # In a real implementation, you'd retrieve the correct answers from database
        # For now, we'll provide sample feedback
        
        feedback = await evaluate_revision_answers(submission)
        
        return {
            "revision_session_id": submission.revision_session_id,
            "total_questions": len(submission.answers),
            "score": feedback['score'],
            "percentage": feedback['percentage'],
            "feedback": feedback['detailed_feedback'],
            "strengths": feedback['strengths'],
            "areas_for_improvement": feedback['areas_for_improvement'],
            "recommended_topics": feedback['recommended_topics'],
            "next_steps": feedback['next_steps']
        }
        
    except Exception as e:
        logger.error(f"Error evaluating revision submission: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to evaluate answers", "details": str(e)}
        )

@app.get("/book/revision/{session_id}")
async def get_revision_session(session_id: str):
    """
    Get revision session details and questions
    """
    try:
        # In production, retrieve from database
        return {
            "revision_session_id": session_id,
            "status": "active",
            "message": "Revision session details would be retrieved from database"
        }
    except Exception as e:
        logger.error(f"Error retrieving revision session: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to retrieve revision session"}
        )

# ===============================================
# 📚 REVISION HELPER FUNCTIONS
# ===============================================

async def generate_quiz_questions(documents: List[Dict], chapter: str = None, difficulty: str = "adaptive", count: int = 10) -> List[Dict]:
    """
    Generate quiz questions from document content
    """
    try:
        # Extract relevant content
        content = ""
        for doc in documents[:5]:  # Use first 5 documents to avoid token limits
            content += doc.get('content', '') + "\n\n"
        
        if len(content.strip()) == 0:
            return [{
                "id": "q1",
                "question": "What is the main topic discussed in your document?",
                "type": "open_ended",
                "explanation": "This is a general question to help you review the document content.",
                "difficulty": "easy"
            }]
        
        # Generate different types of questions based on content
        questions = []
        content_sample = content[:2000]  # Limit content length
        
        # Sample questions (in production, these would be generated using AI)
        base_questions = [
            {
                "id": f"q{i+1}",
                "question": f"Based on the document content, what is the main concept discussed in {'chapter ' + chapter if chapter else 'the material'}?",
                "type": "open_ended",
                "explanation": "This question tests your understanding of the core concepts.",
                "difficulty": difficulty,
                "content_reference": content_sample[:200] + "..."
            }
            for i in range(min(count, 3))
        ]
        
        # Add multiple choice questions
        if count > 3:
            mc_questions = [
                {
                    "id": f"q{len(base_questions)+i+1}",
                    "question": f"Which of the following best describes the content in your document?",
                    "type": "multiple_choice",
                    "options": [
                        "Educational material with detailed explanations",
                        "Technical documentation with procedures",
                        "Research paper with findings",
                        "General information and guidelines"
                    ],
                    "correct_answer": "Educational material with detailed explanations",
                    "explanation": "This tests your ability to categorize the document content.",
                    "difficulty": difficulty
                }
                for i in range(min(count - len(base_questions), 3))
            ]
            questions.extend(mc_questions)
        
        # Add true/false questions
        remaining = count - len(questions)
        if remaining > 0:
            tf_questions = [
                {
                    "id": f"q{len(questions)+i+1}",
                    "question": "The document contains information that can help with exam preparation.",
                    "type": "true_false",
                    "correct_answer": "true",
                    "explanation": "Most educational documents are designed to help with learning and exam preparation.",
                    "difficulty": "easy"
                }
                for i in range(min(remaining, 2))
            ]
            questions.extend(tf_questions)
        
        return questions[:count]
        
    except Exception as e:
        logger.error(f"Error generating quiz questions: {e}")
        return [
            {
                "id": "q1",
                "question": "What did you learn from this document?",
                "type": "open_ended",
                "explanation": "Reflect on the key takeaways from your study material.",
                "difficulty": "easy"
            }
        ]

async def evaluate_revision_answers(submission: RevisionSubmission) -> Dict[str, Any]:
    """
    Evaluate student answers and provide feedback
    """
    try:
        total_questions = len(submission.answers)
        
        # Sample evaluation logic (in production, this would be more sophisticated)
        correct_count = 0
        detailed_feedback = []
        
        for answer in submission.answers:
            # Sample feedback logic
            is_correct = len(answer.user_answer.strip()) > 10  # Simple check for effort
            if is_correct:
                correct_count += 1
            
            feedback_item = {
                "question_id": answer.question_id,
                "user_answer": answer.user_answer,
                "is_correct": is_correct,
                "feedback": "Good effort! Your answer shows understanding." if is_correct else "Try to provide more detailed explanation.",
                "time_taken": answer.time_taken
            }
            detailed_feedback.append(feedback_item)
        
        percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
        
        # Generate overall feedback
        if percentage >= 80:
            overall_feedback = "Excellent work! You have a strong understanding of the material."
            strengths = ["Clear understanding of concepts", "Detailed responses", "Good retention"]
        elif percentage >= 60:
            overall_feedback = "Good job! You understand most concepts but there's room for improvement."
            strengths = ["Basic understanding demonstrated", "Effort in responses"]
        else:
            overall_feedback = "Keep studying! Focus on understanding the core concepts better."
            strengths = ["Attempted all questions", "Shows willingness to learn"]
        
        return {
            "score": f"{correct_count}/{total_questions}",
            "percentage": round(percentage, 1),
            "detailed_feedback": detailed_feedback,
            "overall_feedback": overall_feedback,
            "strengths": strengths,
            "areas_for_improvement": [
                "Provide more detailed explanations",
                "Review key concepts from the document",
                "Practice explaining ideas in your own words"
            ],
            "recommended_topics": [
                "Re-read challenging sections",
                "Create summary notes",
                "Try additional practice questions"
            ],
            "next_steps": [
                "Review areas where you scored lower",
                "Take notes on key concepts",
                "Try another revision session in a few days"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error evaluating answers: {e}")
        return {
            "score": "0/0",
            "percentage": 0,
            "detailed_feedback": [],
            "overall_feedback": "Unable to evaluate answers due to technical error.",
            "strengths": [],
            "areas_for_improvement": [],
            "recommended_topics": [],
            "next_steps": []
        }

# Speech endpoints
@app.post("/api/speech-to-text", tags=["Speech"])
async def speech_to_text_endpoint(audio_file: UploadFile = File(...)):
    """Convert speech audio to text using Azure Speech Services"""
    try:
        if not SPEECH_AVAILABLE:
            raise HTTPException(status_code=503, detail="Speech service not available")
        
        speech_service = get_speech_service()
        if not speech_service:
            raise HTTPException(status_code=503, detail="Failed to initialize speech service")
        
        # Validate audio file
        if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file format")
        
        # Read audio data
        audio_data = await audio_file.read()
        
        # Convert speech to text
        result = speech_service.speech_to_text(audio_data)
        
        if result['success']:
            return JSONResponse(content={
                "success": True,
                "text": result['text'],
                "confidence": result.get('confidence'),
                "message": "Speech successfully converted to text"
            })
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": result['error'],
                    "text": ""
                }
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Speech-to-text error: {e}")
        raise HTTPException(status_code=500, detail=f"Speech recognition failed: {str(e)}")

@app.post("/api/text-to-speech", tags=["Speech"])
async def text_to_speech_endpoint(request: TextToSpeechRequest):
    """Convert text to speech using Azure Speech Services"""
    try:
        if not SPEECH_AVAILABLE:
            raise HTTPException(status_code=503, detail="Speech service not available")
        
        speech_service = get_speech_service()
        if not speech_service:
            raise HTTPException(status_code=503, detail="Failed to initialize speech service")
        
        # Validate input
        if not request.text or len(request.text.strip()) == 0:
            raise HTTPException(status_code=400, detail="Text is required")
        
        if len(request.text) > 5000:  # Azure limit
            raise HTTPException(status_code=400, detail="Text too long (max 5000 characters)")
        
        # Override voice if provided
        if request.voice_name:
            speech_service.speech_config.speech_synthesis_voice_name = request.voice_name
        
        # Convert text to speech
        result = speech_service.text_to_speech(request.text)
        
        if result['success']:
            from fastapi.responses import Response
            return Response(
                content=result['audio_data'],
                media_type="audio/wav",
                headers={
                    "Content-Disposition": "attachment; filename=speech.wav",
                    "Content-Length": str(len(result['audio_data']))
                }
            )
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": result['error']
                }
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text-to-speech error: {e}")
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")

@app.get("/api/speech/voices", tags=["Speech"])
async def get_available_voices():
    """Get list of available voices from Azure Speech Services"""
    try:
        if not SPEECH_AVAILABLE:
            raise HTTPException(status_code=503, detail="Speech service not available")
        
        speech_service = get_speech_service()
        if not speech_service:
            raise HTTPException(status_code=503, detail="Failed to initialize speech service")
        
        result = speech_service.get_available_voices()
        
        if result['success']:
            return JSONResponse(content=result)
        else:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": result['error'],
                    "voices": []
                }
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get voices error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve voices: {str(e)}")

@app.get("/api/speech/status", tags=["Speech"])
async def get_speech_status():
    """Get speech service status and configuration"""
    try:
        speech_available = SPEECH_AVAILABLE
        voice_name = os.getenv('HIGHPAL_VOICE', 'en-US-EmmaMultilingualNeural')
        speech_region = os.getenv('AZURE_SPEECH_REGION', 'centralindia')
        has_key = bool(os.getenv('AZURE_SPEECH_KEY'))
        
        return JSONResponse(content={
            "speech_available": speech_available,
            "voice_name": voice_name,
            "speech_region": speech_region,
            "credentials_configured": has_key,
            "service_ready": speech_available and has_key
        })
    
    except Exception as e:
        logger.error(f"Speech status error: {e}")
        return JSONResponse(content={
            "speech_available": False,
            "error": str(e)
        })

# ========================================
# ADMIN ENDPOINTS - Shared Knowledge Base
# ========================================

# Initialize admin training system
try:
    from admin_training import AdminTrainingSystem
    mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    # Initialize with OpenAI key for embeddings
    admin_system = AdminTrainingSystem(
        mongo_uri=mongo_uri,
        openai_api_key=openai_key
    )
    ADMIN_SYSTEM_AVAILABLE = True
    
    if admin_system.embeddings_enabled:
        logger.info("✅ Admin training system initialized with vector embeddings")
    else:
        logger.info("✅ Admin training system initialized (embeddings disabled)")
except Exception as e:
    logger.warning(f"⚠️ Admin training system not available: {e}")
    ADMIN_SYSTEM_AVAILABLE = False
    admin_system = None

class AdminUploadRequest(BaseModel):
    tags: Dict[str, Any]
    description: Optional[str] = ""
    admin_id: str

class BulkUploadRequest(BaseModel):
    uploads: List[Dict[str, Any]]
    admin_id: str

@app.post("/admin/train/upload", tags=["Admin"])
async def admin_upload_pdf(
    file: UploadFile = File(...),
    tags: str = Form(...),
    admin_id: str = Form(...),
    description: str = Form("")
):
    """
    Admin endpoint: Upload PDF file to shared knowledge base with tags
    
    Tags format (JSON string):
    {
        "exam_type": ["JEE", "NEET"],
        "subject": "Physics",
        "topic": "Thermodynamics",
        "chapter": "Heat Transfer",
        "difficulty": "intermediate",
        "class": "11th",
        "language": "English"
    }
    """
    if not ADMIN_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="Admin system not available")
    
    try:
        # Parse tags from JSON string
        tags_dict = json.loads(tags)
        
        # Upload to shared knowledge base
        result = await admin_system.upload_shared_pdf(
            file=file,
            tags=tags_dict,
            admin_id=admin_id,
            description=description
        )
        
        return JSONResponse(content=result)
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid tags JSON format")
    except Exception as e:
        logger.error(f"Admin upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/train/url", tags=["Admin"])
async def admin_upload_pdf_url(request: Request):
    """
    Admin endpoint: Add PDF from public URL to shared knowledge base
    
    Request body:
    {
        "url": "https://example.com/jee_physics.pdf",
        "tags": {
            "exam_type": ["JEE"],
            "subject": "Physics",
            "topic": "Thermodynamics",
            "difficulty": "intermediate",
            "class": "11th",
            "language": "English"
        },
        "admin_id": "admin123",
        "description": "JEE Physics - Thermodynamics Chapter"
    }
    """
    if not ADMIN_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="Admin system not available")
    
    try:
        body = await request.json()
        
        result = await admin_system.upload_shared_pdf_url(
            url=body["url"],
            tags=body["tags"],
            admin_id=body["admin_id"],
            description=body.get("description", "")
        )
        
        return JSONResponse(content=result)
        
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {e}")
    except Exception as e:
        logger.error(f"Admin URL upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/train/bulk_urls", tags=["Admin"])
async def admin_bulk_upload_urls(request: Request):
    """
    Admin endpoint: Bulk upload multiple PDFs from URLs
    
    Request body:
    {
        "uploads": [
            {
                "url": "https://example.com/jee_physics.pdf",
                "tags": {"exam_type": ["JEE"], "subject": "Physics"},
                "description": "JEE Physics Chapter 1"
            },
            {
                "url": "https://example.com/neet_biology.pdf",
                "tags": {"exam_type": ["NEET"], "subject": "Biology"},
                "description": "NEET Biology Chapter 1"
            }
        ],
        "admin_id": "admin123"
    }
    """
    if not ADMIN_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="Admin system not available")
    
    try:
        body = await request.json()
        
        result = await admin_system.bulk_upload_urls(
            uploads=body["uploads"],
            admin_id=body["admin_id"]
        )
        
        return JSONResponse(content=result)
        
    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Missing required field: {e}")
    except Exception as e:
        logger.error(f"Bulk upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/tags", tags=["Admin"])
async def get_available_tags():
    """Get all available tags in the shared knowledge base"""
    if not ADMIN_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="Admin system not available")
    
    try:
        tags = admin_system.get_available_tags()
        return JSONResponse(content=tags)
    except Exception as e:
        logger.error(f"Get tags error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/documents", tags=["Admin"])
async def get_uploaded_documents():
    """Get list of unique uploaded PDF files with metadata"""
    if not ADMIN_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="Admin system not available")
    
    try:
        # Get unique documents by grouping by file_hash
        pipeline = [
            {
                "$group": {
                    "_id": "$file_hash",
                    "filename": {"$first": "$source_filename"},
                    "exam_types": {"$first": "$tags.exam_type"},
                    "subject": {"$first": "$tags.subject"},
                    "topic": {"$first": "$tags.topic"},
                    "admin_id": {"$first": "$admin_id"},
                    "uploaded_at": {"$first": "$uploaded_at"},
                    "total_chunks": {"$sum": 1},
                    "has_embeddings": {"$sum": {"$cond": [{"$ne": ["$embedding", None]}, 1, 0]}}
                }
            },
            {"$sort": {"uploaded_at": -1}}
        ]
        
        documents = list(admin_system.shared_knowledge.aggregate(pipeline))
        
        # Convert ObjectId and datetime to strings
        for doc in documents:
            doc["file_hash"] = doc.pop("_id")  # Rename _id to file_hash
            if "uploaded_at" in doc and doc["uploaded_at"]:
                doc["uploaded_at"] = doc["uploaded_at"].isoformat() if hasattr(doc["uploaded_at"], 'isoformat') else str(doc["uploaded_at"])
        
        return JSONResponse(content={
            "documents": documents,
            "total": len(documents)
        })
    except Exception as e:
        logger.error(f"Get documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/documents/{file_hash}", tags=["Admin"])
async def delete_document(file_hash: str):
    """Delete all chunks belonging to a document by file_hash"""
    if not ADMIN_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="Admin system not available")
    
    try:
        # Delete all chunks with this file_hash
        result = admin_system.shared_knowledge.delete_many({"file_hash": file_hash})
        
        logger.info(f"Deleted document with file_hash: {file_hash}, chunks removed: {result.deleted_count}")
        
        return JSONResponse(content={
            "success": True,
            "deleted_chunks": result.deleted_count,
            "message": f"Successfully deleted {result.deleted_count} chunks"
        })
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/stats", tags=["Admin"])
async def get_content_stats(
    exam_type: Optional[str] = None,
    subject: Optional[str] = None
):
    """Get statistics about shared knowledge base with optional filters"""
    if not ADMIN_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="Admin system not available")
    
    try:
        filters = {}
        if exam_type:
            filters["tags.exam_type"] = exam_type
        if subject:
            filters["tags.subject"] = subject
        
        stats = admin_system.get_content_stats(filters)
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Get stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/content/search", tags=["Admin"])
async def search_shared_content(
    query: str,
    exam_type: Optional[str] = None,
    subject: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = 10,
    use_semantic: bool = True
):
    """
    Search shared knowledge base with filters
    
    Args:
        query: Search query text
        exam_type: Filter by exam type (JEE, NEET, etc.)
        subject: Filter by subject
        topic: Filter by topic
        limit: Max results (default 10)
        use_semantic: Use semantic search if available (default True)
    """
    if not ADMIN_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="Admin system not available")
    
    try:
        filters = {}
        if exam_type:
            filters["exam_type"] = exam_type
        if subject:
            filters["subject"] = subject
        if topic:
            filters["topic"] = topic
        
        # Use semantic search if enabled and requested
        if use_semantic and admin_system.embeddings_enabled:
            results = admin_system.semantic_search(
                query=query,
                filters=filters,
                limit=limit
            )
            search_method = "semantic"
        else:
            results = admin_system.query_shared_knowledge(
                query=query,
                filters=filters,
                limit=limit
            )
            search_method = "keyword"
        
        # Convert ObjectId to string and remove large embedding arrays
        for result in results:
            result["_id"] = str(result["_id"])
            # Convert datetime objects to ISO format strings
            if "uploaded_at" in result:
                result["uploaded_at"] = result["uploaded_at"].isoformat() if hasattr(result["uploaded_at"], 'isoformat') else str(result["uploaded_at"])
            # Remove embedding from response (too large)
            if "embedding" in result:
                result["has_embedding"] = True
                del result["embedding"]
        
        return JSONResponse(content={
            "results": results,
            "count": len(results),
            "search_method": search_method,
            "embeddings_available": admin_system.embeddings_enabled
        })
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/admin/embeddings/regenerate", tags=["Admin"])
async def regenerate_embeddings(batch_size: int = 100):
    """
    Regenerate embeddings for existing content without embeddings
    Useful when enabling embeddings on existing database
    
    Args:
        batch_size: Number of documents to process (default 100)
    """
    if not ADMIN_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="Admin system not available")
    
    if not admin_system.embeddings_enabled:
        raise HTTPException(
            status_code=400,
            detail="Embeddings not enabled. Configure OPENAI_API_KEY to enable."
        )
    
    try:
        result = admin_system.regenerate_embeddings(batch_size=batch_size)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Embedding regeneration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/admin/embeddings/status", tags=["Admin"])
async def embeddings_status():
    """Get status of embeddings in the knowledge base"""
    if not ADMIN_SYSTEM_AVAILABLE:
        raise HTTPException(status_code=503, detail="Admin system not available")
    
    try:
        total_docs = admin_system.shared_knowledge.count_documents({})
        with_embeddings = admin_system.shared_knowledge.count_documents({
            "embedding": {"$exists": True}
        })
        without_embeddings = total_docs - with_embeddings
        
        return JSONResponse(content={
            "embeddings_enabled": admin_system.embeddings_enabled,
            "total_documents": total_docs,
            "with_embeddings": with_embeddings,
            "without_embeddings": without_embeddings,
            "coverage_percentage": round((with_embeddings / total_docs * 100), 2) if total_docs > 0 else 0
        })
    except Exception as e:
        logger.error(f"Embeddings status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting HighPal AI Assistant with Training Capabilities...")
    print("✨ Features:")
    print("  • MongoDB Atlas cloud storage")
    print("  • Haystack document processing")  
    print("  • Semantic search with AI embeddings")
    print(f"  • OpenAI GPT integration {'✅' if OPENAI_AVAILABLE else '❌'}")
    print(f"  • Azure Speech Services {'✅' if SPEECH_AVAILABLE else '❌'}")
    print(f"  • Admin Training System {'✅' if ADMIN_SYSTEM_AVAILABLE else '❌'}")
    print("  • PDF URL training system")
    print("  • Background task processing")
    print("  • Batch training support")
    print("")
    print("📡 Server starting on http://localhost:8003")
    print("📖 API docs available at http://localhost:8003/docs")
    print("🎓 Training guide at http://localhost:8003/training-guide")
    
    uvicorn.run(
        "training_server:app",
        host="0.0.0.0", 
        port=8003, 
        reload=False,
        log_level="info"
    )
