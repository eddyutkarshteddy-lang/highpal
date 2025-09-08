# 🏗️ HighPal Architecture Overview - Dual Tab System

**Version:** 3.0.0  
**Last Updated:** September 7, 2025

---

## 🎯 System Overview

HighPal is an emotionally intelligent AI educational assistant featuring a dual-tab architecture that provides two distinct learning experiences:

1. **Learn with Pal**: Open-ended, exam-focused conversations with curated public content
2. **My Book**: Document-specific Q&A with user-uploaded materials

## 🏛️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer (React)                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────────┐           ┌───────────────────┐          │
│  │  Learn with Pal   │           │     My Book       │          │
│  │     Tab           │           │      Tab          │          │
│  │                   │           │                   │          │
│  │ • Exam Prep       │           │ • Document Upload │          │
│  │ • Open Dialogue   │           │ • Scoped Q&A      │          │
│  │ • Topic Discovery │           │ • Revision Mode   │          │
│  └───────────────────┘           └───────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                   │
                            ┌──────┴──────┐
                            │  API Gateway │
                            └──────┬──────┘
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                    Orchestration Layer (FastAPI)                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Pal Engine  │  │ Book Engine │  │Memory Engine│              │
│  │             │  │             │  │             │              │
│  │ • Intent    │  │ • Document  │  │ • Session   │              │
│  │   Recognition│  │   Processing│  │   Context   │              │
│  │ • Emotional │  │ • Scope     │  │ • Learning  │              │
│  │   Intelligence│  │   Management│  │   Patterns  │              │
│  │ • Exam Prep │  │ • Quiz      │  │ • Personal  │              │
│  │   Content   │  │   Generation│  │   Memory    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                                   │
┌─────────────────────────────────────────────────────────────────┐
│                      Infrastructure Layer                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  MongoDB    │  │    Redis    │  │  Vector DB  │              │
│  │   Atlas     │  │   Session   │  │ Embeddings  │              │
│  │             │  │   Storage   │  │             │              │
│  │ • Documents │  │ • Context   │  │ • Semantic  │              │
│  │ • User Data │  │ • Real-time │  │   Search    │              │
│  │ • History   │  │   State     │  │ • Content   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎓 Learn with Pal - Engine Architecture

### Purpose
Open-ended educational conversations for exam preparation with emotional intelligence and memory-driven personalization.

### Core Components

#### **Intent Recognition System**
```python
class IntentRecognizer:
    """
    Identifies user intent and routes to appropriate conversation flow
    """
    supported_intents = [
        "exam_preparation",
        "topic_exploration", 
        "difficulty_assessment",
        "study_planning",
        "emotional_support"
    ]
    
    supported_exams = ["CAT", "GRE", "GMAT", "LSAT", "SAT", "MCAT"]
```

#### **Emotional Intelligence Module**
```python
class EmotionalIntelligence:
    """
    Tracks and responds to user emotional state
    """
    def analyze_sentiment(self, user_input, context):
        # Sentiment analysis with context awareness
        pass
    
    def generate_appropriate_response(self, sentiment, content):
        # Emotionally appropriate response generation
        pass
    
    def track_emotional_patterns(self, user_id, session_data):
        # Long-term emotional pattern tracking
        pass
```

#### **Content Router**
```python
class PalContentRouter:
    """
    Routes queries to appropriate knowledge sources
    """
    knowledge_sources = [
        "public_exam_materials",
        "curated_educational_content", 
        "user_memory_context",
        "conversation_history"
    ]
    
    def route_query(self, query, user_context):
        # Intelligent routing based on context
        pass
```

### Knowledge Base Structure
```
Public Educational Content/
├── exam_specific/
│   ├── CAT/
│   │   ├── quantitative_ability/
│   │   ├── verbal_ability/
│   │   └── data_interpretation/
│   ├── GRE/
│   └── GMAT/
├── subject_areas/
│   ├── mathematics/
│   ├── english/
│   ├── reasoning/
│   └── general_knowledge/
└── study_strategies/
    ├── time_management/
    ├── exam_techniques/
    └── stress_management/
```

### Conversation Flow Management
```python
class ConversationManager:
    """
    Manages multi-turn dialogue state and context
    """
    def __init__(self):
        self.conversation_state = {
            "current_topic": None,
            "difficulty_level": "adaptive",
            "emotional_state": "neutral",
            "exam_focus": None,
            "session_goals": []
        }
    
    def update_context(self, user_input, pal_response):
        # Update conversation state based on interaction
        pass
    
    def generate_follow_up(self, context):
        # Generate contextually appropriate follow-up questions
        pass
```

