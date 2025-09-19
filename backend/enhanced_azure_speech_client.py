"""
Enhanced Azure Speech Services Client for HighPal
Integrates speech recognition, synthesis, and emotion analysis
"""

import os
import azure.cognitiveservices.speech as speechsdk
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from typing import Dict, Optional, Tuple
import logging
import asyncio
from dotenv import load_dotenv
from azure_text_analytics_client import AzureTextAnalyticsClient

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class EnhancedAzureSpeechClient:
    """Enhanced Azure Speech Services client with emotion analysis"""
    
    def __init__(self):
        """Initialize Azure Speech Services with emotion analysis"""
        self.speech_key = os.getenv('AZURE_SPEECH_KEY')
        self.speech_region = os.getenv('AZURE_SPEECH_REGION', 'centralindia')
        self.voice_name = os.getenv('HIGHPAL_VOICE', 'en-US-EmmaMultilingualNeural')
        
        # Initialize speech config
        if self.speech_key:
            self.speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, 
                region=self.speech_region
            )
            self.speech_config.speech_synthesis_voice_name = self.voice_name
        else:
            logger.error("Azure Speech Services key not configured")
            self.speech_config = None
        
        # Initialize emotion analysis client
        self.emotion_analyzer = AzureTextAnalyticsClient()
        
        logger.info("Enhanced Azure Speech Services client initialized")
    
    def speech_to_text_with_emotion(self, audio_data: bytes = None) -> Dict:
        """
        Convert speech to text and analyze emotions
        
        Args:
            audio_data: Optional audio bytes, if None uses microphone
            
        Returns:
            Dict: Speech recognition results with emotion analysis
        """
        if not self.speech_config:
            return {"error": "Azure Speech Services not configured"}
        
        try:
            # Configure audio input
            if audio_data:
                # Use audio data
                audio_stream = speechsdk.audio.PushAudioInputStream()
                audio_stream.write(audio_data)
                audio_stream.close()
                audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
            else:
                # Use default microphone
                audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            # Perform speech recognition
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                recognized_text = result.text
                
                # Analyze emotions from the recognized text
                emotion_analysis = self.emotion_analyzer.analyze_sentiment_and_emotions(recognized_text)
                
                return {
                    "success": True,
                    "recognized_text": recognized_text,
                    "emotion_analysis": emotion_analysis,
                    "confidence": self._get_speech_confidence(result)
                }
            
            elif result.reason == speechsdk.ResultReason.NoMatch:
                return {"error": "No speech could be recognized"}
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                return {"error": f"Speech recognition canceled: {cancellation_details.reason}"}
            
        except Exception as e:
            logger.error(f"Error in speech to text with emotion: {e}")
            return {"error": str(e)}
    
    def text_to_speech_with_emotion(self, text: str, emotion_state: str = None) -> Tuple[bool, bytes]:
        """
        Convert text to speech with emotional expression
        
        Args:
            text: Text to synthesize
            emotion_state: Emotional state to guide voice synthesis
            
        Returns:
            Tuple[bool, bytes]: Success flag and audio bytes
        """
        if not self.speech_config:
            logger.error("Azure Speech Services not configured")
            return False, b""
        
        try:
            # Apply emotional SSML based on state
            ssml_text = self._apply_emotional_ssml(text, emotion_state)
            
            # Create speech synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config, 
                audio_config=None
            )
            
            # Synthesize speech
            result = synthesizer.speak_ssml_async(ssml_text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                logger.info(f"Speech synthesized successfully with {emotion_state or 'default'} emotion")
                return True, result.audio_data
            
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.error(f"Speech synthesis canceled: {cancellation_details.reason}")
                return False, b""
            
        except Exception as e:
            logger.error(f"Error in text to speech with emotion: {e}")
            return False, b""
    
    def _apply_emotional_ssml(self, text: str, emotion_state: str = None) -> str:
        """
        Apply SSML tags for emotional expression
        
        Args:
            text: Text to wrap with SSML
            emotion_state: Emotional state for voice modulation
            
        Returns:
            str: SSML formatted text
        """
        # Define emotional speaking styles for Emma Multilingual voice
        emotional_styles = {
            "confident_and_positive": {
                "style": "cheerful",
                "rate": "medium",
                "pitch": "+2st"
            },
            "stressed_or_frustrated": {
                "style": "calm",
                "rate": "slow",
                "pitch": "-1st"
            },
            "confused_or_frustrated": {
                "style": "gentle",
                "rate": "slow",
                "pitch": "medium"
            },
            "calm_and_supportive": {
                "style": "calm",
                "rate": "medium",
                "pitch": "medium"
            },
            "encouraging": {
                "style": "cheerful",
                "rate": "medium",
                "pitch": "+1st"
            },
            "enthusiastic": {
                "style": "excited",
                "rate": "medium",
                "pitch": "+3st"
            }
        }
        
        # Get emotional parameters
        if emotion_state and emotion_state in emotional_styles:
            style_params = emotional_styles[emotion_state]
        else:
            # Default neutral style
            style_params = {
                "style": "friendly",
                "rate": "medium",
                "pitch": "medium"
            }
        
        # Create SSML
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
               xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
            <voice name="{self.voice_name}">
                <mstts:express-as style="{style_params['style']}">
                    <prosody rate="{style_params['rate']}" pitch="{style_params['pitch']}">
                        {text}
                    </prosody>
                </mstts:express-as>
            </voice>
        </speak>
        """
        
        return ssml.strip()
    
    def _get_speech_confidence(self, result) -> float:
        """Extract confidence score from speech recognition result"""
        try:
            # Azure Speech Services provides confidence in properties
            if hasattr(result, 'properties'):
                confidence_str = result.properties.get(speechsdk.PropertyId.SpeechServiceResponse_JsonResult)
                if confidence_str:
                    import json
                    json_result = json.loads(confidence_str)
                    # Extract confidence from the result
                    return json_result.get('confidence', 0.8)
            return 0.8  # Default confidence
        except:
            return 0.8
    
    def process_voice_conversation(self, audio_data: bytes = None) -> Dict:
        """
        Complete voice conversation processing: STT → Emotion Analysis → Response Preparation
        
        Args:
            audio_data: Optional audio bytes
            
        Returns:
            Dict: Complete conversation processing results
        """
        # Step 1: Speech to text with emotion analysis
        stt_result = self.speech_to_text_with_emotion(audio_data)
        
        if not stt_result.get("success"):
            return stt_result
        
        recognized_text = stt_result["recognized_text"]
        emotion_analysis = stt_result["emotion_analysis"]
        
        # Step 2: Prepare response context for AI
        response_context = {
            "user_input": recognized_text,
            "emotional_state": emotion_analysis["emotional_state"],
            "stress_level": emotion_analysis["emotional_indicators"]["stress_level"],
            "confidence_level": emotion_analysis["emotional_indicators"]["confidence_level"],
            "suggested_tone": emotion_analysis["suggested_response_tone"],
            "sentiment": emotion_analysis["sentiment"]["overall"]
        }
        
        logger.info(f"Voice conversation processed - Emotion: {emotion_analysis['emotional_state']}")
        
        return {
            "success": True,
            "recognized_text": recognized_text,
            "emotion_analysis": emotion_analysis,
            "response_context": response_context,
            "speech_confidence": stt_result.get("confidence", 0.8)
        }

# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_enhanced_speech_client():
        client = EnhancedAzureSpeechClient()
        
        # Test text-to-speech with different emotions
        test_responses = [
            ("Great job! You're understanding calculus very well.", "confident_and_positive"),
            ("I understand you're feeling stressed. Let's take this step by step.", "calm_and_supportive"),
            ("That's an excellent question about photosynthesis!", "enthusiastic")
        ]
        
        for text, emotion in test_responses:
            print(f"\nTesting TTS with emotion '{emotion}': {text}")
            success, audio_data = client.text_to_speech_with_emotion(text, emotion)
            print(f"TTS Success: {success}, Audio bytes: {len(audio_data) if audio_data else 0}")
    
    # Run test
    asyncio.run(test_enhanced_speech_client())
