# 🎭 HighPal Emotional Intelligence Setup Guide

This guide covers the setup and configurati# Additional dependencies for emotional intelligence
pip install hume-ai
pip install openai>=1.50.0  # Updated for GPT-5 support
pip install azure-cognitiveservices-speech
pip install websockets
pip install asyncio
pip install python-multipartighPal's revolutionary emotional intelligence features, combining Hume AI's voice emotion detection with Azure Speech Services for enterprise-grade voice processing and OpenAI's contextual content generation.

## 🧠 Overview

HighPal's emotional intelligence system consists of four main components:

1. **Hume AI Integration** - Real-time voice emotion detection (48+ emotions)
2. **Azure Speech Services** - Enterprise STT/TTS with emotional expressiveness
3. **OpenAI GPT-5** - Latest AI model for emotionally aware content generation and responses
4. **Emotional Processing Engine** - Combines voice analysis with adaptive learning

## 🔑 API Keys & Authentication

### Required API Keys

```bash
# .env file configuration
HUME_API_KEY=your_hume_ai_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
AZURE_SPEECH_KEY=your_azure_speech_services_key_here
AZURE_SPEECH_REGION=your_azure_region_here
MONGODB_URI=your_mongodb_connection_string
```

### Getting Your API Keys

#### Hume AI API Key
1. Visit [Hume AI Console](https://console.hume.ai/)
2. Create an account or sign in
3. Navigate to "API Keys" in your dashboard
4. Generate a new API key for voice emotion detection
5. Copy the key to your `.env` file

#### Azure Speech Services Key
1. Visit [Azure Portal](https://portal.azure.com)
2. Create or sign in to your Azure account
3. Create a new "Speech" resource
4. Navigate to "Keys and Endpoint" section
5. Copy Key 1 and Region to your `.env` file

#### OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Navigate to "API Keys" section
4. Generate a new API key
5. Copy the key to your `.env` file

## 🏗️ Architecture Components

### Backend Structure
```
backend/
├── ai_integration/           # NEW: AI service integration
│   ├── hume_client.py        # Hume AI emotion detection
│   ├── openai_client.py      # OpenAI content generation
│   ├── azure_speech_client.py # Azure Speech Services STT/TTS
│   ├── emotion_analyzer.py   # Emotion processing engine
│   └── response_adapter.py   # Emotional response generation
├── emotional_features/       # NEW: Emotional intelligence core
│   ├── emotion_tracker.py    # Emotional state management
│   ├── stress_detector.py    # Stress intervention system
│   ├── confidence_builder.py # Confidence tracking & building
│   └── voice_processor.py    # Azure-powered voice emotion analysis
├── database/                 # Enhanced data management
│   ├── mongodb_config.py     # Updated for emotional data
│   ├── emotional_schema.py   # NEW: Emotional data schemas
│   └── user_profiles.py      # NEW: Emotional user profiles
└── training_server.py        # Enhanced main server
```

### Frontend Enhancements
```
src/
├── components/               
│   ├── EmotionalInterface.jsx # Real-time emotion display
│   ├── AzureVoiceRecorder.jsx # Azure Speech Services voice capture
│   ├── EmotionalDashboard.jsx # Progress tracking
│   ├── SearchResults.jsx     # Enhanced with emotional context
│   └── TrainingInfo.jsx      # Emotional training insights
├── App.jsx                   # Enhanced with emotional intelligence
├── App.css                   # Emotion-adaptive UI styles
└── main.jsx                  # Entry point with emotion setup
```

## 🛠️ Installation & Setup

### 1. Install Enhanced Dependencies

```bash
cd backend
pip install -r requirements.txt

# Additional dependencies for emotional intelligence
pip install hume-ai
pip install openai>=1.0.0
pip install azure-cognitiveservices-speech
pip install websockets
pip install asyncio
pip install python-multipart
```

### 2. MongoDB Emotional Schema Setup

```python
# Create collections for emotional data
collections_to_create = [
    "documents",              # Existing document storage
    "emotional_history",      # Emotion tracking over time
    "user_profiles",          # Emotional baselines and preferences
    "conversation_analytics", # Emotional conversation data
    "stress_patterns",        # Stress detection and intervention logs
    "confidence_metrics"      # Confidence building progress
]
```

### 3. Environment Configuration

```bash
# Enhanced .env configuration
HUME_API_KEY=your_hume_ai_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
AZURE_SPEECH_KEY=your_azure_speech_services_key_here
AZURE_SPEECH_REGION=your_azure_region_here
MONGODB_URI=your_mongodb_connection_string

# Emotional Intelligence Settings
EMOTION_DETECTION_ENABLED=true
VOICE_EMOTION_SENSITIVITY=medium  # low, medium, high
EMOTIONAL_MEMORY_RETENTION=90_days
STRESS_INTERVENTION_THRESHOLD=7   # 1-10 scale
CONFIDENCE_BUILDING_ENABLED=true

# Azure Speech Services Settings
AZURE_SPEECH_VOICE=en-US-JennyNeural  # Emotionally expressive voice
AZURE_SPEECH_RATE=medium
AZURE_SPEECH_STYLE=cheerful          # cheerful, sad, excited, calm

# Server Configuration
PORT=8000  # Updated from 8003 for emotional features
DEBUG_MODE=true
EMOTIONAL_LOGGING=true
```

## 🎤 Voice Processing with Azure Speech Services

### Azure Speech Services Configuration

```python
# azure_speech_client.py example configuration
import azure.cognitiveservices.speech as speechsdk
import asyncio

class AzureSpeechProcessor:
    def __init__(self, subscription_key, region):
        self.speech_config = speechsdk.SpeechConfig(
            subscription=subscription_key, 
            region=region
        )
        self.setup_emotional_voices()
        
    def setup_emotional_voices(self):
        """Configure emotionally expressive voices"""
        self.voice_styles = {
            'calm': 'en-US-JennyNeural',
            'encouraging': 'en-US-AriaNeural', 
            'energetic': 'en-US-GuyNeural',
            'cheerful': 'en-US-JennyNeural'
        }
        
    async def speech_to_text(self, audio_stream):
        """Convert speech to text using Azure STT"""
        audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config, 
            audio_config=audio_config
        )
        
        result = await speech_recognizer.recognize_once_async()
        return {
            'text': result.text,
            'confidence': result.properties.get('SPEECH_RECOGNITION_CONFIDENCE')
        }
        
    async def text_to_speech(self, text, emotion_style='calm'):
        """Convert text to emotionally appropriate speech"""
        voice_name = self.voice_styles.get(emotion_style, 'en-US-JennyNeural')
        
        # Configure SSML for emotional expression
        ssml = f"""
        <speak version='1.0' xml:lang='en-US'>
            <voice name='{voice_name}'>
                <mstts:express-as style='{emotion_style}'>
                    {text}
                </mstts:express-as>
            </voice>
        </speak>
        """
        
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )
        
        result = await synthesizer.speak_ssml_async(ssml)
        return result.audio_data
```

## 🎭 Emotion Detection with Hume AI

### Hume AI Configuration

```python
# hume_client.py example configuration
from hume import HumeVoiceClient
import asyncio

class EmotionDetector:
    def __init__(self, api_key):
        self.client = HumeVoiceClient(api_key)
        
    async def analyze_voice_emotion(self, audio_data):
        """
        Analyze voice emotion from audio data
        Returns: Dictionary with 48+ emotion scores
        """
        result = await self.client.analyze_audio(audio_data)
        return self.process_emotion_scores(result)
        
    def process_emotion_scores(self, raw_results):
        """
        Process raw Hume AI results into actionable emotional insights
        """
        emotions = {}
        predictions = raw_results.get('predictions', [])
        
        for prediction in predictions:
            for emotion in prediction.get('emotions', []):
                emotions[emotion['name']] = emotion['score']
                
        return {
            'primary_emotion': max(emotions, key=emotions.get),
            'emotion_scores': emotions,
            'stress_level': self.calculate_stress_level(emotions),
            'confidence_level': self.calculate_confidence_level(emotions)
        }
```
```

### Real-time Audio Processing with Azure Speech Services

```javascript
// AzureVoiceRecorder.jsx example
import React, { useState, useRef } from 'react';
import * as SpeechSDK from 'microsoft-cognitiveservices-speech-sdk';

const AzureVoiceRecorder = ({ onEmotionDetected, onTranscription }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const recognizer = useRef(null);
    
    const initializeAzureSpeech = () => {
        const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(
            process.env.REACT_APP_AZURE_SPEECH_KEY,
            process.env.REACT_APP_AZURE_SPEECH_REGION
        );
        speechConfig.speechRecognitionLanguage = "en-US";
        
        const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
        recognizer.current = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);
        
        recognizer.current.recognizing = (s, e) => {
            console.log(`RECOGNIZING: Text=${e.result.text}`);
        };
        
        recognizer.current.recognized = async (s, e) => {
            if (e.result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
                const transcription = e.result.text;
                onTranscription(transcription);
                
                // Send audio to Hume AI for emotion analysis
                await analyzeEmotion(e.result.privAudioData);
            }
        };
    };
    
    const analyzeEmotion = async (audioData) => {
        try {
            setIsProcessing(true);
            const response = await fetch('/api/analyze-emotion', {
                method: 'POST',
                body: audioData,
                headers: {
                    'Content-Type': 'audio/wav'
                }
            });
            
            const emotionData = await response.json();
            onEmotionDetected(emotionData);
        } catch (error) {
            console.error('Emotion analysis failed:', error);
        } finally {
            setIsProcessing(false);
        }
    };
    
    const startRecording = () => {
        if (!recognizer.current) {
            initializeAzureSpeech();
        }
        
        setIsRecording(true);
        recognizer.current.startContinuousRecognitionAsync();
    };
    
    const stopRecording = () => {
        setIsRecording(false);
        if (recognizer.current) {
            recognizer.current.stopContinuousRecognitionAsync();
        }
    };
    
    return (
        <div className="azure-voice-recorder">
            <button
                onClick={isRecording ? stopRecording : startRecording}
                className={`voice-button ${isRecording ? 'recording' : ''} ${isProcessing ? 'processing' : ''}`}
                disabled={isProcessing}
            >
                {isRecording ? '🛑 Stop Recording' : '🎤 Start Recording'}
            </button>
            
            {isProcessing && (
                <div className="processing-indicator">
                    🧠 Analyzing emotions...
                </div>
            )}
        </div>
    );
};

export default AzureVoiceRecorder;
```
            const audioBlob = event.data;
            const base64Audio = await blobToBase64(audioBlob);
            
            // Send to emotion detection endpoint
            const response = await fetch('/api/analyze/voice-emotion', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ audio_data: base64Audio })
            });
            
            const emotionData = await response.json();
            onEmotionDetected(emotionData);
        };
        
        mediaRecorder.current.start(1000); // Analyze every second
        setIsRecording(true);
    };
};
```

## 🧠 OpenAI Emotional Enhancement

### Emotional Context Integration

```python
# openai_client.py example configuration
from openai import OpenAI
import json

class EmotionalContentGenerator:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)
        
    async def generate_emotional_response(self, user_message, emotional_context):
        """
        Generate educationally sound response adapted to user's emotional state
        """
        system_prompt = self.build_emotional_system_prompt(emotional_context)
        
        response = await self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )
        
        return self.adapt_response_tone(response.choices[0].message.content, emotional_context)
        
    def build_emotional_system_prompt(self, emotional_context):
        """
        Build system prompt based on detected emotional state
        """
        base_prompt = """You are HighPal, an emotionally intelligent AI educational assistant. 
        You help students prepare for competitive exams while being sensitive to their emotional needs."""
        
        if emotional_context.get('stress_level', 0) > 7:
            return base_prompt + """
            The student is currently feeling stressed or overwhelmed. Please:
            - Use a calm, reassuring tone
            - Break down complex concepts into smaller, manageable parts
            - Offer encouragement and stress-reduction techniques
            - Suggest taking breaks if needed
            """
        elif emotional_context.get('confidence_level', 5) < 3:
            return base_prompt + """
            The student seems to lack confidence. Please:
            - Use an encouraging and supportive tone
            - Highlight their progress and achievements
            - Build confidence with positive reinforcement
            - Start with easier concepts before advancing
            """
        else:
            return base_prompt + """
            The student seems emotionally balanced. Please:
            - Maintain an engaging and motivating tone
            - Challenge them appropriately for their level
            - Keep the conversation dynamic and interesting
            """
```

## 📊 Emotional Analytics Setup

### Database Schema for Emotional Data

```python
# emotional_schema.py
from datetime import datetime
from typing import Dict, List, Optional

class EmotionalEntry:
    def __init__(self):
        self.user_id: str
        self.session_id: str
        self.timestamp: datetime
        self.primary_emotion: str
        self.emotion_scores: Dict[str, float]
        self.stress_level: float
        self.confidence_level: float
        self.conversation_context: str
        self.intervention_triggered: bool
        self.learning_topic: Optional[str]

class UserEmotionalProfile:
    def __init__(self):
        self.user_id: str
        self.emotional_baseline: Dict[str, float]
        self.stress_patterns: List[Dict]
        self.confidence_progression: List[Dict]
        self.preferred_support_style: str
        self.learning_emotional_preferences: Dict
        self.intervention_history: List[Dict]
```

### Analytics Dashboard API

```python
# Enhanced training_server.py emotional endpoints
from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta

@app.get("/analytics/emotional-dashboard")
async def get_emotional_dashboard(user_id: str):
    """
    Get comprehensive emotional learning analytics
    """
    profile = await get_user_emotional_profile(user_id)
    recent_sessions = await get_recent_emotional_sessions(user_id, days=7)
    
    return {
        "emotional_summary": {
            "avg_stress_level": calculate_avg_stress(recent_sessions),
            "avg_confidence_level": calculate_avg_confidence(recent_sessions),
            "primary_emotions": get_emotion_distribution(recent_sessions),
            "improvement_trend": calculate_emotional_trend(recent_sessions)
        },
        "stress_analysis": {
            "stress_triggers": identify_stress_triggers(recent_sessions),
            "stress_patterns": profile.stress_patterns,
            "intervention_effectiveness": measure_intervention_success(recent_sessions)
        },
        "confidence_building": {
            "confidence_growth": profile.confidence_progression,
            "achievement_milestones": get_confidence_milestones(user_id),
            "areas_of_strength": identify_confidence_areas(recent_sessions)
        },
        "recommendations": generate_emotional_recommendations(profile, recent_sessions)
    }

@app.post("/checkin/daily-mood")
async def daily_emotional_checkin(checkin_data: dict):
    """
    Record daily emotional check-in for baseline tracking
    """
    await store_emotional_checkin(checkin_data)
    return {"status": "success", "message": "Daily emotional check-in recorded"}
```

## 🚀 Testing Your Emotional Intelligence Setup

### 1. Test Emotion Detection

```bash
# Test voice emotion analysis
curl -X POST http://localhost:8000/analyze/voice-emotion \
  -H "Content-Type: application/json" \
  -d '{"audio_data": "base64_encoded_audio_sample"}'

# Expected response:
{
  "primary_emotion": "curious",
  "emotion_scores": {
    "curious": 0.85,
    "focused": 0.72,
    "stressed": 0.23
  },
  "stress_level": 2.3,
  "confidence_level": 7.2
}
```

### 2. Test Emotional Chat

```bash
# Test emotionally intelligent conversation
curl -X POST http://localhost:8000/chat/pal-emotional \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I am worried about my JEE preparation",
    "emotional_context": {
      "primary_emotion": "anxious",
      "stress_level": 8.2,
      "confidence_level": 3.1
    }
  }'

# Expected response includes calming, reassuring content
```

### 3. Test Emotional Analytics

```bash
# Test emotional dashboard
curl http://localhost:8000/analytics/emotional-dashboard?user_id=test_user

# Returns comprehensive emotional learning insights
```

## 🔒 Security & Privacy

### Emotional Data Privacy
- All emotional data is encrypted at rest and in transit
- User consent required for emotional data collection
- Emotional data retention policies configurable
- Anonymization options for analytics

### API Security
```python
# Enhanced security for emotional data
from cryptography.fernet import Fernet

class EmotionalDataEncryption:
    def __init__(self, encryption_key):
        self.cipher = Fernet(encryption_key)
    
    def encrypt_emotional_data(self, data):
        return self.cipher.encrypt(json.dumps(data).encode())
    
    def decrypt_emotional_data(self, encrypted_data):
        return json.loads(self.cipher.decrypt(encrypted_data).decode())
```

## 🎯 Next Steps

1. **Complete Backend Implementation** - Finish all emotional intelligence modules
2. **Frontend Emotional Interface** - Implement real-time emotion display
3. **Advanced Analytics** - Build comprehensive emotional insights dashboard
4. **Mobile Integration** - Extend emotional intelligence to mobile platforms
5. **Performance Optimization** - Optimize real-time emotion processing

## 📞 Support

For emotional intelligence setup support:
- Check the main [README.md](../README.md) for general setup
- Review [API Documentation](http://localhost:8000/docs) when server is running
- See [MongoDB Setup](MONGODB_SETUP.md) for database configuration

---

*HighPal Emotional Intelligence: Where cutting-edge AI meets human understanding for the ultimate learning experience* 🎓❤️
