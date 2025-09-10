# 🎓 HighPal - Emotionally Intelligent AI Educational Assistant

**HighPal** is the first AI educational assistant that understands both what you need to learn AND how you feel while learning. Combining advanced emotional intelligence with comprehensive educational support, HighPal adapts to your emotional state and learning needs in real-time.

![Version](https://img.shields.io/badge/version-4.0.0-blue)
![Status](https://img.shields.io/badge/status-enhanced-green)
![AI](https://img.shields.io/badge/AI-Emotional%20Intelligence-purple)
![Voice](https://img.shields.io/badge/Voice-Emotion%20Aware-orange)

## ✨ Revolutionary Features

### � **Emotional Intelligence (NEW)**
- **Real-time emotion detection** from voice tone and speech patterns
- **Adaptive responses** that match your emotional state and learning needs
- **Stress intervention** - automatic support when you're overwhelmed
- **Confidence building** - personalized encouragement based on your progress
- **Emotional learning analytics** - track your emotional journey over time

### 🎤 **Enhanced Dual Learning Modes**
- **Learn with Pal**: Emotionally aware AI tutor for competitive exam preparation
  - Specialized for JEE, NEET, CAT, UPSC, GATE, and other Indian competitive exams
  - Stress-aware explanations and motivational support
  - Real-time emotional adaptation during conversations
- **Learn from My Book**: Document-based Q&A with emotional context
  - Upload PDFs and get emotionally intelligent explanations
  - Adaptive teaching pace based on your comprehension and stress levels

### 🧠 **Advanced AI Integration**
- **Hume AI**: Industry-leading voice emotion detection and analysis
- **OpenAI GPT**: Advanced educational content generation and reasoning
- **Emotional Response Engine**: Combines academic knowledge with emotional support
- **Voice Synthesis**: Emotionally appropriate voice responses (calm, encouraging, energetic)

### 📊 **Emotional Learning Analytics**
- Daily emotional journey visualization
- Stress pattern identification and intervention
- Confidence building progress tracking
- Personalized emotional insights and recommendations

## 🏗️ Next-Generation Architecture

### Frontend (React + Emotional UI)
- **Framework**: React 19.1.1 with emotion-adaptive interface
- **Emotional Interface**: UI adapts colors, animations, and layout based on detected emotions
- **Voice Integration**: Emotion-aware voice recording and playback
- **Mood Tracking**: Daily emotional check-ins and progress visualization
- **Real-time Emotion Display**: Live emotion indicators during conversations
- **Port**: Development server runs on `http://localhost:5173`

### Backend (Emotional AI Orchestration)
- **Main Server**: `training_server.py` - Enhanced FastAPI with emotion processing
- **AI Service Layer**: Multi-platform AI integration and orchestration
  - **Hume AI Client**: Voice emotion detection and analysis
  - **OpenAI Client**: Educational content generation and reasoning
  - **Emotion Processor**: Combines voice and text emotion analysis
  - **Response Adapter**: Generates emotionally appropriate responses
- **Voice Pipeline**: Emotion-aware speech processing and synthesis
- **Session Management**: Emotional state tracking and user profiling
- **Port**: API server runs on `http://localhost:8000`

- **OpenAI Integration**: GPT-4 for educational content, explanations, and reasoning
- **Emotion Database**: Emotional history tracking and pattern analysis
- **Adaptive Engine**: Real-time response adjustment based on emotional feedback

### Database & Emotional Memory
- **MongoDB Atlas**: Document storage, user profiles, and emotional analytics
- **Emotional History**: Track stress, confidence, and learning progression over time
- **User Profiles**: Personalized emotional baselines and learning preferences
- **Session Context**: Real-time emotional state management during conversations
- **Security**: Encrypted emotional data with privacy-first design

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.8+
- MongoDB Atlas account (free tier works)
- **Hume AI API Key** (for emotion detection)
- **OpenAI API Key** (for educational content generation)

### 1. Clone the Repository
```bash
git clone https://github.com/eddyutkarshteddy-lang/highpal.git
cd highpal
```

### 2. Backend Setup & AI Configuration
```bash
cd backend
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env file with your configuration:
# MONGODB_URI=your_mongodb_connection_string
# HUME_API_KEY=your_hume_ai_api_key
# OPENAI_API_KEY=your_openai_api_key
# ENVIRONMENT=development
```

### 3. Frontend Setup  
```bash
cd ../  # Return to root directory
npm install
```

### 4. Start HighPal with Emotional Intelligence
```bash
# Terminal 1: Start the enhanced training server
cd backend
python training_server.py
# ✅ Server starts on http://localhost:8000 with emotion processing

# Terminal 2: Start emotion-aware frontend
npm run dev
# ✅ Frontend starts on http://localhost:5173 with emotional interface
```

## 🎭 Emotional Intelligence in Action

### 🗣️ **Voice Emotion Detection**
- **Real-time Analysis**: HighPal detects your emotional state as you speak
- **Emotional Indicators**: Live emotion display during conversations
- **Stress Detection**: Automatic intervention when you sound overwhelmed
- **Confidence Building**: Encouraging responses when you need motivation

### 💬 **Emotionally Adaptive Responses**
- **Calm & Patient**: When you're confused or struggling with concepts
- **Energetic & Motivating**: When you need encouragement or confidence boost
- **Supportive & Understanding**: When you're stressed or anxious about exams
- **Challenging & Engaging**: When you're confident and ready for advanced topics

## 📖 Enhanced Learning Experience

### 🎯 **Learn with Pal (Emotion-Aware)**
1. **Voice-Enabled Learning**: Speak naturally - HighPal detects your emotions and adapts
2. **Emotional Check-ins**: Daily mood tracking and emotional progress visualization
3. **Stress-Aware Tutoring**: Automatic pace adjustment based on your stress levels
4. **Confidence Building**: Personalized encouragement and achievement recognition
5. **Exam Preparation**: Emotionally intelligent support for JEE, NEET, CAT, UPSC, GATE
6. **Emotional Analytics**: Track your learning confidence and stress patterns over time

### 📚 **Learn from My Book (Context-Aware)**  
1. **Upload Your Materials**: Click **+** and select your PDF or Word documents
2. **Emotional Document Analysis**: HighPal adapts explanations based on your comprehension stress
3. **Adaptive Explanations**: Simpler or more detailed based on your emotional response
4. **Stress-Free Learning**: Automatic pacing when document content seems overwhelming
5. **Progress Tracking**: Monitor comprehension and receive emotionally supportive feedback

### 🎤 **Emotion-Aware Voice Interaction**
1. **Click the microphone** to start emotionally intelligent voice conversation
2. **Emotion Detection**: HighPal analyzes your voice tone and adjusts responses
3. **Adaptive Speaking**: HighPal's voice tone matches your emotional needs
4. **Real-time Emotional Feedback**: Live emotion indicators during conversations
5. **Stress Intervention**: Automatic calming responses when you sound overwhelmed

### 🧠 **Emotional Memory & Personalization**
- **Emotional Baselines**: HighPal learns your typical emotional patterns
- **Learning Confidence Tracking**: Monitor your confidence growth over time
- **Stress Pattern Recognition**: Identify when you typically feel overwhelmed
- **Personalized Emotional Support**: Tailored encouragement based on your history
- **Cross-Session Emotional Continuity**: Remember your emotional state between sessions

## 🔧 API Endpoints (Enhanced for Emotions)

### Core Chat Endpoints
```bash
# Emotionally intelligent chat with Pal
POST http://localhost:8000/chat/pal
{
  "message": "I'm stressed about the JEE exam",
  "voice_emotion_data": {...}  # Hume AI emotion analysis
}

# Document-based Q&A with emotional context
POST http://localhost:8000/chat/book
{
  "message": "Explain this concept",
  "document_id": "doc_123",
  "emotional_state": "confused"
}

# Real-time emotion analysis
POST http://localhost:8000/analyze/emotion
{
  "audio_data": "base64_encoded_audio",
  "text": "optional text for context"
}
```

### Emotional Analytics Endpoints
```bash
# Get emotional learning analytics
GET http://localhost:8000/analytics/emotional-progress

# Daily emotional check-in
POST http://localhost:8000/checkin/emotional-state
{
  "mood": "stressed",
  "confidence_level": 3,
  "learning_goals": ["calculus", "physics"]
}
```

### Training & Content Management
```bash
# Train with emotional context understanding
POST http://localhost:8000/train/pdf-urls
{
  "urls": ["https://example.com/paper.pdf"],
  "emotional_context": "exam_preparation"
}
```

## 🛠️ Enhanced Configuration

### Environment Variables (.env)
```bash
# AI Service Keys
HUME_API_KEY=your_hume_ai_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# MongoDB Atlas (Required)
MONGODB_CONNECTION_STRING=mongodb+srv://<username>:<password>@cluster.mongodb.net/

# Emotional Intelligence Settings
EMOTION_DETECTION_ENABLED=true
VOICE_EMOTION_SENSITIVITY=medium  # low, medium, high
EMOTIONAL_MEMORY_RETENTION=90_days

# Database Settings  
MONGODB_DATABASE=highpal_emotional_learning
MONGODB_COLLECTION=documents
MONGODB_EMOTIONAL_COLLECTION=emotional_history
STORAGE_TYPE=mongodb

# Server Configuration
PORT=8000  # Updated from 8003 for emotional features
DEBUG_MODE=true
EMOTIONAL_LOGGING=true
```

### MongoDB Atlas Setup for Emotional Intelligence
1. **Create free account** at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. **Create cluster** (M0 Free tier is sufficient)
3. **Add database user** with read/write permissions  
4. **Create collections**: 
   - `documents` (existing document storage)
   - `emotional_history` (emotion tracking)
   - `user_profiles` (emotional baselines)
   - `conversation_analytics` (emotional conversation data)
5. **Whitelist IP address** (or use 0.0.0.0/0 for development)
6. **Copy connection string** and add to `.env` file

## 🔧 Enhanced API Reference

### Emotional Intelligence Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze/voice-emotion` | Real-time voice emotion detection |
| POST | `/chat/pal-emotional` | Emotionally aware AI tutoring |
| POST | `/chat/book-emotional` | Document Q&A with emotional adaptation |
| GET | `/analytics/emotional-dashboard` | Emotional learning progress dashboard |
| POST | `/checkin/daily-mood` | Daily emotional check-in tracking |
| GET | `/profile/emotional-baseline` | User's emotional learning patterns |

### Enhanced Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Enhanced health check with AI service status |
| POST | `/upload` | Upload documents with emotional context |
| POST | `/ask_question` | Emotionally intelligent Q&A responses |
| GET | `/documents` | List documents with emotional metadata |
| POST | `/train/pdf-urls` | Train with emotional learning context |
| GET | `/training-guide` | Enhanced training docs with emotional features |

## 🧪 Testing Emotional Intelligence

### Test Emotional Health Check
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","mongodb":"connected","hume_ai":"connected","openai":"connected","emotional_processing":"active"}
```

### Test Emotional Intelligence
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"question":"I am stressed about calculus","emotional_context":"anxious"}' \
  http://localhost:8000/chat/pal-emotional
```

### Test Voice Emotion Detection
```bash
curl -X POST http://localhost:8000/analyze/voice-emotion \
  -H "Content-Type: application/json" \
  -d '{"audio_data": "base64_encoded_audio_data"}'
```

### Test Emotional Analytics
```bash
curl http://localhost:8000/analytics/emotional-dashboard
# Returns: emotional progress, stress patterns, confidence trends
```

## 🚀 Development & Deployment

### Development Mode
- **Hot Reload**: Both frontend and backend support live code updates
- **Emotional Debug Mode**: Detailed emotion detection logging
- **API Testing**: Swagger UI available at `http://localhost:8000/docs`
- **Emotional Monitoring**: Real-time emotion analysis dashboard

### Production Deployment
- **Docker Support**: Multi-service containers for all AI integrations
- **Environment Separation**: Staging and production emotional AI configurations
- **API Rate Limiting**: Managed quota for Hume AI and OpenAI services
- **Security**: Encrypted emotional data storage and transmission

## 📁 Enhanced Project Structure

```
highpal/
├── src/                           # Emotion-aware React frontend
│   ├── components/               
│   │   ├── EmotionalInterface.jsx # Real-time emotion display
│   │   ├── VoiceEmotionRecorder.jsx # Voice emotion capture
│   │   ├── EmotionalDashboard.jsx # Progress tracking
│   │   ├── SearchResults.jsx     # Enhanced with emotional context
│   │   └── TrainingInfo.jsx      # Emotional training insights
│   ├── App.jsx                   # Enhanced with emotional intelligence
│   ├── App.css                   # Emotion-adaptive UI styles
│   └── main.jsx                  # Entry point with emotion setup
├── backend/                      # Multi-AI orchestration backend
│   ├── training_server.py        # 🎯 Enhanced main server (port 8000)
│   ├── ai_integration/           # NEW: AI service integration
│   │   ├── hume_client.py        # Hume AI emotion detection
│   │   ├── openai_client.py      # OpenAI content generation
│   │   ├── emotion_analyzer.py   # Emotion processing engine
│   │   └── response_adapter.py   # Emotional response generation
│   ├── emotional_features/       # NEW: Emotional intelligence core
│   │   ├── emotion_tracker.py    # Emotional state management
│   │   ├── stress_detector.py    # Stress intervention system
│   │   ├── confidence_builder.py # Confidence tracking & building
│   │   └── voice_processor.py    # Voice emotion analysis
│   ├── database/                 # Enhanced data management
│   │   ├── mongodb_config.py     # Updated for emotional data
│   │   ├── emotional_schema.py   # NEW: Emotional data schemas
│   │   └── user_profiles.py      # NEW: Emotional user profiles
│   ├── production_haystack_mongo.py # MongoDB integration
│   ├── pdf_extractor.py          # Advanced PDF processing
│   └── requirements.txt          # Updated dependencies
├── public/                       # Static assets with emotional themes
└── package.json                 # Updated Node.js dependencies
```

## 🎭 Emotional Intelligence Features

### Real-time Emotion Detection
- **48+ Distinct Emotions**: Powered by Hume AI's advanced voice analysis
- **Live Emotional Feedback**: Real-time emotion indicators during conversations  
- **Stress Pattern Recognition**: Automatic detection of learning stress and overwhelm
- **Confidence Tracking**: Monitor and build learning confidence over time

### Adaptive Learning Experience
- **Emotionally Aware Responses**: AI adapts tone and content based on your emotional state
- **Stress Intervention**: Automatic calming and supportive responses when needed
- **Motivation Engine**: Personalized encouragement based on your progress and confidence
- **Pacing Adaptation**: Learning speed adjusts to your emotional readiness

### Emotional Analytics & Insights
- **Daily Emotional Journey**: Visualize your emotional patterns while learning
- **Stress vs. Progress Correlation**: Understand how emotions affect your learning
- **Confidence Building Tracking**: Monitor your academic confidence growth
- **Personalized Emotional Insights**: Tailored recommendations for emotional learning optimization

### 🎯 Simplified Development
- **Single Server**: Only `training_server.py` needs to run
- **Clean Frontend**: Focused on conversation with Pal
- **Auto-reload**: Frontend hot reloads, backend manual restart
- **Persistent Storage**: MongoDB Atlas handles all data

## 📈 Recent Updates (September 2025)

### ✅ Version 2.1.0 - Simplified & Optimized
- **🧹 Massive Cleanup**: Removed 31 unused server files and components
- **🎯 Single Server Architecture**: Consolidated to `training_server.py` only
- **🎤 Enhanced Pal Interface**: Improved voice assistant experience
## 🎯 Roadmap & Recent Updates

### 🚀 Version 4.0.0 - Emotional Intelligence Revolution (Current)
- **🎭 Real-time Emotion Detection**: Hume AI integration for voice emotion analysis
- **🧠 Emotionally Adaptive AI**: OpenAI + Hume AI combined for intelligent responses
- **📊 Emotional Analytics**: Track stress, confidence, and learning emotional patterns
- **🗣️ Voice Emotion Processing**: Real-time emotional feedback during conversations
- **💚 Stress Intervention System**: Automatic calming responses for overwhelmed students
- **🎯 Confidence Building Engine**: Personalized encouragement and motivation system
- **🔄 Multi-AI Orchestration**: Seamless integration of multiple AI services

### ✅ Version 3.0.0 - Enhanced Learning Experience  
- **📚 Hidden Document Lists**: Clean AI responses without showing training documents
- **🔧 Optimized Codebase**: 65% smaller backend, focused functionality
- **✨ Better PDF Processing**: Advanced multi-library PDF extraction

### ✅ Version 2.0.0 - Foundation Features
- **Fixed Connection Issues**: Stable frontend-backend communication
- **Document Persistence**: MongoDB Atlas integration working
- **Voice Assistant**: Pal voice interface implemented
- **Conversation History**: Complete chat functionality

### 🔮 Next Planned Features (Version 5.0.0)
- **📚 Revision Mode Integration (HIGH PRIORITY)**: Complete quiz-based learning system
  - Finish main view routing for seamless navigation between chat and revision modes
  - Add emotional intelligence to quiz feedback and encouragement
  - Integrate quiz performance analytics and learning progress tracking
- **Advanced Emotional Modeling**: Predictive emotional state analysis
- **Multi-modal Emotion Detection**: Text + voice + facial expression analysis
- **Personalized Learning Paths**: AI-generated study plans based on emotional preferences
- **Group Learning Emotional Intelligence**: Emotion-aware collaborative learning features
- **Advanced Voice Synthesis**: Emotionally expressive AI voice responses
- **Mobile Emotional Intelligence**: Native mobile app with full emotional features

## 🤝 Contributing to Emotional AI Education

We welcome contributions to make HighPal the most emotionally intelligent educational AI assistant!

### Priority Contribution Areas
1. **📚 Revision Feature Completion**: Complete quiz-based learning system integration (IMMEDIATE)
2. **Emotional Intelligence Features**: Enhance emotion detection and response algorithms
3. **AI Integration**: Improve Hume AI and OpenAI orchestration
4. **User Experience**: Emotional interface design and interaction improvements
5. **Analytics & Insights**: Advanced emotional learning analytics
6. **Performance Optimization**: Emotional processing speed and accuracy

### Development Process
1. **Fork** the repository
2. **Create feature branch**: `git checkout -b feature/emotional-enhancement`
3. **Commit changes**: `git commit -m 'Add emotional intelligence feature'`
4. **Test emotional features**: Ensure emotion detection and response work correctly
5. **Push to branch**: `git push origin feature/emotional-enhancement`
6. **Open Pull Request**: Describe emotional intelligence improvements clearly

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Community

## 🆘 Support & Community

- **🎭 Emotional AI Support**: [GitHub Issues](https://github.com/eddyutkarshteddy-lang/highpal/issues) for emotional intelligence features
- **📚 Enhanced API Docs**: Visit `http://localhost:8000/docs` for comprehensive emotional AI documentation
- **🧠 Emotional Setup Guide**: See [EMOTIONAL_AI_SETUP.md](backend/EMOTIONAL_AI_SETUP.md)
- **📊 Emotional Analytics**: Access `http://localhost:8000/emotional-dashboard` for learning insights

## 🌟 Why Choose HighPal's Emotional Intelligence?

### 🎯 **World's First Emotionally Intelligent Educational AI**
- **Revolutionary Approach**: Combines academic knowledge with emotional understanding
- **Real Student Impact**: Reduces learning stress while building confidence
- **Scientifically Backed**: Uses advanced emotion detection and response psychology

### 🧠 **Advanced AI Technology Stack**
- **Hume AI Integration**: Industry-leading voice emotion detection with 48+ emotions
- **OpenAI Enhancement**: GPT-4 powered educational content with emotional context
- **Emotional Memory**: Learns your emotional patterns and adapts over time
- **Real-time Processing**: Instant emotional feedback and response adaptation

### 🎓 **Educational Excellence with Emotional Support**
- **Exam Stress Management**: Specialized support for JEE, NEET, CAT, UPSC, GATE preparation
- **Confidence Building**: Systematic approach to building academic self-confidence
- **Personalized Learning**: Adapts to your emotional state and learning preferences
- **24/7 Emotional Support**: Always available when you need encouragement or stress relief

### 🚀 **Future-Ready Learning Platform**
- **Cutting-edge Technology**: Stay ahead with the latest in AI and emotional intelligence
- **Continuous Evolution**: Regular updates with new emotional intelligence features
- **Student-Centric Design**: Built specifically for emotionally aware learning experiences
- **Privacy-First**: Your emotional data is encrypted and secure

---

*HighPal: Where Artificial Intelligence meets Emotional Intelligence for the ultimate learning experience* 🎓❤️
- ** Gets Smarter**: Learns from your documents and stays updated
- ** Always Available**: Cloud storage means your assistant is always ready
- ** Simple Setup**: One server, clean architecture, easy deployment

---

**Built with  for students and researchers worldwide**

*"Every question is a step toward understanding"* - HighPal Team
