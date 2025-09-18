import os
import azure.cognitiveservices.speech as speechsdk
from typing import Optional, BinaryIO
import io
import wave
import json

class SpeechService:
    def __init__(self):
        """Initialize Azure Speech Service with credentials from environment"""
        self.speech_key = os.getenv('AZURE_SPEECH_KEY')
        self.speech_region = os.getenv('AZURE_SPEECH_REGION', 'centralindia')
        self.voice_name = os.getenv('HIGHPAL_VOICE', 'en-US-EmmaMultilingualNeural')
        
        if not self.speech_key:
            raise ValueError("AZURE_SPEECH_KEY environment variable is required")
        
        # Configure speech config
        self.speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key, 
            region=self.speech_region
        )
        
        # Set voice for text-to-speech
        self.speech_config.speech_synthesis_voice_name = self.voice_name
        
        # Configure speech recognition language
        self.speech_config.speech_recognition_language = "en-US"
    
    def speech_to_text(self, audio_data: bytes) -> dict:
        """
        Convert speech audio data to text
        
        Args:
            audio_data: Audio data in WAV format
            
        Returns:
            Dictionary with 'text' and 'success' keys
        """
        try:
            # Create audio stream from bytes
            audio_stream = speechsdk.audio.PushAudioInputStream()
            audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=self.speech_config, 
                audio_config=audio_config
            )
            
            # Push audio data to stream
            audio_stream.write(audio_data)
            audio_stream.close()
            
            # Perform recognition
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return {
                    'success': True,
                    'text': result.text,
                    'confidence': getattr(result, 'confidence', None)
                }
            elif result.reason == speechsdk.ResultReason.NoMatch:
                return {
                    'success': False,
                    'error': 'No speech could be recognized',
                    'text': ''
                }
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                return {
                    'success': False,
                    'error': f'Speech recognition canceled: {cancellation_details.reason}',
                    'text': ''
                }
            else:
                return {
                    'success': False,
                    'error': 'Unknown recognition result',
                    'text': ''
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Speech recognition error: {str(e)}',
                'text': ''
            }
    
    def text_to_speech(self, text: str) -> dict:
        """
        Convert text to speech audio
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Dictionary with 'audio_data' (bytes) and 'success' keys
        """
        try:
            # Create speech synthesizer with default audio output
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=self.speech_config,
                audio_config=None  # Use default audio output to get audio data
            )
            
            # Perform synthesis
            result = synthesizer.speak_text_async(text).get()
            
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                # Get audio data directly from result
                audio_data = result.audio_data
                return {
                    'success': True,
                    'audio_data': audio_data,
                    'format': 'wav'
                }
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                error_msg = f'Speech synthesis canceled: {cancellation_details.reason}'
                if cancellation_details.error_details:
                    error_msg += f' - {cancellation_details.error_details}'
                return {
                    'success': False,
                    'error': error_msg,
                    'audio_data': None
                }
            else:
                return {
                    'success': False,
                    'error': f'Unknown synthesis result: {result.reason}',
                    'audio_data': None
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Speech synthesis error: {str(e)}',
                'audio_data': None
            }
    
    def get_available_voices(self) -> dict:
        """
        Get list of available voices for the current region
        
        Returns:
            Dictionary with available voices information
        """
        try:
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
            result = synthesizer.get_voices_async().get()
            
            if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
                voices = []
                for voice in result.voices:
                    voices.append({
                        'name': voice.name,
                        'display_name': voice.display_name,
                        'local_name': voice.local_name,
                        'locale': voice.locale,
                        'gender': voice.gender.name,
                        'voice_type': voice.voice_type.name
                    })
                
                return {
                    'success': True,
                    'voices': voices,
                    'current_voice': self.voice_name
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to retrieve voices',
                    'voices': []
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error retrieving voices: {str(e)}',
                'voices': []
            }

# Global speech service instance
speech_service = None

def get_speech_service():
    """Get or create speech service instance"""
    global speech_service
    if speech_service is None:
        try:
            speech_service = SpeechService()
        except Exception as e:
            print(f"Failed to initialize speech service: {e}")
            return None
    return speech_service
