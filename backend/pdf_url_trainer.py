"""
PDF URL Training System for HighPal
Downloads, processes, and trains model with PDFs from public URLs
"""

import os
import requests
import hashlib
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, unquote
import tempfile
from datetime import datetime
import asyncio
import aiohttp
from pathlib import Path

# PDF Processing
try:
    import PyPDF2
    import fitz  # PyMuPDF - better PDF extraction
    PDF_PROCESSING_AVAILABLE = True
except ImportError:
    try:
        import PyPDF2
        PDF_PROCESSING_AVAILABLE = True
        print("⚠️ Using PyPDF2 only (install PyMuPDF for better results)")
    except ImportError:
        PDF_PROCESSING_AVAILABLE = False
        print("❌ No PDF processing libraries available")

# Import your existing integration
from production_haystack_mongo import HaystackStyleMongoIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFURLTrainer:
    """
    Comprehensive PDF URL training system for HighPal
    Downloads and processes PDFs from public URLs to train your model
    """
    
    def __init__(self, haystack_mongo_integration=None):
        """Initialize with existing MongoDB integration"""
        self.haystack_mongo = haystack_mongo_integration or HaystackStyleMongoIntegration()
        self.session = None
        self.temp_dir = tempfile.mkdtemp(prefix="highpal_pdf_")
        logger.info(f"📁 PDF processing directory: {self.temp_dir}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300),  # 5 minutes timeout
            headers={
                'User-Agent': 'HighPal-AI-Assistant/1.0 (PDF Training Bot)',
                'Accept': 'application/pdf,*/*'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using multiple methods"""
        text = ""
        
        # Method 1: Try PyMuPDF (fitz) first - better text extraction
        if 'fitz' in globals():
            try:
                doc = fitz.open(pdf_path)
                for page in doc:
                    text += page.get_text() + "\\n"
                doc.close()
                logger.info(f"✅ Extracted text using PyMuPDF: {len(text)} characters")
                return text
            except Exception as e:
                logger.warning(f"⚠️ PyMuPDF failed: {e}, trying PyPDF2...")
        
        # Method 2: Fallback to PyPDF2
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        text += page.extract_text() + "\\n"
                    except Exception as e:
                        logger.warning(f"⚠️ Error extracting page {page_num}: {e}")
                        continue
            
            logger.info(f"✅ Extracted text using PyPDF2: {len(text)} characters")
            return text
            
        except Exception as e:
            logger.error(f"❌ PDF text extraction failed: {e}")
            return ""
    
    async def download_pdf(self, url: str) -> Optional[str]:
        """Download PDF from URL and return local file path"""
        try:
            # Create filename from URL
            parsed_url = urlparse(url)
            filename = os.path.basename(unquote(parsed_url.path))
            if not filename.endswith('.pdf'):
                filename = f"{hashlib.md5(url.encode()).hexdigest()}.pdf"
            
            local_path = os.path.join(self.temp_dir, filename)
            
            logger.info(f"📥 Downloading PDF: {url}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '')
                    if 'pdf' not in content_type.lower():
                        logger.warning(f"⚠️ Content type is {content_type}, not PDF")
                    
                    # Stream download for large files
                    with open(local_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            f.write(chunk)
                    
                    file_size = os.path.getsize(local_path)
                    logger.info(f"✅ Downloaded: {filename} ({file_size:,} bytes)")
                    return local_path
                else:
                    logger.error(f"❌ Failed to download: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Download failed for {url}: {e}")
            return None
    
    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks for better context preservation"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings in the last 100 characters
                last_part = text[end-100:end]
                sentence_ends = ['.', '!', '?', '\\n']
                best_break = -1
                
                for sentence_end in sentence_ends:
                    pos = last_part.rfind(sentence_end)
                    if pos > best_break:
                        best_break = pos
                
                if best_break > -1:
                    end = end - 100 + best_break + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = max(start + chunk_size - overlap, end)
        
        return chunks
    
    async def process_single_pdf_url(self, url: str, metadata: Dict = None) -> Dict:
        """Process a single PDF URL and add to training data"""
        result = {
            'url': url,
            'success': False,
            'document_id': None,
            'chunks_added': 0,
            'error': None,
            'metadata': metadata or {}
        }
        
        try:
            # Download PDF
            pdf_path = await self.download_pdf(url)
            if not pdf_path:
                result['error'] = 'Download failed'
                return result
            
            # Extract text
            text = self.extract_text_from_pdf(pdf_path)
            if not text.strip():
                result['error'] = 'No text extracted'
                return result
            
            # Create document metadata
            doc_metadata = {
                'source_url': url,
                'source_type': 'pdf_url',
                'filename': os.path.basename(pdf_path),
                'processed_at': datetime.now().isoformat(),
                'text_length': len(text),
                **metadata
            }
            
            # Chunk the text for better processing
            chunks = self.chunk_text(text, chunk_size=800, overlap=100)
            logger.info(f"📄 Split into {len(chunks)} chunks")
            
            # Process each chunk
            doc_ids = []
            for i, chunk in enumerate(chunks):
                chunk_metadata = {
                    **doc_metadata,
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'chunk_id': f"{hashlib.md5(url.encode()).hexdigest()}_{i}"
                }
                
                # Add to MongoDB + create embeddings
                doc_id = self.haystack_mongo.add_document(
                    content=chunk,
                    metadata=chunk_metadata
                )
                
                if doc_id:
                    doc_ids.append(doc_id)
            
            # Cleanup
            try:
                os.remove(pdf_path)
            except:
                pass
            
            result.update({
                'success': True,
                'document_id': doc_ids[0] if doc_ids else None,
                'chunks_added': len(doc_ids),
                'text_length': len(text)
            })
            
            logger.info(f"✅ Successfully processed: {url} ({len(doc_ids)} chunks)")
            
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"❌ Error processing {url}: {e}")
        
        return result
    
    async def train_from_pdf_urls(self, urls: List[str], metadata: Dict = None) -> Dict:
        """Train model from multiple PDF URLs"""
        logger.info(f"🚀 Starting PDF URL training with {len(urls)} URLs")
        
        results = {
            'total_urls': len(urls),
            'successful': 0,
            'failed': 0,
            'total_chunks': 0,
            'details': [],
            'errors': []
        }
        
        # Process URLs concurrently (but limit concurrent downloads)
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent downloads
        
        async def process_with_semaphore(url):
            async with semaphore:
                return await self.process_single_pdf_url(url, metadata)
        
        # Execute all downloads
        tasks = [process_with_semaphore(url) for url in urls]
        pdf_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(pdf_results):
            if isinstance(result, Exception):
                results['failed'] += 1
                results['errors'].append({
                    'url': urls[i],
                    'error': str(result)
                })
            else:
                results['details'].append(result)
                if result['success']:
                    results['successful'] += 1
                    results['total_chunks'] += result['chunks_added']
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'url': result['url'],
                        'error': result['error']
                    })
        
        logger.info(f"🎉 Training complete: {results['successful']}/{results['total_urls']} URLs processed")
        logger.info(f"📊 Total chunks added: {results['total_chunks']}")
        
        return results
    
    def get_training_status(self) -> Dict:
        """Get current training data statistics"""
        try:
            total_docs = self.haystack_mongo.get_document_count()
            pdf_url_docs = self.haystack_mongo.collection.count_documents({
                'metadata.source_type': 'pdf_url'
            })
            
            return {
                'total_documents': total_docs,
                'pdf_url_documents': pdf_url_docs,
                'other_documents': total_docs - pdf_url_docs,
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            return {'error': str(e)}

# Convenience functions for easy use

async def train_from_urls(pdf_urls: List[str], metadata: Dict = None) -> Dict:
    """
    Simple function to train from PDF URLs
    
    Usage:
    result = await train_from_urls([
        'https://example.com/document1.pdf',
        'https://example.com/document2.pdf'
    ])
    """
    async with PDFURLTrainer() as trainer:
        return await trainer.train_from_pdf_urls(pdf_urls, metadata)

def train_from_urls_sync(pdf_urls: List[str], metadata: Dict = None) -> Dict:
    """Synchronous wrapper for training from URLs"""
    return asyncio.run(train_from_urls(pdf_urls, metadata))

# Example usage
if __name__ == "__main__":
    # Example PDF URLs for testing
    example_urls = [
        "https://arxiv.org/pdf/2023.01234.pdf",  # Replace with real URLs
        "https://example.com/whitepaper.pdf",
        "https://research.example.com/paper.pdf"
    ]
    
    # Training metadata
    training_metadata = {
        'training_session': 'initial_batch_2025',
        'domain': 'research_papers',
        'priority': 'high'
    }
    
    print("🚀 Starting PDF URL training...")
    result = train_from_urls_sync(example_urls, training_metadata)
    print(f"✅ Training completed: {result}")
