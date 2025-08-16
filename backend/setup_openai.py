#!/usr/bin/env python3
"""
Setup script for HighPal OpenAI integration
"""

import os
import sys
from dotenv import load_dotenv, set_key

def check_openai_setup():
    """Check if OpenAI is properly configured"""
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or api_key == "your-openai-api-key-here":
        return False, "Not configured"
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=5
        )
        return True, "Working correctly"
    except Exception as e:
        return False, f"Error: {e}"

def setup_openai_key():
    """Interactive setup for OpenAI API key"""
    print("🔑 OpenAI API Key Setup")
    print("-" * 30)
    print("Get your API key from: https://platform.openai.com/api-keys")
    print("(New accounts get $5 free credit)")
    print()
    
    api_key = input("Enter your OpenAI API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        return False
    
    # Save to .env file
    env_path = ".env"
    try:
        set_key(env_path, "OPENAI_API_KEY", api_key)
        print(f"✅ API key saved to {env_path}")
        
        # Test the key
        os.environ["OPENAI_API_KEY"] = api_key
        is_working, message = check_openai_setup()
        
        if is_working:
            print("🎉 OpenAI integration is working!")
            return True
        else:
            print(f"⚠️ API key saved but test failed: {message}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to save API key: {e}")
        return False

def main():
    print("🚀 HighPal OpenAI Setup Checker")
    print("=" * 40)
    
    # Check current status
    is_working, status = check_openai_setup()
    
    if is_working:
        print(f"✅ OpenAI Status: {status}")
        print("🎉 You're all set! Your app can now answer general questions.")
    else:
        print(f"❌ OpenAI Status: {status}")
        print()
        
        setup_choice = input("Would you like to set up OpenAI now? (y/n): ").lower().strip()
        
        if setup_choice in ['y', 'yes']:
            if setup_openai_key():
                print("\n🎉 Setup completed! Restart your backend server to apply changes.")
            else:
                print("\n❌ Setup failed. You can try again later.")
        else:
            print("\nℹ️ OpenAI setup skipped. Your app will work with limited Q&A capabilities.")
    
    print("\n" + "=" * 40)
    print("Next steps:")
    print("1. Restart your backend server if you updated the API key")
    print("2. Test with questions like 'hi' or 'what is AI?'")
    print("3. Upload documents for document-specific questions")

if __name__ == "__main__":
    main()
