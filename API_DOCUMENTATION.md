# 📡 HighPal API Documentation

**Version:** 5.0.0+  
**Base URL:** `http://localhost:8003`  
**Server:** FastAPI with advanced conversation management and emotional intelligence integration
**Status:** Production-Ready with Advanced Features
**Last Updated:** September 27, 2025

---

## 🌐 API Overview

HighPal provides a comprehensive RESTful API for advanced educational assistance with sophisticated conversation management, voice processing, and intelligent document handling. The API supports dual learning modes, persistent conversation history, advanced voice interaction, and comprehensive revision systems.

### Architecture
- **Advanced Orchestration Layer**: FastAPI with sophisticated conversation management and voice processing
- **Pal Engine**: Intelligent exam preparation and educational conversations with context awareness
- **Book Engine**: Comprehensive document processing with quiz generation and revision capabilities
- **Conversation Engine**: Persistent conversation history with intelligent management and deduplication
- **Voice Processing Engine**: Advanced voice interaction with barge-in detection and mathematical speech processing
- **Memory Engine**: Conversation state tracking and intelligent context preservation

### Voice Processing Pipeline
- **Azure STT**: Convert student speech to text with high accuracy
- **Azure Text Analytics**: Analyze voice emotions and stress patterns using sentiment analysis
- **OpenAI**: Generate contextually and emotionally appropriate responses
- **Azure TTS**: Deliver responses with emotionally expressive neural voices

### Authentication
JWT token authentication for production. Local development supports demo mode.
- **Guest Mode**: Limited functionality without emotional memory persistence
- **Authenticated Mode**: Full emotional intelligence and personalization

### Content-Type
- **Uploads:** `multipart/form-data`  
- **JSON:** `application/json`
- **Responses:** `application/json`

---

## 📋 Core Endpoints

### 🏥 Health & Status

#### `GET /health`
Check server health, database connectivity, and engine status.

**Response:**
```json
{
  "status": "healthy",
  "mongodb": "connected",
  "redis": "connected",
  "pal_engine": "ready",
  "book_engine": "ready",
  "memory_engine": "ready",
  "timestamp": "2025-09-07T17:38:47.821432"
}
```

#### `GET /`
Get API overview and available endpoints.

**Response:**
```json
{
  "message": "HighPal AI Educational Assistant",
  "version": "3.0.0",
  "status": "running",
  "modes": [
    "Learn with Pal - Exam preparation and open dialogue",
    "My Book - Document-focused Q&A and revision"
  ],
  "features": [
    "Emotionally intelligent conversations",
    "Memory-driven personalization", 
    "Dual-mode learning support",
    "Secure document processing",
    "Multi-model AI integration"
  ],
  "endpoints": {
    "docs": "/docs",
    "health": "/health",
    "pal": "/pal",
    "book": "/book",
    "memory": "/memory"
  }
}
```

---

## � Voice & Emotional Intelligence Endpoints

### `POST /voice/speech-to-text`
Convert student speech to text using Azure Speech Services.

**Request:**
```json
{
  "audio_data": "base64_encoded_audio",
  "user_id": "user123",
  "context": {
    "learning_mode": "pal",
    "current_topic": "mathematics"
  }
}
```

**Response:**
```json
{
  "transcription": {
    "text": "I'm struggling with this calculus problem",
    "confidence": 0.95,
    "language": "en-US"
  },
  "processing_time": 245,
  "audio_quality": "excellent"
}
```

### `POST /voice/analyze-emotion`
Analyze emotional state from voice using Azure Text Analytics and Speech Services.

**Request:**
```json
{
  "audio_data": "base64_encoded_audio",
  "user_id": "user123",
  "session_context": {
    "previous_emotions": ["neutral", "confused"],
    "learning_session_duration": 15
  }
}
```

**Response:**
```json
{
  "emotion_analysis": {
    "primary_emotion": "frustration",
    "emotion_scores": {
      "frustration": 0.78,
      "confusion": 0.65,
      "determination": 0.43
    },
    "stress_level": 6.2,
    "confidence_level": 3.1,
    "intervention_needed": true
  },
  "recommendations": {
    "voice_style": "calm",
    "response_approach": "supportive",
    "suggested_break": false
  }
}
```

### `POST /voice/text-to-speech`
Generate emotionally appropriate speech using Azure Neural Voices.

**Request:**
```json
{
  "text": "I understand you're finding this challenging. Let's break it down step by step.",
  "emotion_context": {
    "student_emotion": "frustration",
    "stress_level": 6.2,
    "confidence_level": 3.1
  },
  "voice_preferences": {
    "style": "supportive",
    "rate": "medium",
    "pitch": "medium"
  }
}
```

