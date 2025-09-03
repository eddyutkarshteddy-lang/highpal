"""
Simple MongoDB Atlas Integration for HighPal
Provides document storage with basic semantic search using sentence transformers
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import pymongo
import hashlib
import json

# For embeddings
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️ Sentence transformers not available. Install with: pip install sentence-transformers")

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleMongoDB:
    """
    Simple MongoDB Atlas integration with semantic search
    Features:
    - Document storage with metadata
    - Embedding-based semantic search
    - File deduplication
    - Statistics and management
    """
    
    def __init__(self):
        """Initialize MongoDB connection and embedding model"""
        try:
            # Get MongoDB connection details
            connection_string = os.getenv('MONGODB_CONNECTION_STRING')
            self.database_name = os.getenv('MONGODB_DATABASE', 'highpal_documents')
            self.collection_name = os.getenv('MONGODB_COLLECTION', 'documents')
            
            if not connection_string:
                raise ValueError("MongoDB connection string not found in environment variables")
            
            # Initialize MongoDB client
            self.client = pymongo.MongoClient(connection_string)
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("✅ MongoDB Atlas connection successful!")
            
            # Initialize embedding model if available
            self.embedding_model = None
            if EMBEDDINGS_AVAILABLE:
                try:
                    self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                    logger.info("✅ Sentence transformer model loaded!")
                except Exception as e:
                    logger.warning(f"⚠️ Could not load embedding model: {e}")
            
            # Create indexes for better performance
            self.create_indexes()
            
            logger.info(f"📊 Database: {self.database_name}")
            logger.info(f"📂 Collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize MongoDB store: {e}")
            raise
    
    def create_indexes(self):
        """Create indexes for better query performance"""
        try:
            # Create text index for full-text search
            self.collection.create_index([("content", "text"), ("filename", "text")])
            
            # Create indexes for metadata fields
            self.collection.create_index("filename")
            self.collection.create_index("file_type")
            self.collection.create_index("upload_date")
            self.collection.create_index("user_id")
            self.collection.create_index("file_hash")
            
            logger.info("✅ Database indexes created")
        except Exception as e:
            logger.warning(f"⚠️ Index creation warning: {e}")
    
    def add_documents(self, documents_data: List[Dict[str, Any]]) -> int:
        """
        Add documents to MongoDB with optional embeddings
        
        Args:
            documents_data: List of document dictionaries
            
        Returns:
            Number of documents added
        """
        try:
            documents_to_insert = []
            duplicates_skipped = 0
            
            for doc_data in documents_data:
                # Create file hash for deduplication
                content = doc_data.get('content', '')
                file_hash = hashlib.md5(content.encode()).hexdigest()
                
                # Check if document already exists
                existing = self.collection.find_one({"file_hash": file_hash})
                if existing:
                    logger.info(f"⏭️ Skipping duplicate: {doc_data.get('filename', 'Unknown')}")
                    duplicates_skipped += 1
                    continue
                
                # Create document with metadata
                document = {
                    'content': content,
                    'filename': doc_data.get('filename', ''),
                    'file_type': doc_data.get('file_type', ''),
                    'upload_date': doc_data.get('upload_date', datetime.now().isoformat()),
                    'file_size': doc_data.get('file_size', len(content)),
                    'user_id': doc_data.get('user_id', 'default_user'),
                    'tags': doc_data.get('tags', []),
                    'source': doc_data.get('source', 'upload'),
                    'language': doc_data.get('language', 'en'),
                    'file_hash': file_hash,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                
                # Add embeddings if model is available
                if self.embedding_model and content.strip():
                    try:
                        embedding = self.embedding_model.encode(content)
                        document['embedding'] = embedding.tolist()
                        document['embedding_model'] = 'all-MiniLM-L6-v2'
                    except Exception as e:
                        logger.warning(f"⚠️ Could not create embedding for {doc_data.get('filename', 'Unknown')}: {e}")
                
                documents_to_insert.append(document)
            
            # Insert documents
            if documents_to_insert:
                result = self.collection.insert_many(documents_to_insert)
                logger.info(f"✅ Added {len(result.inserted_ids)} documents to MongoDB")
                
                if duplicates_skipped > 0:
                    logger.info(f"⏭️ Skipped {duplicates_skipped} duplicate documents")
                
                return len(result.inserted_ids)
            else:
                logger.info("ℹ️ No new documents to add")
                return 0
            
        except Exception as e:
            logger.error(f"❌ Error adding documents: {e}")
            raise
    
    def search_documents(self, query: str, top_k: int = 5, search_type: str = "semantic") -> List[Dict[str, Any]]:
        """
        Search documents using different methods
        
        Args:
            query: Search query
            top_k: Number of results to return
            search_type: "semantic", "text", or "hybrid"
            
        Returns:
            List of matching documents with scores
        """
        try:
            results = []
            
            if search_type == "semantic" and self.embedding_model:
                results = self._semantic_search(query, top_k)
            elif search_type == "text":
                results = self._text_search(query, top_k)
            elif search_type == "hybrid" and self.embedding_model:
                # Combine semantic and text search results
                semantic_results = self._semantic_search(query, top_k // 2 + 1)
                text_results = self._text_search(query, top_k // 2 + 1)
                
                # Merge and deduplicate results
                seen_ids = set()
                results = []
                
                for result in semantic_results + text_results:
                    doc_id = str(result.get('_id', ''))
                    if doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        results.append(result)
                        if len(results) >= top_k:
                            break
            else:
                # Fallback to text search
                results = self._text_search(query, top_k)
            
            logger.info(f"🔍 Found {len(results)} documents for query: '{query}' (method: {search_type})")
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []
    
    def _semantic_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform semantic search using embeddings"""
        if not self.embedding_model:
            return []
        
        # Create query embedding
        query_embedding = self.embedding_model.encode(query)
        
        # Find documents with embeddings
        pipeline = [
            {"$match": {"embedding": {"$exists": True}}},
            {"$limit": 1000}  # Limit for performance
        ]
        
        documents = list(self.collection.aggregate(pipeline))
        
        if not documents:
            return []
        
        # Calculate similarities
        similarities = []
        for doc in documents:
            if 'embedding' in doc:
                doc_embedding = np.array(doc['embedding'])
                similarity = np.dot(query_embedding, doc_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)
                )
                similarities.append((similarity, doc))
        
        # Sort by similarity and return top results
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for similarity, doc in similarities[:top_k]:
            result = {
                '_id': doc['_id'],
                'content': doc['content'],
                'score': float(similarity),
                'filename': doc.get('filename', 'Unknown'),
                'file_type': doc.get('file_type', 'Unknown'),
                'upload_date': doc.get('upload_date', ''),
                'file_size': doc.get('file_size', 0),
                'tags': doc.get('tags', []),
                'search_method': 'semantic'
            }
            results.append(result)
        
        return results
    
    def _text_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform text search using MongoDB text index"""
        try:
            # Use MongoDB text search
            cursor = self.collection.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(top_k)
            
            results = []
            for doc in cursor:
                result = {
                    '_id': doc['_id'],
                    'content': doc['content'],
                    'score': doc.get('score', 0.0),
                    'filename': doc.get('filename', 'Unknown'),
                    'file_type': doc.get('file_type', 'Unknown'),
                    'upload_date': doc.get('upload_date', ''),
                    'file_size': doc.get('file_size', 0),
                    'tags': doc.get('tags', []),
                    'search_method': 'text'
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.warning(f"⚠️ Text search failed, using regex fallback: {e}")
            return self._regex_search(query, top_k)
    
    def _regex_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Fallback regex search"""
        cursor = self.collection.find(
            {"$or": [
                {"content": {"$regex": query, "$options": "i"}},
                {"filename": {"$regex": query, "$options": "i"}}
            ]}
        ).limit(top_k)
        
        results = []
        for doc in cursor:
            result = {
                '_id': doc['_id'],
                'content': doc['content'],
                'score': 1.0,  # Fixed score for regex
                'filename': doc.get('filename', 'Unknown'),
                'file_type': doc.get('file_type', 'Unknown'),
                'upload_date': doc.get('upload_date', ''),
                'file_size': doc.get('file_size', 0),
                'tags': doc.get('tags', []),
                'search_method': 'regex'
            }
            results.append(result)
        
        return results
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about stored documents"""
        try:
            total_docs = self.collection.count_documents({})
            docs_with_embeddings = self.collection.count_documents({"embedding": {"$exists": True}})
            
            # Get file type distribution
            pipeline = [
                {"$group": {"_id": "$file_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            file_types = {doc["_id"]: doc["count"] for doc in self.collection.aggregate(pipeline)}
            
            # Get recent uploads
            from datetime import timedelta
            recent_docs = self.collection.count_documents({
                "upload_date": {"$gte": (datetime.now() - timedelta(days=7)).isoformat()}
            })
            
            stats = {
                'total_documents': total_docs,
                'documents_with_embeddings': docs_with_embeddings,
                'embedding_coverage': f"{(docs_with_embeddings/total_docs*100):.1f}%" if total_docs > 0 else "0%",
                'database': self.database_name,
                'collection': self.collection_name,
                'file_types': file_types,
                'recent_uploads_7_days': recent_docs,
                'storage_type': 'MongoDB Atlas + Simple Embeddings',
                'features': [
                    'Document Storage',
                    'Semantic Search' if EMBEDDINGS_AVAILABLE else 'Text Search Only',
                    'File Deduplication',
                    'Metadata Support',
                    'Cloud Storage'
                ]
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {'error': str(e)}
    
    def delete_documents(self, filters: Optional[Dict] = None, document_ids: Optional[List[str]] = None) -> int:
        """Delete documents from the store"""
        try:
            if document_ids:
                from bson import ObjectId
                result = self.collection.delete_many({"_id": {"$in": [ObjectId(id) for id in document_ids]}})
            elif filters:
                result = self.collection.delete_many(filters)
            else:
                logger.warning("⚠️ No filters or IDs provided for deletion")
                return 0
            
            deleted = result.deleted_count
            logger.info(f"🗑️ Deleted {deleted} documents")
            return deleted
            
        except Exception as e:
            logger.error(f"❌ Error deleting documents: {e}")
            return 0
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("✅ MongoDB connection closed")

# Test the connection if run directly
if __name__ == "__main__":
    try:
        # Test initialization
        store = SimpleMongoDB()
        
        # Test adding a sample document
        test_doc = [{
            'content': 'This is a test document for HighPal AI Assistant. It demonstrates the simple MongoDB integration with semantic search capabilities.',
            'filename': 'test_document.txt',
            'file_type': 'text/plain',
            'tags': ['test', 'demo', 'mongodb']
        }]
        
        added = store.add_documents(test_doc)
        print(f"✅ Added {added} documents")
        
        # Test different search methods
        print("\n🔍 Testing semantic search:")
        results = store.search_documents('HighPal AI Assistant', top_k=3, search_type="semantic")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['filename']} (score: {result['score']:.3f}, method: {result['search_method']})")
        
        print("\n🔍 Testing text search:")
        results = store.search_documents('test document', top_k=3, search_type="text")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['filename']} (score: {result['score']:.3f}, method: {result['search_method']})")
        
        # Test stats
        stats = store.get_document_stats()
        print(f"\n📊 Document stats:")
        print(f"  Total documents: {stats['total_documents']}")
        print(f"  With embeddings: {stats['documents_with_embeddings']}")
        print(f"  Embedding coverage: {stats['embedding_coverage']}")
        print(f"  File types: {stats['file_types']}")
        
        store.close()
        print("\n✅ Simple MongoDB integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
