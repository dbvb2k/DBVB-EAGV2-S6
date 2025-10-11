import re
import time
from typing import Dict, List, Any, Optional, Tuple

class CitationNormalizerAgent:
    """
    Agent for normalizing legal citations to standard formats (Bluebook, etc.)
    """
    
    def __init__(self):
        self.supported_formats = ['bluebook', 'apa', 'mla', 'chicago']
        self._setup_patterns()
    
    def _setup_patterns(self):
        """Setup regex patterns for different citation types"""
        self.citation_patterns = {
            # Case citations
            'case_citation': {
                'pattern': r'(\w+(?:\s+\w+)*)\s+v\.?\s+(\w+(?:\s+\w+)*),?\s*(\d+)\s+([A-Za-z\.]+)\s+(\d+)(?:\s*\(([^)]+)\))?',
                'groups': ['plaintiff', 'defendant', 'volume', 'reporter', 'page', 'court_year']
            },
            
            # Statute citations
            'statute_citation': {
                'pattern': r'(\d+)\s+([A-Za-z\.]+)\s+[§§]?\s*(\d+(?:\.\d+)*)',
                'groups': ['title', 'code', 'section']
            },
            
            # Constitutional citations
            'constitutional_citation': {
                'pattern': r'(U\.S\.)\s+Const\.?\s+(art\.?\s+[IVX]+|amend\.?\s+[IVX]+)',
                'groups': ['country', 'provision']
            },
            
            # Journal citations
            'journal_citation': {
                'pattern': r'([^,]+),\s*([^,]+),\s*(\d+)\s+([A-Za-z\.\s]+)\s+(\d+)(?:\s*\((\d{4})\))?',
                'groups': ['author', 'title', 'volume', 'journal', 'page', 'year']
            }
        }
        
        # Format templates for different citation styles
        self.format_templates = {
            'bluebook': {
                'case': '{plaintiff} v. {defendant}, {volume} {reporter} {page} ({court} {year})',
                'statute': '{title} {code} § {section}',
                'constitutional': '{country} Const. {provision}',
                'journal': '{author}, {title}, {volume} {journal} {page} ({year})'
            },
            'apa': {
                'case': '{plaintiff} v. {defendant}, {volume} {reporter} {page} ({court} {year})',
                'statute': '{title} {code} § {section}',
                'constitutional': '{country} Constitution, {provision}',
                'journal': '{author} ({year}). {title}. {journal}, {volume}, {page}'
            },
            'mla': {
                'case': '{plaintiff} v. {defendant}. {reporter}, vol. {volume}, {year}, p. {page}',
                'statute': '{code}, title {title}, sec. {section}',
                'constitutional': '{country} Constitution, {provision}',
                'journal': '{author}. "{title}." {journal} {volume} ({year}): {page}'
            },
            'chicago': {
                'case': '{plaintiff} v. {defendant}, {volume} {reporter} {page} ({court} {year})',
                'statute': '{title} {code} § {section}',
                'constitutional': '{country} Constitution, {provision}',
                'journal': '{author}, "{title}," {journal} {volume} ({year}): {page}'
            }
        }
    
    def normalize(self, citations: List[str], format_type: str = 'bluebook') -> Dict[str, Any]:
        """
        Normalize citations to specified format
        
        Args:
            citations (List[str]): List of raw citations
            format_type (str): Target citation format
            
        Returns:
            Dict: Normalization result
        """
        start_time = time.time()
        
        try:
            if format_type not in self.supported_formats:
                return {
                    'success': False,
                    'error': f'Unsupported format: {format_type}. Supported: {", ".join(self.supported_formats)}',
                    'processing_time': time.time() - start_time
                }
            
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
            
            normalized_citations = []
            validation_errors = []
            
            for i, citation in enumerate(citations):
                try:
                    normalized = self._normalize_single_citation(citation, format_type)
                    if normalized:
                        normalized_citations.append(normalized)
                    else:
                        validation_errors.append(f"Citation {i+1}: Could not parse citation format")
                        # Keep original if normalization fails
                        normalized_citations.append({
                            'original': citation,
                            'normalized': citation,
                            'type': 'unknown',
                            'confidence': 0.0,
                            'format': format_type
                        })
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
                'format': format_type,
                'total_processed': len(citations),
                'validation_errors': validation_errors,
                'supported_formats': self.supported_formats,
                'processing_time': time.time() - start_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Citation normalization failed: {str(e)}',
                'processing_time': time.time() - start_time
            }
    
    def _normalize_single_citation(self, citation: str, format_type: str) -> Optional[Dict[str, Any]]:
        """
        Normalize a single citation
        
        Args:
            citation (str): Raw citation text
            format_type (str): Target format
            
        Returns:
            Dict: Normalized citation data
        """
        citation = citation.strip()
        if not citation:
            return None
        
        # Try to identify citation type and extract components
        for citation_type, pattern_info in self.citation_patterns.items():
            match = re.search(pattern_info['pattern'], citation, re.IGNORECASE)
            
            if match:
                # Extract components
                components = {}
                groups = pattern_info['groups']
                
                for i, group_name in enumerate(groups):
                    if i + 1 <= len(match.groups()) and match.group(i + 1):
                        components[group_name] = match.group(i + 1).strip()
                
                # Clean and enhance components
                components = self._clean_citation_components(components, citation_type)
                
                # Format according to target style
                formatted_citation = self._format_citation(components, citation_type, format_type)
                
                # Calculate confidence score
                confidence = self._calculate_citation_confidence(components, citation_type)
                
                return {
                    'original': citation,
                    'normalized': formatted_citation,
                    'type': citation_type,
                    'components': components,
                    'confidence': confidence,
                    'format': format_type
                }
        
        # If no pattern matched, try generic cleanup
        cleaned_citation = self._generic_citation_cleanup(citation)
        
        return {
            'original': citation,
            'normalized': cleaned_citation,
            'type': 'generic',
            'confidence': 0.3,
            'format': format_type
        }
    
    def _clean_citation_components(self, components: Dict[str, str], citation_type: str) -> Dict[str, str]:
        """Clean and standardize citation components"""
        cleaned = {}
        
        for key, value in components.items():
            if not value:
                continue
                
            # General cleaning
            value = value.strip()
            value = re.sub(r'\s+', ' ', value)  # Normalize whitespace
            
            # Specific cleaning based on component type
            if key in ['plaintiff', 'defendant']:
                # Clean party names
                value = self._clean_party_name(value)
            elif key == 'reporter':
                # Standardize reporter abbreviations
                value = self._standardize_reporter(value)
            elif key == 'court':
                # Clean court names
                value = self._clean_court_name(value)
            elif key in ['volume', 'page', 'section']:
                # Clean numeric values
                value = re.sub(r'[^\d.-]', '', value)
            elif key == 'year':
                # Extract year
                year_match = re.search(r'\d{4}', value)
                if year_match:
                    value = year_match.group(0)
            
            cleaned[key] = value
        
        return cleaned
    
    def _clean_party_name(self, name: str) -> str:
        """Clean party names"""
        # Remove common suffixes
        name = re.sub(r',?\s*(Inc\.?|Corp\.?|Co\.?|Ltd\.?|LLC)$', '', name, flags=re.IGNORECASE)
        
        # Capitalize properly
        words = name.split()
        cleaned_words = []
        
        for word in words:
            if word.lower() in ['v', 'v.', 'vs', 'vs.']:
                cleaned_words.append('v.')
            elif len(word) > 1:
                cleaned_words.append(word.capitalize())
            else:
                cleaned_words.append(word.upper())
        
        return ' '.join(cleaned_words)
    
    def _standardize_reporter(self, reporter: str) -> str:
        """Standardize reporter abbreviations"""
        reporter_mapping = {
            'f.supp': 'F. Supp.',
            'f.supp.2d': 'F. Supp. 2d',
            'f.2d': 'F.2d',
            'f.3d': 'F.3d',
            'u.s.': 'U.S.',
            's.ct.': 'S. Ct.',
            'l.ed.': 'L. Ed.',
            'l.ed.2d': 'L. Ed. 2d'
        }
        
        reporter_lower = reporter.lower()
        return reporter_mapping.get(reporter_lower, reporter)
    
    def _clean_court_name(self, court: str) -> str:
        """Clean court names"""
        # Extract year if present
        year_match = re.search(r'\d{4}', court)
        year = year_match.group(0) if year_match else ''
        
        # Remove year from court name
        court_name = re.sub(r'\d{4}', '', court).strip()
        court_name = re.sub(r'[,\s]+$', '', court_name)
        
        return f"{court_name} {year}".strip()
    
    def _format_citation(self, components: Dict[str, str], citation_type: str, format_type: str) -> str:
        """Format citation according to specified style"""
        # Get the appropriate template
        type_key = citation_type.replace('_citation', '')
        template = self.format_templates.get(format_type, {}).get(type_key)
        
        if not template:
            # Fallback to bluebook format
            template = self.format_templates.get('bluebook', {}).get(type_key)
        
        if not template:
            # Return cleaned original if no template available
            return ' '.join(components.values())
        
        try:
            # Fill in the template
            formatted = template.format(**components)
            
            # Clean up any remaining formatting issues
            formatted = re.sub(r'\s+', ' ', formatted)  # Normalize spaces
            formatted = re.sub(r'\(\s*\)', '', formatted)  # Remove empty parentheses
            formatted = formatted.strip()
            
            return formatted
            
        except KeyError as e:
            # If template formatting fails, return a basic format
            return ' '.join(v for v in components.values() if v)
    
    def _generic_citation_cleanup(self, citation: str) -> str:
        """Generic citation cleanup for unrecognized formats"""
        # Basic cleanup
        cleaned = re.sub(r'\s+', ' ', citation)  # Normalize whitespace
        cleaned = cleaned.strip()
        
        # Fix common issues
        cleaned = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned)  # Add space between camelCase
        cleaned = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', cleaned)  # Add space between letter and number
        cleaned = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', cleaned)  # Add space between number and letter
        
        return cleaned
    
    def _calculate_citation_confidence(self, components: Dict[str, str], citation_type: str) -> float:
        """Calculate confidence score for citation parsing"""
        required_components = {
            'case_citation': ['plaintiff', 'defendant', 'volume', 'reporter', 'page'],
            'statute_citation': ['title', 'code', 'section'],
            'constitutional_citation': ['country', 'provision'],
            'journal_citation': ['author', 'title', 'volume', 'journal', 'page']
        }
        
        required = required_components.get(citation_type, [])
        if not required:
            return 0.5  # Default confidence for unknown types
        
        found_components = sum(1 for comp in required if comp in components and components[comp])
        confidence = found_components / len(required)
        
        # Bonus for having year information
        if 'year' in components and components['year']:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def get_citation_suggestions(self, citation: str) -> List[Dict[str, str]]:
        """Get suggestions for improving citation format"""
        suggestions = []
        
        # Check for common issues
        if not re.search(r'\d{4}', citation):
            suggestions.append({
                'type': 'missing_year',
                'message': 'Consider adding the year of the decision',
                'example': 'Smith v. Jones, 123 F.3d 456 (2d Cir. 2000)'
            })
        
        if 'v' in citation.lower() and not re.search(r'v\.', citation):
            suggestions.append({
                'type': 'abbreviation',
                'message': 'Use "v." instead of "v" in case citations',
                'example': 'Smith v. Jones (not Smith v Jones)'
            })
        
        if re.search(r'\d+\s*-\s*\d+', citation):
            suggestions.append({
                'type': 'page_range',
                'message': 'Use specific page number instead of range when possible',
                'example': '123 F.3d 456 (not 123 F.3d 456-460)'
            })
        
        return suggestions
    
    def validate_citation_format(self, citation: str, format_type: str) -> Dict[str, Any]:
        """Validate if citation follows the specified format rules"""
        validation_result = {
            'is_valid': True,
            'format': format_type,
            'errors': [],
            'warnings': [],
            'suggestions': []
        }
        
        # Get format-specific validation rules
        if format_type == 'bluebook':
            validation_result = self._validate_bluebook_format(citation, validation_result)
        elif format_type == 'apa':
            validation_result = self._validate_apa_format(citation, validation_result)
        # Add more format validations as needed
        
        return validation_result
    
    def _validate_bluebook_format(self, citation: str, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Bluebook citation format"""
        # Check for proper case citation format
        if ' v. ' in citation:
            if not re.search(r'\w+ v\. \w+, \d+ [A-Za-z\.]+ \d+', citation):
                validation_result['warnings'].append('Case citation may not follow standard Bluebook format')
        
        # Check for proper punctuation
        if citation.count('(') != citation.count(')'):
            validation_result['errors'].append('Unmatched parentheses')
            validation_result['is_valid'] = False
        
        return validation_result
    
    def _validate_apa_format(self, citation: str, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Validate APA citation format"""
        # APA specific validations
        if not re.search(r'\(\d{4}\)', citation):
            validation_result['warnings'].append('APA format typically includes year in parentheses')
        
        return validation_result
