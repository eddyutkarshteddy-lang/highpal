#!/usr/bin/env python3
"""
Check and clean up duplicate documents in MongoDB Atlas
"""
import requests
import json
from collections import defaultdict

def check_documents():
    """Check for duplicate documents"""
    try:
        # Get all documents
        response = requests.get("http://localhost:8002/documents")
        
        if response.status_code != 200:
            print(f"❌ Failed to get documents: {response.status_code}")
            return
            
        documents = response.json()
        print(f"📊 Total documents found: {len(documents['documents'])}")
        
        # Group documents by content/title to find duplicates
        content_groups = defaultdict(list)
        title_groups = defaultdict(list)
        
        for doc in documents['documents']:
            doc_id = doc.get('id', 'no-id')
            title = doc.get('title', 'no-title')
            content = doc.get('content', '')[:100]  # First 100 chars
            source = doc.get('source', 'unknown')
            
            print(f"\n📄 Document ID: {doc_id}")
            print(f"   Title: {title}")
            print(f"   Source: {source}")
            print(f"   Content preview: {content[:50]}...")
            
            # Group by title and content to find potential duplicates
            title_groups[title].append(doc_id)
            content_groups[content].append(doc_id)
        
        # Check for duplicates
        print(f"\n🔍 DUPLICATE ANALYSIS:")
        print(f"========================")
        
        for title, doc_ids in title_groups.items():
            if len(doc_ids) > 1:
                print(f"⚠️ Duplicate titles found for '{title}': {doc_ids}")
        
        for content_preview, doc_ids in content_groups.items():
            if len(doc_ids) > 1:
                print(f"⚠️ Duplicate content found: {doc_ids}")
                print(f"   Content: {content_preview}...")
                
        # Show statistics
        response = requests.get("http://localhost:8002/statistics")
        if response.status_code == 200:
            stats = response.json()
            print(f"\n📈 STATISTICS:")
            print(f"================")
            print(f"Total documents: {stats.get('total_documents', 'unknown')}")
            print(f"Total characters: {stats.get('total_characters', 'unknown')}")
            print(f"Storage type: {stats.get('storage_type', 'unknown')}")
            print(f"Connection status: {stats.get('connection_status', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_documents()
