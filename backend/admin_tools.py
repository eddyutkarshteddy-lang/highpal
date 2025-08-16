#!/usr/bin/env python3
"""
Admin tools for managing training data and knowledge base
Use this to add your curated training data, not user documents
"""

import os
import sys
import hashlib
from pathlib import Path
from typing import List, Dict
import json

# Add the backend directory to the path so we can import main modules
sys.path.append(str(Path(__file__).parent))

def add_training_document(content: str, category: str, metadata: Dict = None):
    """
    Add a training document to the knowledge base
    
    Args:
        content: The text content to index
        category: Category/type of training data (e.g., 'company_info', 'product_features')
        metadata: Additional metadata
    """
    try:
        from main import document_store, indexing_pipeline, Document
        
        if not indexing_pipeline:
            print("❌ Haystack not available. Training data will be stored in fallback only.")
            return False
            
        doc_id = hashlib.md5(content.encode()).hexdigest()
        
        # Create document with training data metadata
        doc_metadata = {
            "doc_id": doc_id,
            "category": category,
            "source": "training_data",
            "type": "knowledge_base",
            "admin_added": True
        }
        
        if metadata:
            doc_metadata.update(metadata)
            
        document = Document(
            content=content,
            meta=doc_metadata
        )
        
        # Index the training document
        indexing_pipeline.run({"embedder": {"documents": [document]}})
        print(f"✅ Added training document to category: {category}")
        return True
        
    except Exception as e:
        print(f"❌ Error adding training document: {e}")
        return False

def bulk_import_training_data(training_folder: str):
    """
    Import all documents from a training data folder
    
    Args:
        training_folder: Path to folder containing training documents
    """
    folder_path = Path(training_folder)
    if not folder_path.exists():
        print(f"❌ Training folder not found: {training_folder}")
        return
        
    processed = 0
    for file_path in folder_path.glob("*.txt"):
        try:
            content = file_path.read_text(encoding='utf-8')
            category = file_path.stem  # Use filename as category
            
            if add_training_document(content, category):
                processed += 1
                print(f"📄 Processed: {file_path.name}")
                
        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")
            
    print(f"✅ Imported {processed} training documents")

def add_faq_data(faq_file: str):
    """
    Import FAQ data from JSON file
    
    Args:
        faq_file: Path to JSON file with FAQ data
    """
    try:
        with open(faq_file, 'r', encoding='utf-8') as f:
            faq_data = json.load(f)
            
        for item in faq_data:
            question = item.get('question', '')
            answer = item.get('answer', '')
            category = item.get('category', 'faq')
            
            # Combine question and answer for better search
            content = f"Q: {question}\nA: {answer}"
            
            metadata = {
                "question": question,
                "answer": answer,
                "faq_item": True
            }
            
            add_training_document(content, category, metadata)
            
        print(f"✅ Imported FAQ data from {faq_file}")
        
    except Exception as e:
        print(f"❌ Error importing FAQ data: {e}")

def clear_training_data():
    """Clear all training data (keeps user documents)"""
    try:
        from main import document_store
        
        if document_store:
            # Only delete documents marked as training data
            document_store.delete_documents(filters={"source": "training_data"})
            print("✅ Cleared all training data")
        else:
            print("❌ Document store not available")
            
    except Exception as e:
        print(f"❌ Error clearing training data: {e}")

def list_training_data():
    """List all training data categories and counts"""
    try:
        from main import document_store
        
        if document_store:
            # Get all training documents
            training_docs = document_store.filter_documents(filters={"source": "training_data"})
            
            categories = {}
            for doc in training_docs:
                category = doc.meta.get('category', 'unknown')
                categories[category] = categories.get(category, 0) + 1
                
            print("📊 Training Data Summary:")
            for category, count in categories.items():
                print(f"  - {category}: {count} documents")
                
            print(f"Total training documents: {sum(categories.values())}")
        else:
            print("❌ Document store not available")
            
    except Exception as e:
        print(f"❌ Error listing training data: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Admin tools for managing training data")
    parser.add_argument('action', choices=['add', 'bulk', 'faq', 'clear', 'list'], 
                       help='Action to perform')
    parser.add_argument('--content', help='Content to add (for add action)')
    parser.add_argument('--category', help='Category for the content')
    parser.add_argument('--folder', help='Folder path for bulk import')
    parser.add_argument('--file', help='File path for FAQ import')
    
    args = parser.parse_args()
    
    if args.action == 'add':
        if not args.content or not args.category:
            print("❌ --content and --category are required for add action")
        else:
            add_training_document(args.content, args.category)
            
    elif args.action == 'bulk':
        if not args.folder:
            print("❌ --folder is required for bulk action")
        else:
            bulk_import_training_data(args.folder)
            
    elif args.action == 'faq':
        if not args.file:
            print("❌ --file is required for faq action")
        else:
            add_faq_data(args.file)
            
    elif args.action == 'clear':
        clear_training_data()
        
    elif args.action == 'list':
        list_training_data()
