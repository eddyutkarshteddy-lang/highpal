"""
Cloud-enabled Haystack Document Manager for HighPal
Supports both local and cloud storage (MongoDB, PostgreSQL, etc.)
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

class CloudDocumentManager:
    """Document manager with cloud storage capabilities"""
    
    def __init__(self, storage_type: str = "local", connection_string: str = None):
        """
        Initialize cloud document manager
        
        Args:
            storage_type: "local", "mongodb", "postgresql", "firebase"
            connection_string: Connection string for cloud database
        """
        self.storage_type = storage_type
        self.connection_string = connection_string
        self.documents = {}
        
        # Local backup files
        self.local_backup_path = "haystack_backup.json"
        self.local_storage_path = "training_data.json"
        
        # Initialize storage backend
        self._init_storage_backend()
        
        # Load existing documents
        self.load_existing_documents()
        
        logger.info(f"✅ Cloud Document Manager initialized (Storage: {storage_type})")
    
    def _init_storage_backend(self):
        """Initialize the selected storage backend"""
        if self.storage_type == "mongodb":
            self._init_mongodb()
        elif self.storage_type == "postgresql":
            self._init_postgresql()
        elif self.storage_type == "firebase":
            self._init_firebase()
        else:
            logger.info("📁 Using local storage")
    
    def _init_mongodb(self):
        """Initialize MongoDB connection"""
        try:
            from pymongo import MongoClient
            self.mongo_client = MongoClient(self.connection_string)
            self.mongo_db = self.mongo_client.haystack_documents
            self.mongo_collection = self.mongo_db.documents
            logger.info("✅ MongoDB connection established")
        except ImportError:
            logger.error("❌ pymongo not installed. Run: pip install pymongo")
            self.storage_type = "local"
        except Exception as e:
            logger.error(f"❌ MongoDB connection failed: {e}")
            self.storage_type = "local"
    
    def _init_postgresql(self):
        """Initialize PostgreSQL connection"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            self.pg_conn = psycopg2.connect(self.connection_string)
            self.pg_cursor = self.pg_conn.cursor(cursor_factory=RealDictCursor)
            
            # Create table if not exists
            self.pg_cursor.execute("""
                CREATE TABLE IF NOT EXISTS haystack_documents (
                    id VARCHAR PRIMARY KEY,
                    content TEXT,
                    metadata JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.pg_conn.commit()
            logger.info("✅ PostgreSQL connection established")
        except ImportError:
            logger.error("❌ psycopg2 not installed. Run: pip install psycopg2-binary")
            self.storage_type = "local"
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            self.storage_type = "local"
    
    def _init_firebase(self):
        """Initialize Firebase connection"""
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            # Initialize Firebase (requires service account key)
            if not firebase_admin._apps:
                cred = credentials.Certificate("firebase-service-account.json")
                firebase_admin.initialize_app(cred)
            
            self.firestore_db = firestore.client()
            logger.info("✅ Firebase connection established")
        except ImportError:
            logger.error("❌ firebase-admin not installed. Run: pip install firebase-admin")
            self.storage_type = "local"
        except Exception as e:
            logger.error(f"❌ Firebase connection failed: {e}")
            self.storage_type = "local"
    
    def add_document(self, content: str, metadata: dict = None) -> str:
        """Add a document to the store (cloud or local)"""
        doc_id = str(uuid.uuid4())
        
        document = {
            'id': doc_id,
            'content': content,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat()
        }
        
        # Store in memory for fast access
        self.documents[doc_id] = document
        
        # Save to cloud or local storage
        if self.storage_type == "mongodb":
            self._save_to_mongodb(document)
        elif self.storage_type == "postgresql":
            self._save_to_postgresql(document)
        elif self.storage_type == "firebase":
            self._save_to_firebase(document)
        else:
            self._save_to_local(document)
        
        logger.info(f"📄 Added document {doc_id} ({len(content)} characters) to {self.storage_type}")
        return doc_id
    
    def _save_to_mongodb(self, document: dict):
        """Save document to MongoDB"""
        try:
            result = self.mongo_collection.insert_one(document)
            logger.debug(f"📊 Saved to MongoDB: {result.inserted_id}")
        except Exception as e:
            logger.error(f"❌ MongoDB save failed: {e}")
            self._save_to_local(document)  # Fallback to local
    
    def _save_to_postgresql(self, document: dict):
        """Save document to PostgreSQL"""
        try:
            self.pg_cursor.execute("""
                INSERT INTO haystack_documents (id, content, metadata, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    created_at = EXCLUDED.created_at
            """, (
                document['id'],
                document['content'],
                json.dumps(document['metadata']),
                document['created_at']
            ))
            self.pg_conn.commit()
            logger.debug(f"🐘 Saved to PostgreSQL: {document['id']}")
        except Exception as e:
            logger.error(f"❌ PostgreSQL save failed: {e}")
            self._save_to_local(document)  # Fallback to local
    
    def _save_to_firebase(self, document: dict):
        """Save document to Firebase"""
        try:
            doc_ref = self.firestore_db.collection('haystack_documents').document(document['id'])
            doc_ref.set(document)
            logger.debug(f"🔥 Saved to Firebase: {document['id']}")
        except Exception as e:
            logger.error(f"❌ Firebase save failed: {e}")
            self._save_to_local(document)  # Fallback to local
    
    def _save_to_local(self, document: dict):
        """Save document to local JSON file"""
        try:
            with open(self.local_backup_path, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Local save failed: {e}")
    
    def load_existing_documents(self):
        """Load documents from cloud or local storage"""
        if self.storage_type == "mongodb":
            self._load_from_mongodb()
        elif self.storage_type == "postgresql":
            self._load_from_postgresql()
        elif self.storage_type == "firebase":
            self._load_from_firebase()
        else:
            self._load_from_local()
    
    def _load_from_mongodb(self):
        """Load documents from MongoDB"""
        try:
            cursor = self.mongo_collection.find()
            for doc in cursor:
                doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
                self.documents[doc['id']] = doc
            logger.info(f"📊 Loaded {len(self.documents)} documents from MongoDB")
        except Exception as e:
            logger.error(f"❌ MongoDB load failed: {e}")
            self._load_from_local()  # Fallback to local
    
    def _load_from_postgresql(self):
        """Load documents from PostgreSQL"""
        try:
            self.pg_cursor.execute("SELECT * FROM haystack_documents")
            rows = self.pg_cursor.fetchall()
            for row in rows:
                doc = {
                    'id': row['id'],
                    'content': row['content'],
                    'metadata': row['metadata'],
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None
                }
                self.documents[doc['id']] = doc
            logger.info(f"🐘 Loaded {len(self.documents)} documents from PostgreSQL")
        except Exception as e:
            logger.error(f"❌ PostgreSQL load failed: {e}")
            self._load_from_local()  # Fallback to local
    
    def _load_from_firebase(self):
        """Load documents from Firebase"""
        try:
            docs = self.firestore_db.collection('haystack_documents').stream()
            for doc in docs:
                doc_data = doc.to_dict()
                self.documents[doc_data['id']] = doc_data
            logger.info(f"🔥 Loaded {len(self.documents)} documents from Firebase")
        except Exception as e:
            logger.error(f"❌ Firebase load failed: {e}")
            self._load_from_local()  # Fallback to local
    
    def _load_from_local(self):
        """Load documents from local storage"""
        # Load from backup
        if os.path.exists(self.local_backup_path):
            try:
                with open(self.local_backup_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                    self.documents.update(backup_data)
                    logger.info(f"📂 Loaded {len(backup_data)} documents from local backup")
            except Exception as e:
                logger.warning(f"Failed to load backup: {e}")
        
        # Load from training data
        if os.path.exists(self.local_storage_path):
            try:
                with open(self.local_storage_path, 'r', encoding='utf-8') as f:
                    training_data = json.load(f)
                    for doc_id, doc_data in training_data.items():
                        if doc_id not in self.documents and isinstance(doc_data, dict) and 'content' in doc_data:
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
    
    def search_documents(self, query: str, method: str = "simple", top_k: int = 5) -> List[Dict]:
        """Simple text search in documents"""
        results = []
        query_lower = query.lower()
        
        for doc_id, doc in self.documents.items():
            content_lower = doc['content'].lower()
            if query_lower in content_lower:
                score = content_lower.count(query_lower) / len(content_lower.split())
                results.append({
                    'id': doc_id,
                    'content': doc['content'],
                    'metadata': doc['metadata'],
                    'score': score
                })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def get_all_documents(self) -> List[Dict]:
        """Get all documents"""
        return [
            {
                'id': doc_id,
                'content': doc['content'][:200] + '...' if len(doc['content']) > 200 else doc['content'],
                'metadata': doc['metadata'],
                'created_at': doc.get('created_at', 'Unknown'),
                'storage': self.storage_type
            }
            for doc_id, doc in self.documents.items()
        ]
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """Get a document by ID"""
        return self.documents.get(doc_id)
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from cloud and local storage"""
        if doc_id in self.documents:
            # Delete from memory
            del self.documents[doc_id]
            
            # Delete from cloud storage
            if self.storage_type == "mongodb":
                self.mongo_collection.delete_one({'id': doc_id})
            elif self.storage_type == "postgresql":
                self.pg_cursor.execute("DELETE FROM haystack_documents WHERE id = %s", (doc_id,))
                self.pg_conn.commit()
            elif self.storage_type == "firebase":
                self.firestore_db.collection('haystack_documents').document(doc_id).delete()
            
            # Update local backup
            self._save_to_local({'id': 'dummy'})  # This will save all documents
            
            logger.info(f"🗑️ Deleted document {doc_id} from {self.storage_type}")
            return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get document store statistics"""
        total_docs = len(self.documents)
        total_chars = sum(len(doc['content']) for doc in self.documents.values())
        avg_length = total_chars / total_docs if total_docs > 0 else 0
        
        categories = {}
        for doc in self.documents.values():
            category = doc['metadata'].get('category', 'unknown')
            categories[category] = categories.get(category, 0) + 1
        
        return {
            'total_documents': total_docs,
            'total_characters': total_chars,
            'average_document_length': avg_length,
            'categories': categories,
            'storage_type': self.storage_type,
            'connection_status': 'connected' if self.storage_type != 'local' else 'local'
        }

# Global instance
_cloud_manager = None

def get_cloud_haystack_manager(storage_type: str = "local", connection_string: str = None) -> CloudDocumentManager:
    """Get the global cloud document manager instance"""
    global _cloud_manager
    if _cloud_manager is None:
        _cloud_manager = CloudDocumentManager(storage_type, connection_string)
    return _cloud_manager
