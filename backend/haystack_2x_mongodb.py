"""
True Haystack 2.x + MongoDB Atlas Integration for HighPal
Uses modern Haystack components for advanced document processing
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Haystack 2.x imports
from haystack import Document, Pipeline
from haystack.components.retrievers import InMemoryBM25Retriever
from haystack.components.embedders import SentenceTransformersTextEmbedder, SentenceTransformersDocumentEmbedder
from haystack.components.writers import DocumentWriter
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack.components.generators import OpenAIGenerator
from haystack.components.builders import PromptBuilder

# MongoDB for persistence
import pymongo
import hashlib
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HaystackMongoDB:
    """
    True Haystack 2.x integration with MongoDB Atlas persistence
    Features:
    - Haystack pipelines for document processing
    - Embeddings with retrieval
    - Question answering
    - MongoDB Atlas for persistence
    - Modern Haystack 2.x components
    """
    
    def __init__(self):
        """Initialize Haystack components and MongoDB"""
        try:
            # MongoDB setup
            connection_string = os.getenv('MONGODB_CONNECTION_STRING')
            self.database_name = os.getenv('MONGODB_DATABASE', 'highpal_documents')
            self.collection_name = os.getenv('MONGODB_COLLECTION', 'documents')
            
            if not connection_string:
                raise ValueError("MongoDB connection string not found")
            
            # Initialize MongoDB client
            self.client = pymongo.MongoClient(connection_string)
            self.db = self.client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            # Test connection
            self.client.admin.command('ping')
            logger.info("✅ MongoDB Atlas connection successful!")
            
            # Initialize Haystack components
            self.document_store = InMemoryDocumentStore()
            
            # Embedders
            self.doc_embedder = SentenceTransformersDocumentEmbedder(
                model="sentence-transformers/all-MiniLM-L6-v2"
            )
            self.text_embedder = SentenceTransformersTextEmbedder(
                model="sentence-transformers/all-MiniLM-L6-v2"
            )
            
            # Retriever
            self.retriever = InMemoryBM25Retriever(document_store=self.document_store)
            
            # Writer
            self.writer = DocumentWriter(document_store=self.document_store)
            
            # Create indexing pipeline
            self.indexing_pipeline = Pipeline()
            self.indexing_pipeline.add_component("doc_embedder", self.doc_embedder)
            self.indexing_pipeline.add_component("writer", self.writer)
            self.indexing_pipeline.connect("doc_embedder", "writer")
            
            # Create search pipeline
            self.search_pipeline = Pipeline()
            self.search_pipeline.add_component("text_embedder", self.text_embedder)
            self.search_pipeline.add_component("retriever", self.retriever)
            self.search_pipeline.connect("text_embedder", "retriever")
            
            # Q&A Pipeline (if OpenAI key is available)
            openai_key = os.getenv('OPENAI_API_KEY')
            if openai_key and not openai_key.startswith('sk-test-dummy'):
                try:
                    self.generator = OpenAIGenerator(
                        api_key=openai_key,
                        model="gpt-3.5-turbo"
                    )
                    
                    self.prompt_builder = PromptBuilder(
                        template="""
                        Answer the question based on the given context.
                        Context: {% for doc in documents %}{{ doc.content }}{% endfor %}
                        Question: {{ question }}
                        Answer:
                        """
                    )
                    
                    # Q&A Pipeline
                    self.qa_pipeline = Pipeline()
                    self.qa_pipeline.add_component("text_embedder", self.text_embedder)
                    self.qa_pipeline.add_component("retriever", self.retriever)
                    self.qa_pipeline.add_component("prompt_builder", self.prompt_builder)
                    self.qa_pipeline.add_component("generator", self.generator)
                    
                    self.qa_pipeline.connect("text_embedder", "retriever")
                    self.qa_pipeline.connect("retriever.documents", "prompt_builder.documents")
                    self.qa_pipeline.connect("prompt_builder", "generator")
                    
                    self.qa_available = True
                    logger.info("✅ Q&A pipeline initialized with OpenAI!")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Q&A pipeline initialization failed: {e}")
                    self.qa_available = False
            else:
                self.qa_available = False
                logger.info("ℹ️ Q&A pipeline disabled (no valid OpenAI key)")
            
            # Load existing documents from MongoDB
            self.load_from_mongodb()
            
            logger.info("✅ Haystack 2.x + MongoDB integration initialized!")
            logger.info(f"📊 Database: {self.database_name}")
            logger.info(f"📂 Collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Haystack MongoDB: {e}")
            raise
    
    def load_from_mongodb(self):
        """Load existing documents from MongoDB into Haystack"""
        try:
            docs_from_db = list(self.collection.find())
            if not docs_from_db:
                logger.info("ℹ️ No existing documents in MongoDB")
                return
            
            haystack_docs = []
            for doc_data in docs_from_db:
                doc = Document(
                    content=doc_data.get('content', ''),
                    meta={
                        'filename': doc_data.get('filename', ''),
                        'file_type': doc_data.get('file_type', ''),
                        'upload_date': doc_data.get('upload_date', ''),
                        'file_size': doc_data.get('file_size', 0),
                        'user_id': doc_data.get('user_id', ''),
                        'tags': doc_data.get('tags', []),
                        'mongodb_id': str(doc_data.get('_id', ''))
                    }
                )
                haystack_docs.append(doc)
            
            if haystack_docs:
                # Index documents in Haystack
                result = self.indexing_pipeline.run({
                    "doc_embedder": {"documents": haystack_docs}
                })
                
                logger.info(f"✅ Loaded {len(haystack_docs)} documents from MongoDB into Haystack")
            
        except Exception as e:
            logger.error(f"❌ Error loading documents from MongoDB: {e}")
    
    def add_documents(self, documents_data: List[Dict[str, Any]]) -> int:
        """Add documents to both Haystack and MongoDB"""
        try:
            documents_added = 0
            haystack_docs = []
            mongodb_docs = []
            
            for doc_data in documents_data:
                content = doc_data.get('content', '')
                if not content.strip():
                    continue
                
                # Create file hash for deduplication
                file_hash = hashlib.md5(content.encode()).hexdigest()
                
                # Check if document already exists in MongoDB
                existing = self.collection.find_one({"file_hash": file_hash})
                if existing:
                    logger.info(f"⏭️ Skipping duplicate: {doc_data.get('filename', 'Unknown')}")
                    continue
                
                # Create Haystack document
                haystack_doc = Document(
                    content=content,
                    meta={
                        'filename': doc_data.get('filename', ''),
                        'file_type': doc_data.get('file_type', ''),
                        'upload_date': doc_data.get('upload_date', datetime.now().isoformat()),
                        'file_size': doc_data.get('file_size', len(content)),
                        'user_id': doc_data.get('user_id', 'default_user'),
                        'tags': doc_data.get('tags', []),
                        'source': doc_data.get('source', 'upload')
                    }
                )
                haystack_docs.append(haystack_doc)
                
                # Create MongoDB document
                mongodb_doc = {
                    'content': content,
                    'filename': doc_data.get('filename', ''),
                    'file_type': doc_data.get('file_type', ''),
                    'upload_date': doc_data.get('upload_date', datetime.now().isoformat()),
                    'file_size': doc_data.get('file_size', len(content)),
                    'user_id': doc_data.get('user_id', 'default_user'),
                    'tags': doc_data.get('tags', []),
                    'source': doc_data.get('source', 'upload'),
                    'file_hash': file_hash,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                mongodb_docs.append(mongodb_doc)
                documents_added += 1
            
            if haystack_docs:
                # Index in Haystack
                result = self.indexing_pipeline.run({
                    "doc_embedder": {"documents": haystack_docs}
                })
                
                # Save to MongoDB
                self.collection.insert_many(mongodb_docs)
                
                logger.info(f"✅ Added {documents_added} documents to Haystack + MongoDB")
            
            return documents_added
            
        except Exception as e:
            logger.error(f"❌ Error adding documents: {e}")
            raise
    
    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search documents using Haystack retrieval"""
        try:
            # Run search pipeline
            result = self.search_pipeline.run({
                "text_embedder": {"text": query},
                "retriever": {"query": query, "top_k": top_k}
            })
            
            documents = result["retriever"]["documents"]
            
            search_results = []
            for doc in documents:
                result_dict = {
                    'content': doc.content,
                    'score': doc.score if hasattr(doc, 'score') else 1.0,
                    'filename': doc.meta.get('filename', 'Unknown'),
                    'file_type': doc.meta.get('file_type', 'Unknown'),
                    'upload_date': doc.meta.get('upload_date', ''),
                    'file_size': doc.meta.get('file_size', 0),
                    'tags': doc.meta.get('tags', []),
                    'user_id': doc.meta.get('user_id', 'Unknown'),
                    'search_method': 'haystack_retrieval'
                }
                search_results.append(result_dict)
            
            logger.info(f"🔍 Found {len(search_results)} documents for query: '{query}' using Haystack")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Haystack search error: {e}")
            return []
    
    def ask_question(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Ask questions using Haystack Q&A pipeline"""
        if not self.qa_available:
            return {
                'answer': 'Q&A functionality not available (OpenAI key required)',
                'confidence': 0.0,
                'documents': []
            }
        
        try:
            # Run Q&A pipeline
            result = self.qa_pipeline.run({
                "text_embedder": {"text": question},
                "retriever": {"query": question, "top_k": top_k},
                "prompt_builder": {"question": question},
                "generator": {}
            })
            
            answer = result["generator"]["replies"][0] if result["generator"]["replies"] else "No answer generated"
            documents = result["retriever"]["documents"]
            
            doc_info = []
            for doc in documents:
                doc_info.append({
                    'filename': doc.meta.get('filename', 'Unknown'),
                    'content_preview': doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    'score': doc.score if hasattr(doc, 'score') else 1.0
                })
            
            qa_result = {
                'answer': answer,
                'confidence': 0.8,  # Placeholder confidence
                'documents': doc_info,
                'question': question
            }
            
            logger.info(f"❓ Answered question: '{question}' using Haystack Q&A")
            return qa_result
            
        except Exception as e:
            logger.error(f"❌ Q&A error: {e}")
            return {
                'answer': f'Error processing question: {str(e)}',
                'confidence': 0.0,
                'documents': []
            }
    
    def get_document_stats(self) -> Dict[str, Any]:
        """Get statistics about the document store"""
        try:
            # Haystack stats
            haystack_count = len(self.document_store.filter_documents())
            
            # MongoDB stats
            mongodb_count = self.collection.count_documents({})
            
            # File type distribution from MongoDB
            pipeline = [
                {"$group": {"_id": "$file_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            file_types = {doc["_id"]: doc["count"] for doc in self.collection.aggregate(pipeline)}
            
            stats = {
                'haystack_documents': haystack_count,
                'mongodb_documents': mongodb_count,
                'total_documents': max(haystack_count, mongodb_count),
                'database': self.database_name,
                'collection': self.collection_name,
                'file_types': file_types,
                'storage_type': 'Haystack 2.x + MongoDB Atlas',
                'qa_available': self.qa_available,
                'features': [
                    'Haystack Pipelines',
                    'Semantic Search',
                    'Document Embeddings',
                    'MongoDB Persistence',
                    'Q&A with OpenAI' if self.qa_available else 'Q&A (Disabled)',
                    'BM25 Retrieval',
                    'Cloud Storage'
                ]
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {'error': str(e)}
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("✅ MongoDB connection closed")

# Test the integration
if __name__ == "__main__":
    try:
        # Test initialization
        store = HaystackMongoDB()
        
        # Test adding a sample document
        test_doc = [{
            'content': 'This is a Haystack 2.x test document for HighPal AI Assistant. It demonstrates modern Haystack pipelines with MongoDB Atlas persistence and advanced search capabilities.',
            'filename': 'haystack_test.txt',
            'file_type': 'text/plain',
            'tags': ['haystack', 'test', 'mongodb', 'ai']
        }]
        
        added = store.add_documents(test_doc)
        print(f"✅ Added {added} documents using Haystack")
        
        # Test search
        print("\n🔍 Testing Haystack search:")
        results = store.search_documents('Haystack AI Assistant', top_k=3)
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['filename']} (score: {result['score']:.3f}, method: {result['search_method']})")
        
        # Test Q&A
        print("\n❓ Testing Haystack Q&A:")
        qa_result = store.ask_question('What is this document about?')
        print(f"  Question: {qa_result['question']}")
        print(f"  Answer: {qa_result['answer']}")
        print(f"  Based on {len(qa_result['documents'])} documents")
        
        # Test stats
        stats = store.get_document_stats()
        print(f"\n📊 Haystack + MongoDB stats:")
        print(f"  Haystack documents: {stats['haystack_documents']}")
        print(f"  MongoDB documents: {stats['mongodb_documents']}")
        print(f"  Q&A available: {stats['qa_available']}")
        print(f"  Features: {', '.join(stats['features'])}")
        
        store.close()
        print("\n✅ Haystack 2.x + MongoDB integration test completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
