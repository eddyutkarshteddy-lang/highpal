"""
Test Azure Services Integration for HighPal
Tests Azure Speech Services and Text Analytics integration
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from azure_text_analytics_client import AzureTextAnalyticsClient
from enhanced_azure_speech_client import EnhancedAzureSpeechClient

def test_environment_variables():
    """Test if environment variables are properly configured"""
    print("🔍 Testing Environment Variables:")
    print("-" * 40)
    
    # Check Azure Speech Services
    speech_key = os.getenv('AZURE_SPEECH_KEY')
    speech_region = os.getenv('AZURE_SPEECH_REGION')
    
    print(f"✅ AZURE_SPEECH_KEY: {'Configured' if speech_key and speech_key != 'your_azure_speech_key_here' else '❌ Not configured'}")
    print(f"✅ AZURE_SPEECH_REGION: {speech_region or '❌ Not configured'}")
    
    # Check Azure Text Analytics
    text_analytics_key = os.getenv('AZURE_TEXT_ANALYTICS_KEY')
    text_analytics_endpoint = os.getenv('AZURE_TEXT_ANALYTICS_ENDPOINT')
    
    print(f"⚠️  AZURE_TEXT_ANALYTICS_KEY: {'Configured' if text_analytics_key and text_analytics_key != 'your_azure_text_analytics_key_here' else '❌ Not configured (will use fallback)'}")
    print(f"⚠️  AZURE_TEXT_ANALYTICS_ENDPOINT: {'Configured' if text_analytics_endpoint and 'your-resource-name' not in text_analytics_endpoint else '❌ Not configured (will use fallback)'}")
    
    # Check OpenAI
    openai_key = os.getenv('OPENAI_API_KEY')
    print(f"✅ OPENAI_API_KEY: {'Configured' if openai_key and openai_key != 'your_openai_api_key_here' else '❌ Not configured'}")
    
    print()

def test_text_analytics():
    """Test Azure Text Analytics emotion detection"""
    print("🧠 Testing Azure Text Analytics Emotion Detection:")
    print("-" * 50)
    
    client = AzureTextAnalyticsClient()
    
    test_cases = [
        "I'm really stressed about the JEE exam and I don't understand calculus at all!",
        "Thank you so much! I finally understand photosynthesis. This is great!",
        "Can you explain more about Newton's laws? I'm curious about the physics.",
        "I'm confused about organic chemistry. This is so difficult.",
        "I feel confident about solving these equations now."
    ]
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: '{text}'")
        result = client.analyze_sentiment_and_emotions(text)
        
        print(f"   Emotional State: {result['emotional_state']}")
        print(f"   Sentiment: {result['sentiment']['overall']}")
        print(f"   Stress Level: {result['emotional_indicators']['stress_level']}")
        print(f"   Confidence Level: {result['emotional_indicators']['confidence_level']}")
        print(f"   Suggested Response Tone: {result['suggested_response_tone']}")
        
        if result.get('fallback_mode'):
            print("   ⚠️  Using fallback emotion detection (Azure Text Analytics not configured)")
    
    print()

def test_speech_synthesis():
    """Test Azure Speech Services text-to-speech with emotions"""
    print("🗣️  Testing Azure Speech Services (Text-to-Speech):")
    print("-" * 50)
    
    client = EnhancedAzureSpeechClient()
    
    if not client.speech_config:
        print("❌ Azure Speech Services not configured - skipping TTS test")
        return
    
    test_responses = [
        ("Great job! You're really getting the hang of calculus now.", "confident_and_positive"),
        ("I understand you're feeling overwhelmed. Let's take this step by step, slowly.", "calm_and_supportive"),
        ("That's an excellent question about photosynthesis! I love your curiosity.", "enthusiastic"),
        ("Don't worry if this seems confusing at first. Many students find this topic challenging.", "encouraging")
    ]
    
    for i, (text, emotion) in enumerate(test_responses, 1):
        print(f"\n{i}. Synthesizing with '{emotion}' emotion:")
        print(f"   Text: '{text}'")
        
        success, audio_data = client.text_to_speech_with_emotion(text, emotion)
        
        if success:
            print(f"   ✅ Success! Generated {len(audio_data)} bytes of audio")
        else:
            print(f"   ❌ Failed to synthesize speech")
    
    print()

def test_complete_integration():
    """Test the complete voice conversation processing"""
    print("🔄 Testing Complete Azure Integration:")
    print("-" * 40)
    
    # Test text analytics with different emotional contexts
    text_client = AzureTextAnalyticsClient()
    speech_client = EnhancedAzureSpeechClient()
    
    conversation_scenarios = [
        {
            "student_input": "I'm really struggling with these physics problems. I feel so lost!",
            "expected_emotion": "stressed_or_frustrated"
        },
        {
            "student_input": "Wow, that explanation was perfect! I totally get it now!",
            "expected_emotion": "confident_and_positive"
        }
    ]
    
    for i, scenario in enumerate(conversation_scenarios, 1):
        print(f"\n{i}. Scenario: Student says '{scenario['student_input']}'")
        
        # Analyze emotion
        emotion_result = text_client.analyze_sentiment_and_emotions(scenario['student_input'])
        
        print(f"   Detected Emotion: {emotion_result['emotional_state']}")
        print(f"   Suggested Response Tone: {emotion_result['suggested_response_tone']}")
        
        # Generate appropriate response
        if emotion_result['emotional_state'] == 'stressed_or_frustrated':
            ai_response = "I understand this can be challenging. Let me break it down into smaller, easier steps for you."
        elif emotion_result['emotional_state'] == 'confident_and_positive':
            ai_response = "That's fantastic! You're really mastering this concept. Should we try a more advanced problem?"
        else:
            ai_response = "Great question! Let me help you understand this better."
        
        print(f"   AI Response: '{ai_response}'")
        
        # Test speech synthesis with appropriate emotion
        if speech_client.speech_config:
            success, audio_data = speech_client.text_to_speech_with_emotion(
                ai_response, 
                emotion_result['suggested_response_tone']
            )
            if success:
                print(f"   ✅ Speech synthesized successfully ({len(audio_data)} bytes)")
            else:
                print(f"   ❌ Speech synthesis failed")
        else:
            print(f"   ⚠️  Speech synthesis skipped (not configured)")
    
    print()

def main():
    """Run all Azure integration tests"""
    print("🚀 HighPal Azure Integration Test Suite")
    print("=" * 50)
    print()
    
    test_environment_variables()
    test_text_analytics()
    test_speech_synthesis()
    test_complete_integration()
    
    print("✅ Azure Integration Testing Complete!")
    print()
    print("📋 Next Steps:")
    print("1. If Text Analytics shows 'fallback mode', get Azure Text Analytics API key")
    print("2. If Speech Services failed, verify your Azure Speech key and region")
    print("3. Test the complete system with your HighPal voice conversation")

if __name__ == "__main__":
    main()
