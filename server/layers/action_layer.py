"""
Action Layer - Task Execution

This layer executes specific tasks (legal extraction, brief generation, citation normalization)
based on decisions from the Decision Layer, using the Perception Layer for LLM interactions.
"""

import time
import re
import json
from typing import Dict, Any, List, Optional
from .perception_layer import PerceptionLayer
from .memory_layer import MemoryLayer


class ActionLayer:
    """
    Action Layer handles execution of specific tasks like extraction, generation, normalization
    """
    
    def __init__(
        self,
        perception_layer: PerceptionLayer,
        memory_layer: MemoryLayer
    ):
        """
        Initialize Action Layer
        
        Args:
            perception_layer: Perception layer for LLM interactions
            memory_layer: Memory layer for preferences and context
        """
        self.perception = perception_layer
        self.memory = memory_layer
    
    # ========== LEGAL EXTRACTION ==========
    
    def extract_legal_information(
        self,
        document_text: str,
        preferences: Optional[Dict[str, Any]] = None,
        detail_level: str = 'summary'
    ) -> Dict[str, Any]:
        """
        Extract structured legal information from document text
        
        Args:
            document_text: The legal document text
            preferences: User preferences (if None, loaded from memory)
            detail_level: 'summary' or 'detailed' for logging verbosity
            
        Returns:
            Extraction result with success status and extracted data
        """
        start_time = time.time()
        
        # Log based on detail level
        if detail_level == 'detailed':
            print(f"  ⚡ [Action Layer] Legal Extraction - Starting")
            print(f"  [Action] Document length: {len(document_text)} characters")
        else:
            print(f"  ⚡ [Action Layer] Legal Extraction - Starting")
        
        try:
            # Validate input
            if not document_text or len(document_text.strip()) < 100:
                return {
                    'success': False,
                    'error': 'Document text is too short or empty (minimum 100 characters)',
                    'processing_time': time.time() - start_time
                }
            
            # Get preferences
            if not preferences:
                preferences = self.memory.get_preferences()
            
            # Truncate if too long (to avoid token limits)
            max_length = 50000
            if len(document_text) > max_length:
                document_text = document_text[:max_length] + "... [truncated]"
            
            # Get extraction prompt from perception layer
            prompt = self.perception.get_prompt(
                'legal_extraction',
                document_text=document_text,
                output_language=preferences.get('general', {}).get('language', 'en'),
                verbosity=preferences.get('general', {}).get('verbosity_level', 'standard')
            )
            
            # Get LLM preferences
            llm_prefs = preferences.get('llm', {})
            preferred_model = llm_prefs.get('primary_model', 'gemini')
            temperature = float(llm_prefs.get('temperature', 0.1))
            
            # Process with LLM
            result = self.perception.process_with_llm(
                prompt=prompt,
                preferred_model=preferred_model,
                temperature=temperature,
                detail_level=detail_level
            )
            
            if not result['success']:
                return {
                    'success': False,
                    'error': f'LLM processing failed: {result.get("error", "Unknown error")}',
                    'processing_time': time.time() - start_time
                }
            
            # Parse JSON response
            extracted_data = self.perception.parse_json_response(result['response'])
            
            if not extracted_data:
                return {
                    'success': False,
                    'error': 'Failed to parse LLM response as JSON',
                    'processing_time': time.time() - start_time
                }
            
            # Calculate confidence score
            confidence = self._calculate_extraction_confidence(extracted_data)
            
            # Validate and enhance extracted data
            enhanced_data = self._enhance_extraction_data(extracted_data)
            
            print(f"  ✅ [Action Layer] Legal Extraction - Completed (Confidence: {confidence:.2%})")
            
            return {
                'success': True,
                'data': enhanced_data,
                'confidence': confidence,
                'model_used': result.get('model_used', 'unknown'),
                'processing_time': time.time() - start_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Extraction failed: {str(e)}',
                'processing_time': time.time() - start_time
            }
    
    def _calculate_extraction_confidence(self, extracted_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on extracted data completeness"""
        required_fields = [
            'case_name', 'court', 'date', 'facts',
            'legal_issues', 'holdings', 'reasoning'
        ]
        
        found_fields = 0
        total_fields = len(required_fields)
        
        for field in required_fields:
            value = extracted_data.get(field)
            if value and value != "Not found" and value != "" and value != []:
                if isinstance(value, list) and len(value) > 0:
                    found_fields += 1
                elif isinstance(value, str) and len(value.strip()) > 0:
                    found_fields += 1
        
        # Base confidence on field completeness
        base_confidence = found_fields / total_fields
        
        # Bonus points for having citations
        citations = extracted_data.get('citations', [])
        if citations and len(citations) > 0:
            base_confidence += 0.1
        
        # Bonus for having case number
        case_number = extracted_data.get('case_number')
        if case_number and case_number != "Not found":
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def _enhance_extraction_data(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance extracted data with additional metadata"""
        enhanced = extracted_data.copy()
        
        # Ensure lists are properly formatted
        list_fields = ['facts', 'legal_issues', 'holdings', 'reasoning', 'citations', 'judges']
        for field in list_fields:
            if field in enhanced:
                if not isinstance(enhanced[field], list):
                    if enhanced[field]:
                        enhanced[field] = [str(enhanced[field])]
                    else:
                        enhanced[field] = []
        
        # Ensure strings are properly formatted
        string_fields = ['case_name', 'court', 'date', 'disposition', 'case_number']
        for field in string_fields:
            if field in enhanced:
                if not isinstance(enhanced[field], str):
                    enhanced[field] = str(enhanced[field]) if enhanced[field] else 'Not found'
        
        # Add metadata
        enhanced['metadata'] = {
            'extraction_timestamp': time.time(),
            'sections_extracted': list(enhanced.keys())
        }
        
        return enhanced
    
    # ========== BRIEF GENERATION ==========
    
    def generate_legal_brief(
        self,
        extracted_data: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None,
        detail_level: str = 'summary'
    ) -> Dict[str, Any]:
        """
        Generate legal brief from extracted data
        
        Args:
            extracted_data: Extracted legal information
            preferences: User preferences (if None, loaded from memory)
            detail_level: 'summary' or 'detailed' for logging verbosity
            
        Returns:
            Brief generation result with success status and generated brief
        """
        start_time = time.time()
        
        # Log based on detail level
        if detail_level == 'detailed':
            print(f"  ⚡ [Action Layer] Brief Generation - Starting")
            print(f"  [Action] Extracted fields: {list(extracted_data.keys())}")
        else:
            print(f"  ⚡ [Action Layer] Brief Generation - Starting")
        
        try:
            # Validate input
            if not extracted_data:
                return {
                    'success': False,
                    'error': 'No extracted data provided',
                    'processing_time': time.time() - start_time
                }
            
            # Check for minimum required fields
            required_fields = ['facts', 'legal_issues', 'holdings']
            missing_fields = [field for field in required_fields if not extracted_data.get(field)]
            
            if missing_fields:
                return {
                    'success': False,
                    'error': f'Missing required fields: {", ".join(missing_fields)}',
                    'processing_time': time.time() - start_time
                }
            
            # Get preferences
            if not preferences:
                preferences = self.memory.get_preferences()
            
            # Format extracted data for prompt
            def format_field(field_data):
                if isinstance(field_data, list):
                    return '; '.join(str(item) for item in field_data if item)
                return str(field_data) if field_data else "Not provided"
            
            # Get brief generation prompt
            prompt = self.perception.get_prompt(
                'brief_generation',
                case_name=format_field(extracted_data.get('case_name', 'Not provided')),
                court=format_field(extracted_data.get('court', 'Not provided')),
                date=format_field(extracted_data.get('date', 'Not provided')),
                facts=format_field(extracted_data.get('facts', 'Not provided')),
                legal_issues=format_field(extracted_data.get('legal_issues', [])),
                holdings=format_field(extracted_data.get('holdings', [])),
                reasoning=format_field(extracted_data.get('reasoning', [])),
                citations=format_field(extracted_data.get('citations', [])),
                disposition=format_field(extracted_data.get('disposition', 'Not provided')),
                output_language=preferences.get('general', {}).get('language', 'en'),
                verbosity=preferences.get('general', {}).get('verbosity_level', 'standard')
            )
            
            # Get LLM preferences
            llm_prefs = preferences.get('llm', {})
            preferred_model = llm_prefs.get('primary_model', 'gemini')
            temperature = float(llm_prefs.get('temperature', 0.2))
            
            # Process with LLM
            result = self.perception.process_with_llm(
                prompt=prompt,
                preferred_model=preferred_model,
                temperature=temperature,
                detail_level=detail_level
            )
            
            if not result['success']:
                return {
                    'success': False,
                    'error': f'LLM processing failed: {result.get("error", "Unknown error")}',
                    'processing_time': time.time() - start_time
                }
            
            # Parse JSON response
            brief_data = self.perception.parse_json_response(result['response'])
            
            if not brief_data:
                return {
                    'success': False,
                    'error': 'Failed to parse LLM response as JSON',
                    'processing_time': time.time() - start_time
                }
            
            # Enhance brief data
            enhanced_brief = self._enhance_brief_data(brief_data, extracted_data)
            
            print(f"  ✅ [Action Layer] Brief Generation - Completed (Word count: {enhanced_brief.get('word_count', 0)})")
            
            return {
                'success': True,
                'data': enhanced_brief,
                'model_used': result.get('model_used', 'unknown'),
                'processing_time': time.time() - start_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Brief generation failed: {str(e)}',
                'processing_time': time.time() - start_time
            }
    
    def _enhance_brief_data(self, brief_data: Dict[str, Any], extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance brief data with additional metadata"""
        enhanced = brief_data.copy()
        
        # Calculate actual word count
        total_words = 0
        text_fields = ['issue', 'facts', 'holding']
        
        for field in text_fields:
            if field in enhanced and enhanced[field]:
                total_words += len(str(enhanced[field]).split())
        
        # Add reasoning words
        if 'reasoning' in enhanced and isinstance(enhanced['reasoning'], list):
            for reason in enhanced['reasoning']:
                total_words += len(str(reason).split())
        
        enhanced['word_count'] = total_words
        
        # Validate confidence score
        confidence = enhanced.get('confidence_score', 0)
        if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 100:
            enhanced['confidence_score'] = self._calculate_brief_confidence(enhanced, extracted_data)
        
        # Add metadata
        enhanced['metadata'] = {
            'source_case': extracted_data.get('case_name', 'Unknown'),
            'source_court': extracted_data.get('court', 'Unknown'),
            'generation_timestamp': time.time()
        }
        
        # Ensure all required sections exist
        required_sections = ['issue', 'facts', 'holding', 'reasoning']
        for section in required_sections:
            if section not in enhanced:
                enhanced[section] = "Not available"
        
        # Add key_citations if not present
        if 'key_citations' not in enhanced:
            enhanced['key_citations'] = []
        
        return enhanced
    
    def _calculate_brief_confidence(self, brief_data: Dict[str, Any], extracted_data: Dict[str, Any]) -> int:
        """Calculate confidence score for the generated brief"""
        score = 0
        
        # Check completeness of required sections
        required_sections = ['issue', 'facts', 'holding', 'reasoning']
        for section in required_sections:
            if section in brief_data and brief_data[section] and brief_data[section] != "Not available":
                if section == 'reasoning' and isinstance(brief_data[section], list):
                    score += 20 if len(brief_data[section]) >= 3 else 10
                else:
                    score += 20
        
        # Check word count
        word_count = brief_data.get('word_count', 0)
        if 200 <= word_count <= 400:
            score += 10
        elif 100 <= word_count < 200 or 400 < word_count <= 500:
            score += 5
        
        # Check citations
        citations = brief_data.get('key_citations', [])
        if citations and len(citations) > 0:
            score += 10
        
        return min(score, 100)
    
    # ========== CITATION NORMALIZATION ==========
    
    def normalize_citations(
        self,
        citations: List[str],
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Normalize citations to specified format
        
        Args:
            citations: List of raw citations
            preferences: User preferences (if None, loaded from memory)
            
        Returns:
            Normalization result
        """
        start_time = time.time()
        
        try:
            # Get preferences
            if not preferences:
                preferences = self.memory.get_preferences()
            
            # Get citation format from preferences
            citation_prefs = preferences.get('citation', {})
            format_type = citation_prefs.get('format', 'bluebook')
            
            if not citations:
                return {
                    'success': True,
                    'data': {
                        'normalized_citations': [],
                        'format': format_type,
                        'total_processed': 0
                    },
                    'processing_time': time.time() - start_time
                }
            
            # Normalize each citation
            normalized_citations = []
            validation_errors = []
            
            for i, citation in enumerate(citations):
                try:
                    normalized = self._normalize_single_citation(citation, format_type)
                    normalized_citations.append(normalized)
                except Exception as e:
                    validation_errors.append(f"Citation {i+1}: {str(e)}")
                    # Keep original if error occurs
                    normalized_citations.append({
                        'original': citation,
                        'normalized': citation,
                        'type': 'error',
                        'confidence': 0.0,
                        'format': format_type
                    })
            
            return {
                'success': True,
                'data': {
                    'normalized_citations': normalized_citations,
                    'format': format_type,
                    'total_processed': len(citations)
                },
                'validation_errors': validation_errors,
                'processing_time': time.time() - start_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Citation normalization failed: {str(e)}',
                'processing_time': time.time() - start_time
            }
    
    def _normalize_single_citation(self, citation: str, format_type: str) -> Dict[str, Any]:
        """Normalize a single citation using pattern matching"""
        citation = citation.strip()
        
        # Citation patterns
        case_pattern = r'(\w+(?:\s+\w+)*)\s+v\.?\s+(\w+(?:\s+\w+)*),?\s*(\d+)\s+([A-Za-z\.]+)\s+(\d+)(?:\s*\(([^)]+)\))?'
        
        # Try case citation pattern
        match = re.search(case_pattern, citation, re.IGNORECASE)
        if match:
            plaintiff, defendant, volume, reporter, page, court_year = match.groups()
            
            # Format based on citation style
            if format_type == 'bluebook':
                normalized = f"{plaintiff} v. {defendant}, {volume} {reporter} {page}"
                if court_year:
                    normalized += f" ({court_year})"
            else:
                normalized = f"{plaintiff} v. {defendant}, {volume} {reporter} {page}"
                if court_year:
                    normalized += f" ({court_year})"
            
            return {
                'original': citation,
                'normalized': normalized,
                'type': 'case_citation',
                'confidence': 0.9,
                'format': format_type
            }
        
        # If no pattern matched, return cleaned version
        cleaned = re.sub(r'\s+', ' ', citation).strip()
        return {
            'original': citation,
            'normalized': cleaned,
            'type': 'generic',
            'confidence': 0.3,
            'format': format_type
        }
    
    # ========== VALIDATION ==========
    
    def validate_extraction(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted data"""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check required fields
        required_fields = ['case_name', 'facts', 'legal_issues', 'holdings']
        
        for field in required_fields:
            if field not in extracted_data or not extracted_data[field]:
                validation_result['errors'].append(f"Missing required field: {field}")
                validation_result['is_valid'] = False
        
        # Check list fields
        list_fields = ['legal_issues', 'holdings', 'reasoning', 'citations']
        for field in list_fields:
            if field in extracted_data and not isinstance(extracted_data[field], list):
                validation_result['warnings'].append(f"{field} should be a list")
        
        return validation_result
    
    def validate_brief(self, brief_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate generated brief"""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check required sections
        required_sections = ['issue', 'facts', 'holding', 'reasoning']
        
        for section in required_sections:
            if section not in brief_data or not brief_data[section]:
                validation_result['errors'].append(f"Missing required section: {section}")
                validation_result['is_valid'] = False
        
        # Check word count
        word_count = brief_data.get('word_count', 0)
        if word_count > 500:
            validation_result['warnings'].append(f"Brief is too long ({word_count} words)")
        elif word_count < 100:
            validation_result['warnings'].append(f"Brief is very short ({word_count} words)")
        
        return validation_result

