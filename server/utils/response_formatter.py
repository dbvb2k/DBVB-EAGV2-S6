from typing import Dict, List, Any
from datetime import datetime

class ResponseFormatter:
    """
    Formats API responses for consistent structure
    """
    
    def __init__(self):
        self.version = "1.0.0"
    
    def format_extraction_response(self, extraction_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the legal extraction response
        
        Args:
            extraction_result (Dict): Result from legal extractor agent
            
        Returns:
            Dict: Formatted response
        """
        return {
            'success': extraction_result.get('success', False),
            'timestamp': datetime.utcnow().isoformat(),
            'version': self.version,
            'data': {
                'extracted_fields': extraction_result.get('data', {}),
                'confidence_score': extraction_result.get('confidence', 0.0),
                'processing_time': extraction_result.get('processing_time', 0),
                'model_used': extraction_result.get('model_used', 'unknown')
            },
            'metadata': {
                'document_type': extraction_result.get('document_type', 'unknown'),
                'total_length': extraction_result.get('total_length', 0),
                'sections_found': extraction_result.get('sections_found', [])
            }
        }
    
    def format_brief_response(self, brief_result: Dict[str, Any], citation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format the brief generation response
        
        Args:
            brief_result (Dict): Result from brief generator agent
            citation_result (Dict): Result from citation normalizer
            
        Returns:
            Dict: Formatted response
        """
        return {
            'success': brief_result.get('success', False),
            'timestamp': datetime.utcnow().isoformat(),
            'version': self.version,
            'data': {
                'brief': brief_result.get('data', {}),
                'citations': citation_result.get('data', {}) if citation_result else {},
                'confidence_score': brief_result.get('confidence', 0.0),
                'word_count': self._count_words(brief_result.get('data', {})),
                'processing_time': brief_result.get('processing_time', 0),
                'model_used': brief_result.get('model_used', 'unknown')
            },
            'metadata': {
                'citation_format': citation_result.get('format', 'bluebook') if citation_result else 'bluebook',
                'total_citations': len(citation_result.get('data', {}).get('normalized_citations', []) if citation_result and citation_result.get('data') else []),
                'generation_parameters': brief_result.get('parameters', {})
            }
        }
    
    def format_error_response(self, error_message: str, error_code: str = None, details: Dict = None) -> Dict[str, Any]:
        """
        Format error response
        
        Args:
            error_message (str): Error message
            error_code (str): Optional error code
            details (Dict): Optional error details
            
        Returns:
            Dict: Formatted error response
        """
        response = {
            'success': False,
            'timestamp': datetime.utcnow().isoformat(),
            'version': self.version,
            'error': {
                'message': error_message,
                'code': error_code or 'UNKNOWN_ERROR'
            }
        }
        
        if details:
            response['error']['details'] = details
        
        return response
    
    def format_citation_response(self, citation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format citation normalization response
        
        Args:
            citation_result (Dict): Result from citation normalizer
            
        Returns:
            Dict: Formatted response
        """
        return {
            'success': citation_result.get('success', False),
            'timestamp': datetime.utcnow().isoformat(),
            'version': self.version,
            'data': {
                'normalized_citations': citation_result.get('data', {}).get('normalized_citations', []),
                'format_used': citation_result.get('format', 'bluebook'),
                'total_processed': citation_result.get('total_processed', 0),
                'processing_time': citation_result.get('processing_time', 0)
            },
            'metadata': {
                'supported_formats': citation_result.get('supported_formats', []),
                'validation_errors': citation_result.get('validation_errors', [])
            }
        }
    
    def _count_words(self, brief_data: Dict[str, Any]) -> int:
        """
        Count total words in the generated brief
        
        Args:
            brief_data (Dict): Brief data
            
        Returns:
            int: Total word count
        """
        total_words = 0
        
        if isinstance(brief_data, dict):
            for key, value in brief_data.items():
                if isinstance(value, str):
                    total_words += len(value.split())
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            total_words += len(item.split())
        
        return total_words
    
    def create_success_response(self, data: Any, message: str = None, metadata: Dict = None) -> Dict[str, Any]:
        """
        Create a generic success response
        
        Args:
            data (Any): Response data
            message (str): Optional success message
            metadata (Dict): Optional metadata
            
        Returns:
            Dict: Formatted success response
        """
        response = {
            'success': True,
            'timestamp': datetime.utcnow().isoformat(),
            'version': self.version,
            'data': data
        }
        
        if message:
            response['message'] = message
        
        if metadata:
            response['metadata'] = metadata
        
        return response
