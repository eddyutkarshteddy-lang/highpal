#!/usr/bin/env python3
"""
Simple test script to upload a document directly to the MongoDB server
"""
import requests
import json

def test_upload():
    # Create a simple text file to test upload
    test_content = """
    This is a test document for HighPal MongoDB Atlas integration.
    
    Testing Features:
    - Cloud storage with MongoDB Atlas
    - Document indexing and search
    - PDF processing capabilities
    - API endpoint functionality
    
    This document should be stored in MongoDB Atlas and be searchable.
    """
    
    # Test the simple document endpoint first
    url = "http://localhost:8002/documents"
    
    data = {
        "title": "MongoDB Atlas Test Document",
        "content": test_content,
        "category": "test",
        "source": "direct_upload_test"
    }
    
    try:
        print("🚀 Testing document upload to MongoDB Atlas...")
        print(f"URL: {url}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        response = requests.post(url, json=data)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📋 Response Content: {response.text}")
        
        if response.status_code == 200:
            print("✅ Upload successful!")
        else:
            print("❌ Upload failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_upload()
