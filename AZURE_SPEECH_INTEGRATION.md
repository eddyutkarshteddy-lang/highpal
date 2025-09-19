# 🎙️ Azure Speech Services Integration Guide

This document covers the complete integration of Azure Speech Services into HighPal's emotionally intelligent educational assistant.

## 🌟 Why Azure Speech Services?

### Perfect Match for HighPal's Requirements:
- **Enterprise-grade STT/TTS**: Reliable voice processing for educational content
- **Emotional expressiveness**: Neural voices with emotional styles (calm, encouraging, energetic)
- **Student-friendly**: Age-appropriate voices with clear pronunciation
- **Cost-effective scaling**: Better pricing than ElevenLabs for concurrent users
- **Educational focus**: Supports multiple languages for diverse learning needs
- **Real-time processing**: Low latency for interactive conversations

## 🏗️ Architecture Integration

### HighPal's Voice Processing Pipeline:
```
Student Voice Input
    ↓
Azure Speech-to-Text (STT)
    ↓
Azure Text Analytics Emotion Analysis
    ↓
OpenAI GPT-5 Content Generation + Emotional Context
    ↓
Azure Text-to-Speech (TTS) with Emotional Style
    ↓
Emotionally Appropriate Voice Response
```

## 🔧 Technical Implementation

### Backend Integration (`azure_speech_client.py`)

```python
import azure.cognitiveservices.speech as speechsdk
import asyncio
import os
from typing import Dict, Optional

class AzureSpeechProcessor:
    def __init__(self):
        self.speech_key = os.getenv('AZURE_SPEECH_KEY')
        self.speech_region = os.getenv('AZURE_SPEECH_REGION')
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key,
            region=self.speech_region
        )
        self.setup_emotional_voices()
    
    def setup_emotional_voices(self):
        """Configure emotionally appropriate voices for students"""
        self.voice_styles = {
            'calm': {
                'voice': 'en-US-JennyNeural',
                'style': 'calm',
                'rate': 'medium'
            },
            'encouraging': {
                'voice': 'en-US-AriaNeural', 
                'style': 'cheerful',
                'rate': 'medium'
            },
            'energetic': {
                'voice': 'en-US-GuyNeural',
                'style': 'excited',
                'rate': 'fast'
            },
            'supportive': {
                'voice': 'en-US-JennyNeural',
                'style': 'empathetic',
                'rate': 'slow'
            }
        }
    
    async def speech_to_text_continuous(self, audio_stream):
        """Continuous speech recognition for real-time conversation"""
        audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )
        
        # Configure for educational content
        speech_recognizer.properties.set_property(
            speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, 
            "5000"
        )
        
        results = []
        done = False
        
        def recognized_handler(evt):
            if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
                results.append({
                    'text': evt.result.text,
                    'confidence': evt.result.properties.get(
                        speechsdk.PropertyId.SpeechServiceResponse_RecognitionLatencyMs
                    ),
                    'timestamp': evt.result.offset
                })
        
        speech_recognizer.recognized.connect(recognized_handler)
        speech_recognizer.start_continuous_recognition()
        
        return results
    
    async def text_to_speech_emotional(self, text: str, emotion_context: Dict) -> bytes:
        """Generate emotionally appropriate speech for students"""
        
        # Determine appropriate voice style based on emotion context
        emotion_style = self.determine_voice_style(emotion_context)
        voice_config = self.voice_styles[emotion_style]
        
        # Create SSML with emotional expression
        ssml = self.create_educational_ssml(text, voice_config, emotion_context)
        
        # Configure audio output
        audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config,
            audio_config=audio_config
        )
        
        # Generate speech
        result = synthesizer.speak_ssml_async(ssml).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data
        else:
            raise Exception(f"Speech synthesis failed: {result.reason}")
    
    def determine_voice_style(self, emotion_context: Dict) -> str:
        """Determine appropriate voice style for student's emotional state"""
        if not emotion_context:
            return 'calm'
        
        stress_level = emotion_context.get('stress_level', 0)
        confidence_level = emotion_context.get('confidence_level', 5)
        primary_emotion = emotion_context.get('primary_emotion', 'neutral')
        
        # Adaptive voice selection logic
        if stress_level > 7:
            return 'calm'  # Calming voice for stressed students
        elif confidence_level < 3:
            return 'encouraging'  # Encouraging voice for low confidence
        elif primary_emotion in ['excitement', 'joy']:
            return 'energetic'  # Match their energy
        elif primary_emotion in ['sadness', 'frustration']:
            return 'supportive'  # Supportive for difficult emotions
        else:
            return 'calm'  # Default calm and clear
    
    def create_educational_ssml(self, text: str, voice_config: Dict, emotion_context: Dict) -> str:
        """Create SSML optimized for educational content"""
        voice_name = voice_config['voice']
        style = voice_config['style']
        rate = voice_config['rate']
        
        # Add educational emphasis and pacing
        enhanced_text = self.enhance_text_for_learning(text, emotion_context)
        
        ssml = f"""
        <speak version='1.0' xml:lang='en-US'>
            <voice name='{voice_name}'>
                <mstts:express-as style='{style}' styledegree='0.8'>
                    <prosody rate='{rate}' pitch='medium'>
                        {enhanced_text}
                    </prosody>
                </mstts:express-as>
            </voice>
        </speak>
        """
        
        return ssml
    
    def enhance_text_for_learning(self, text: str, emotion_context: Dict) -> str:
        """Enhance text with educational speaking patterns"""
        
        # Add pauses for better comprehension
        text = text.replace('.', '.<break time="500ms"/>')
        text = text.replace(',', ',<break time="300ms"/>')
        
        # Emphasize important educational terms
        educational_keywords = ['theorem', 'formula', 'concept', 'important', 'remember']
        for keyword in educational_keywords:
            text = text.replace(keyword, f'<emphasis level="moderate">{keyword}</emphasis>')
        
        # Add encouraging phrases for low confidence
        if emotion_context.get('confidence_level', 5) < 4:
            text = "You're doing great! " + text
        
        return text

# Integration with FastAPI endpoint
async def process_voice_interaction(audio_data: bytes, emotion_context: Dict):
    """Complete voice processing pipeline"""
    speech_processor = AzureSpeechProcessor()
    
    # Step 1: Convert speech to text
    transcription = await speech_processor.speech_to_text_continuous(audio_data)
    
    # Step 2: Generate AI response (handled by existing OpenAI integration)
    ai_response = await generate_educational_response(transcription, emotion_context)
    
    # Step 3: Convert response to emotionally appropriate speech
    audio_response = await speech_processor.text_to_speech_emotional(
        ai_response, emotion_context
    )
    
    return {
        'transcription': transcription,
        'ai_response': ai_response,
        'audio_response': audio_response,
        'emotion_context': emotion_context
    }
```

