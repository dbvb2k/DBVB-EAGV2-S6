import google.generativeai as genai
import requests
import json
import time
from typing import Dict, Any, List, Optional
from config import Config

class MasterOrchestratorAgent:
    """
    Master Orchestrator Agent that uses LLM to decide agent execution sequence
    and coordinate the entire legal analysis pipeline
    """
    
    def __init__(self):
        self.config = Config()
        self._setup_models()
        
        # Available agents and their capabilities
        self.available_agents = {
            'legal_extractor': {
                'name': 'Legal Extractor Agent',
                'description': 'Extracts structured legal information from documents',
                'input_required': ['document_text'],
                'output_provides': ['case_name', 'court', 'date', 'facts', 'legal_issues', 'holdings', 'reasoning', 'citations', 'disposition'],
                'dependencies': []
            },
            'brief_generator': {
                'name': 'Brief Generator Agent', 
                'description': 'Generates comprehensive legal briefs from extracted data',
                'input_required': ['extracted_data'],
                'output_provides': ['issue', 'facts', 'holding', 'reasoning', 'key_citations', 'word_count', 'confidence_score'],
                'dependencies': ['legal_extractor']
            },
            'citation_normalizer': {
                'name': 'Citation Normalizer Agent',
                'description': 'Normalizes citations to standard formats (Bluebook, APA, MLA, Chicago)',
                'input_required': ['citations'],
                'output_provides': ['normalized_citations', 'format_used', 'total_processed'],
                'dependencies': ['legal_extractor']
            },
            'case_retriever': {
                'name': 'Case Retriever Agent',
                'description': 'Finds similar cases and legal precedents',
                'input_required': ['legal_issues', 'key_phrases'],
                'output_provides': ['similar_cases', 'precedents', 'statutes', 'relevance_scores'],
                'dependencies': ['legal_extractor']
            },
            'comparator': {
                'name': 'Comparator Agent',
                'description': 'Compares target case with similar cases and highlights similarities',
                'input_required': ['target_case', 'similar_cases'],
                'output_provides': ['similarity_analysis', 'conflicting_holdings', 'reasoning_comparison'],
                'dependencies': ['legal_extractor', 'case_retriever']
            }
        }
        
        # Orchestration prompt template
        self.orchestration_prompt = """
You are the Master Orchestrator for a legal analysis system. Your job is to analyze the user's request and determine the optimal sequence of AI agents to execute.

AVAILABLE AGENTS:
{available_agents}

USER REQUEST:
{user_request}

CURRENT CONTEXT:
{current_context}

INSTRUCTIONS:
1. Analyze the user's request and determine what legal analysis is needed
2. Select the appropriate agents to execute in the optimal sequence
3. Consider agent dependencies (some agents require output from others)
4. Determine if any agents should be skipped based on the request
5. Provide reasoning for your agent selection and sequence

RESPONSE FORMAT (JSON):
{{
    "analysis": "Brief analysis of what the user wants to accomplish",
    "selected_agents": [
        {{
            "agent_id": "agent_name",
            "reason": "Why this agent is needed",
            "priority": 1,
            "required_inputs": ["input1", "input2"],
            "expected_outputs": ["output1", "output2"]
        }}
    ],
    "execution_sequence": ["agent1", "agent2", "agent3"],
    "conditional_logic": {{
        "if_extraction_fails": "skip_brief_generation",
        "if_no_citations": "skip_citation_normalization"
    }},
    "confidence": 0.95
}}

IMPORTANT:
- Always start with legal_extractor for document analysis
- brief_generator requires extracted_data from legal_extractor
- citation_normalizer can run in parallel with brief_generator
- case_retriever and comparator are optional based on user needs
- Consider the user's specific requirements (e.g., "just extract facts" vs "full brief")
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
            print(f"Master Orchestrator model setup error: {e}")
            self.gemini_model = None
            self.ollama_available = False
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.config.OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def orchestrate(self, user_request: str, current_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Orchestrate the execution sequence based on user request
        
        Args:
            user_request (str): User's request/input
            current_context (Dict): Current context/state
            
        Returns:
            Dict: Orchestration plan with agent sequence and execution logic
        """
        start_time = time.time()
        
        try:
            # Prepare context
            if not current_context:
                current_context = {
                    'has_document': False,
                    'has_extracted_data': False,
                    'user_preferences': {},
                    'previous_results': {}
                }
            
            # Format available agents for prompt
            agents_info = "\n".join([
                f"- {agent_id}: {info['description']} (requires: {', '.join(info['input_required'])})"
                for agent_id, info in self.available_agents.items()
            ])
            
            # Try primary model first
            if self.config.PRIMARY_MODEL == 'gemini' and self.gemini_model:
                result = self._orchestrate_with_gemini(user_request, current_context, agents_info)
                if result['success']:
                    result['model_used'] = 'gemini'
                    result['processing_time'] = time.time() - start_time
                    return result
            
            # Try fallback model
            if self.config.FALLBACK_MODEL == 'ollama' and self.ollama_available:
                result = self._orchestrate_with_ollama(user_request, current_context, agents_info)
                if result['success']:
                    result['model_used'] = 'ollama'
                    result['processing_time'] = time.time() - start_time
                    return result
            
            # Return default orchestration plan when no AI models available
            return self._get_default_orchestration_plan(user_request, current_context, time.time() - start_time)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Orchestration failed: {str(e)}',
                'processing_time': time.time() - start_time
            }
    
    def _orchestrate_with_gemini(self, user_request: str, current_context: Dict[str, Any], agents_info: str) -> Dict[str, Any]:
        """Orchestrate using Gemini model"""
        try:
            prompt = self.orchestration_prompt.format(
                available_agents=agents_info,
                user_request=user_request,
                current_context=json.dumps(current_context, indent=2)
            )
            
            response = self.gemini_model.generate_content(prompt)
            
            if not response.text:
                return {
                    'success': False,
                    'error': 'Empty response from Gemini'
                }
            
            # Parse JSON response
            orchestration_plan = self._parse_orchestration_response(response.text)
            
            if not orchestration_plan:
                return {
                    'success': False,
                    'error': 'Failed to parse Gemini orchestration response'
                }
            
            return {
                'success': True,
                'data': orchestration_plan,
                'raw_response': response.text
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Gemini orchestration failed: {str(e)}'
            }
    
    def _orchestrate_with_ollama(self, user_request: str, current_context: Dict[str, Any], agents_info: str) -> Dict[str, Any]:
        """Orchestrate using Ollama model"""
        try:
            prompt = self.orchestration_prompt.format(
                available_agents=agents_info,
                user_request=user_request,
                current_context=json.dumps(current_context, indent=2)
            )
            
            payload = {
                "model": self.config.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1  # Low temperature for consistent orchestration
                }
            }
            
            response = requests.post(
                f"{self.config.OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=60
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
            orchestration_plan = self._parse_orchestration_response(generated_text)
            
            if not orchestration_plan:
                return {
                    'success': False,
                    'error': 'Failed to parse Ollama orchestration response'
                }
            
            return {
                'success': True,
                'data': orchestration_plan,
                'raw_response': generated_text
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Ollama orchestration failed: {str(e)}'
            }
    
    def _parse_orchestration_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the AI model response to extract orchestration plan"""
        try:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            
            # If no JSON found, try to parse the entire response
            return json.loads(response_text)
        except:
            return None
    
    def _get_default_orchestration_plan(self, user_request: str, current_context: Dict[str, Any], processing_time: float) -> Dict[str, Any]:
        """Get default orchestration plan when no AI models are available"""
        try:
            # Analyze request to determine what's needed
            request_lower = user_request.lower()
            
            # Default sequence based on common patterns
            if 'brief' in request_lower or 'summary' in request_lower:
                sequence = ['legal_extractor', 'brief_generator', 'citation_normalizer']
            elif 'extract' in request_lower or 'analyze' in request_lower:
                sequence = ['legal_extractor', 'citation_normalizer']
            elif 'citation' in request_lower:
                sequence = ['legal_extractor', 'citation_normalizer']
            elif 'similar' in request_lower or 'precedent' in request_lower:
                sequence = ['legal_extractor', 'case_retriever', 'comparator']
            else:
                # Default full analysis
                sequence = ['legal_extractor', 'brief_generator', 'citation_normalizer']
            
            default_plan = {
                'analysis': f"Default orchestration for request: {user_request[:100]}...",
                'selected_agents': [
                    {
                        'agent_id': agent,
                        'reason': f'Default selection for {agent}',
                        'priority': i + 1,
                        'required_inputs': self.available_agents[agent]['input_required'],
                        'expected_outputs': self.available_agents[agent]['output_provides']
                    }
                    for i, agent in enumerate(sequence)
                ],
                'execution_sequence': sequence,
                'conditional_logic': {
                    'if_extraction_fails': 'skip_all_subsequent',
                    'if_no_citations': 'skip_citation_normalization'
                },
                'confidence': 0.7
            }
            
            return {
                'success': True,
                'data': default_plan,
                'model_used': 'default',
                'processing_time': processing_time,
                'raw_response': 'Default orchestration plan generated'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Default orchestration failed: {str(e)}',
                'processing_time': processing_time
            }
    
    def validate_orchestration_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the orchestration plan and provide feedback"""
        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'suggestions': []
        }
        
        # Check if plan has required fields
        required_fields = ['selected_agents', 'execution_sequence']
        for field in required_fields:
            if field not in plan:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"Missing required field: {field}")
        
        # Check agent dependencies
        if 'execution_sequence' in plan:
            sequence = plan['execution_sequence']
            for i, agent in enumerate(sequence):
                if agent in self.available_agents:
                    dependencies = self.available_agents[agent]['dependencies']
                    for dep in dependencies:
                        if dep not in sequence[:i]:
                            validation_result['warnings'].append(f"Agent {agent} requires {dep} but it's not executed before")
        
        # Check for circular dependencies
        if 'execution_sequence' in plan:
            sequence = plan['execution_sequence']
            for i, agent in enumerate(sequence):
                if agent in self.available_agents:
                    dependencies = self.available_agents[agent]['dependencies']
                    for dep in dependencies:
                        if dep in sequence[i:]:
                            validation_result['errors'].append(f"Circular dependency detected: {agent} -> {dep}")
                            validation_result['is_valid'] = False
        
        return validation_result
    
    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific agent"""
        return self.available_agents.get(agent_id)
    
    def list_available_agents(self) -> Dict[str, Any]:
        """List all available agents and their capabilities"""
        return self.available_agents.copy()
