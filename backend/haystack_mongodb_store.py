"""
Haystack MongoDB Atlas Integration for HighPal
Provides advanced document storage, embeddings, and semantic search capabilities
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Haystack imports
from haystack.document_stores import MongoDBDocumentStore
from haystack.nodes import EmbeddingRetriever, FARMReader
from haystack.pipelines import ExtractiveQAPipeline
from haystack import Document

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HaystackMongoDBStore:
    """
    Advanced document storage using Haystack + MongoDB Atlas
    Features:
    - Semantic search with embeddings
    - Question answering on documents
    - Metadata-rich storage
    - Scalable cloud storage
    """
    
    def __init__(self):
        """Initialize Haystack MongoDB document store"""
        try:
            # Get MongoDB connection details
            connection_string = os.getenv('MONGODB_CONNECTION_STRING')
            database_name = os.getenv('MONGODB_DATABASE', 'highpal_documents')
            collection_name = os.getenv('MONGODB_COLLECTION', 'documents')
            
            if not connection_string:
                raise ValueError("MongoDB connection string not found in environment variables")
            
            # Initialize MongoDB Document Store
            self.document_store = MongoDBDocumentStore(
                host=connection_string,
                database_name=database_name,
                collection_name=collection_name,
                embedding_dim=384,  # For all-MiniLM-L6-v2 model
                similarity="cosine",
                return_embedding=True,
                duplicate_documents="overwrite",
                index="document"
            )
            
            # Initialize Embedding Retriever
            embedding_model = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
            self.retriever = EmbeddingRetriever(
                document_store=self.document_store,
                embedding_model=embedding_model,
                model_format="sentence_transformers",
                use_gpu=False,
                scale_score=False
            )
            
            # Initialize Reader for Q&A (optional)
            try:
                self.reader = FARMReader(
                    model_name_or_path="deepset/roberta-base-squad2",
                    use_gpu=False,
                    top_k=5,
                    context_window_size=100
                )
                self.qa_pipeline = ExtractiveQAPipeline(self.reader, self.retriever)
                logger.info("✅ Q&A pipeline initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ Q&A pipeline initialization failed: {e}")
                self.reader = None
                self.qa_pipeline = None
            
            logger.info("✅ Haystack MongoDB store initialized successfully!")
            logger.info(f"📊 Database: {database_name}")
            logger.info(f"📂 Collection: {collection_name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Haystack MongoDB store: {e}")
            raise
    
    def add_documents(self, documents_data: List[Dict[str, Any]]) -> int:
        """
        Add documents to the store with embeddings
        
        Args:
            documents_data: List of document dictionaries with content and metadata
            
        Returns:
            Number of documents added
        """
        try:
            documents = []
            
            for doc_data in documents_data:
                # Create Haystack Document object
                doc = Document(
                    content=doc_data.get('content', ''),
                    meta={
                        'filename': doc_data.get('filename', ''),
                        'file_type': doc_data.get('file_type', ''),
                        'upload_date': doc_data.get('upload_date', datetime.now().isoformat()),
                        'file_size': doc_data.get('file_size', 0),
                        'user_id': doc_data.get('user_id', 'default_user'),
                        'tags': doc_data.get('tags', []),
                        'source': doc_data.get('source', 'upload'),
                        'language': doc_data.get('language', 'en')
                    }
                )
                documents.append(doc)
            
            # Write documents to MongoDB
            self.document_store.write_documents(documents)
            
            # Update embeddings for new documents
            self.document_store.update_embeddings(self.retriever)
            
            logger.info(f"✅ Added {len(documents)} documents to Haystack MongoDB store")
            return len(documents)
            
        except Exception as e:
            logger.error(f"❌ Error adding documents: {e}")
            raise
    
    def search_documents(self, query: str, top_k: int = 5, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search documents using semantic similarity
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of matching documents with scores
        """
        try:
            # Perform semantic search
            documents = self.retriever.retrieve(
                query=query,
                top_k=top_k,
                filters=filters
            )
            
            results = []
            for doc in documents:
                result = {
                    'content': doc.content,
                    'score': float(doc.score) if doc.score else 0.0,
                    'filename': doc.meta.get('filename', 'Unknown'),
                    'file_type': doc.meta.get('file_type', 'Unknown'),
                    'upload_date': doc.meta.get('upload_date', ''),
                    'file_size': doc.meta.get('file_size', 0),
                    'tags': doc.meta.get('tags', []),
                    'user_id': doc.meta.get('user_id', 'Unknown')
                }
                results.append(result)
            
            logger.info(f"🔍 Found {len(results)} documents for query: '{query}'")
            return results
            
        except Exception as e:
            logger.error(f"❌ Search error: {e}")
            return []
    
    def ask_question(self, question: str, top_k_retriever: int = 10, top_k_reader: int = 5) -> List[Dict[str, Any]]:
        """
        Ask questions about your documents using Q&A pipeline
        
        Args:
            question: Question to ask
            top_k_retriever: Number of documents to retrieve
            top_k_reader: Number of answers to return
            
        Returns:
            List of answers with confidence scores
        """
        if not self.qa_pipeline:
            logger.warning("⚠️ Q&A pipeline not available")
            return []
        
        try:
            # Run Q&A pipeline
            prediction = self.qa_pipeline.run(
                query=question,
                params={
                    "Retriever": {"top_k": top_k_retriever},
                    "Reader": {"top_k": top_k_reader}
                }
            )
            
            answers = []
            for answer in prediction['answers']:
                answer_dict = {
                    'answer': answer.answer,
                    'confidence': float(answer.score) if answer.score else 0.0,
                    'context': answer.context,
                    'start_idx': answer.offset_start_in_doc,
                    'end_idx': answer.offset_end_in_doc,
                    'document_filename': answer.meta.get('filename', 'Unknown'),
                    'document_id': answer.document_id
                }
                answers.append(answer_dict)
            
            logger.info(f"❓ Answered question: '{question}' with {len(answers)} results")
            return answers
            
        except Exception as e:
            logger.error(f"❌ Q&A error: {e}")
            return []
    
    def get_document_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored documents
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            stats = {
                'total_documents': self.document_store.get_document_count(),
                'database': os.getenv('MONGODB_DATABASE'),
                'collection': os.getenv('MONGODB_COLLECTION'),
                'embedding_model': os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2'),
                'storage_type': 'MongoDB Atlas + Haystack',
                'features': [
                    'Semantic Search',
                    'Document Embeddings',
                    'Question Answering',
                    'Metadata Filtering',
                    'Cloud Storage'
                ]
            }
            
            # Get some sample documents for additional stats
            sample_docs = self.document_store.get_all_documents(return_embedding=False, batch_size=10)
            if sample_docs:
                file_types = {}
                for doc in sample_docs:
                    file_type = doc.meta.get('file_type', 'unknown')
                    file_types[file_type] = file_types.get(file_type, 0) + 1
                
                stats['file_types'] = file_types
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {'error': str(e)}
    
    def delete_documents(self, filters: Optional[Dict] = None, document_ids: Optional[List[str]] = None) -> int:
        """
        Delete documents from the store
        
        Args:
            filters: Metadata filters to match documents
            document_ids: Specific document IDs to delete
            
        Returns:
            Number of documents deleted
        """
        try:
            if document_ids:
                deleted = self.document_store.delete_documents(ids=document_ids)
            elif filters:
                deleted = self.document_store.delete_documents(filters=filters)
            else:
                logger.warning("⚠️ No filters or IDs provided for deletion")
                return 0
            
            logger.info(f"🗑️ Deleted {deleted} documents")
            return deleted
            
        except Exception as e:
            logger.error(f"❌ Error deleting documents: {e}")
            return 0
    
    def update_embeddings(self):
        """Update embeddings for all documents"""
        try:
            self.document_store.update_embeddings(self.retriever)
            logger.info("✅ Updated embeddings for all documents")
        except Exception as e:
            logger.error(f"❌ Error updating embeddings: {e}")
            raise

# Test the connection if run directly
if __name__ == "__main__":
    try:
        # Test initialization
        store = HaystackMongoDBStore()
        
        # Test adding a sample document
        test_doc = [{
            'content': 'This is a test document for HighPal AI Assistant. It demonstrates the Haystack MongoDB integration.',
            'filename': 'test_document.txt',
            'file_type': 'text/plain',
            'tags': ['test', 'demo']
        }]
        
        store.add_documents(test_doc)
        
        # Test search
        results = store.search_documents('HighPal AI Assistant', top_k=3)
        print(f"Search results: {len(results)}")
        
        # Test stats
        stats = store.get_document_stats()
        print(f"Document stats: {stats}")
        
        print("✅ Haystack MongoDB integration test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