### Frontend Integration (`AzureVoiceComponent.jsx`)

```javascript
import React, { useState, useEffect, useRef } from 'react';
import * as SpeechSDK from 'microsoft-cognitiveservices-speech-sdk';

const AzureVoiceComponent = ({ onConversationUpdate }) => {
    const [isListening, setIsListening] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [currentEmotion, setCurrentEmotion] = useState('neutral');
    
    const recognizer = useRef(null);
    const synthesizer = useRef(null);
    
    useEffect(() => {
        initializeAzureServices();
        return () => cleanup();
    }, []);
    
    const initializeAzureServices = () => {
        // Speech-to-Text setup
        const speechConfig = SpeechSDK.SpeechConfig.fromSubscription(
            process.env.REACT_APP_AZURE_SPEECH_KEY,
            process.env.REACT_APP_AZURE_SPEECH_REGION
        );
        
        speechConfig.speechRecognitionLanguage = "en-US";
        speechConfig.setProperty(
            SpeechSDK.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs,
            "5000"
        );
        
        const audioConfig = SpeechSDK.AudioConfig.fromDefaultMicrophoneInput();
        recognizer.current = new SpeechSDK.SpeechRecognizer(speechConfig, audioConfig);
        
        // Text-to-Speech setup
        synthesizer.current = new SpeechSDK.SpeechSynthesizer(speechConfig);
        
        setupRecognitionHandlers();
    };
    
    const setupRecognitionHandlers = () => {
        recognizer.current.recognizing = (s, e) => {
            console.log(`Recognizing: ${e.result.text}`);
        };
        
        recognizer.current.recognized = async (s, e) => {
            if (e.result.reason === SpeechSDK.ResultReason.RecognizedSpeech) {
                const userInput = e.result.text;
                await processUserInput(userInput, e.result.privAudioData);
            }
        };
        
        recognizer.current.canceled = (s, e) => {
            console.log(`Recognition canceled: ${e.reason}`);
            setIsListening(false);
        };
    };
    
    const processUserInput = async (text, audioData) => {
        try {
            setIsProcessing(true);
            
            // Send to backend for complete processing
            const response = await fetch('/api/voice-interaction', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    audio_data: Array.from(new Uint8Array(audioData)),
                    emotion_context: {
                        current_emotion: currentEmotion,
                        timestamp: Date.now()
                    }
                })
            });
            
            const result = await response.json();
            
            // Update emotion state
            setCurrentEmotion(result.emotion_context.primary_emotion);
            
            // Play AI response with appropriate emotion
            await playAudioResponse(result.audio_response);
            
            // Update conversation UI
            onConversationUpdate({
                user_input: text,
                ai_response: result.ai_response,
                emotion_data: result.emotion_context
            });
            
        } catch (error) {
            console.error('Voice processing failed:', error);
        } finally {
            setIsProcessing(false);
        }
    };
    
    const playAudioResponse = async (audioData) => {
        return new Promise((resolve) => {
            const audioContext = new AudioContext();
            const audioBuffer = audioContext.createBuffer(1, audioData.length, 22050);
            const channelData = audioBuffer.getChannelData(0);
            
            for (let i = 0; i < audioData.length; i++) {
                channelData[i] = audioData[i] / 32768.0;
            }
            
            const source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContext.destination);
            source.onended = resolve;
            source.start();
        });
    };
    
    const startListening = () => {
        setIsListening(true);
        recognizer.current.startContinuousRecognitionAsync();
    };
    
    const stopListening = () => {
        setIsListening(false);
        recognizer.current.stopContinuousRecognitionAsync();
    };
    
    const cleanup = () => {
        if (recognizer.current) {
            recognizer.current.close();
        }
        if (synthesizer.current) {
            synthesizer.current.close();
        }
    };
    
    return (
        <div className="azure-voice-component">
            <div className="voice-controls">
                <button
                    onClick={isListening ? stopListening : startListening}
                    disabled={isProcessing}
                    className={`voice-button ${isListening ? 'listening' : ''} ${isProcessing ? 'processing' : ''}`}
                >
                    {isListening ? '🛑 Stop' : '🎤 Talk to HighPal'}
                </button>
            </div>
            
            <div className="emotion-indicator">
                <span className={`emotion-badge emotion-${currentEmotion}`}>
                    Current mood: {currentEmotion}
                </span>
            </div>
            
            {isProcessing && (
                <div className="processing-status">
                    <div className="spinner"></div>
                    <span>🧠 Understanding your emotions and generating response...</span>
                </div>
            )}
        </div>
    );
};

export default AzureVoiceComponent;
```

