# 🎓 HighPal - AI-Powered Educational Assistant

**HighPal** is an emotionally intelligent AI educational assistant designed for exam preparation and personalized learning. With two distinct learning modes, HighPal adapts to your study needs whether you're exploring topics or diving deep into your own materials.

![Version](https://img.shields.io/badge/version-3.0.0-blue)
![Status](https://img.shields.io/badge/status-active-green)
![MongoDB](https://img.shields.io/badge/database-MongoDB%20Atlas-green)
![AI](https://img.shields.io/badge/AI-Multi%20Model%20Integration-orange)

## ✨ Key Features

### 🎤 **Dual Learning Modes**
- **Learn with Pal**: Open-ended, emotionally intelligent conversation for exam prep
- **My Book**: Personalized Q&A based on your uploaded study materials

### 🧠 **Emotional Intelligence**
- Adaptive conversation flow based on your confidence and stress levels
- Memory-driven personalization that remembers your learning patterns
- Encouragement and motivation tailored to your progress

### 📚 **Smart Content Management** 
- Public educational content ingestion for comprehensive exam preparation
- Secure personal document processing with strict scope management
- Permission-based knowledge expansion between personal and public sources

### 🎯 **Exam Preparation Focus**
- Specialized support for CAT, GRE, GMAT, and other competitive exams
- Topic-specific guidance with difficulty progression
- Comprehensive revision modes with quiz-style assessments

## 🏗️ Enhanced Architecture

### Frontend (React + Vite)
- **Framework**: React 19.1.1 with dual-tab interface design
- **Tab 1 - Learn with Pal**: Open-ended conversation for exam preparation
- **Tab 2 - My Book**: Document-focused Q&A with your materials
- **Voice Interface**: WebKit Speech Recognition + Web Speech Synthesis
- **Memory Integration**: Persistent user context and learning patterns
- **Port**: Development server runs on `http://localhost:5173`

### Backend (Multi-Service Architecture)
- **Orchestration Layer**: `training_server.py` - FastAPI application with dual-engine routing
- **Pal Engine**: Emotionally intelligent conversation manager for exam prep
- **Book Engine**: Document-scoped Q&A with permission-based knowledge expansion
- **Memory Engine**: Multi-layered context management (session, personal, knowledge)
- **AI/ML Stack**: Multi-model integration (local + cloud LLMs, sentence transformers)
- **Port**: API server runs on `http://localhost:8003`

### Database & Storage
- **Knowledge Storage**: MongoDB Atlas with vector search capabilities
- **Memory Management**: Redis for session state, MongoDB for long-term memory
- **Document Processing**: Advanced multi-format extraction with security scanning
- **Public Content**: Curated educational materials and exam preparation resources

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm/yarn
- Python 3.8+
- MongoDB Atlas account (free tier works)

### 1. Clone the Repository
```bash
git clone https://github.com/eddyutkarshteddy-lang/highpal.git
cd highpal
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Configure MongoDB Atlas connection
cp .env.example .env
# Edit .env file with your MongoDB connection string
```

### 3. Frontend Setup  
```bash
cd ../  # Return to root directory
npm install
```

### 4. Start HighPal
```bash
# Terminal 1: Start the training server
cd backend
python training_server.py
# ✅ Server starts on http://localhost:8003

# Terminal 2: Start frontend
npm run dev
# ✅ Frontend starts on http://localhost:5173
```

## 📖 How to Use HighPal

### � **Learn with Pal Tab**
1. **Start Exam Preparation**: Say "I want to prepare for the CAT exam"
2. **Guided Learning**: Pal provides topic suggestions and adaptive dialogue
3. **Memory-Driven Support**: Pal remembers your weak areas and study patterns
4. **Emotional Intelligence**: Receive encouragement and motivation based on your progress
5. **Multi-Turn Conversations**: Engage in natural, flowing educational discussions

### 📚 **My Book Tab**  
1. **Upload Your Materials**: Click **+** and select your PDF or Word documents
2. **Document-Scoped Q&A**: Ask questions strictly from your uploaded content
3. **Knowledge Expansion**: Grant permission to blend your content with external knowledge
4. **Revision Mode**: Trigger quiz-style sessions after completing chapters
5. **Progress Tracking**: Monitor comprehension and receive personalized feedback

### 🎤 **Voice Interaction**
1. **Click the microphone** to start voice conversation in either tab
2. **Natural Speech**: Talk to Pal as you would with a human tutor
3. **Context Awareness**: Pal maintains conversation context across interactions
4. **Text-to-Speech**: Listen to responses with emotionally appropriate tone

### 🧠 **Memory & Personalization**
- **Learning Patterns**: Pal tracks your study habits and preferences
- **Difficulty Adaptation**: Content difficulty adjusts based on your performance
- **Personal Anecdotes**: Share stories that Pal remembers for better rapport
- **Cross-Session Continuity**: Pick up conversations where you left off
Train Pal with educational content from the web:
```bash
POST http://localhost:8003/train/pdf-urls
{
  "urls": [
    "https://arxiv.org/pdf/2023.12345.pdf",
    "https://example.edu/research-paper.pdf"
  ]
}
```

## 🛠️ Configuration

### Environment Variables (.env)
```bash
# MongoDB Atlas (Required)
MONGODB_CONNECTION_STRING=mongodb+srv://<username>:<password>@cluster.mongodb.net/

# Database Settings  
MONGODB_DATABASE=highpal_documents
MONGODB_COLLECTION=documents
STORAGE_TYPE=mongodb

# OpenAI (Optional - for enhanced responses)
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### MongoDB Atlas Setup
1. **Create free account** at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. **Create cluster** (M0 Free tier is sufficient)
3. **Add database user** with read/write permissions
4. **Whitelist IP address** (or use 0.0.0.0/0 for development)
5. **Copy connection string** and add to `.env` file

## 📊 Core API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server health check and MongoDB status |
| POST | `/upload` | Upload documents (PDF, text) for Pal's knowledge |
| POST | `/ask_question` | Ask Pal a question - get AI response |
| GET | `/documents` | List uploaded documents |
| POST | `/train/pdf-urls` | Train Pal with PDF URLs |
| GET | `/training-guide` | Training documentation |

## 🧪 Testing

### Test Pal's Connection
```bash
curl http://localhost:8003/health
# Should return: {"status":"healthy","mongodb":"connected","training_ready":true}
```

### Test Pal's Intelligence
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"question":"What is machine learning?"}' \
  http://localhost:8003/ask_question
```

### Test Q&A
```bash
curl -X POST http://localhost:8003/ask_question \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'
```

## 🔧 Development

## 📁 Project Structure (Simplified)

```
highpal/
├── src/                    # Frontend React application
│   ├── components/         # UI components (minimal, focused)
│   ├── App.jsx            # Main app with Pal voice interface
│   └── main.jsx           # Application entry point
├── backend/               # Clean Python backend
│   ├── training_server.py # 🎯 Main server (only server needed)
│   ├── production_haystack_mongo.py # MongoDB integration
│   ├── training_endpoints.py # PDF URL training
│   ├── pdf_extractor.py   # Advanced PDF processing
│   ├── pdf_url_trainer.py # Web PDF training
│   └── requirements.txt   # Python dependencies
├── public/                # Static assets
└── package.json          # Node.js dependencies
```

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
- **📚 Hidden Document Lists**: Clean AI responses without showing training documents
- **🔧 Optimized Codebase**: 65% smaller backend, focused functionality
- **✨ Better PDF Processing**: Advanced multi-library PDF extraction

### ✅ Version 2.0.0 - Foundation Features
- **Fixed Connection Issues**: Stable frontend-backend communication
- **Document Persistence**: MongoDB Atlas integration working
- **Voice Assistant**: Pal voice interface implemented
- **Conversation History**: Complete chat functionality

### 🔄 Next Planned Features
- Continuous voice conversation mode
- Emotional intelligence for student support
- ElevenLabs premium voice integration
- Mobile app optimization
- Advanced learning analytics

## 🤝 Contributing

1. **Fork** the repository
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit changes**: `git commit -m 'Add amazing feature'`
4. **Push to branch**: `git push origin feature/amazing-feature`
5. **Open Pull Request**: Describe your changes clearly

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support & Community

- **Issues**: [GitHub Issues](https://github.com/eddyutkarshteddy-lang/highpal/issues)
- **Documentation**: Check the `/docs` endpoint when server is running
- **MongoDB Setup**: See [MONGODB_SETUP.md](backend/MONGODB_SETUP.md)

---
##  Support & Community

- ** Issues**: [GitHub Issues](https://github.com/eddyutkarshteddy-lang/highpal/issues)
- ** API Docs**: Visit `http://localhost:8003/docs` when server is running
- ** MongoDB Setup**: See [MONGODB_SETUP.md](backend/MONGODB_SETUP.md)
- ** Training Guide**: Available at `http://localhost:8003/training-guide`

##  Why Choose HighPal?

- ** Focused on Learning**: Designed specifically for students and researchers
- ** Natural Interaction**: Talk to Pal like a real study partner
- ** Gets Smarter**: Learns from your documents and stays updated
- ** Always Available**: Cloud storage means your assistant is always ready
- ** Simple Setup**: One server, clean architecture, easy deployment

---

**Built with  for students and researchers worldwide**

*"Every question is a step toward understanding"* - HighPal Team
