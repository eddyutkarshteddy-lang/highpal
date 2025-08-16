#!/usr/bin/env python3
"""
Script to check Elasticsearch connection and setup the document store
"""

import os
import time
import requests
from elasticsearch import Elasticsearch
from haystack.document_stores import ElasticsearchDocumentStore

def check_elasticsearch_connection(host="localhost", port=9200, max_retries=5):
    """Check if Elasticsearch is running"""
    url = f"http://{host}:{port}"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(f"{url}/_cluster/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ Elasticsearch is running at {url}")
                return True
        except requests.ConnectionError:
            print(f"⏳ Attempt {attempt + 1}: Waiting for Elasticsearch at {url}...")
            time.sleep(2)
    
    print(f"❌ Could not connect to Elasticsearch at {url}")
    return False

def setup_document_store():
    """Initialize the document store"""
    try:
        document_store = ElasticsearchDocumentStore(
            hosts=["http://localhost:9200"],
            index="highpal_documents"
        )
        print("✅ Document store initialized successfully")
        
        # Test basic operations
        count = document_store.count_documents()
        print(f"📊 Current document count: {count}")
        
        return document_store
    except Exception as e:
        print(f"❌ Failed to initialize document store: {e}")
        return None

def print_elasticsearch_info():
    """Print helpful information about Elasticsearch setup"""
    print("\n" + "="*60)
    print("🔍 ELASTICSEARCH SETUP INFORMATION")
    print("="*60)
    print("""
To install and run Elasticsearch:

1. Using Docker (Recommended):
   docker run -d --name elasticsearch \\
     -p 9200:9200 -p 9300:9300 \\
     -e "discovery.type=single-node" \\
     -e "xpack.security.enabled=false" \\
     elasticsearch:8.11.0

2. Using Docker Compose (create docker-compose.yml):
   version: '3.8'
   services:
     elasticsearch:
       image: elasticsearch:8.11.0
       environment:
         - discovery.type=single-node
         - xpack.security.enabled=false
       ports:
         - "9200:9200"
         - "9300:9300"

3. Download and install from:
   https://www.elastic.co/downloads/elasticsearch

After starting Elasticsearch:
- Web interface: http://localhost:9200
- Health check: http://localhost:9200/_cluster/health
- Indices: http://localhost:9200/_cat/indices?v
""")
    print("="*60)

if __name__ == "__main__":
    print("🚀 HighPal Elasticsearch Setup")
    print("-" * 30)
    
    if check_elasticsearch_connection():
        document_store = setup_document_store()
        if document_store:
            print("🎉 Setup completed successfully!")
        else:
            print("⚠️  Document store setup failed")
    else:
        print_elasticsearch_info()