## 📊 Cost Optimization for Students

### Azure Speech Services Pricing Strategy:
- **STT**: $1 per hour of audio processed (student input only)
- **TTS**: $4 per 1M characters (text input only)
- **No concurrent limits**: Unlike ElevenLabs, scales seamlessly
- **Student Discounts**: Azure for Students provides $100 credit

### Cost Calculation:
- **Per Student Session**: ~$0.175 (10 min speaking + 2K char response)
- **Per Student Monthly**: ~$3.50 (20 sessions)
- **100 Students**: ~$350/month
- **1000 Students**: ~$3,500/month

### Cost Comparison vs ElevenLabs:
- **Azure**: $3.50 per student/month (unlimited concurrent)
- **ElevenLabs**: $99/month for 10 concurrent users = $9.90/user
- **Savings**: 65% cheaper for educational applications

### Revenue Model Example:
- **Student Premium**: $10/month
- **Voice Costs**: $3.50/month
- **Profit Margin**: $6.50/month per student (65%)

## 🎯 Educational Optimizations

### Voice Characteristics for Students:
- **Clear Pronunciation**: Neural voices optimized for comprehension
- **Appropriate Pace**: Adjustable speaking rate based on content complexity
- **Emotional Support**: Encouraging tones for confidence building
- **Stress Intervention**: Calming voices when students are overwhelmed

### SSML Features for Learning:
```xml
<speak version='1.0' xml:lang='en-US'>
    <voice name='en-US-JennyNeural'>
        <mstts:express-as style='cheerful'>
            <prosody rate='medium' pitch='medium'>
                Great job on that answer! 
                <break time='500ms'/>
                Let's move to the next <emphasis level='moderate'>concept</emphasis>.
            </prosody>
        </mstts:express-as>
    </voice>
</speak>
```

## 🔐 Security & Privacy

### Student Data Protection:
- **No Audio Storage**: Azure processes audio in real-time
- **GDPR Compliant**: Azure Speech Services meets educational privacy standards
- **Regional Processing**: Data stays in selected Azure region
- **Encryption**: All audio transmitted over HTTPS

## 🚀 Deployment Configuration

### Environment Variables:
```bash
# Azure Speech Services Configuration
AZURE_SPEECH_KEY=your_azure_speech_services_key
AZURE_SPEECH_REGION=eastus  # or your preferred region

# Voice Configuration for Students
AZURE_DEFAULT_VOICE=en-US-JennyNeural
AZURE_SPEECH_RATE=medium
AZURE_SPEECH_STYLE=cheerful

# Educational Optimizations
EDUCATIONAL_EMPHASIS_ENABLED=true
STRESS_DETECTION_THRESHOLD=7
CONFIDENCE_BUILDING_ENABLED=true
```

### Package Dependencies:
```json
{
  "dependencies": {
    "azure-cognitiveservices-speech": "^1.30.0",
    "microsoft-cognitiveservices-speech-sdk": "^1.30.0"
  }
}
```

```bash
# Python Backend
pip install azure-cognitiveservices-speech==1.30.0
```

## 📈 Monitoring & Analytics

### Voice Interaction Metrics:
- **Recognition Accuracy**: Track STT confidence scores
- **Emotional Progression**: Monitor student emotional journey
- **Engagement Metrics**: Voice interaction duration and frequency
- **Learning Outcomes**: Correlation between emotional state and comprehension

This integration provides HighPal with enterprise-grade voice processing that's specifically optimized for educational use cases while maintaining cost-effectiveness for student applications.
