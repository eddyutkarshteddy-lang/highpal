"""
Haystack + MongoDB Atlas Integration for HighPal
Advanced document processing with semantic search and Q&A capabilities
"""

import os
import logging
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Haystack 2.x imports
from haystack import Document, Pipeline
from haystack.components.embedders import SentenceTransformersTextEmbedder, SentenceTransformersDocumentEmbedder
from haystack.components.retrievers import InMemoryEmbeddingRetriever
from haystack.components.writers import DocumentWriter
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.document_stores.types import DuplicatePolicy

# MongoDB for persistence
import pymongo
from bson import ObjectId

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HaystackMongoIntegration:
    """
    Advanced Haystack + MongoDB Atlas integration
    Features:
    - Dual storage: MongoDB Atlas (persistence) + Haystack (fast retrieval)
    - Semantic search with embeddings
    - Question answering with OpenAI
    - Document deduplication
    - Auto-sync between storage systems
    """
    
    def __init__(self):
        """Initialize Haystack components and MongoDB connection"""
        try:
            # MongoDB Atlas setup
            self.connection_string = os.getenv('MONGODB_CONNECTION_STRING')
            self.database_name = os.getenv('MONGODB_DATABASE', 'highpal_documents')
            self.collection_name = os.getenv('MONGODB_COLLECTION', 'documents')
            
            if not self.connection_string:
                raise ValueError("MongoDB connection string not found in environment variables")
            
            # Initialize MongoDB client
            self.mongo_client = pymongo.MongoClient(self.connection_string)
            self.db = self.mongo_client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            # Test MongoDB connection
            self.mongo_client.admin.command('ping')
            logger.info("✅ MongoDB Atlas connection successful!")
            
            # Create MongoDB indexes for better performance
            self._create_mongodb_indexes()
            
            # Initialize Haystack components
            self._initialize_haystack()
            
            # Load existing documents from MongoDB into Haystack
            self._sync_from_mongodb()
            
            logger.info("🚀 Haystack + MongoDB Atlas integration ready!")
            logger.info(f"📊 Database: {self.database_name}")
            logger.info(f"📂 Collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Haystack + MongoDB integration: {e}")
            raise
    
    def _create_mongodb_indexes(self):
        """Create indexes for better MongoDB query performance"""
        try:
            # Text search index
            self.collection.create_index([("content", "text"), ("filename", "text")])
            
            # Metadata indexes
            self.collection.create_index("filename")
            self.collection.create_index("file_type")
            self.collection.create_index("upload_date")
            self.collection.create_index("file_hash")
            
            # Embedding index for future vector search
            self.collection.create_index("embedding")
            
            logger.info("✅ MongoDB indexes created successfully")
        except Exception as e:
            logger.warning(f"⚠️ MongoDB index creation warning: {e}")
    
    def _initialize_haystack(self):
        """Initialize Haystack components and pipelines"""
        try:
            # Document store (in-memory for fast retrieval)
            self.document_store = InMemoryDocumentStore()
            
            # Embedders for semantic search
            embedding_model = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
            
            self.document_embedder = SentenceTransformersDocumentEmbedder(
                model=embedding_model,
                progress_bar=False
            )
            
            self.query_embedder = SentenceTransformersTextEmbedder(
                model=embedding_model,
                progress_bar=False
            )
            
            # Retriever for semantic search
            self.retriever = InMemoryEmbeddingRetriever(
                document_store=self.document_store
            )
            
            # Document writer
            self.writer = DocumentWriter(
                document_store=self.document_store,
                policy=DuplicatePolicy.OVERWRITE
            )
            
            # Create indexing pipeline
            self.indexing_pipeline = Pipeline()
            self.indexing_pipeline.add_component("embedder", self.document_embedder)
            self.indexing_pipeline.add_component("writer", self.writer)
            self.indexing_pipeline.connect("embedder", "writer")
            
            # Create search pipeline
            self.search_pipeline = Pipeline()
            self.search_pipeline.add_component("query_embedder", self.query_embedder)
            self.search_pipeline.add_component("retriever", self.retriever)
            self.search_pipeline.connect("query_embedder.embedding", "retriever.query_embedding")
            
            # Initialize Q&A pipeline if OpenAI key is available
            self._initialize_qa_pipeline()
            
            logger.info("✅ Haystack components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing Haystack: {e}")
            raise
    
    def _initialize_qa_pipeline(self):
        """Initialize Q&A pipeline with OpenAI (if API key is available)"""
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if openai_key and not openai_key.startswith('sk-test-dummy'):
            try:
                # Q&A pipeline components
                self.prompt_builder = PromptBuilder(
                    template="""
                    Based on the following documents, answer the question. If you cannot find the answer in the documents, say so.
                    
                    Documents:
                    {% for doc in documents %}
                    {{ doc.content }}
                    {% endfor %}
                    
                    Question: {{ question }}
                    Answer:
                    """
                )
                
                self.generator = OpenAIGenerator(
                    api_key=openai_key,
                    model="gpt-3.5-turbo",
                    generation_kwargs={"max_tokens": 500, "temperature": 0.3}
                )
                
                # Create Q&A pipeline
                self.qa_pipeline = Pipeline()
                self.qa_pipeline.add_component("query_embedder", self.query_embedder)
                self.qa_pipeline.add_component("retriever", self.retriever)
                self.qa_pipeline.add_component("prompt_builder", self.prompt_builder)
                self.qa_pipeline.add_component("generator", self.generator)
                
                # Connect components
                self.qa_pipeline.connect("query_embedder.embedding", "retriever.query_embedding")
                self.qa_pipeline.connect("retriever.documents", "prompt_builder.documents")
                self.qa_pipeline.connect("prompt_builder.prompt", "generator.prompt")
                
                self.qa_available = True
                logger.info("✅ Q&A pipeline with OpenAI initialized!")
                
            except Exception as e:
                logger.warning(f"⚠️ Q&A pipeline initialization failed: {e}")
                self.qa_available = False
        else:
            self.qa_available = False
            logger.info("ℹ️ Q&A pipeline disabled (no valid OpenAI API key)")
    
    def _sync_from_mongodb(self):
        """Load existing documents from MongoDB into Haystack"""
        try:
            mongo_docs = list(self.collection.find())
            
            if not mongo_docs:
                logger.info("ℹ️ No existing documents in MongoDB to sync")
                return
            
            haystack_docs = []
            for doc in mongo_docs:
                haystack_doc = Document(
                    content=doc.get('content', ''),
                    meta={
                        'filename': doc.get('filename', 'Unknown'),
                        'file_type': doc.get('file_type', 'Unknown'),
                        'upload_date': doc.get('upload_date', ''),
                        'file_size': doc.get('file_size', 0),
                        'user_id': doc.get('user_id', 'default'),
                        'tags': doc.get('tags', []),
                        'mongo_id': str(doc['_id']),
                        'source': 'mongodb_sync'
                    }
                )
                haystack_docs.append(haystack_doc)
            
            if haystack_docs:
                # Process documents through indexing pipeline
                result = self.indexing_pipeline.run({"embedder": {"documents": haystack_docs}})
                logger.info(f"✅ Synced {len(haystack_docs)} documents from MongoDB to Haystack")
            
        except Exception as e:
            logger.error(f"❌ Error syncing from MongoDB: {e}")
    
    def add_documents(self, documents_data: List[Dict[str, Any]]) -> int:
        """Add documents to both MongoDB and Haystack with deduplication"""
        try:
            documents_added = 0
            haystack_docs = []
            mongo_docs = []
            
            for doc_data in documents_data:
                content = doc_data.get('content', '').strip()
                if not content:
                    continue
                
                # Create file hash for deduplication
                file_hash = hashlib.md5(content.encode()).hexdigest()
                
                # Check if document already exists in MongoDB
                existing = self.collection.find_one({"file_hash": file_hash})
                if existing:
                    logger.info(f"⏭️ Skipping duplicate document: {doc_data.get('filename', 'Unknown')}")
                    continue
                
                # Prepare Haystack document
                haystack_doc = Document(
                    content=content,
                    meta={
                        'filename': doc_data.get('filename', 'Unknown'),
                        'file_type': doc_data.get('file_type', 'Unknown'),
                        'upload_date': doc_data.get('upload_date', datetime.now().isoformat()),
                        'file_size': doc_data.get('file_size', len(content)),
                        'user_id': doc_data.get('user_id', 'default'),
                        'tags': doc_data.get('tags', []),
                        'source': 'upload'
                    }
                )
                haystack_docs.append(haystack_doc)
                
                # Prepare MongoDB document
                mongo_doc = {
                    'content': content,
                    'filename': doc_data.get('filename', 'Unknown'),
                    'file_type': doc_data.get('file_type', 'Unknown'),
                    'upload_date': doc_data.get('upload_date', datetime.now().isoformat()),
                    'file_size': doc_data.get('file_size', len(content)),
                    'user_id': doc_data.get('user_id', 'default'),
                    'tags': doc_data.get('tags', []),
                    'file_hash': file_hash,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'source': 'upload'
                }
                mongo_docs.append(mongo_doc)
                documents_added += 1
            
            if haystack_docs and mongo_docs:
                # Save to MongoDB first (persistence)
                mongo_result = self.collection.insert_many(mongo_docs)
                logger.info(f"💾 Saved {len(mongo_result.inserted_ids)} documents to MongoDB Atlas")
                
                # Process through Haystack indexing pipeline
                haystack_result = self.indexing_pipeline.run({"embedder": {"documents": haystack_docs}})
                logger.info(f"🔍 Indexed {len(haystack_docs)} documents in Haystack for semantic search")
                
                logger.info(f"✅ Successfully added {documents_added} documents with dual storage")
            
            return documents_added
            
        except Exception as e:
            logger.error(f"❌ Error adding documents: {e}")
            raise
    
    def search_documents(self, query: str, top_k: int = 5, search_method: str = "semantic") -> List[Dict[str, Any]]:
        """
        Search documents using different methods
        
        Args:
            query: Search query
            top_k: Number of results to return
            search_method: "semantic" (Haystack) or "text" (MongoDB)
        """
        if search_method == "semantic":
            return self._semantic_search(query, top_k)
        elif search_method == "text":
            return self._text_search_mongodb(query, top_k)
        else:
            # Default to semantic search
            return self._semantic_search(query, top_k)
    
    def _semantic_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform semantic search using Haystack"""
        try:
            # Run search pipeline
            result = self.search_pipeline.run({
                "query_embedder": {"text": query},
                "retriever": {"top_k": top_k}
            })
            
            documents = result.get("retriever", {}).get("documents", [])
            
            search_results = []
            for doc in documents:
                search_results.append({
                    'content': doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                    'score': float(doc.score) if hasattr(doc, 'score') and doc.score else 0.0,
                    'filename': doc.meta.get('filename', 'Unknown'),
                    'file_type': doc.meta.get('file_type', 'Unknown'),
                    'upload_date': doc.meta.get('upload_date', ''),
                    'file_size': doc.meta.get('file_size', 0),
                    'tags': doc.meta.get('tags', []),
                    'search_method': 'semantic_haystack'
                })
            
            logger.info(f"🔍 Found {len(search_results)} documents using Haystack semantic search")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Semantic search error: {e}")
            return []
    
    def _text_search_mongodb(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform text search using MongoDB"""
        try:
            # Use MongoDB text search
            cursor = self.collection.find(
                {"$text": {"$search": query}},
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(top_k)
            
            results = []
            for doc in cursor:
                results.append({
                    'content': doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'],
                    'score': doc.get('score', 0.0),
                    'filename': doc.get('filename', 'Unknown'),
                    'file_type': doc.get('file_type', 'Unknown'),
                    'upload_date': doc.get('upload_date', ''),
                    'file_size': doc.get('file_size', 0),
                    'tags': doc.get('tags', []),
                    'search_method': 'text_mongodb'
                })
            
            logger.info(f"🔍 Found {len(results)} documents using MongoDB text search")
            return results
            
        except Exception as e:
            logger.error(f"❌ MongoDB text search error: {e}")
            return []
    
    def ask_question(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Ask questions about documents using Haystack Q&A pipeline"""
        if not self.qa_available:
            # Fallback to semantic search
            search_results = self.search_documents(question, top_k, "semantic")
            return {
                "answer": "Q&A functionality requires a valid OpenAI API key. Here are relevant documents:",
                "confidence": 0.0,
                "source_documents": search_results,
                "fallback": True
            }
        
        try:
            # Run Q&A pipeline
            result = self.qa_pipeline.run({
                "query_embedder": {"text": question},
                "retriever": {"top_k": top_k},
                "prompt_builder": {"question": question}
            })
            
            # Extract results
            answer = result.get("generator", {}).get("replies", ["No answer generated"])[0]
            documents = result.get("retriever", {}).get("documents", [])
            
            # Format source documents
            source_docs = []
            for doc in documents[:3]:  # Top 3 sources
                source_docs.append({
                    'filename': doc.meta.get('filename', 'Unknown'),
                    'content_preview': doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    'relevance_score': float(doc.score) if hasattr(doc, 'score') and doc.score else 0.0
                })
            
            qa_result = {
                "answer": answer,
                "confidence": 0.85,  # Placeholder confidence score
                "source_documents": source_docs,
                "question": question,
                "fallback": False
            }
            
            logger.info(f"❓ Answered question using Haystack Q&A: '{question[:50]}...'")
            return qa_result
            
        except Exception as e:
            logger.error(f"❌ Q&A error: {e}")
            # Fallback to search
            search_results = self.search_documents(question, top_k, "semantic")
            return {
                "answer": f"Error processing question: {str(e)}. Here are relevant documents:",
                "confidence": 0.0,
                "source_documents": search_results,
                "fallback": True
            }
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the integrated system"""
        try:
            # Haystack stats
            haystack_count = self.document_store.count_documents()
            
            # MongoDB stats
            mongo_count = self.collection.count_documents({})
            
            # File type distribution
            pipeline = [
                {"$group": {"_id": "$file_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            file_types = {doc["_id"]: doc["count"] for doc in self.collection.aggregate(pipeline)}
            
            # Recent uploads (last 7 days)
            from datetime import timedelta
            recent_cutoff = (datetime.now() - timedelta(days=7)).isoformat()
            recent_count = self.collection.count_documents({
                "upload_date": {"$gte": recent_cutoff}
            })
            
            return {
                "storage": {
                    "mongodb_documents": mongo_count,
                    "haystack_documents": haystack_count,
                    "in_sync": mongo_count == haystack_count,
                    "database": self.database_name,
                    "collection": self.collection_name
                },
                "capabilities": {
                    "semantic_search": True,
                    "text_search": True,
                    "question_answering": self.qa_available,
                    "embedding_model": os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
                },
                "content": {
                    "total_documents": max(mongo_count, haystack_count),
                    "file_types": file_types,
                    "recent_uploads_7_days": recent_count
                },
                "system": {
                    "storage_type": "Haystack + MongoDB Atlas",
                    "connection_status": "connected",
                    "features": [
                        "Dual Storage (MongoDB + Haystack)",
                        "Semantic Search with Embeddings",
                        "Traditional Text Search",
                        "Document Deduplication",
                        "Auto-Sync Between Systems",
                        "Q&A with OpenAI" if self.qa_available else "Q&A (Disabled - No OpenAI Key)",
                        "Cloud Storage (MongoDB Atlas)",
                        "Fast In-Memory Retrieval"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting comprehensive stats: {e}")
            return {"error": str(e)}
    
    def sync_documents(self) -> Dict[str, Any]:
        """Manually sync documents between MongoDB and Haystack"""
        try:
            # Clear Haystack document store
            self.document_store.delete_documents(filters={})
            
            # Reload from MongoDB
            self._sync_from_mongodb()
            
            stats = self.get_comprehensive_stats()
            logger.info("🔄 Manual sync completed successfully")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Sync error: {e}")
            return {"error": str(e)}
    
    def close(self):
        """Close MongoDB connection"""
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("✅ MongoDB Atlas connection closed")

# Test the integration
if __name__ == "__main__":
    try:
        # Initialize the integration
        haystack_mongo = HaystackMongoIntegration()
        
        # Test adding documents
        test_documents = [
            {
                "content": "Artificial Intelligence and Machine Learning are transforming modern healthcare through automated diagnosis, predictive analytics, and personalized treatment recommendations.",
                "filename": "ai_healthcare.txt",
                "file_type": "text/plain",
                "tags": ["AI", "healthcare", "machine learning"]
            },
            {
                "content": "Natural Language Processing enables computers to understand and process human language, making chatbots and virtual assistants more intelligent and helpful.",
                "filename": "nlp_guide.txt",
                "file_type": "text/plain",
                "tags": ["NLP", "AI", "chatbots"]
            }
        ]
        
        added = haystack_mongo.add_documents(test_documents)
        print(f"✅ Added {added} test documents")
        
        # Test semantic search
        print("\n🔍 Testing semantic search:")
        results = haystack_mongo.search_documents("medical AI applications", top_k=3, search_method="semantic")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['filename']} (score: {result['score']:.3f}, method: {result['search_method']})")
        
        # Test Q&A
        print("\n❓ Testing Q&A:")
        qa_result = haystack_mongo.ask_question("How is AI used in healthcare?")
        print(f"  Q: {qa_result['question']}")
        print(f"  A: {qa_result['answer']}")
        print(f"  Sources: {len(qa_result['source_documents'])} documents")
        print(f"  Fallback mode: {qa_result['fallback']}")
        
        # Get comprehensive stats
        stats = haystack_mongo.get_comprehensive_stats()
        print(f"\n📊 System Statistics:")
        print(f"  Total documents: {stats['content']['total_documents']}")
        print(f"  MongoDB docs: {stats['storage']['mongodb_documents']}")
        print(f"  Haystack docs: {stats['storage']['haystack_documents']}")
        print(f"  In sync: {stats['storage']['in_sync']}")
        print(f"  Q&A available: {stats['capabilities']['question_answering']}")
        print(f"  Features: {len(stats['system']['features'])}")
        
        haystack_mongo.close()
        print("\n🎉 Haystack + MongoDB Atlas integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
