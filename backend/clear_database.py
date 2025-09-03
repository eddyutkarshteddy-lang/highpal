#!/usr/bin/env python3
"""
Clear all documents from MongoDB Atlas database
"""
import requests
import json

def clear_all_documents():
    """Delete all documents from the database"""
    try:
        print("🧹 Starting database cleanup...")
        
        # First, get all documents to see what we're deleting
        print("📋 Getting current documents...")
        response = requests.get("http://localhost:8002/documents")
        
        if response.status_code != 200:
            print(f"❌ Failed to get documents: {response.status_code}")
            return
            
        documents = response.json()
        doc_list = documents.get('documents', [])
        print(f"📊 Found {len(doc_list)} documents to delete")
        
        # Delete each document
        deleted_count = 0
        failed_count = 0
        
        for doc in doc_list:
            doc_id = doc.get('id')
            title = doc.get('title', 'Untitled')[:50]
            
            if doc_id:
                print(f"🗑️  Deleting: {title} (ID: {doc_id[:8]}...)")
                
                # Use the delete endpoint
                delete_url = f"http://localhost:8002/documents/{doc_id}"
                delete_response = requests.delete(delete_url)
                
                if delete_response.status_code == 200:
                    deleted_count += 1
                    print(f"   ✅ Deleted successfully")
                else:
                    failed_count += 1
                    print(f"   ❌ Failed to delete: {delete_response.status_code}")
            else:
                print(f"⚠️  Document without ID, skipping: {title}")
        
        print(f"\n🎯 CLEANUP RESULTS:")
        print(f"================")
        print(f"✅ Successfully deleted: {deleted_count}")
        print(f"❌ Failed to delete: {failed_count}")
        print(f"📊 Total processed: {len(doc_list)}")
        
        # Check final status
        print(f"\n🔍 Checking final status...")
        final_response = requests.get("http://localhost:8002/statistics")
        if final_response.status_code == 200:
            stats = final_response.json()
            remaining_docs = stats.get('total_documents', 'unknown')
            print(f"📈 Documents remaining: {remaining_docs}")
            
            if remaining_docs == 0:
                print(f"🎉 SUCCESS! Database is now clean and ready for fresh uploads!")
            else:
                print(f"⚠️  Still {remaining_docs} documents remaining")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    print("🚨 WARNING: This will delete ALL documents from MongoDB Atlas!")
    print("Press Ctrl+C to cancel, or wait 3 seconds to continue...")
    
    import time
    for i in range(3, 0, -1):
        print(f"⏳ Starting cleanup in {i}...")
        time.sleep(1)
    
    print("🧹 Starting cleanup now!\n")
    clear_all_documents()
