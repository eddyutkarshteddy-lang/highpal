# 🏗️ HighPal Architecture Overview

**Version:** 5.1.0  
**Last Updated:** October 20, 2025  
**Status:** Production-Ready with Enhanced Voice Accuracy & Echo Prevention

---

## 🎯 System Overview

HighPal is an advanced AI educational assistant featuring **emotional intelligence**, **dual learning modes**, **sophisticated conversation management**, and **professional-grade voice accuracy**. The system combines cutting-edge voice processing with persistent conversation history, adaptive learning capabilities, and multi-locale speech recognition.

### Core Philosophy
- **Student-Centric Design**: Everything built around enhancing the learning experience
- **Emotional Intelligence**: AI that understands and adapts to student emotional states
- **Conversation Continuity**: Advanced memory management for seamless learning sessions
- **Dual Learning Modes**: Flexible approach supporting both guided and document-based learning
- **Voice Accuracy Excellence**: Sesame.com-level speech recognition with accent adaptation

---

## 🏛️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HighPal Frontend                         │
│                   (React 19.1.1)                          │
├─────────────────────────────────────────────────────────────┤
│  Landing Page  │  Chat Interface  │  Revision Mode         │
│  • Mode Select │  • Talks Sidebar │  • Quiz Generation     │
│  • Navigation  │  • Voice Overlay │  • Progress Tracking   │
└─────────────────────────────────────────────────────────────┘
                              │
                    HTTP/WebSocket API
                              │
┌─────────────────────────────────────────────────────────────┐
│                 HighPal Backend (FastAPI)                  │
├─────────────────────────────────────────────────────────────┤
│         Dual Engine Architecture                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ Pal Engine  │    │ Book Engine │    │Memory Engine│     │
│  │ • Exam Prep │    │ • Doc Q&A   │    │ • Conv Hist │     │
│  │ • Open Chat │    │ • Revision  │    │ • User Prof │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              │
                    External Services
                              │
┌─────────────────────────────────────────────────────────────┐
│  MongoDB Atlas  │  OpenAI GPT-4o  │  Azure Speech Services │
│  • Documents    │  • Conversations │  • Multi-Locale STT   │
│  • Conversations│  • Intelligence  │  • Neural TTS         │
│  • User Data    │  • Responses     │  • 6 Regional Accents │
│                 │                  │  • Vocabulary Hints   │
│                 │                  │  • Disfluency Removal │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 Frontend Architecture

### React Application Structure
```
src/
├── App.jsx                     # Main application with routing & voice
├── App.css                     # Global styling with voice animations
├── main.jsx                   # Application entry point
├── components/
│   ├── RevisionMode.jsx        # Quiz-based learning component
│   ├── RevisionMode.css        # Revision mode styling
│   ├── GPT5Chat.jsx           # Enhanced chat interface
│   └── TrainingInfo.jsx       # Training information display
└── services/
    ├── azureStreamingClient.js # Azure STT with multi-locale support
    ├── vadDetector.js          # Silero VAD ML-based detection
    └── interruptManager.js     # Conversation state machine
```

### Key Frontend Features (v5.1.0)
- **Advanced Conversation Management**: Persistent talks sidebar with conversation history
- **Multi-Locale Voice Processing**: 6 English accents with persistent user preference
- **Echo Prevention System**: 4-layer protection against AI self-interruption
- **Educational Speech Accuracy**: Vocabulary hints, disfluency removal, confidence scoring
- **Animated Voice UI**: State-based Pal avatar with real-time visual feedback
- **Mathematical Speech Processing**: Specialized handling for educational content
- **Real-time UI Updates**: Dynamic conversation status and progress indicators
- **Responsive Design**: Optimized for desktop and mobile learning environments

---

## 🔧 Backend Architecture

### FastAPI Server Structure
```
backend/
├── training_server.py           # Main FastAPI application
├── mongodb_config.py           # Database configuration
├── production_haystack_mongo.py # Document processing
├── requirements.txt            # Python dependencies
└── training_data/             # Training datasets
    ├── faq_data.json
    ├── product_overview.txt
    └── technical_details.txt
```

### API Architecture
- **Port**: 8003 (production-ready)
- **Framework**: FastAPI with async support
- **Documentation**: Auto-generated Swagger UI at `/docs`
- **Health Monitoring**: Comprehensive system status at `/health`

### Core Endpoints
```
GET  /health                    # System health check
POST /ask_question             # Main Q&A endpoint
POST /upload                   # Document upload
GET  /documents                # Document management
POST /book/revision            # Quiz generation
POST /book/revision/submit     # Quiz evaluation
```

---

## 🧠 AI Integration Architecture

### Multi-AI Orchestration
```
User Input → Voice Processing → Intent Analysis → AI Routing
    │             │                   │              │
    │         Azure STT          Conversation      GPT-4o
    │         Emotion AI         Classification   Response
    │             │                   │              │
    └─── Audio ←── Azure TTS ←─── Response ←─── Enhanced
                                 Synthesis        Content
```

### AI Services Integration
- **OpenAI GPT-4o**: Advanced conversation and educational content generation
- **Azure Speech Services**: Enterprise-grade STT/TTS with emotional expressiveness
- **Azure Text Analytics**: Emotion detection and sentiment analysis
- **Custom Processing**: Mathematical expression handling and educational optimization

---

## 💾 Data Architecture