**Response:**
```json
{
  "audio_data": "base64_encoded_audio",
  "voice_config": {
    "voice_name": "en-US-JennyNeural",
    "style": "empathetic",
    "rate": "slow",
    "ssml_used": true
  },
  "emotional_adaptations": [
    "calming_tone",
    "encouraging_emphasis",
    "supportive_pace"
  ]
}
```

### `POST /voice/conversation`
Complete voice interaction pipeline with emotional intelligence.

**Request:**
```json
{
  "audio_input": "base64_encoded_audio",
  "user_id": "user123",
  "learning_context": {
    "mode": "pal",
    "subject": "physics",
    "current_emotion": "confused",
    "session_progress": 0.6
  }
}
```

**Response:**
```json
{
  "transcription": "I don't understand how momentum is conserved",
  "emotion_analysis": {
    "primary_emotion": "confusion",
    "stress_level": 4.5,
    "confidence_level": 4.0
  },
  "ai_response": {
    "text": "Great question! Momentum conservation is one of the fundamental principles in physics. Let me explain it with a simple example...",
    "emotional_tone": "encouraging",
    "educational_level": "intermediate"
  },
  "audio_response": "base64_encoded_audio",
  "learning_insights": {
    "concept_difficulty": "medium",
    "suggested_examples": ["billiard_balls", "car_collision"],
    "follow_up_topics": ["kinetic_energy", "elastic_collisions"]
  }
}
```

### `GET /voice/emotional-history/{user_id}`
Retrieve user's emotional learning journey and patterns.

**Response:**
```json
{
  "emotional_timeline": [
    {
      "timestamp": "2025-09-14T10:30:00Z",
      "primary_emotion": "excitement",
      "stress_level": 2.1,
      "confidence_level": 7.8,
      "learning_topic": "algebra"
    }
  ],
  "patterns": {
    "peak_learning_emotions": ["curiosity", "engagement"],
    "stress_triggers": ["time_pressure", "complex_problems"],
    "confidence_builders": ["step_by_step_explanations", "encouragement"]
  },
  "recommendations": {
    "optimal_learning_time": "morning",
    "preferred_voice_style": "cheerful",
    "stress_intervention_threshold": 6.0
  }
}
```

---

## �🎯 Learn with Pal Endpoints

### `POST /pal/conversation`
Start or continue an open-ended educational conversation.

**Request:**
```json
{
  "message": "I want to prepare for the CAT exam",
  "user_id": "user123",
  "context": {
    "emotional_state": "confident",
    "session_type": "exam_prep"
  }
}
```

**Response:**
```json
{
  "response": "Great choice! CAT has three main sections: Quantitative Ability, Verbal Ability, and Data Interpretation. Based on your previous sessions, I remember you found quantitative topics challenging. Which area would you like to focus on today?",
  "emotional_tone": "encouraging",
  "suggested_topics": ["Quantitative Ability", "Verbal Ability", "Data Interpretation"],
  "memory_context": {
    "remembered_topics": ["previous difficulty with algebra"],
    "study_streak": 5
  },
  "conversation_id": "conv_789"
}
```

### `GET /pal/exams`
Get supported exam types and preparation materials.

**Response:**
```json
{
  "supported_exams": [
    {
      "name": "CAT",
      "full_name": "Common Admission Test",
      "sections": ["Quantitative Ability", "Verbal Ability", "Data Interpretation"],
      "preparation_materials": 1250
    },
    {
      "name": "GRE", 
      "full_name": "Graduate Record Examination",
      "sections": ["Verbal Reasoning", "Quantitative Reasoning", "Analytical Writing"],
      "preparation_materials": 890
    }
  ]
}
```

---

## 📚 My Book Endpoints

### `POST /book/upload`
Upload personal study materials with security scanning.

**Request:**
- **Method:** POST
- **Content-Type:** multipart/form-data
- **Parameters:**
  - `file` (required): PDF or Word document
  - `user_id` (required): User identifier
  - `scope` (optional): "document_only" or "expandable" (default: "document_only")

**Response:**
```json
{
  "success": true,
  "document_id": "book_a1b2c3d4e5f6",
  "filename": "calculus_textbook.pdf",
  "size": 2457600,
  "processing_status": "completed",
  "scope": "document_only",
  "chapters_detected": 12,
  "question_bank_generated": true
}
```

### `POST /book/question`
Ask questions about uploaded documents with scope management.

**Request:**
```json
{
  "question": "Explain the concept of limits in calculus",
  "document_id": "book_a1b2c3d4e5f6",
  "user_id": "user123",
  "allow_external": false
}
```

