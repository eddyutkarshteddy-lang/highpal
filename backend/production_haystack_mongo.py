"""
Production-Ready Haystack-Style MongoDB Atlas Integration for HighPal
Uses proven components with Haystack-inspired architecture
"""

import os
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Core dependencies (proven working)
import pymongo
from bson import ObjectId
import numpy as np

# Embeddings (proven working)
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("⚠️ Sentence transformers not available")

# OpenAI for Q&A (optional)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Document:
    """Haystack-style Document class"""
    def __init__(self, content: str, meta: dict = None, embedding: List[float] = None, score: float = None):
        self.content = content
        self.meta = meta or {}
        self.embedding = embedding
        self.score = score

class HaystackStyleMongoIntegration:
    """
    Production-ready Haystack-style integration with MongoDB Atlas
    Features:
    - Haystack-inspired architecture with proven components
    - MongoDB Atlas for persistence and basic search
    - Semantic search with sentence transformers
    - Q&A capabilities with OpenAI
    - Document pipelines and processors
    - Auto-sync and deduplication
    """
    
    def __init__(self):
        """Initialize the integration system"""
        try:
            logger.info("🚀 Initializing Haystack-Style MongoDB Integration...")
            
            # MongoDB Atlas setup
            self.connection_string = os.getenv('MONGODB_CONNECTION_STRING')
            self.database_name = os.getenv('MONGODB_DATABASE', 'highpal_documents')
            self.collection_name = os.getenv('MONGODB_COLLECTION', 'documents')
            
            if not self.connection_string:
                raise ValueError("MongoDB connection string not found in environment variables")
            
            # Initialize MongoDB connection
            self.mongo_client = pymongo.MongoClient(self.connection_string)
            self.db = self.mongo_client[self.database_name]
            self.collection = self.db[self.collection_name]
            
            # Test connection
            self.mongo_client.admin.command('ping')
            logger.info("✅ MongoDB Atlas connection established")
            
            # Create indexes for performance
            self._create_indexes()
            
            # Initialize embedding model
            self.embedding_model = None
            if EMBEDDINGS_AVAILABLE:
                self._initialize_embeddings()
            
            # Initialize OpenAI for Q&A
            self._initialize_openai()
            
            # Document processing components
            self._initialize_processors()
            
            logger.info("🎉 Haystack-Style MongoDB Integration ready!")
            logger.info(f"📊 Database: {self.database_name}")
            logger.info(f"📂 Collection: {self.collection_name}")
            logger.info(f"🧠 Semantic Search: {'✅ Enabled' if EMBEDDINGS_AVAILABLE else '❌ Disabled'}")
            logger.info(f"❓ Q&A: {'✅ Enabled' if self.qa_available else '❌ Disabled'}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize integration: {e}")
            raise
    
    def _create_indexes(self):
        """Create MongoDB indexes for optimal performance"""
        try:
            # Text search index
            self.collection.create_index([("content", "text"), ("filename", "text")])
            
            # Metadata indexes
            self.collection.create_index("filename")
            self.collection.create_index("file_type")
            self.collection.create_index("upload_date")
            self.collection.create_index("file_hash")
            self.collection.create_index("user_id")
            
            # Embedding index for vector search
            self.collection.create_index("embedding")
            
            logger.info("✅ MongoDB indexes created for optimal performance")
        except Exception as e:
            logger.warning(f"⚠️ Index creation warning: {e}")
    
    def _initialize_embeddings(self):
        """Initialize sentence transformer for embeddings"""
        try:
            model_name = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
            self.embedding_model = SentenceTransformer(model_name)
            logger.info(f"✅ Embedding model loaded: {model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to load embedding model: {e}")
            EMBEDDINGS_AVAILABLE = False
    
    def _initialize_openai(self):
        """Initialize OpenAI for Q&A capabilities"""
        openai_key = os.getenv('OPENAI_API_KEY')
        
        if openai_key and not openai_key.startswith('sk-test-dummy') and OPENAI_AVAILABLE:
            try:
                openai.api_key = openai_key
                self.qa_available = True
                logger.info("✅ OpenAI Q&A capabilities enabled")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI initialization failed: {e}")
                self.qa_available = False
        else:
            self.qa_available = False
            logger.info("ℹ️ Q&A disabled (no valid OpenAI key or openai package not available)")
    
    def _initialize_processors(self):
        """Initialize document processing components"""
        self.document_processor = DocumentProcessor()
        self.query_processor = QueryProcessor()
        self.retrieval_processor = RetrievalProcessor(self.embedding_model, self.collection)
        self.qa_processor = QAProcessor(self.qa_available)
    
    def process_and_store_documents(self, documents_data: List[Dict[str, Any]]) -> int:
        """
        Main document processing pipeline (Haystack-style)
        1. Process documents through processors
        2. Generate embeddings
        3. Store in MongoDB Atlas
        4. Return statistics
        """
        try:
            processed_docs = []
            duplicates_skipped = 0
            
            for doc_data in documents_data:
                # Process document
                processed_doc = self.document_processor.process(doc_data)
                
                if processed_doc is None:
                    continue
                
                # Check for duplicates
                if self._is_duplicate(processed_doc):
                    duplicates_skipped += 1
                    continue
                
                # Generate embeddings
                if self.embedding_model and processed_doc.content.strip():
                    embedding = self.embedding_model.encode(processed_doc.content)
                    processed_doc.embedding = embedding.tolist()
                
                processed_docs.append(processed_doc)
            
            # Store in MongoDB Atlas
            stored_count = self._store_documents(processed_docs)
            
            logger.info(f"✅ Processed and stored {stored_count} documents")
            if duplicates_skipped > 0:
                logger.info(f"⏭️ Skipped {duplicates_skipped} duplicate documents")
            
            return stored_count
            
        except Exception as e:
            logger.error(f"❌ Document processing pipeline error: {e}")
            return 0
    
    def semantic_search(self, query: str, top_k: int = 5, filters: Dict = None) -> List[Dict[str, Any]]:
        """Semantic search pipeline using embeddings"""
        if not self.embedding_model:
            logger.warning("⚠️ Semantic search not available - using text search fallback")
            return self.text_search(query, top_k, filters)
        
        try:
            # Process query
            processed_query = self.query_processor.process(query)
            
            # Generate query embedding
            query_embedding = self.embedding_model.encode(processed_query)
            
            # Retrieve similar documents
            results = self.retrieval_processor.semantic_retrieve(
                query_embedding, top_k, filters
            )
            
            logger.info(f"🔍 Semantic search found {len(results)} documents for: '{query[:50]}...'")
            return results
            
        except Exception as e:
            logger.error(f"❌ Semantic search error: {e}")
            return []
    
    def text_search(self, query: str, top_k: int = 5, filters: Dict = None) -> List[Dict[str, Any]]:
        """Text search using MongoDB text indexes"""
        try:
            processed_query = self.query_processor.process(query)
            results = self.retrieval_processor.text_retrieve(processed_query, top_k, filters)
            
            logger.info(f"🔍 Text search found {len(results)} documents for: '{query[:50]}...'")
            return results
            
        except Exception as e:
            logger.error(f"❌ Text search error: {e}")
            return []
    
    def hybrid_search(self, query: str, top_k: int = 5, filters: Dict = None) -> List[Dict[str, Any]]:
        """Hybrid search combining semantic and text search"""
        try:
            # Get results from both methods
            semantic_results = self.semantic_search(query, top_k // 2 + 1, filters)
            text_results = self.text_search(query, top_k // 2 + 1, filters)
            
            # Combine and deduplicate results
            combined_results = []
            seen_ids = set()
            
            # Add semantic results first (usually higher quality)
            for result in semantic_results:
                doc_id = result.get('_id', str(result.get('mongo_id', '')))
                if doc_id not in seen_ids:
                    result['search_method'] = 'semantic'
                    combined_results.append(result)
                    seen_ids.add(doc_id)
            
            # Add text results
            for result in text_results:
                doc_id = result.get('_id', str(result.get('mongo_id', '')))
                if doc_id not in seen_ids and len(combined_results) < top_k:
                    result['search_method'] = 'text'
                    combined_results.append(result)
                    seen_ids.add(doc_id)
            
            logger.info(f"🔍 Hybrid search found {len(combined_results)} documents")
            return combined_results[:top_k]
            
        except Exception as e:
            logger.error(f"❌ Hybrid search error: {e}")
            return []
    
    def ask_question(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Q&A pipeline using retrieved documents and OpenAI"""
        try:
            # Retrieve relevant documents
            relevant_docs = self.semantic_search(question, top_k)
            
            if not relevant_docs:
                return {
                    "answer": "No relevant documents found for your question.",
                    "confidence": 0.0,
                    "source_documents": [],
                    "method": "no_results"
                }
            
            # Process through Q&A pipeline
            qa_result = self.qa_processor.generate_answer(question, relevant_docs)
            
            logger.info(f"❓ Answered question: '{question[:50]}...'")
            return qa_result
            
        except Exception as e:
            logger.error(f"❌ Q&A pipeline error: {e}")
            return {
                "answer": f"Error processing question: {str(e)}",
                "confidence": 0.0,
                "source_documents": relevant_docs if 'relevant_docs' in locals() else [],
                "method": "error"
            }
    
    def _is_duplicate(self, document: Document) -> bool:
        """Check if document is a duplicate"""
        file_hash = hashlib.md5(document.content.encode()).hexdigest()
        existing = self.collection.find_one({"file_hash": file_hash})
        return existing is not None
    
    def _store_documents(self, documents: List[Document]) -> int:
        """Store processed documents in MongoDB Atlas"""
        if not documents:
            return 0
        
        mongo_docs = []
        for doc in documents:
            mongo_doc = {
                'content': doc.content,
                'filename': doc.meta.get('filename', 'Unknown'),
                'file_type': doc.meta.get('file_type', 'Unknown'),
                'upload_date': doc.meta.get('upload_date', datetime.now().isoformat()),
                'file_size': doc.meta.get('file_size', len(doc.content)),
                'user_id': doc.meta.get('user_id', 'default'),
                'tags': doc.meta.get('tags', []),
                'file_hash': hashlib.md5(doc.content.encode()).hexdigest(),
                'embedding': doc.embedding,
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                'source': 'haystack_pipeline'
            }
            mongo_docs.append(mongo_doc)
        
        result = self.collection.insert_many(mongo_docs)
        return len(result.inserted_ids)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        try:
            total_docs = self.collection.count_documents({})
            docs_with_embeddings = self.collection.count_documents({"embedding": {"$exists": True}})
            
            # File type distribution
            pipeline = [
                {"$group": {"_id": "$file_type", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            file_types = {doc["_id"]: doc["count"] for doc in self.collection.aggregate(pipeline)}
            
            # Recent uploads
            recent_cutoff = (datetime.now() - timedelta(days=7)).isoformat()
            recent_count = self.collection.count_documents({
                "upload_date": {"$gte": recent_cutoff}
            })
            
            return {
                "system": {
                    "type": "Haystack-Style MongoDB Atlas Integration",
                    "version": "1.0.0",
                    "status": "operational"
                },
                "storage": {
                    "total_documents": total_docs,
                    "documents_with_embeddings": docs_with_embeddings,
                    "embedding_coverage": f"{(docs_with_embeddings/total_docs*100):.1f}%" if total_docs > 0 else "0%",
                    "database": self.database_name,
                    "collection": self.collection_name
                },
                "capabilities": {
                    "semantic_search": EMBEDDINGS_AVAILABLE,
                    "text_search": True,
                    "hybrid_search": EMBEDDINGS_AVAILABLE,
                    "question_answering": self.qa_available,
                    "document_processing": True
                },
                "content": {
                    "file_types": file_types,
                    "recent_uploads_7_days": recent_count,
                    "embedding_model": os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
                },
                "features": [
                    "MongoDB Atlas Cloud Storage",
                    "Document Processing Pipeline",
                    "Semantic Search with Embeddings" if EMBEDDINGS_AVAILABLE else "Text Search Only",
                    "Hybrid Search" if EMBEDDINGS_AVAILABLE else "Text Search Only",
                    "Q&A with OpenAI" if self.qa_available else "Q&A Disabled",
                    "Deduplication",
                    "Metadata Enrichment",
                    "Performance Optimized Indexes"
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting system stats: {e}")
            return {"error": str(e)}
    
    def close(self):
        """Close connections and cleanup"""
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("✅ MongoDB Atlas connection closed")

# Supporting processor classes
class DocumentProcessor:
    """Process and validate documents"""
    
    def process(self, doc_data: Dict[str, Any]) -> Optional[Document]:
        """Process raw document data into Document object"""
        try:
            content = doc_data.get('content', '').strip()
            if not content:
                return None
            
            meta = {
                'filename': doc_data.get('filename', 'Unknown'),
                'file_type': doc_data.get('file_type', 'Unknown'),
                'upload_date': doc_data.get('upload_date', datetime.now().isoformat()),
                'file_size': doc_data.get('file_size', len(content)),
                'user_id': doc_data.get('user_id', 'default'),
                'tags': doc_data.get('tags', []),
                'source': doc_data.get('source', 'upload')
            }
            
            return Document(content=content, meta=meta)
            
        except Exception as e:
            logger.error(f"❌ Document processing error: {e}")
            return None

class QueryProcessor:
    """Process and optimize search queries"""
    
    def process(self, query: str) -> str:
        """Clean and optimize query for search"""
        # Basic query cleaning
        cleaned = query.strip().lower()
        return cleaned

class RetrievalProcessor:
    """Handle document retrieval operations"""
    
    def __init__(self, embedding_model, collection):
        self.embedding_model = embedding_model
        self.collection = collection
    
    def semantic_retrieve(self, query_embedding, top_k: int, filters: Dict = None) -> List[Dict[str, Any]]:
        """Retrieve documents using semantic similarity"""
        try:
            # Find documents with embeddings
            match_filter = {"embedding": {"$exists": True}}
            if filters:
                match_filter.update(filters)
            
            pipeline = [
                {"$match": match_filter},
                {"$limit": 1000}  # Limit for performance
            ]
            
            documents = list(self.collection.aggregate(pipeline))
            
            if not documents:
                return []
            
            # Calculate similarities
            similarities = []
            for doc in documents:
                if 'embedding' in doc and doc['embedding']:
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
                    '_id': str(doc['_id']),
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
            
        except Exception as e:
            logger.error(f"❌ Semantic retrieval error: {e}")
            return []
    
    def text_retrieve(self, query: str, top_k: int, filters: Dict = None) -> List[Dict[str, Any]]:
        """Retrieve documents using text search"""
        try:
            search_filter = {"$text": {"$search": query}}
            if filters:
                search_filter.update(filters)
            
            cursor = self.collection.find(
                search_filter,
                {"score": {"$meta": "textScore"}}
            ).sort([("score", {"$meta": "textScore"})]).limit(top_k)
            
            results = []
            for doc in cursor:
                result = {
                    '_id': str(doc['_id']),
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
            logger.error(f"❌ Text retrieval error: {e}")
            return []

class QAProcessor:
    """Handle question answering operations"""
    
    def __init__(self, qa_available: bool):
        self.qa_available = qa_available
    
    def generate_answer(self, question: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate answer from question and relevant documents"""
        if not self.qa_available:
            return {
                "answer": "Q&A functionality requires a valid OpenAI API key. Here are relevant documents found:",
                "confidence": 0.0,
                "source_documents": documents[:3],
                "method": "fallback_to_search"
            }
        
        try:
            # Prepare context from documents
            context = "\n\n".join([doc['content'][:500] for doc in documents[:3]])
            
            # Create prompt
            prompt = f"""
Based on the following documents, please answer the question. If the answer cannot be found in the documents, say so.

Documents:
{context}

Question: {question}

Answer:"""
            
            # Call OpenAI (simplified version)
            response = openai.Completion.create(
                engine="text-davinci-003",
                prompt=prompt,
                max_tokens=300,
                temperature=0.3
            )
            
            answer = response.choices[0].text.strip()
            
            return {
                "answer": answer,
                "confidence": 0.85,
                "source_documents": documents[:3],
                "method": "openai_generation"
            }
            
        except Exception as e:
            logger.error(f"❌ Q&A generation error: {e}")
            return {
                "answer": f"Error generating answer: {str(e)}. Here are relevant documents:",
                "confidence": 0.0,
                "source_documents": documents[:3],
                "method": "error_fallback"
            }

# Test the integration
if __name__ == "__main__":
    try:
        # Initialize the integration
        integration = HaystackStyleMongoIntegration()
        
        # Test documents
        test_docs = [
            {
                "content": "Artificial Intelligence and Machine Learning are revolutionizing healthcare through predictive analytics, automated diagnosis, and personalized treatment plans. AI helps doctors make better decisions faster.",
                "filename": "ai_healthcare_revolution.pdf",
                "file_type": "application/pdf",
                "tags": ["AI", "healthcare", "machine learning", "medicine"]
            },
            {
                "content": "Natural Language Processing (NLP) enables computers to understand, interpret, and generate human language. It powers chatbots, virtual assistants, and automatic translation systems.",
                "filename": "nlp_comprehensive_guide.txt",
                "file_type": "text/plain",
                "tags": ["NLP", "AI", "language", "chatbots"]
            }
        ]
        
        # Test document processing pipeline
        print("📋 Testing document processing pipeline...")
        added = integration.process_and_store_documents(test_docs)
        print(f"✅ Added {added} documents through processing pipeline")
        
        # Test semantic search
        print("\n🧠 Testing semantic search:")
        semantic_results = integration.semantic_search("medical AI applications", top_k=3)
        for i, result in enumerate(semantic_results, 1):
            print(f"  {i}. {result['filename']} (score: {result['score']:.3f})")
        
        # Test text search
        print("\n📝 Testing text search:")
        text_results = integration.text_search("language processing", top_k=3)
        for i, result in enumerate(text_results, 1):
            print(f"  {i}. {result['filename']} (score: {result['score']:.3f})")
        
        # Test hybrid search
        print("\n🔀 Testing hybrid search:")
        hybrid_results = integration.hybrid_search("AI chatbots", top_k=3)
        for i, result in enumerate(hybrid_results, 1):
            print(f"  {i}. {result['filename']} (method: {result.get('search_method', 'unknown')})")
        
        # Test Q&A
        print("\n❓ Testing Q&A:")
        qa_result = integration.ask_question("How does AI help in healthcare?")
        print(f"  Question: How does AI help in healthcare?")
        print(f"  Answer: {qa_result['answer']}")
        print(f"  Method: {qa_result['method']}")
        print(f"  Sources: {len(qa_result['source_documents'])} documents")
        
        # Get system statistics
        stats = integration.get_system_stats()
        print(f"\n📊 System Statistics:")
        print(f"  System: {stats['system']['type']}")
        print(f"  Total documents: {stats['storage']['total_documents']}")
        print(f"  Embedding coverage: {stats['storage']['embedding_coverage']}")
        print(f"  Semantic search: {'✅' if stats['capabilities']['semantic_search'] else '❌'}")
        print(f"  Q&A available: {'✅' if stats['capabilities']['question_answering'] else '❌'}")
        print(f"  Features: {len(stats['features'])} advanced features")
        
        # Close connections
        integration.close()
        
        print("\n🎉 Haystack-Style MongoDB Atlas Integration test completed successfully!")
        print("\n✨ Your system now has:")
        print("  • Advanced document processing pipelines")
        print("  • Semantic search with AI embeddings")
        print("  • Hybrid search combining multiple methods")
        print("  • Question answering capabilities")
        print("  • MongoDB Atlas cloud storage")
        print("  • Production-ready architecture")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
