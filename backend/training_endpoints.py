"""
Training API Endpoints for HighPal
Adds PDF URL training capabilities to your FastAPI server
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional, Any
import asyncio
import logging
from datetime import datetime

# Import your PDF trainer
from pdf_url_trainer import PDFURLTrainer

logger = logging.getLogger(__name__)

# Pydantic models for API
class PDFURLTrainingRequest(BaseModel):
    urls: List[HttpUrl]
    metadata: Optional[Dict[str, Any]] = {}
    
class TrainingStatusResponse(BaseModel):
    total_documents: int
    pdf_url_documents: int
    other_documents: int
    last_updated: str

class TrainingResultResponse(BaseModel):
    total_urls: int
    successful: int
    failed: int
    total_chunks: int
    details: List[Dict]
    errors: List[Dict]

# Background task storage
training_tasks = {}

def create_training_endpoints(app: FastAPI):
    """Add training endpoints to your FastAPI app"""
    
    @app.post("/train/pdf-urls", response_model=TrainingResultResponse)
    async def train_from_pdf_urls(request: PDFURLTrainingRequest):
        """
        Train model from PDF URLs
        
        **Parameters:**
        - urls: List of PDF URLs to process
        - metadata: Optional metadata to attach to documents
        
        **Returns:**
        Training results including success/failure counts and details
        """
        try:
            logger.info(f"🚀 Starting PDF training with {len(request.urls)} URLs")
            
            # Convert HttpUrl objects to strings
            url_strings = [str(url) for url in request.urls]
            
            async with PDFURLTrainer() as trainer:
                result = await trainer.train_from_pdf_urls(
                    urls=url_strings,
                    metadata=request.metadata
                )
            
            logger.info(f"✅ Training completed: {result['successful']}/{result['total_urls']}")
            return TrainingResultResponse(**result)
            
        except Exception as e:
            logger.error(f"❌ Training failed: {e}")
            raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")
    
    @app.post("/train/pdf-urls/background")
    async def train_from_pdf_urls_background(
        request: PDFURLTrainingRequest, 
        background_tasks: BackgroundTasks
    ):
        """
        Start PDF URL training as background task
        
        Returns immediately with task ID for status checking
        """
        task_id = f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        async def background_training():
            try:
                url_strings = [str(url) for url in request.urls]
                async with PDFURLTrainer() as trainer:
                    result = await trainer.train_from_pdf_urls(
                        urls=url_strings,
                        metadata=request.metadata
                    )
                training_tasks[task_id] = {
                    'status': 'completed',
                    'result': result,
                    'completed_at': datetime.now().isoformat()
                }
            except Exception as e:
                training_tasks[task_id] = {
                    'status': 'failed',
                    'error': str(e),
                    'completed_at': datetime.now().isoformat()
                }
        
        background_tasks.add_task(background_training)
        training_tasks[task_id] = {
            'status': 'running',
            'started_at': datetime.now().isoformat()
        }
        
        return {
            'task_id': task_id,
            'status': 'started',
            'message': f'Training started with {len(request.urls)} URLs'
        }
    
    @app.get("/train/status/{task_id}")
    async def get_training_task_status(task_id: str):
        """Get status of background training task"""
        if task_id not in training_tasks:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return training_tasks[task_id]
    
    @app.get("/train/status", response_model=TrainingStatusResponse)
    async def get_training_status():
        """
        Get overall training data statistics
        
        **Returns:**
        - Total documents in system
        - Documents from PDF URLs
        - Other document sources
        """
        try:
            async with PDFURLTrainer() as trainer:
                status = trainer.get_training_status()
            
            if 'error' in status:
                raise HTTPException(status_code=500, detail=status['error'])
            
            return TrainingStatusResponse(**status)
            
        except Exception as e:
            logger.error(f"❌ Failed to get training status: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/train/pdf-urls/batch")
    async def train_from_pdf_url_batch(urls_batch: List[List[HttpUrl]]):
        """
        Process multiple batches of PDF URLs
        Useful for large-scale training with rate limiting
        """
        try:
            all_results = []
            
            for i, batch in enumerate(urls_batch):
                logger.info(f"📦 Processing batch {i+1}/{len(urls_batch)} with {len(batch)} URLs")
                
                url_strings = [str(url) for url in batch]
                
                async with PDFURLTrainer() as trainer:
                    batch_result = await trainer.train_from_pdf_urls(url_strings)
                
                all_results.append({
                    'batch_index': i,
                    'batch_size': len(batch),
                    **batch_result
                })
                
                # Small delay between batches to be respectful
                if i < len(urls_batch) - 1:
                    await asyncio.sleep(2)
            
            # Aggregate results
            total_results = {
                'batches_processed': len(urls_batch),
                'total_urls': sum(r['total_urls'] for r in all_results),
                'successful': sum(r['successful'] for r in all_results),
                'failed': sum(r['failed'] for r in all_results),
                'total_chunks': sum(r['total_chunks'] for r in all_results),
                'batch_details': all_results
            }
            
            return total_results
            
        except Exception as e:
            logger.error(f"❌ Batch training failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/train/clear-pdf-urls")
    async def clear_pdf_url_training_data():
        """
        Clear all training data from PDF URLs
        **WARNING: This will delete all PDF URL documents!**
        """
        try:
            async with PDFURLTrainer() as trainer:
                deleted_count = trainer.haystack_mongo.collection.delete_many({
                    'metadata.source_type': 'pdf_url'
                }).deleted_count
            
            return {
                'success': True,
                'deleted_documents': deleted_count,
                'message': f'Cleared {deleted_count} PDF URL documents'
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to clear training data: {e}")
            raise HTTPException(status_code=500, detail=str(e))

# Example training endpoints usage documentation
TRAINING_EXAMPLES = {
    "single_batch": {
        "urls": [
            "https://arxiv.org/pdf/2023.12345.pdf",
            "https://example.com/whitepaper.pdf"
        ],
        "metadata": {
            "domain": "research",
            "priority": "high",
            "training_session": "2025_q1"
        }
    },
    "background_task": "POST /train/pdf-urls/background with same payload",
    "batch_processing": [
        ["https://arxiv.org/pdf/paper1.pdf", "https://arxiv.org/pdf/paper2.pdf"],
        ["https://example.com/doc1.pdf", "https://example.com/doc2.pdf"]
    ]
}

if __name__ == "__main__":
    print("🚀 Training API endpoints ready!")
    print("📖 Available endpoints:")
    print("  POST /train/pdf-urls - Train from PDF URLs")
    print("  POST /train/pdf-urls/background - Background training")
    print("  GET /train/status/{task_id} - Check task status")
    print("  GET /train/status - Overall training statistics")
    print("  POST /train/pdf-urls/batch - Batch processing")
    print("  DELETE /train/clear-pdf-urls - Clear PDF training data")