---

## 📚 My Book - Engine Architecture

### Purpose
Document-specific Q&A with strict scope management, permission-based knowledge expansion, and revision capabilities.

### Core Components

#### **Document Processor**
```python
class DocumentProcessor:
    """
    Secure document processing with multiple extraction methods
    """
    supported_formats = [".pdf", ".docx", ".txt", ".pptx"]
    
    def process_document(self, file_path, user_id):
        # Security scan → Format detection → Text extraction
        # → Chunking → Embedding generation → Storage
        pass
    
    def generate_question_bank(self, document_chunks):
        # Automatic quiz question generation from content
        pass
    
    def detect_structure(self, document):
        # Chapter/section detection for navigation
        pass
```

#### **Scope Manager**
```python
class ScopeManager:
    """
    Maintains strict boundaries between document and external knowledge
    """
    def __init__(self):
        self.scope_levels = {
            "document_only": "strict document boundaries",
            "document_plus": "document + approved external context",
            "expanded": "full knowledge integration with citations"
        }
    
    def check_scope_boundaries(self, query, document_id, scope_level):
        # Enforce content scope restrictions
        pass
    
    def request_expansion_permission(self, query, potential_external_context):
        # Generate permission prompt for knowledge expansion
        pass
```

#### **Revision Engine**
```python
class RevisionEngine:
    """
    Quiz generation and assessment capabilities
    """
    def generate_quiz(self, document_id, chapter=None, difficulty="adaptive"):
        # Create quiz questions from document content
        pass
    
    def assess_comprehension(self, user_answers, correct_answers):
        # Analyze understanding and provide feedback
        pass
    
    def recommend_review_topics(self, performance_data):
        # Suggest areas needing more attention
        pass
```

### Document Processing Pipeline
```
Upload → Security Scan → Virus Check → Format Detection
    ↓
Text Extraction (Multi-library fallback)
    ↓ 
Content Analysis → Structure Detection → Chapter Mapping
    ↓
Chunking Strategy → Embedding Generation → Vector Storage
    ↓
Question Bank Generation → Metadata Creation → Index Building
    ↓
User Notification → Ready for Q&A
```

---

## 🧠 Memory Engine Architecture

### Purpose
Multi-layered memory management for personalization, context continuity, and learning optimization.

### Memory Layers

#### **Session Memory (Redis)**
```python
class SessionMemory:
    """
    Real-time session context and state management
    """
    def __init__(self):
        self.session_data = {
            "current_conversation": [],
            "active_documents": [],
            "emotional_state": "neutral",
            "topic_progression": [],
            "real_time_preferences": {}
        }
    
    def update_session_context(self, interaction_data):
        pass
    
    def get_session_context(self, session_id):
        pass
```

#### **Personal Memory (MongoDB)**
```python
class PersonalMemory:
    """
    Long-term user learning patterns and preferences
    """
    def __init__(self):
        self.user_profile = {
            "learning_style": "visual|auditory|kinesthetic",
            "difficulty_preferences": {},
            "topic_mastery_levels": {},
            "emotional_patterns": {},
            "study_habits": {},
            "personal_anecdotes": []
        }
    
    def update_learning_profile(self, user_id, interaction_data):
        pass
    
    def get_personalization_context(self, user_id):
        pass
```

#### **Knowledge Memory (Vector Database)**
```python
class KnowledgeMemory:
    """
    Semantic embeddings for content retrieval
    """
    def __init__(self):
        self.vector_stores = {
            "public_content": "exam_prep_embeddings",
            "user_documents": "personal_doc_embeddings", 
            "conversation_history": "dialogue_embeddings"
        }
    
    def semantic_search(self, query, vector_store, filters=None):
        pass
    
    def hybrid_search(self, query, multiple_stores, weights):
        pass
```

### Context Switching Logic
```python
class ContextManager:
    """
    Intelligent context switching between modes and memory layers
    """
    def determine_context(self, user_input, current_tab, session_memory):
        if current_tab == "pal":
            return self.merge_pal_context()
        elif current_tab == "book":
            return self.merge_book_context()
    
    def merge_pal_context(self):
        return {
            "public_knowledge": self.get_exam_content(),
            "user_memory": self.get_personal_memory(),
            "session_context": self.get_session_state(),
            "emotional_context": self.get_emotional_state()
        }
    
    def merge_book_context(self, document_id, permission_level):
        base_context = {"document_content": self.get_document(document_id)}
        
        if permission_level == "expanded":
            base_context.update({
                "external_knowledge": self.get_relevant_external(),
                "user_memory": self.get_personal_memory()
            })
        
        return base_context
```

