"""
Enhanced PDF URL Trainer with Optional Local Caching
Allows keeping local files based on configuration
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

class EnhancedPDFURLTrainer:
    """PDF trainer with flexible local file management"""
    
    def __init__(self, 
                 haystack_mongo_integration=None,
                 cache_pdfs: bool = False,
                 cache_directory: str = None,
                 max_cache_size_gb: float = 5.0):
        """
        Initialize trainer with caching options
        
        Args:
            cache_pdfs: Whether to keep PDF files after processing
            cache_directory: Where to store cached PDFs (None = temp dir)
            max_cache_size_gb: Maximum cache size in GB
        """
        from production_haystack_mongo import HaystackStyleMongoIntegration
        
        self.haystack_mongo = haystack_mongo_integration or HaystackStyleMongoIntegration()
        self.session = None
        
        # Cache configuration
        self.cache_pdfs = cache_pdfs
        self.max_cache_size_bytes = max_cache_size_gb * 1024 * 1024 * 1024
        
        if cache_pdfs and cache_directory:
            # Use specified cache directory
            self.cache_dir = Path(cache_directory)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dir = str(self.cache_dir)
        else:
            # Use temporary directory (will be deleted)
            self.temp_dir = tempfile.mkdtemp(prefix="highpal_pdf_")
            self.cache_dir = Path(self.temp_dir)
    
    def cleanup_file(self, pdf_path: str, metadata: dict) -> bool:
        """
        Decide whether to keep or delete the PDF file
        
        Returns:
            bool: True if file was deleted, False if kept
        """
        if not self.cache_pdfs:
            # Always delete (current behavior)
            try:
                os.remove(pdf_path)
                return True
            except Exception as e:
                print(f"⚠️ Could not delete {pdf_path}: {e}")
                return False
        
        # Cache management logic
        try:
            # Check cache size limit
            total_size = sum(f.stat().st_size for f in self.cache_dir.rglob('*.pdf'))
            
            if total_size > self.max_cache_size_bytes:
                # Remove oldest files to make space
                self._cleanup_old_files()
            
            # Keep the file in cache
            print(f"📦 Cached: {os.path.basename(pdf_path)}")
            return False
            
        except Exception as e:
            print(f"⚠️ Cache error, deleting file: {e}")
            try:
                os.remove(pdf_path)
                return True
            except:
                return False
    
    def _cleanup_old_files(self):
        """Remove oldest cached PDF files to free space"""
        try:
            pdf_files = list(self.cache_dir.glob('*.pdf'))
            pdf_files.sort(key=lambda f: f.stat().st_mtime)  # Sort by modification time
            
            # Remove oldest 20% of files
            files_to_remove = pdf_files[:len(pdf_files) // 5]
            
            for file_path in files_to_remove:
                try:
                    file_path.unlink()
                    print(f"🗑️ Removed old cache: {file_path.name}")
                except:
                    pass
        except Exception as e:
            print(f"⚠️ Cache cleanup error: {e}")
    
    def get_cache_info(self) -> Dict:
        """Get information about cached files"""
        try:
            if not self.cache_pdfs:
                return {"caching": "disabled"}
            
            pdf_files = list(self.cache_dir.glob('*.pdf'))
            total_size = sum(f.stat().st_size for f in pdf_files)
            
            return {
                "caching": "enabled",
                "cached_files": len(pdf_files),
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "cache_directory": str(self.cache_dir),
                "max_size_gb": self.max_cache_size_bytes / (1024 * 1024 * 1024)
            }
        except:
            return {"caching": "error"}

# Configuration examples
CACHING_STRATEGIES = {
    "no_cache": {
        "cache_pdfs": False,
        "description": "Delete all PDFs after processing (current default)"
    },
    "small_cache": {
        "cache_pdfs": True,
        "cache_directory": "./pdf_cache",
        "max_cache_size_gb": 1.0,
        "description": "Keep up to 1GB of recent PDFs"
    },
    "large_cache": {
        "cache_pdfs": True,
        "cache_directory": "./pdf_cache", 
        "max_cache_size_gb": 10.0,
        "description": "Keep up to 10GB of PDFs for reprocessing"
    },
    "unlimited_cache": {
        "cache_pdfs": True,
        "cache_directory": "./pdf_archive",
        "max_cache_size_gb": float('inf'),
        "description": "Keep all PDFs permanently"
    }
}

if __name__ == "__main__":
    print("📁 PDF Caching Strategy Options:")
    for name, config in CACHING_STRATEGIES.items():
        print(f"\\n{name.upper()}:")
        print(f"  {config['description']}")
        if config.get('cache_directory'):
            print(f"  Directory: {config['cache_directory']}")
        if config.get('max_cache_size_gb') != float('inf'):
            print(f"  Max Size: {config['max_cache_size_gb']}GB")
