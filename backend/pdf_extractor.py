"""
Advanced PDF Text Extraction Module
Python equivalent of the Node.js enhanced PDF extraction capabilities
"""

import io
import logging
import tempfile
import os
from typing import Dict, Any, Optional, Tuple
import fitz  # PyMuPDF
import PyPDF2
import pdfplumber
from pdfminer.high_level import extract_text as pdfminer_extract
from pdfminer.layout import LAParams

logger = logging.getLogger(__name__)

class AdvancedPDFExtractor:
    """Advanced PDF text extraction with multiple strategies"""
    
    def __init__(self):
        self.extraction_methods = [
            self._extract_with_pymupdf,
            self._extract_with_pdfplumber,
            self._extract_with_pypdf2,
            self._extract_with_pdfminer,
            self._extract_with_pymupdf_detailed,
            self._extract_with_pdfplumber_detailed
        ]
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """
        Extract text from PDF using multiple methods and return the best result
        Similar to the Node.js enhanced extraction
        """
        results = {
            'best_text': '',
            'extraction_info': {
                'methods': [],
                'total_length': 0,
                'pages': 0,
                'final_method': '',
                'all_results': {}
            }
        }
        
        logger.info(f"🚀 Starting enhanced PDF extraction for {len(pdf_content)} bytes...")
        
        # Try all extraction methods
        extraction_results = []
        
        for i, method in enumerate(self.extraction_methods, 1):
            try:
                method_name = method.__name__.replace('_extract_with_', '')
                logger.info(f"🔍 Trying method {i}: {method_name}")
                
                text, pages, method_info = method(pdf_content)
                
                extraction_results.append({
                    'method': method_name,
                    'text': text,
                    'length': len(text),
                    'pages': pages,
                    'info': method_info
                })
                
                results['extraction_info']['methods'].append(method_name)
                results['extraction_info']['all_results'][method_name] = {
                    'length': len(text),
                    'pages': pages
                }
                
                logger.info(f"📄 {method_name} extraction: {len(text)} characters from {pages} pages")
                
            except Exception as e:
                logger.warning(f"❌ {method.__name__} failed: {str(e)}")
                results['extraction_info']['all_results'][method_name] = {
                    'error': str(e)
                }
        
        # Choose the best result (longest text)
        if extraction_results:
            best_result = max(extraction_results, key=lambda x: x['length'])
            results['best_text'] = best_result['text']
            results['extraction_info']['total_length'] = best_result['length']
            results['extraction_info']['pages'] = best_result['pages']
            results['extraction_info']['final_method'] = best_result['method']
            
            logger.info(f"✅ FINAL RESULT: {best_result['length']} characters using best method: {best_result['method']}")
            logger.info(f"📊 All methods comparison: {', '.join([f'{r['method']}={r['length']}' for r in extraction_results])}")
        else:
            logger.error("❌ All extraction methods failed")
            results['best_text'] = f"PDF content ({len(pdf_content)} bytes) - All extraction methods failed"
        
        return results
    
    def _extract_with_pymupdf(self, pdf_content: bytes) -> Tuple[str, int, Dict]:
        """Extract using PyMuPDF (fitz) - usually the most reliable"""
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text = ""
        pages = doc.page_count
        
        for page_num in range(pages):
            page = doc.load_page(page_num)
            text += page.get_text() + "\n\n"
        
        doc.close()
        return text.strip(), pages, {'method': 'pymupdf_standard'}
    
    def _extract_with_pymupdf_detailed(self, pdf_content: bytes) -> Tuple[str, int, Dict]:
        """Extract using PyMuPDF with detailed text extraction"""
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text = ""
        pages = doc.page_count
        
        for page_num in range(pages):
            page = doc.load_page(page_num)
            # Use detailed extraction with blocks
            blocks = page.get_text("dict")
            page_text = ""
            
            for block in blocks.get("blocks", []):
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line.get("spans", []):
                            page_text += span.get("text", "") + " "
                        page_text += "\n"
                    page_text += "\n"
            
            text += page_text + "\n\n"
        
        doc.close()
        return text.strip(), pages, {'method': 'pymupdf_detailed'}
    
    def _extract_with_pdfplumber(self, pdf_content: bytes) -> Tuple[str, int, Dict]:
        """Extract using pdfplumber - good for tables and structured data"""
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            text = ""
            pages = len(pdf.pages)
            
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
        
        return text.strip(), pages, {'method': 'pdfplumber_standard'}
    
    def _extract_with_pdfplumber_detailed(self, pdf_content: bytes) -> Tuple[str, int, Dict]:
        """Extract using pdfplumber with table awareness"""
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            text = ""
            pages = len(pdf.pages)
            
            for page in pdf.pages:
                # Extract regular text
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
                
                # Extract tables separately
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            text += " | ".join(str(cell) if cell else "" for cell in row) + "\n"
                    text += "\n"
        
        return text.strip(), pages, {'method': 'pdfplumber_detailed'}
    
    def _extract_with_pypdf2(self, pdf_content: bytes) -> Tuple[str, int, Dict]:
        """Extract using PyPDF2 - basic but reliable"""
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        text = ""
        pages = len(reader.pages)
        
        for page in reader.pages:
            try:
                text += page.extract_text() + "\n\n"
            except Exception as e:
                logger.warning(f"PyPDF2 page extraction failed: {e}")
                continue
        
        return text.strip(), pages, {'method': 'pypdf2_standard'}
    
    def _extract_with_pdfminer(self, pdf_content: bytes) -> Tuple[str, int, Dict]:
        """Extract using pdfminer.six - good for complex layouts"""
        # Create a temporary file for pdfminer
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_content)
            tmp_file.flush()
            
            try:
                # Standard extraction
                text = pdfminer_extract(tmp_file.name)
                
                # Get page count using PyMuPDF (faster for metadata)
                doc = fitz.open(tmp_file.name)
                pages = doc.page_count
                doc.close()
                
                return text.strip(), pages, {'method': 'pdfminer_standard'}
            
            finally:
                os.unlink(tmp_file.name)

# Global instance
pdf_extractor = AdvancedPDFExtractor()

def extract_pdf_text_advanced(pdf_content: bytes) -> Dict[str, Any]:
    """
    Main function to extract text from PDF content
    Returns the same format as the Node.js version
    """
    return pdf_extractor.extract_text_from_pdf(pdf_content)
