"""
Simplified Haystack Document Manager for HighPal
Handles document storage and basic search without complex dependencies
"""

import json
import os
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleDocument:
    """Simple document class to replace Haystack Document"""
    def __init__(self, content: str, meta: dict = None, id: str = None):
        self.content = content
        self.meta = meta or {}
        self.id = id or str(uuid.uuid4())

class SimpleDocumentManager:
    """Simplified document management without complex Haystack dependencies"""
    
    def __init__(self, storage_path: str = "training_data.json"):
        """Initialize simple document manager"""
        self.storage_path = storage_path
        self.local_backup_path = "haystack_backup.json"
        self.documents = {}
        
        # Load existing documents
        self.load_existing_documents()
        
        logger.info("✅ Simple Document Manager initialized")
    
    def add_document(self, content: str, metadata: dict = None) -> str:
        """Add a document to the store"""
        doc_id = str(uuid.uuid4())
        
        document = {
            'id': doc_id,
            'content': content,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat()
        }
        
        self.documents[doc_id] = document
        self._save_to_backup()
        
        logger.info(f"📄 Added document {doc_id} ({len(content)} characters)")
        return doc_id
    
    def search_documents(self, query: str, method: str = "simple", top_k: int = 5) -> List[Dict]:
        """Simple text search in documents"""
        results = []
        query_lower = query.lower()
        
        for doc_id, doc in self.documents.items():
            content_lower = doc['content'].lower()
            
            # Simple keyword matching
            if query_lower in content_lower:
                # Calculate simple relevance score
                score = content_lower.count(query_lower) / len(content_lower.split())
                
                result = {
                    'id': doc_id,
                    'content': doc['content'],
                    'metadata': doc['metadata'],
                    'score': score
                }
                results.append(result)
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def get_all_documents(self) -> List[Dict]:
        """Get all documents"""
        return [
            {
                'id': doc_id,
                'content': doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content'],
                'metadata': doc['metadata'],
                'created_at': doc.get('created_at', 'Unknown')
            }
            for doc_id, doc in self.documents.items()
        ]
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """Get a document by ID"""
        return self.documents.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document"""
        if doc_id in self.documents:
            del self.documents[doc_id]
            self._save_to_backup()
            logger.info(f"🗑️ Deleted document {doc_id}")
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get document store statistics"""
        total_docs = len(self.documents)
        total_chars = sum(len(doc['content']) for doc in self.documents.values())
        avg_length = total_chars / total_docs if total_docs > 0 else 0
        
        # Count categories
        categories = {}
        for doc in self.documents.values():
            category = doc['metadata'].get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
        
        return {
            'total_documents': total_docs,
            'total_characters': total_chars,
            'average_document_length': avg_length,
            'categories': categories
        }
    
    def load_existing_documents(self):
        """Load documents from local storage"""
        # Try to load from backup first
        if os.path.exists(self.local_backup_path):
            try:
                with open(self.local_backup_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                    self.documents.update(backup_data)
                    logger.info(f"📂 Loaded {len(backup_data)} documents from backup")
            except Exception as e:
                logger.warning(f"Failed to load backup: {e}")
        
        # Also try to load from original training data
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    training_data = json.load(f)
                    
                    # Convert old format to new format
                    for doc_id, doc_data in training_data.items():
                        if doc_id not in self.documents:
                            if isinstance(doc_data, dict) and 'content' in doc_data:
                                self.documents[doc_id] = {
                                    'id': doc_id,
                                    'content': doc_data['content'],
                                    'metadata': {
                                        'filename': doc_data.get('filename', 'unknown'),
                                        'category': doc_data.get('category', 'training'),
                                        'source': 'migrated_training_data'
                                    },
                                    'created_at': doc_data.get('upload_date', datetime.now().isoformat())
                                }
                    
                    logger.info(f"📂 Migrated {len(training_data)} documents from training data")
            except Exception as e:
                logger.warning(f"Failed to load training data: {e}")
    
    def _save_to_backup(self):
        """Save documents to backup file"""
        try:
            with open(self.local_backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save backup: {e}")

# Global instance
_document_manager = None

def get_haystack_manager() -> SimpleDocumentManager:
    """Get the global document manager instance"""
    global _document_manager
    if _document_manager is None:
        _document_manager = SimpleDocumentManager()
    return _document_manager