**Response:**
```json
{
  "answer": "According to your textbook (Chapter 2, page 45), a limit describes the value that a function approaches as the input approaches some value...",
  "source": "document_only",
  "page_references": [45, 46, 47],
  "confidence": 0.92,
  "external_available": true,
  "external_prompt": "I can provide broader context about limits and their applications in machine learning. Would you like me to access external knowledge?"
}
```

### `POST /book/expand_knowledge`
Grant permission to blend document content with external knowledge.

**Request:**
```json
{
  "document_id": "book_a1b2c3d4e5f6",
  "user_id": "user123",
  "permission_granted": true,
  "scope": "session"
}
```

### `POST /book/revision`
Start revision mode with quiz-style questions.

**Request:**
```json
{
  "document_id": "book_a1b2c3d4e5f6",
  "chapter": 5,
  "difficulty": "adaptive",
  "question_count": 10
}
```

**Response:**
```json
{
  "revision_session_id": "rev_xyz789",
  "questions": [
    {
      "id": "q1",
      "question": "What is the derivative of x²?",
      "type": "multiple_choice",
      "options": ["2x", "x", "2", "x²"],
      "page_reference": 67
    }
  ],
  "estimated_duration": "15 minutes"
}
```

---

## 🧠 Memory Management Endpoints

### `GET /memory/profile/{user_id}`
Retrieve user's learning profile and memory context.

**Response:**
```json
{
  "user_id": "user123",
  "learning_profile": {
    "preferred_learning_style": "visual",
    "strong_subjects": ["mathematics", "physics"],
    "challenging_topics": ["organic chemistry", "statistics"],
    "study_streak": 7,
    "total_sessions": 45
  },
  "emotional_patterns": {
    "confidence_trend": "improving",
    "stress_indicators": ["late_night_sessions"],
    "motivation_triggers": ["progress_visualization", "peer_comparison"]
  },
  "conversation_context": {
    "recent_topics": ["calculus limits", "CAT preparation"],
    "unresolved_questions": 2,
    "scheduled_reviews": ["algebra_basics", "reading_comprehension"]
  }
}
```

### `POST /memory/update`
Update user memory with new learning data.

**Request:**
```json
{
  "user_id": "user123",
  "memory_type": "topic_mastery",
  "data": {
    "topic": "calculus_limits",
    "mastery_level": 0.75,
    "session_feedback": "understood basic concept, needs more practice",
    "emotional_state": "confident"
  }
}
```

---

## ⚠️ Error Handling & Edge Cases

### Standard Error Response
```json
{
  "error": {
    "code": "DOCUMENT_PROCESSING_FAILED",
    "message": "Unable to extract text from uploaded PDF",
    "details": "File may be corrupted or password-protected",
    "suggested_action": "Try uploading a different file or contact support"
  },
  "fallback_options": [
    "manual_text_input",
    "ocr_processing",
    "alternative_format"
  ]
}
```

### Engine Fallback Logic
- **Pal Engine Unavailable**: Fall back to basic Q&A mode
- **Book Engine Unavailable**: Redirect to general document search
- **Memory Engine Unavailable**: Continue with session-only memory
- **External LLM Unavailable**: Use local models with reduced capability notice

---

## 🔒 Security & Privacy

### Data Classification
- **Public Content**: Freely accessible exam preparation materials
- **Personal Memory**: Encrypted user learning patterns and preferences  
- **User Documents**: Encrypted with user-controlled access
- **Conversation History**: Optional local storage with user consent

### Privacy Controls
- **Memory Opt-out**: Users can disable memory tracking
- **Data Export**: Full user data export in standard formats
- **Selective Deletion**: Granular control over stored information
- **Anonymous Mode**: Basic functionality without data persistence

---

## 🧪 Testing the API

### Quick Health Check
```bash
curl http://localhost:8003/health
```

### Test Pal Conversation
```bash
curl -X POST http://localhost:8003/pal/conversation \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to prepare for CAT exam", "user_id": "test_user"}'
```

### Test Book Upload
```bash
curl -X POST http://localhost:8003/book/upload \
  -F "file=@textbook.pdf" \
  -F "user_id=test_user"
```

### Test Memory Profile
```bash
curl http://localhost:8003/memory/profile/test_user
```

---

## 📚 Additional Resources

- **Interactive Docs:** http://localhost:8003/docs (Swagger UI)
- **OpenAPI Schema:** http://localhost:8003/openapi.json
- **Health Dashboard:** http://localhost:8003/health
- **Engine Status:** http://localhost:8003/engines/status

---

**Last Updated:** September 7, 2025  
**API Version:** 3.0.0  
**Maintained by:** HighPal Development Team
