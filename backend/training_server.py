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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import training capabilities (optional)
try:
    from training_endpoints import create_training_endpoints
    TRAINING_AVAILABLE = True
    logger.info("✅ Training endpoints loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Training endpoints not available: {e}")
    TRAINING_AVAILABLE = False
    def create_training_endpoints(app):
        pass

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

# Pydantic models for request/response
class QuestionRequest(BaseModel):
    question: str
    uploaded_files: list = []  # Optional list of uploaded file IDs

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
        "training_ready": mongo_status == "connected",
        "timestamp": datetime.now().isoformat()
    }

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
        else:
            text_content = f"File: {file.filename} ({file.content_type})"
            extraction_info = {"method": "fallback", "status": "success"}
        
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
        
        # Store in MongoDB
        result = mongo.add_document(
            text_content,
            metadata=document
        )
        
        return {
            "success": True,
            "document_id": doc_id,
            "filename": file.filename,
            "size": len(content),
            "message": "Document uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.post("/ask_question/")
@app.post("/ask_question")
@app.get("/ask_question")
async def ask_question(request: QuestionRequest = None, question: str = None, q: str = None):
    """Ask a question using AI - supports both GET (query params) and POST (JSON body)"""
    try:
        # Handle different request formats
        if request and request.question:
            query = request.question
            uploaded_files = getattr(request, 'uploaded_files', [])
        else:
            # Accept both 'question' and 'q' parameters for GET requests
            query = question or q
            uploaded_files = []
            
        if not query:
            raise HTTPException(status_code=400, detail="Question parameter required")
        
        mongo = get_mongo_integration()
        if not mongo:
            # Fallback response when MongoDB is not available
            return {
                "question": query,
                "answer": f"Hello! I'm Pal, your AI learning assistant. You asked: '{query}'. While I can't access the document database right now, I'm here to help you with your studies! Please try uploading some documents first.",
                "source": "Pal AI Assistant (Fallback Mode)",
                "timestamp": datetime.now().isoformat(),
                "search_results": []
            }
        
        # Search for relevant documents
        search_results = mongo.semantic_search(query, top_k=5)
        
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
            context = "\\n".join([doc.get('content', '') for doc in valid_search_results[:3]])
            answer = f"Here's what I found about '{query}': {context[:500]}..."
        else:
            answer = f"I don't have specific information about '{query}' in my knowledge base. Could you try rephrasing your question or asking about a different topic?"
        
        # Don't show documents to users - they're only for training/context
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

# Add training endpoints to the app
create_training_endpoints(app)

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
        haystack_mongo = haystack_integration if hasattr(globals(), 'haystack_integration') and haystack_integration else None
        if not haystack_mongo:
            return JSONResponse(
                status_code=503,
                content={"error": "Document processing service not available"}
            )
        
        # Get document content
        doc_search = await haystack_mongo.search_documents(
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

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting HighPal AI Assistant with Training Capabilities...")
    print("✨ Features:")
    print("  • MongoDB Atlas cloud storage")
    print("  • Haystack document processing")  
    print("  • Semantic search with AI embeddings")
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
