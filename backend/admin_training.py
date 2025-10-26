"""
Admin Training System for Shared Knowledge Base
Handles proprietary content upload with tagging for exam preparation
"""

import os
import hashlib
import tempfile
from datetime import datetime
from typing import List, Dict, Optional
from fastapi import UploadFile, HTTPException
from pymongo import MongoClient
from pathlib import Path
import aiohttp
import asyncio
from openai import OpenAI
import numpy as np

from pdf_url_trainer import PDFURLTrainer
from pdf_extractor import AdvancedPDFExtractor

# Initialize PDF extractor
pdf_extractor = AdvancedPDFExtractor()

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()
    result = pdf_extractor.extract_text_from_pdf(pdf_content)
    return result['best_text']

class AdminTrainingSystem:
    """
    Manages shared knowledge base for all students
    Supports tagging content by exam type, subject, topic, etc.
    """
    
    def __init__(self, mongo_uri: str, openai_api_key: str = None):
        """Initialize with MongoDB connection and OpenAI client"""
        self.client = MongoClient(mongo_uri)
        self.db = self.client['highpal_db']
        
        # Collections
        self.shared_knowledge = self.db['shared_knowledge']  # Main knowledge base
        self.training_metadata = self.db['training_metadata']  # Upload tracking
        
        # Initialize OpenAI for embeddings
        self.openai_client = None
        self.embeddings_enabled = False
        if openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=openai_api_key)
                self.embeddings_enabled = True
                print("✅ OpenAI embeddings enabled for semantic search")
            except Exception as e:
                print(f"⚠️ OpenAI embeddings disabled: {e}")
        
        # Create indexes for fast querying
        self._setup_indexes()
    
    def _setup_indexes(self):
        """Create indexes for efficient querying"""
        # Tag-based search indexes
        self.shared_knowledge.create_index([("tags.exam_type", 1)])
        self.shared_knowledge.create_index([("tags.subject", 1)])
        self.shared_knowledge.create_index([("tags.topic", 1)])
        self.shared_knowledge.create_index([("tags.difficulty", 1)])
        
        # Content type and verification
        self.shared_knowledge.create_index([("content_type", 1)])
        self.shared_knowledge.create_index([("verified", 1)])
        
        # Full-text search
        self.shared_knowledge.create_index([("content", "text")])
        
        # Vector search index (for embeddings)
        # Note: Vector search requires MongoDB Atlas with Atlas Search configured
        # Configure Atlas Search index manually with vectorSearch type
    
    def _generate_embedding(self, text: str, retries: int = 3) -> Optional[List[float]]:
        """
        Generate embedding vector for text using OpenAI text-embedding-3-small
        
        Args:
            text: Text to generate embedding for
            retries: Number of retry attempts on failure
            
        Returns:
            List of 1536 floats or None if embeddings disabled
        """
        if not self.embeddings_enabled or not self.openai_client:
            return None
        
        import time
        for attempt in range(retries):
            try:
                # Use text-embedding-3-small (1536 dimensions, cost-effective)
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text[:8000],  # Limit to 8000 chars to avoid token limits
                    timeout=30.0  # 30 second timeout
                )
                return response.data[0].embedding
            except Exception as e:
                if attempt < retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"⚠️ Embedding attempt {attempt + 1} failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Embedding generation failed after {retries} attempts: {e}")
                    return None
    
    def semantic_search(
        self, 
        query: str, 
        exam_type: Optional[str] = None,
        subject: Optional[str] = None,
        top_k: int = 5,
        similarity_threshold: float = 0.40  # Lowered to 40% for hybrid context
    ) -> List[Dict]:
        """
        Search shared knowledge base using semantic similarity
        
        Args:
            query: User's question
            exam_type: Optional filter by exam (e.g., 'CAT', 'JEE')
            subject: Optional filter by subject (e.g., 'Logical reasoning')
            top_k: Number of results to return
            similarity_threshold: Minimum cosine similarity (0-1)
            
        Returns:
            List of relevant documents with similarity scores
        """
        if not self.embeddings_enabled:
            print("⚠️ Semantic search unavailable - embeddings disabled")
            return []
        
        # Generate embedding for the query
        query_embedding = self._generate_embedding(query)
        if not query_embedding:
            print("❌ Failed to generate query embedding")
            return []
        
        # Build MongoDB filters
        match_filters = {"embedding": {"$ne": None}}  # Only docs with embeddings
        if exam_type:
            match_filters["tags.exam_type"] = exam_type
        if subject:
            match_filters["tags.subject"] = subject
        
        # Fetch candidate documents (limit to 500 for performance)
        results = list(self.shared_knowledge.find(match_filters).limit(500))
        
        if not results:
            print(f"📭 No documents found matching filters: {match_filters}")
            return []
        
        # Calculate cosine similarity for each document
        def cosine_similarity(vec1, vec2):
            """Calculate cosine similarity between two vectors"""
            try:
                vec1 = np.array(vec1)
                vec2 = np.array(vec2)
                dot_product = np.dot(vec1, vec2)
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)
                if norm1 == 0 or norm2 == 0:
                    return 0.0
                return dot_product / (norm1 * norm2)
            except Exception as e:
                print(f"⚠️ Cosine similarity calculation error: {e}")
                return 0.0
        
        scored_results = []
        try:
            for doc in results:
                if doc.get('embedding'):
                    try:
                        similarity = cosine_similarity(query_embedding, doc['embedding'])
                        if similarity >= similarity_threshold:
                            scored_results.append({
                                'content': doc.get('content', ''),
                                'source_filename': doc.get('source_filename', 'Unknown'),
                                'exam_types': doc.get('tags', {}).get('exam_type', []),
                                'subject': doc.get('tags', {}).get('subject', 'Unknown'),
                                'topic': doc.get('tags', {}).get('topic'),
                                'similarity_score': float(similarity),
                                'chunk_index': doc.get('chunk_index', 0),
                                'uploaded_at': doc.get('uploaded_at')
                            })
                    except Exception as e:
                        print(f"⚠️ Error processing document: {e}")
                        continue
        except Exception as e:
            print(f"❌ Error during semantic search: {e}")
            return []
        
        # Sort by similarity score (highest first)
        scored_results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Return top_k results
        top_results = scored_results[:top_k]
        
        print(f"🔍 Semantic search found {len(scored_results)} results (returning top {len(top_results)})")
        for i, result in enumerate(top_results[:3]):
            print(f"  {i+1}. {result['source_filename']} - Similarity: {result['similarity_score']:.3f}")
        
        return top_results
    
    async def upload_shared_pdf(
        self,
        file: UploadFile,
        tags: Dict,
        admin_id: str,
        description: str = ""
    ) -> Dict:
        """
        Upload a PDF file to shared knowledge base with tags
        
        Args:
            file: Uploaded PDF file
            tags: {
                "exam_type": ["JEE", "NEET", "CAT"],  # Can be multiple
                "subject": "Physics",
                "topic": "Thermodynamics",
                "chapter": "Heat Transfer",
                "difficulty": "intermediate",
                "class": "11th",
                "language": "English"
            }
            admin_id: ID of admin uploading content
            description: Brief description of content
        """
        try:
            # Validate tags
            self._validate_tags(tags)
            
            # Save file temporarily using system temp directory
            temp_dir = tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, file.filename)
            with open(temp_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            # Extract text from PDF
            text = extract_text_from_pdf(temp_path)
            
            if not text or len(text.strip()) < 100:
                raise ValueError("Insufficient text extracted from PDF")
            
            # Chunk text for better retrieval (larger chunks = fewer API calls)
            chunks = self._chunk_text(text, chunk_size=2000, overlap=200)
            
            # Calculate file hash for deduplication
            file_hash = hashlib.sha256(content).hexdigest()
            
            # Check for duplicates
            existing = self.shared_knowledge.find_one({"file_hash": file_hash})
            if existing:
                return {
                    "success": False,
                    "error": "Duplicate content detected",
                    "existing_id": str(existing["_id"])
                }
            
            # Store chunks in batches for better performance
            doc_ids = []
            batch_size = 50  # Process 50 chunks at a time
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_docs = []
                
                for j, chunk in enumerate(batch):
                    chunk_index = i + j
                    
                    # Generate embedding for semantic search
                    embedding = self._generate_embedding(chunk)
                    
                    doc = {
                        "content": chunk,
                        "content_type": "pdf_file",
                        "source_filename": file.filename,
                        "file_hash": file_hash,
                        "chunk_index": chunk_index,
                        "total_chunks": len(chunks),
                        "tags": tags,
                        "description": description,
                        "admin_id": admin_id,
                        "uploaded_at": datetime.now(),
                        "verified": True,  # Admin uploads are pre-verified
                        "access_level": "all_students",
                        "embedding": embedding,  # Store 1536-dim vector
                        "metadata": {
                            "file_size": len(content),
                            "text_length": len(text),
                            "chunk_length": len(chunk),
                            "has_embedding": embedding is not None
                        }
                    }
                    batch_docs.append(doc)
                
                # Insert batch
                if batch_docs:
                    result = self.shared_knowledge.insert_many(batch_docs)
                    doc_ids.extend([str(id) for id in result.inserted_ids])
                    
                    # Log progress
                    print(f"✅ Processed {len(doc_ids)}/{len(chunks)} chunks ({len(doc_ids)/len(chunks)*100:.1f}%)")
            
            # Track upload in metadata
            self._track_upload(
                source_type="pdf_file",
                source_name=file.filename,
                tags=tags,
                admin_id=admin_id,
                chunks_created=len(chunks),
                doc_ids=doc_ids
            )
            
            # Cleanup temp file
            os.remove(temp_path)
            
            return {
                "success": True,
                "message": f"Successfully uploaded and processed {file.filename}",
                "chunks_created": len(chunks),
                "document_ids": doc_ids,
                "tags": tags
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def upload_shared_pdf_url(
        self,
        url: str,
        tags: Dict,
        admin_id: str,
        description: str = ""
    ) -> Dict:
        """
        Download PDF from URL and add to shared knowledge base
        
        Args:
            url: Public URL to PDF
            tags: Same tagging structure as upload_shared_pdf
            admin_id: ID of admin
            description: Brief description
        """
        try:
            self._validate_tags(tags)
            
            # Use existing PDF URL trainer
            async with PDFURLTrainer() as trainer:
                # Download and process
                pdf_path = await trainer.download_pdf(url)
                
                if not pdf_path:
                    raise ValueError("Failed to download PDF from URL")
                
                # Extract text
                text = trainer.extract_text_from_pdf(pdf_path)
                
                if not text or len(text.strip()) < 100:
                    raise ValueError("Insufficient text extracted from PDF")
                
                # Chunk text
                chunks = trainer.chunk_text(text, chunk_size=1000, overlap=100)
                
                # Calculate content hash
                content_hash = hashlib.sha256(text.encode()).hexdigest()
                
                # Check duplicates
                existing = self.shared_knowledge.find_one({"content_hash": content_hash})
                if existing:
                    return {
                        "success": False,
                        "error": "Duplicate content detected",
                        "existing_id": str(existing["_id"])
                    }
                
                # Store chunks
                doc_ids = []
                for i, chunk in enumerate(chunks):
                    # Generate embedding for semantic search
                    embedding = self._generate_embedding(chunk)
                    
                    doc = {
                        "content": chunk,
                        "content_type": "pdf_url",
                        "source_url": url,
                        "content_hash": content_hash,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "tags": tags,
                        "description": description,
                        "admin_id": admin_id,
                        "uploaded_at": datetime.now(),
                        "verified": True,
                        "access_level": "all_students",
                        "embedding": embedding,  # Store 1536-dim vector
                        "metadata": {
                            "text_length": len(text),
                            "chunk_length": len(chunk),
                            "has_embedding": embedding is not None
                        }
                    }
                    
                    result = self.shared_knowledge.insert_one(doc)
                    doc_ids.append(str(result.inserted_id))
                
                # Track upload
                self._track_upload(
                    source_type="pdf_url",
                    source_name=url,
                    tags=tags,
                    admin_id=admin_id,
                    chunks_created=len(chunks),
                    doc_ids=doc_ids
                )
                
                # Cleanup
                try:
                    os.remove(pdf_path)
                except:
                    pass
                
                return {
                    "success": True,
                    "message": f"Successfully processed PDF from URL",
                    "url": url,
                    "chunks_created": len(chunks),
                    "document_ids": doc_ids,
                    "tags": tags
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def bulk_upload_urls(
        self,
        uploads: List[Dict],
        admin_id: str
    ) -> Dict:
        """
        Bulk upload multiple URLs with different tags
        
        Args:
            uploads: [
                {
                    "url": "https://example.com/jee_physics.pdf",
                    "tags": {"exam_type": ["JEE"], "subject": "Physics"},
                    "description": "JEE Main Physics Chapter 1"
                },
                ...
            ]
        """
        results = {
            "total": len(uploads),
            "successful": 0,
            "failed": 0,
            "details": []
        }
        
        for upload_item in uploads:
            result = await self.upload_shared_pdf_url(
                url=upload_item["url"],
                tags=upload_item["tags"],
                admin_id=admin_id,
                description=upload_item.get("description", "")
            )
            
            results["details"].append({
                "url": upload_item["url"],
                "result": result
            })
            
            if result["success"]:
                results["successful"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    def semantic_search(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Semantic search using vector embeddings (preferred method)
        
        Args:
            query: Search query
            filters: Tag filters (exam_type, subject, etc.)
            limit: Max results to return
            
        Returns:
            List of matching documents with similarity scores
        """
        if not self.embeddings_enabled:
            # Fallback to text search if embeddings disabled
            return self.query_shared_knowledge(query, filters, limit)
        
        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            if not query_embedding:
                return self.query_shared_knowledge(query, filters, limit)
            
            # Build filter for tags
            search_filter = {"verified": True, "embedding": {"$exists": True}}
            if filters:
                for key, value in filters.items():
                    if value:
                        search_filter[f"tags.{key}"] = value
            
            # Vector similarity search using aggregation pipeline
            pipeline = [
                {"$match": search_filter},
                {
                    "$addFields": {
                        "similarity": {
                            "$reduce": {
                                "input": {"$range": [0, {"$size": "$embedding"}]},
                                "initialValue": 0,
                                "in": {
                                    "$add": [
                                        "$$value",
                                        {
                                            "$multiply": [
                                                {"$arrayElemAt": ["$embedding", "$$this"]},
                                                {"$arrayElemAt": [query_embedding, "$$this"]}
                                            ]
                                        }
                                    ]
                                }
                            }
                        }
                    }
                },
                {"$sort": {"similarity": -1}},
                {"$limit": limit}
            ]
            
            results = list(self.shared_knowledge.aggregate(pipeline))
            return results
            
        except Exception as e:
            print(f"⚠️ Semantic search failed, falling back to text search: {e}")
            return self.query_shared_knowledge(query, filters, limit)
    
    def query_shared_knowledge(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 5
    ) -> List[Dict]:
        """
        Query shared knowledge base with keyword search (fallback method)
        
        Args:
            query: Search query
            filters: {
                "exam_type": "JEE",
                "subject": "Physics",
                "topic": "Thermodynamics",
                "difficulty": "intermediate"
            }
            limit: Max results to return
        """
        search_filter = {"verified": True}
        
        # Add tag filters
        if filters:
            for key, value in filters.items():
                if value:
                    search_filter[f"tags.{key}"] = value
        
        # Text search
        results = self.shared_knowledge.find(
            {
                **search_filter,
                "$text": {"$search": query}
            },
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})]).limit(limit)
        
        return list(results)
    
    def get_available_tags(self) -> Dict:
        """Get all available tags in the system for filtering"""
        return {
            "exam_types": self.shared_knowledge.distinct("tags.exam_type"),
            "subjects": self.shared_knowledge.distinct("tags.subject"),
            "topics": self.shared_knowledge.distinct("tags.topic"),
            "difficulties": self.shared_knowledge.distinct("tags.difficulty"),
            "classes": self.shared_knowledge.distinct("tags.class"),
            "languages": self.shared_knowledge.distinct("tags.language")
        }
    
    def get_content_stats(self, filters: Optional[Dict] = None) -> Dict:
        """Get statistics about shared knowledge base"""
        base_filter = filters or {}
        
        # Get last upload and convert datetime
        last_upload = self.shared_knowledge.find_one(
            base_filter,
            sort=[("uploaded_at", -1)]
        )
        
        # Convert ObjectId and datetime to strings for JSON serialization
        if last_upload:
            last_upload["_id"] = str(last_upload["_id"])
            if "uploaded_at" in last_upload:
                last_upload["uploaded_at"] = last_upload["uploaded_at"].isoformat() if hasattr(last_upload["uploaded_at"], 'isoformat') else str(last_upload["uploaded_at"])
            # Remove embedding to reduce response size
            if "embedding" in last_upload:
                del last_upload["embedding"]
        
        return {
            "total_documents": self.shared_knowledge.count_documents(base_filter),
            "total_chunks": self.shared_knowledge.count_documents(base_filter),
            "verified_content": self.shared_knowledge.count_documents({**base_filter, "verified": True}),
            "by_exam_type": list(self.shared_knowledge.aggregate([
                {"$match": base_filter},
                {"$unwind": "$tags.exam_type"},
                {"$group": {"_id": "$tags.exam_type", "count": {"$sum": 1}}}
            ])),
            "by_subject": list(self.shared_knowledge.aggregate([
                {"$match": base_filter},
                {"$group": {"_id": "$tags.subject", "count": {"$sum": 1}}}
            ])),
            "last_upload": last_upload
        }
    
    def _validate_tags(self, tags: Dict):
        """Validate tag structure and values"""
        required_fields = ["exam_type", "subject"]
        
        for field in required_fields:
            if field not in tags:
                raise ValueError(f"Missing required tag field: {field}")
        
        # Validate exam types
        valid_exam_types = [
            "JEE", "NEET", "CAT", "GATE", "UPSC", "SSC", 
            "Banking", "Railways", "State_PSC", "NDA", "CDS",
            "CLAT", "AIIMS", "JIPMER", "Other"
        ]
        
        exam_types = tags["exam_type"] if isinstance(tags["exam_type"], list) else [tags["exam_type"]]
        for exam_type in exam_types:
            if exam_type not in valid_exam_types:
                raise ValueError(f"Invalid exam_type: {exam_type}. Must be one of: {valid_exam_types}")
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                last_part = text[max(0, end-100):end]
                for delimiter in ['. ', '! ', '? ', '\n\n']:
                    pos = last_part.rfind(delimiter)
                    if pos > -1:
                        end = end - 100 + pos + len(delimiter)
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(start + chunk_size - overlap, end)
        
        return chunks
    
    def _track_upload(self, source_type: str, source_name: str, tags: Dict, 
                     admin_id: str, chunks_created: int, doc_ids: List[str]):
        """Track upload in metadata collection"""
        self.training_metadata.insert_one({
            "source_type": source_type,
            "source_name": source_name,
            "tags": tags,
            "admin_id": admin_id,
            "chunks_created": chunks_created,
            "document_ids": doc_ids,
            "uploaded_at": datetime.now(),
            "status": "completed"
        })
    
    def regenerate_embeddings(self, batch_size: int = 100) -> Dict:
        """
        Regenerate embeddings for existing content that doesn't have them
        Useful when enabling embeddings on existing database
        
        Args:
            batch_size: Number of documents to process per batch
            
        Returns:
            Statistics about regeneration process
        """
        if not self.embeddings_enabled:
            return {
                "success": False,
                "error": "Embeddings not enabled. Provide OpenAI API key."
            }
        
        # Find documents without embeddings
        docs_without_embeddings = self.shared_knowledge.find({
            "embedding": {"$exists": False}
        }).limit(batch_size)
        
        updated = 0
        failed = 0
        
        for doc in docs_without_embeddings:
            try:
                # Generate embedding
                embedding = self._generate_embedding(doc["content"])
                
                if embedding:
                    # Update document
                    self.shared_knowledge.update_one(
                        {"_id": doc["_id"]},
                        {
                            "$set": {
                                "embedding": embedding,
                                "metadata.has_embedding": True,
                                "metadata.embedding_generated_at": datetime.now()
                            }
                        }
                    )
                    updated += 1
                else:
                    failed += 1
                    
            except Exception as e:
                print(f"Failed to generate embedding for doc {doc['_id']}: {e}")
                failed += 1
        
        return {
            "success": True,
            "updated": updated,
            "failed": failed,
            "batch_size": batch_size,
            "message": f"Successfully generated {updated} embeddings, {failed} failed"
        }

# Example usage
if __name__ == "__main__":
    # Initialize system
    admin_system = AdminTrainingSystem(mongo_uri="mongodb://localhost:27017/")
    
    # Example: Upload JEE Physics content
    jee_physics_tags = {
        "exam_type": ["JEE", "JEE Advanced"],
        "subject": "Physics",
        "topic": "Thermodynamics",
        "chapter": "Heat Transfer",
        "difficulty": "advanced",
        "class": "11th",
        "language": "English"
    }
    
    # Example: Bulk upload
    bulk_uploads = [
        {
            "url": "https://example.com/jee_physics_thermo.pdf",
            "tags": jee_physics_tags,
            "description": "JEE Advanced Thermodynamics - Complete Theory"
        },
        {
            "url": "https://example.com/jee_math_calculus.pdf",
            "tags": {
                "exam_type": ["JEE"],
                "subject": "Mathematics",
                "topic": "Calculus",
                "difficulty": "intermediate",
                "class": "12th",
                "language": "English"
            },
            "description": "JEE Main Calculus - Problem Solving"
        }
    ]
    
    print("Admin Training System initialized")
    print("Available tags:", admin_system.get_available_tags())
    print("Content stats:", admin_system.get_content_stats())
