import PyPDF2
import io
import re
from typing import Dict, Optional

class PDFProcessor:
    """
    Handles PDF text extraction and preprocessing for legal documents
    """
    
    def __init__(self):
        self.legal_patterns = {
            'case_citation': r'\d+\s+[A-Z][a-z]+\.?\s+\d+',
            'court_name': r'(Supreme Court|High Court|District Court|Tribunal)',
            'date_pattern': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            'section_headers': r'(FACTS?|ISSUE|HOLDING|REASONING|CONCLUSION|JUDGMENT)'
        }
    
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from PDF file
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            str: Extracted text content
            
        Raises:
            Exception: If PDF processing fails
        """
        try:
            text_content = ""
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    raise Exception("PDF is password protected")
                
                # Extract text from all pages
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    
                    if page_text:
                        text_content += f"\n--- Page {page_num + 1} ---\n"
                        text_content += page_text
                
            if not text_content.strip():
                raise Exception("No text could be extracted from PDF")
            
            # Clean and preprocess the text
            cleaned_text = self._preprocess_text(text_content)
            
            return cleaned_text
            
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    def extract_from_bytes(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF bytes
        
        Args:
            pdf_bytes (bytes): PDF file as bytes
            
        Returns:
            str: Extracted text content
        """
        try:
            text_content = ""
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            if pdf_reader.is_encrypted:
                raise Exception("PDF is password protected")
            
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                
                if page_text:
                    text_content += f"\n--- Page {page_num + 1} ---\n"
                    text_content += page_text
            
            if not text_content.strip():
                raise Exception("No text could be extracted from PDF")
            
            return self._preprocess_text(text_content)
            
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    def _preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess extracted text
        
        Args:
            text (str): Raw extracted text
            
        Returns:
            str: Cleaned and preprocessed text
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page markers
        text = re.sub(r'--- Page \d+ ---', '', text)
        
        # Fix common OCR issues
        text = text.replace('ﬁ', 'fi')  # Fix ligature
        text = text.replace('ﬂ', 'fl')  # Fix ligature
        text = text.replace('\u2018', "'")   # Fix smart quotes
        text = text.replace('\u2019', "'")   # Fix smart quotes
        text = text.replace('\u201c', '"')   # Fix smart quotes
        text = text.replace('\u201d', '"')   # Fix smart quotes
        
        # Normalize line breaks
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
    
    def identify_document_type(self, text: str) -> Dict[str, any]:
        """
        Identify the type of legal document and extract basic metadata
        
        Args:
            text (str): Document text
            
        Returns:
            Dict: Document type and metadata
        """
        doc_info = {
            'type': 'unknown',
            'confidence': 0.0,
            'metadata': {}
        }
        
        text_lower = text.lower()
        
        # Check for judgment/opinion indicators
        judgment_indicators = [
            'judgment', 'opinion', 'decision', 'ruling', 'order',
            'court', 'justice', 'judge', 'plaintiff', 'defendant'
        ]
        
        judgment_score = sum(1 for indicator in judgment_indicators if indicator in text_lower)
        
        if judgment_score >= 3:
            doc_info['type'] = 'judgment'
            doc_info['confidence'] = min(judgment_score / len(judgment_indicators), 1.0)
        
        # Extract basic metadata
        court_matches = re.findall(self.legal_patterns['court_name'], text, re.IGNORECASE)
        if court_matches:
            doc_info['metadata']['court'] = court_matches[0]
        
        date_matches = re.findall(self.legal_patterns['date_pattern'], text)
        if date_matches:
            doc_info['metadata']['dates'] = date_matches[:3]  # First 3 dates found
        
        citation_matches = re.findall(self.legal_patterns['case_citation'], text)
        if citation_matches:
            doc_info['metadata']['citations'] = citation_matches[:5]  # First 5 citations
        
        return doc_info
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        Attempt to extract common legal document sections
        
        Args:
            text (str): Document text
            
        Returns:
            Dict: Extracted sections
        """
        sections = {}
        
        # Split text by common section headers
        section_pattern = r'(?i)\b(FACTS?|ISSUE|HOLDING|REASONING|CONCLUSION|JUDGMENT)\b'
        parts = re.split(section_pattern, text)
        
        current_section = None
        for i, part in enumerate(parts):
            if re.match(section_pattern, part, re.IGNORECASE):
                current_section = part.upper()
            elif current_section and part.strip():
                sections[current_section] = part.strip()
                current_section = None
        
        return sections