---

## 🔧 Integration Points

### STT/TTS Service Integration
```python
class VoiceInterface:
    """
    Speech recognition and synthesis with emotional tone
    """
    def __init__(self):
        self.stt_config = {
            "language": "en-US",
            "continuous": True,
            "interim_results": False
        }
        
        self.tts_config = {
            "voice": "emotionally_adaptive",
            "rate": 0.9,
            "pitch": 1.1,
            "volume": 0.8
        }
    
    def process_speech_input(self, audio_stream):
        # Convert speech to text with context awareness
        pass
    
    def generate_speech_output(self, text, emotional_tone):
        # Text-to-speech with appropriate emotional coloring
        pass
```

### LLM Integration Strategy
```python
class LLMRouter:
    """
    Intelligent routing between local and cloud models
    """
    def __init__(self):
        self.model_hierarchy = [
            {"type": "local", "model": "sentence_transformers", "use_case": "embeddings"},
            {"type": "local", "model": "small_conv_model", "use_case": "simple_queries"},
            {"type": "cloud", "model": "gpt-4", "use_case": "complex_reasoning"},
            {"type": "cloud", "model": "claude", "use_case": "structured_analysis"}
        ]
    
    def route_request(self, request_type, complexity_level, privacy_level):
        # Route to appropriate model based on requirements
        pass
```

---

## ⚡ Performance & Scalability

### Caching Strategy
```python
class CacheManager:
    """
    Multi-tier caching for optimal performance
    """
    def __init__(self):
        self.cache_tiers = {
            "L1": "in_memory_frequent_queries",
            "L2": "redis_session_data", 
            "L3": "mongodb_persistent_cache"
        }
    
    def cache_strategy(self, data_type):
        strategies = {
            "document_embeddings": "L3_persistent",
            "user_preferences": "L2_session",
            "frequent_qa": "L1_memory",
            "conversation_context": "L2_session"
        }
        return strategies.get(data_type, "L3_persistent")
```

### Load Balancing
```python
class LoadBalancer:
    """
    Distribute load across services and models
    """
    def __init__(self):
        self.service_weights = {
            "pal_engine": 0.6,
            "book_engine": 0.3, 
            "memory_engine": 0.1
        }
    
    def route_request(self, request_type, current_load):
        # Intelligent request routing based on load and capacity
        pass
```

---

## 🔒 Security & Privacy

### Data Classification
```python
class DataClassifier:
    """
    Classify and handle data based on sensitivity
    """
    classification_levels = {
        "public": {
            "data": "exam_prep_materials",
            "storage": "public_vector_db",
            "encryption": "basic"
        },
        "personal": {
            "data": "learning_patterns", 
            "storage": "encrypted_mongodb",
            "encryption": "AES_256"
        },
        "sensitive": {
            "data": "user_documents",
            "storage": "encrypted_user_vault",
            "encryption": "end_to_end"
        }
    }
```

### Privacy Controls
```python
class PrivacyManager:
    """
    User privacy control and data management
    """
    def __init__(self):
        self.privacy_settings = {
            "memory_tracking": "user_controlled",
            "conversation_logging": "opt_in",
            "external_model_usage": "permission_based",
            "data_retention": "user_defined"
        }
    
    def enforce_privacy_settings(self, user_id, action):
        # Check and enforce user privacy preferences
        pass
```

---

## 🚀 Deployment Architecture

### Development Environment
```yaml
services:
  frontend:
    build: .
    ports: ["5173:5173"]
    environment:
      - VITE_API_URL=http://localhost:8003
  
  backend:
    build: ./backend
    ports: ["8003:8003"]
    environment:
      - MONGODB_URI=${MONGODB_URI}
      - REDIS_URL=${REDIS_URL}
  
  redis:
    image: redis:alpine
    ports: ["6379:6379"]
```

### Production Considerations
- **Microservices**: Each engine can be deployed independently
- **Auto-scaling**: Based on user load and computational requirements
- **CDN**: Static educational content delivery
- **Geographic Distribution**: Edge deployment for reduced latency
- **Model Optimization**: Quantized models for faster inference

---

This architecture provides a robust foundation for the dual-tab educational assistant with clear separation of concerns, scalable design, and comprehensive user experience management.
