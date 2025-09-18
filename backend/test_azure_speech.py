"""
Test Azure Speech Services Configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_azure_speech_config():
    """Test Azure Speech configuration"""
    key = os.getenv('AZURE_SPEECH_KEY')
    region = os.getenv('AZURE_SPEECH_REGION')
    voice = os.getenv('HIGHPAL_VOICE')
    
    print("🔍 Azure Speech Configuration:")
    print(f"  • Key: {'✅ Present' if key else '❌ Missing'}")
    print(f"  • Region: {region}")
    print(f"  • Voice: {voice}")
    print()
    
    if not key:
        print("❌ Azure Speech Key is missing!")
        return False
    
    # Test Speech Service initialization
    try:
        import azure.cognitiveservices.speech as speechsdk
        
        # Create speech config
        speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
        speech_config.speech_synthesis_voice_name = voice
        
        print("✅ Speech Config created successfully")
        
        # Test Text-to-Speech (most likely to work)
        print("\n🎤 Testing Text-to-Speech...")
        synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        
        # Simple test synthesis
        test_text = "Hello, this is a test of Azure Speech Services."
        result = synthesizer.speak_text_async(test_text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            print("✅ Text-to-Speech: WORKING")
            print(f"  • Audio data size: {len(result.audio_data)} bytes")
            return True
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"❌ Text-to-Speech: FAILED")
            print(f"  • Reason: {cancellation_details.reason}")
            if cancellation_details.error_details:
                print(f"  • Error: {cancellation_details.error_details}")
            return False
        else:
            print(f"❌ Text-to-Speech: Unknown result ({result.reason})")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Azure Speech: {e}")
        return False

if __name__ == "__main__":
    test_azure_speech_config()