### MongoDB Atlas Schema
```javascript
// Documents Collection
{
  _id: ObjectId,
  filename: String,
  content: String,
  metadata: {
    source_type: String,
    upload_date: Date,
    extraction_info: Object
  },
  embeddings: Array
}

// Conversations Collection
{
  _id: ObjectId,
  user_id: String,
  conversation_id: String,
  messages: [{
    role: String,
    content: String,
    timestamp: Date,
    emotion_context: Object
  }],
  created_at: Date,
  last_modified: Date
}
```

### Local Storage Management
- **Conversation History**: Persistent chat sessions with auto-save
- **User Preferences**: Learning mode preferences and settings
- **Session State**: Current conversation context and progress

---

## 🎤 Voice Processing Architecture

### Advanced Voice Pipeline with Echo Prevention
```
Microphone → VAD Detection → Speech Guard → Azure Recognition → Echo Filter
    │              │               │              │                │
    │       Silero VAD      Timing-based    Multi-locale      Word Match
    │       ML Model        Protection      STT (6 accents)    Algorithm
    │              │               │              │                │
    │              ├─ 2s Initial Block             └─ 70% Overlap Check
    │              ├─ 8s No-Mic Threshold          
    │              └─ 5s With-Mic Threshold        
    │                                                              │
    └── Response ← TTS Synthesis ← AI Processing ← Transcript Processing
         Audio      Azure Neural   GPT-4o           • Disfluency Removal
                   Voices          Response         • Confidence Scoring
                                                     • Math Recognition
```

### Voice Features (v5.1.0)
- **Multi-Locale Support**: 6 English accents (en-IN, en-US, en-GB, en-AU, en-CA, en-NZ)
- **Educational Vocabulary**: PhraseListGrammar with 30+ technical terms
- **Continuous Recognition**: Always-on Azure streaming for complete sentence capture
- **Echo Prevention**: Multi-layer protection against AI self-interruption
- **Confidence Display**: Real-time recognition quality feedback (0-100%)
- **Disfluency Removal**: Automatic "um", "uh" filtering via Azure TrueText
- **Barge-in Detection**: Natural interruption with strict echo guards
- **State-Based Processing**: Intelligent transcript handling based on conversation state

### VAD (Voice Activity Detection) System
```
@ricky0123/vad-web (Silero VAD Model)
├── Speech Start Detection (threshold: 0.85)
├── Guard Callback System (prevents echo)
├── False Positive Filtering (300ms min duration)
└── State Management Integration
```

### Echo Prevention Architecture
```
Layer 1: VAD Guard (Timing-Based)
├── 2s Initial Block (AI speech start)
├── 8s No-Mic-Data Threshold
└── 5s With-Mic-Data Threshold

Layer 2: AI Speech Text Matching
├── Word Tokenization
├── 70% Overlap Detection
└── Transcript Rejection

Layer 3: State-Based Filtering
├── Ignore during AI_SPEAKING
├── Process during USER_SPEAKING/PROCESSING
└── IDLE state recovery

Layer 4: Conversation State Check
└── Block all after conversationActiveRef = false
```

---

## 🔒 Security Architecture

### Environment Protection
```
.env files (Protected by .gitignore):
├── OPENAI_API_KEY
├── MONGODB_CONNECTION_STRING
├── AZURE_SPEECH_KEY
├── AZURE_TEXT_ANALYTICS_KEY
└── Other sensitive configurations
```

### Security Measures
- **API Key Protection**: All sensitive keys in environment variables
- **Data Encryption**: Secure transmission and storage
- **Input Validation**: Comprehensive request validation
- **Error Handling**: Secure error responses without data leakage

---

## 🚀 Deployment Architecture

### Development Environment
- **Frontend**: Vite dev server on port 5173
- **Backend**: FastAPI server on port 8003
- **Database**: MongoDB Atlas cloud connection
- **Voice Services**: Azure Speech Services integration

### Production Considerations
- **Containerization**: Docker support for both frontend and backend
- **Load Balancing**: Multi-instance deployment capability
- **Monitoring**: Health checks and performance monitoring
- **Scaling**: Horizontal scaling support for high-traffic scenarios

---

## 📊 Performance Architecture

### Optimization Strategies
- **Conversation Caching**: Intelligent conversation history management
- **Voice Processing**: Optimized audio processing and barge-in detection
- **Database Queries**: Efficient MongoDB queries with proper indexing
- **AI Response Time**: Smart timeout handling based on query complexity

### Resource Management
- **Memory Usage**: Efficient conversation history storage and cleanup
- **API Rate Limits**: Smart request throttling and retry mechanisms
- **Audio Processing**: Optimized real-time audio handling

---

## 🔄 Integration Points

### External Service Integration
- **MongoDB Atlas**: Cloud document and conversation storage
- **OpenAI API**: GPT-4o for intelligent responses
- **Azure Cognitive Services**: Speech and text analytics
- **Browser APIs**: Web Audio, Speech Recognition, LocalStorage

### Internal Service Communication
- **REST API**: JSON-based communication between frontend and backend
- **WebSocket**: Real-time communication for voice features
- **Event System**: Internal event handling for conversation management

---

## 📈 Scalability Considerations

### Current Capacity
- **Concurrent Users**: Designed for 100+ simultaneous conversations
- **Document Storage**: Unlimited through MongoDB Atlas
- **Conversation History**: Efficient storage with intelligent cleanup

### Future Scaling
- **Microservices**: Modular architecture ready for service separation
- **CDN Integration**: Static asset delivery optimization
- **Caching Layer**: Redis integration for enhanced performance
- **Multi-region**: Geographic distribution capability

---

*This architecture supports HighPal's mission to provide the world's most advanced emotionally intelligent educational AI assistant.*