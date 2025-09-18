"""
Simple HighPal Voice Test Server
Just for testing voice functionality without training dependencies
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging
import os
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
    if api_key:
        openai_client = OpenAI(api_key=api_key)
        OPENAI_AVAILABLE = True
        logger.info("✅ OpenAI client initialized")
    else:
        OPENAI_AVAILABLE = False
        logger.warning("⚠️ OpenAI API key not found")
except Exception as e:
    logger.warning(f"⚠️ OpenAI not available: {e}")
    OPENAI_AVAILABLE = False
    openai_client = None

# Import speech service
try:
    from speech_service import get_speech_service
    SPEECH_AVAILABLE = True
    logger.info("✅ Azure Speech Service loaded successfully")
except ImportError as e:
    logger.warning(f"⚠️ Speech service not available: {e}")
    SPEECH_AVAILABLE = False

# Pydantic models
class QuestionRequest(BaseModel):
    question: str
    uploaded_files: list = []
    is_first_message: bool = False

class TextToSpeechRequest(BaseModel):
    text: str
    voice_name: Optional[str] = None

# Initialize FastAPI app
app = FastAPI(
    title="HighPal Voice Test Server",
    description="Simple server for testing voice functionality",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "HighPal Voice Test Server", "voice_available": SPEECH_AVAILABLE}

@app.post("/api/ask-pal")
async def ask_pal(request: QuestionRequest):
    """Simple ask endpoint for testing voice conversation"""
    try:
        question = request.question
        
        if OPENAI_AVAILABLE and openai_client:
            # Use OpenAI for response
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are Pal, a helpful AI assistant. Give brief, clear answers."},
                        {"role": "user", "content": question}
                    ],
                    max_completion_tokens=200,
                    temperature=0.7
                )
                answer = response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI error: {e}")
                answer = f"I heard you say: '{question}'. I'm having a small technical issue with my AI right now, but I'm here to help!"
        else:
            # Simple echo response
            answer = f"I heard you say: '{question}'. This is a test response from Pal!"
        
        return JSONResponse(content={
            "answer": answer,
            "success": True
        })
        
    except Exception as e:
        logger.error(f"Error in ask_pal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
        
        if len(request.text) > 1000:  # Reduce limit for testing
            raise HTTPException(status_code=400, detail="Text too long (max 1000 characters)")
        
        logger.info(f"Converting text to speech: {request.text[:50]}...")
        
        # Convert text to speech using the working method from test
        result = speech_service.text_to_speech(request.text)
        
        if result['success']:
            audio_data = result['audio_data']
            logger.info(f"Generated audio data: {len(audio_data)} bytes")
            
            return Response(
                content=audio_data,
                media_type="audio/wav",
                headers={
                    "Content-Type": "audio/wav",
                    "Content-Length": str(len(audio_data)),
                    "Cache-Control": "no-cache"
                }
            )
        else:
            logger.error(f"Text-to-speech failed: {result['error']}")
            raise HTTPException(status_code=400, detail=result['error'])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text-to-speech error: {e}")
        raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")

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

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting HighPal Voice Test Server...")
    print("✨ Features:")
    print(f"  • OpenAI GPT integration {'✅' if OPENAI_AVAILABLE else '❌'}")
    print(f"  • Azure Speech Services {'✅' if SPEECH_AVAILABLE else '❌'}")
    print("")
    print("📡 Server starting on http://localhost:8003")
    print("📖 API docs available at http://localhost:8003/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8003)
