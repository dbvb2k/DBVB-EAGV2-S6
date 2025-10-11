import google.generativeai as genai
import requests
import json
import time
import re
from typing import Dict, Any, Optional
from config import Config

class BriefGeneratorAgent:
    """
    AI Agent for generating comprehensive legal briefs from extracted legal information
    """
    
    def __init__(self):
        self.config = Config()
        self._setup_models()
        
        # Brief generation prompt template
        self.brief_prompt = """
You are a legal-summarization assistant. Given structured fields (facts, issues, holdings) and a list of supporting cases with snippets and citations, draft a short legal brief of max 400 words with the following structure:

REQUIRED SECTIONS:
1. **Issue**: Main legal question(s) presented (1-2 sentences)
2. **Facts**: Key factual background (2-3 sentences, essential facts only)
3. **Holding**: Court's main ruling/decision (1-2 sentences)
4. **Reasoning**: Court's legal reasoning (3-5 bullet points, key arguments)
5. **Key Citations**: Important case law and legal references cited

EXTRACTED LEGAL DATA:
Case Name: {case_name}
Court: {court}
Date: {date}
Facts: {facts}
Legal Issues: {legal_issues}
Holdings: {holdings}
Reasoning: {reasoning}
Citations: {citations}
Disposition: {disposition}

INSTRUCTIONS:
- Keep the brief concise but comprehensive (max 400 words)
- Use clear, professional legal writing
- Ensure each section flows logically
- Include only the most relevant citations
- Provide a confidence score (0-100) for brief completeness
- Use bullet points for reasoning section
- Make the brief self-contained and understandable

Return the response as a valid JSON object:
{{
    "issue": "...",
    "facts": "...",
    "holding": "...",
    "reasoning": ["...", "...", "..."],
    "key_citations": ["...", "..."],
    "word_count": 0,
    "confidence_score": 0
}}
"""
    
    def _setup_models(self):
        """Initialize AI models"""
        try:
            # Setup Gemini
            if self.config.GEMINI_API_KEY:
                genai.configure(api_key=self.config.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel(self.config.GEMINI_MODEL)
            else:
                self.gemini_model = None
                
            # Ollama setup (no API key needed)
            self.ollama_available = self._check_ollama_availability()
            
        except Exception as e:
            print(f"Model setup error: {e}")
            self.gemini_model = None
            self.ollama_available = False
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.config.OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate legal brief from extracted data
        
        Args:
            extracted_data (Dict): Extracted legal information
            
        Returns:
            Dict: Brief generation result with success status and generated brief
        """
        start_time = time.time()
        
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
            
            # Try primary model first
            if self.config.PRIMARY_MODEL == 'gemini' and self.gemini_model:
                result = self._generate_with_gemini(extracted_data)
                if result['success']:
                    result['model_used'] = 'gemini'
                    result['processing_time'] = time.time() - start_time
                    return result
            
            # Try fallback model
            if self.config.FALLBACK_MODEL == 'ollama' and self.ollama_available:
                result = self._generate_with_ollama(extracted_data)
                if result['success']:
                    result['model_used'] = 'ollama'
                    result['processing_time'] = time.time() - start_time
                    return result
            
            # Return mock brief for testing when no AI models available
            return self._generate_mock_brief(extracted_data, time.time() - start_time)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Brief generation failed: {str(e)}',
                'processing_time': time.time() - start_time
            }
    
    def _generate_with_gemini(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate brief using Gemini model"""
        try:
            prompt = self._format_prompt(extracted_data)
            response = self.gemini_model.generate_content(prompt)
            
            if not response.text:
                return {
                    'success': False,
                    'error': 'Empty response from Gemini'
                }
            
            # Parse JSON response
            brief_data = self._parse_brief_response(response.text)
            
            if not brief_data:
                return {
                    'success': False,
                    'error': 'Failed to parse Gemini response'
                }
            
            # Validate and enhance brief data
            enhanced_brief = self._enhance_brief_data(brief_data, extracted_data)
            
            return {
                'success': True,
                'data': enhanced_brief,
                'raw_response': response.text
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Gemini brief generation failed: {str(e)}'
            }
    
    def _generate_with_ollama(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate brief using Ollama model"""
        try:
            prompt = self._format_prompt(extracted_data)
            
            payload = {
                "model": self.config.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            }
            
            response = requests.post(
                f"{self.config.OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=90
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Ollama API error: {response.status_code}'
                }
            
            response_data = response.json()
            generated_text = response_data.get('response', '')
            
            if not generated_text:
                return {
                    'success': False,
                    'error': 'Empty response from Ollama'
                }
            
            # Parse JSON response
            brief_data = self._parse_brief_response(generated_text)
            
            if not brief_data:
                return {
                    'success': False,
                    'error': 'Failed to parse Ollama response'
                }
            
            # Validate and enhance brief data
            enhanced_brief = self._enhance_brief_data(brief_data, extracted_data)
            
            return {
                'success': True,
                'data': enhanced_brief,
                'raw_response': generated_text
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Ollama brief generation failed: {str(e)}'
            }
    
    def _format_prompt(self, extracted_data: Dict[str, Any]) -> str:
        """Format the prompt with extracted data"""
        # Convert lists to strings for better prompt formatting
        def format_field(field_data):
            if isinstance(field_data, list):
                return '; '.join(str(item) for item in field_data if item)
            return str(field_data) if field_data else "Not provided"
        
        try:
            return self.brief_prompt.format(
                case_name=format_field(extracted_data.get('case_name', 'Not provided')),
                court=format_field(extracted_data.get('court', 'Not provided')),
                date=format_field(extracted_data.get('date', 'Not provided')),
                facts=format_field(extracted_data.get('facts', 'Not provided')),
                legal_issues=format_field(extracted_data.get('legal_issues', [])),
                holdings=format_field(extracted_data.get('holdings', [])),
                reasoning=format_field(extracted_data.get('reasoning', [])),
                citations=format_field(extracted_data.get('citations', [])),
                disposition=format_field(extracted_data.get('disposition', 'Not provided'))
            )
        except Exception as e:
            print(f"DEBUG: Error formatting prompt: {str(e)}")
            # Return a simplified prompt if formatting fails
            return f"Generate a legal brief for case: {extracted_data.get('case_name', 'Unknown Case')}"
    
    def _parse_brief_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the AI model response to extract JSON"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            
            # If no JSON found, try to parse the entire response
            return json.loads(response_text)
            
        except json.JSONDecodeError:
            # Try to clean up common JSON issues
            try:
                # Remove markdown code blocks
                cleaned_text = re.sub(r'```json\n?', '', response_text)
                cleaned_text = re.sub(r'```\n?', '', cleaned_text)
                cleaned_text = cleaned_text.strip()
                
                return json.loads(cleaned_text)
            except:
                return None
    
    def _enhance_brief_data(self, brief_data: Dict[str, Any], extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance brief data with additional metadata and validation"""
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
            'generation_timestamp': time.time(),
            'sections_included': list(enhanced.keys())
        }
        
        # Ensure all required sections exist
        required_sections = ['issue', 'facts', 'holding', 'reasoning']
        for section in required_sections:
            if section not in enhanced:
                enhanced[section] = "Not available"
        
        # Add key_citations if not present (optional)
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
        
        # Check word count (should be reasonable but not too long)
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
    
    def validate_brief(self, brief_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate generated brief and provide feedback"""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
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
            validation_result['warnings'].append(f"Brief is too long ({word_count} words). Consider shortening.")
        elif word_count < 100:
            validation_result['warnings'].append(f"Brief is very short ({word_count} words). Consider expanding.")
        
        # Check reasoning structure
        reasoning = brief_data.get('reasoning', [])
        if isinstance(reasoning, list):
            if len(reasoning) < 2:
                validation_result['suggestions'].append("Consider adding more reasoning points (3-5 recommended)")
            elif len(reasoning) > 6:
                validation_result['suggestions'].append("Consider condensing reasoning points (3-5 recommended)")
        
        # Check citations
        citations = brief_data.get('key_citations', [])
        if not citations or len(citations) == 0:
            validation_result['warnings'].append("No citations found. Legal briefs typically include citations.")
        
        return validation_result
    
    def _generate_mock_brief(self, extracted_data: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Generate a mock brief for testing purposes when no AI models are available"""
        try:
            # Extract basic information
            case_name = extracted_data.get('case_name', 'Unknown Case')
            court = extracted_data.get('court', 'Unknown Court')
            facts = extracted_data.get('facts', ['No facts provided'])
            legal_issues = extracted_data.get('legal_issues', ['No legal issues identified'])
            holdings = extracted_data.get('holdings', ['No holdings provided'])
            reasoning = extracted_data.get('reasoning', ['No reasoning provided'])
            
            # Format facts
            facts_text = facts[0] if isinstance(facts, list) and facts else str(facts)
            
            # Format issues
            issues_text = legal_issues[0] if isinstance(legal_issues, list) and legal_issues else str(legal_issues)
            
            # Format holdings
            holdings_text = holdings[0] if isinstance(holdings, list) and holdings else str(holdings)
            
            # Format reasoning
            if isinstance(reasoning, list) and reasoning:
                reasoning_text = reasoning[:3]  # Take first 3 reasoning points
            else:
                reasoning_text = [str(reasoning)]
            
            # Create mock brief
            citations = extracted_data.get('citations', [])
            if not isinstance(citations, list):
                citations = []
            
            mock_brief = {
                'issue': f"The main legal question presented in {case_name} is: {issues_text}",
                'facts': f"The relevant facts of the case are: {facts_text}",
                'holding': f"The court's holding in {case_name} was: {holdings_text}",
                'reasoning': reasoning_text,
                'key_citations': citations[:3] if citations else [],  # Take first 3 citations safely
                'word_count': 0,  # Will be calculated by _enhance_brief_data
                'confidence_score': 75  # Mock confidence score
            }
            
            # Enhance the brief data
            enhanced_brief = self._enhance_brief_data(mock_brief, extracted_data)
            
            return {
                'success': True,
                'data': enhanced_brief,
                'model_used': 'mock',
                'processing_time': processing_time,
                'raw_response': 'Mock brief generated for testing purposes'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Mock brief generation failed: {str(e)}',
                'processing_time': processing_time
            }
