"""
Haystack Document Manager for HighPal
Handles document storage, indexing, and retrieval using Haystack
"""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from haystack import Document, Pipeline
from haystack.document_stores import InMemoryDocumentStore
from haystack.retriever import BM25Retriever
from haystack.nodes import EmbeddingRetriever, SentenceTransformersDocumentEmbedder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HaystackDocumentManager:
    """Advanced document management using Haystack"""
    
    def __init__(self, storage_path: str = "training_data.json"):
        """Initialize Haystack document manager"""
        self.storage_path = storage_path
        self.local_backup_path = "haystack_backup.json"
        
        # Initialize document store
        self.document_store = InMemoryDocumentStore()
        
        # Initialize retrievers
        self.bm25_retriever = InMemoryBM25Retriever(document_store=self.document_store)
        self.embedding_retriever = InMemoryEmbeddingRetriever(document_store=self.document_store)
        
        # Initialize embedders
        self.text_embedder = SentenceTransformersTextEmbedder(model="all-MiniLM-L6-v2")
        self.doc_embedder = SentenceTransformersDocumentEmbedder(model="all-MiniLM-L6-v2")
        
        # Initialize ranker
        self.ranker = TransformersSimilarityRanker(model="cross-encoder/ms-marco-MiniLM-L-6-v2")
        
        # Load existing documents
        self.load_existing_documents()
        
        logger.info("HaystackDocumentManager initialized successfully")
    
    def load_existing_documents(self):
        """Load documents from local storage into Haystack"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                documents = []
                for doc_id, doc_data in data.items():
                    # Create Haystack document
                    doc = Document(
                        content=doc_data.get('content', ''),
                        meta={
                            'filename': doc_data.get('filename', 'unknown'),
                            'size': doc_data.get('size', 0),
                            'category': doc_data.get('category', 'general'),
                            'source': doc_data.get('source', 'local'),
                            'title': doc_data.get('title', ''),
                            'upload_date': doc_data.get('upload_date', ''),
                            'extraction_info': doc_data.get('extraction_info', {}),
                            'document_id': doc_id
                        },
                        id=doc_id
                    )
                    documents.append(doc)
                
                if documents:
                    # Embed documents
                    embedded_docs = self.doc_embedder.run(documents=documents)
                    
                    # Write to document store
                    self.document_store.write_documents(embedded_docs["documents"])
                    
                    logger.info(f"Loaded {len(documents)} documents into Haystack")
                else:
                    logger.info("No documents found in local storage")
                    
        except Exception as e:
            logger.error(f"Error loading existing documents: {e}")
    
    def add_document(self, content: str, metadata: Dict[str, Any]) -> str:
        """Add a new document to Haystack and local storage"""
        try:
            # Generate document ID
            doc_id = metadata.get('document_id', f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Create Haystack document
            doc = Document(
                content=content,
                meta=metadata,
                id=doc_id
            )
            
            # Embed document
            embedded_docs = self.doc_embedder.run(documents=[doc])
            
            # Add to document store
            self.document_store.write_documents(embedded_docs["documents"])
            
            # Save to local backup
            self.save_to_local_backup(doc_id, content, metadata)
            
            logger.info(f"Added document {doc_id} to Haystack")
            return doc_id
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    def search_documents(self, query: str, method: str = "hybrid", top_k: int = 5) -> List[Dict[str, Any]]:
        """Search documents using various methods"""
        try:
            if method == "bm25":
                return self._search_bm25(query, top_k)
            elif method == "embedding":
                return self._search_embedding(query, top_k)
            elif method == "hybrid":
                return self._search_hybrid(query, top_k)
            else:
                raise ValueError(f"Unknown search method: {method}")
                
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []
    
    def _search_bm25(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """BM25 keyword search"""
        results = self.bm25_retriever.run(query=query, top_k=top_k)
        return self._format_search_results(results["documents"])
    
    def _search_embedding(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Semantic embedding search"""
        # Embed the query
        query_embedding = self.text_embedder.run(text=query)
        
        # Search using embeddings
        results = self.embedding_retriever.run(
            query_embedding=query_embedding["embedding"],
            top_k=top_k
        )
        return self._format_search_results(results["documents"])
    
    def _search_hybrid(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Hybrid search combining BM25 and embeddings"""
        # Get BM25 results
        bm25_results = self._search_bm25(query, top_k * 2)
        
        # Get embedding results
        embedding_results = self._search_embedding(query, top_k * 2)
        
        # Combine and deduplicate
        combined_docs = {}
        
        for result in bm25_results + embedding_results:
            doc_id = result.get('id', result.get('document_id'))
            if doc_id not in combined_docs:
                combined_docs[doc_id] = result
            else:
                # Boost score for documents found in both methods
                combined_docs[doc_id]['score'] = max(
                    combined_docs[doc_id].get('score', 0),
                    result.get('score', 0)
                ) * 1.2
        
        # Sort by score and return top_k
        sorted_results = sorted(
            combined_docs.values(),
            key=lambda x: x.get('score', 0),
            reverse=True
        )
        
        return sorted_results[:top_k]
    
    def _format_search_results(self, documents: List[Document]) -> List[Dict[str, Any]]:
        """Format search results for API response"""
        results = []
        for doc in documents:
            result = {
                'id': doc.id,
                'content': doc.content[:500] + "..." if len(doc.content) > 500 else doc.content,
                'score': getattr(doc, 'score', 1.0),
                'metadata': doc.meta
            }
            results.append(result)
        return results
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific document by ID"""
        try:
            docs = self.document_store.filter_documents(filters={"field": "id", "operator": "==", "value": doc_id})
            if docs:
                doc = docs[0]
                return {
                    'id': doc.id,
                    'content': doc.content,
                    'metadata': doc.meta
                }
            return None
        except Exception as e:
            logger.error(f"Error retrieving document {doc_id}: {e}")
            return None
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from Haystack and local storage"""
        try:
            # Delete from document store
            self.document_store.delete_documents([doc_id])
            
            # Remove from local backup
            self.remove_from_local_backup(doc_id)
            
            logger.info(f"Deleted document {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents with metadata"""
        try:
            docs = self.document_store.filter_documents()
            return self._format_search_results(docs)
        except Exception as e:
            logger.error(f"Error retrieving all documents: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get document store statistics"""
        try:
            docs = self.document_store.filter_documents()
            total_docs = len(docs)
            total_chars = sum(len(doc.content) for doc in docs)
            
            # Category breakdown
            categories = {}
            for doc in docs:
                category = doc.meta.get('category', 'uncategorized')
                categories[category] = categories.get(category, 0) + 1
            
            return {
                'total_documents': total_docs,
                'total_characters': total_chars,
                'categories': categories,
                'average_document_length': total_chars / total_docs if total_docs > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def save_to_local_backup(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        """Save document to local JSON backup"""
        try:
            backup_data = {}
            if os.path.exists(self.local_backup_path):
                with open(self.local_backup_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
            
            backup_data[doc_id] = {
                'content': content,
                **metadata
            }
            
            with open(self.local_backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Error saving to local backup: {e}")
    
    def remove_from_local_backup(self, doc_id: str):
        """Remove document from local JSON backup"""
        try:
            if os.path.exists(self.local_backup_path):
                with open(self.local_backup_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                if doc_id in backup_data:
                    del backup_data[doc_id]
                    
                    with open(self.local_backup_path, 'w', encoding='utf-8') as f:
                        json.dump(backup_data, f, indent=2, ensure_ascii=False)
                        
        except Exception as e:
            logger.error(f"Error removing from local backup: {e}")

# Global instance
haystack_manager = None

def get_haystack_manager() -> HaystackDocumentManager:
    """Get or create global Haystack manager instance"""
    global haystack_manager
    if haystack_manager is None:
        haystack_manager = HaystackDocumentManager()
    return haystack_manager
