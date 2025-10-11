"""
Perception Layer - LLM Interaction and Model Management

This layer handles all interactions with Language Models (LLMs),
managing model selection, switching, and prompt processing.
"""

import google.generativeai as genai
import requests
import json
import time
from typing import Dict, Any, Optional, List
from config import Config


class PerceptionLayer:
    """
    Perception Layer handles all LLM interactions and model management
    """
    
    def __init__(self, config: Config, prompts: Dict[str, Any]):
        """
        Initialize Perception Layer
        
        Args:
            config: Configuration object
            prompts: System prompts dictionary
        """
        self.config = config
        self.prompts = prompts
        self._setup_models()
    
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
            print(f"Perception Layer model setup error: {e}")
            self.gemini_model = None
            self.ollama_available = False
    
    def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.config.OLLAMA_BASE_URL}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def process_with_llm(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        preferred_model: str = None,
        temperature: float = 0.7,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """
        Process a prompt with the LLM using preferred model with fallback
        
        Args:
            prompt: The prompt to send to the LLM
            context: Additional context for the prompt
            preferred_model: Preferred model ('gemini' or 'ollama')
            temperature: Temperature for generation
            max_retries: Maximum number of retries
            
        Returns:
            Dict with success status, response text, and metadata
        """
        start_time = time.time()
        
        # Determine model priority
        if preferred_model:
            primary = preferred_model
            fallback = 'ollama' if preferred_model == 'gemini' else 'gemini'
        else:
            primary = self.config.PRIMARY_MODEL
            fallback = self.config.FALLBACK_MODEL
        
        # Try primary model
        if primary == 'gemini' and self.gemini_model:
            result = self._process_with_gemini(prompt, temperature, max_retries)
            if result['success']:
                result['model_used'] = 'gemini'
                result['processing_time'] = time.time() - start_time
                return result
        
        if primary == 'ollama' and self.ollama_available:
            result = self._process_with_ollama(prompt, temperature, max_retries)
            if result['success']:
                result['model_used'] = 'ollama'
                result['processing_time'] = time.time() - start_time
                return result
        
        # Try fallback model
        if fallback == 'gemini' and self.gemini_model:
            result = self._process_with_gemini(prompt, temperature, max_retries)
            if result['success']:
                result['model_used'] = 'gemini (fallback)'
                result['processing_time'] = time.time() - start_time
                return result
        
        if fallback == 'ollama' and self.ollama_available:
            result = self._process_with_ollama(prompt, temperature, max_retries)
            if result['success']:
                result['model_used'] = 'ollama (fallback)'
                result['processing_time'] = time.time() - start_time
                return result
        
        # No model available
        return {
            'success': False,
            'error': 'No LLM models available',
            'processing_time': time.time() - start_time
        }
    
    def _process_with_gemini(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """Process with Gemini model"""
        for attempt in range(max_retries):
            try:
                generation_config = {
                    "temperature": temperature,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                }
                
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                if not response.text:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return {
                        'success': False,
                        'error': 'Empty response from Gemini'
                    }
                
                return {
                    'success': True,
                    'response': response.text,
                    'raw_response': response
                }
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return {
                    'success': False,
                    'error': f'Gemini error: {str(e)}'
                }
        
        return {
            'success': False,
            'error': 'Max retries exceeded for Gemini'
        }
    
    def _process_with_ollama(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_retries: int = 2
    ) -> Dict[str, Any]:
        """Process with Ollama model"""
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": self.config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature
                    }
                }
                
                response = requests.post(
                    f"{self.config.OLLAMA_BASE_URL}/api/generate",
                    json=payload,
                    timeout=120
                )
                
                if response.status_code != 200:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return {
                        'success': False,
                        'error': f'Ollama API error: {response.status_code}'
                    }
                
                response_data = response.json()
                generated_text = response_data.get('response', '')
                
                if not generated_text:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    return {
                        'success': False,
                        'error': 'Empty response from Ollama'
                    }
                
                return {
                    'success': True,
                    'response': generated_text,
                    'raw_response': response_data
                }
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return {
                    'success': False,
                    'error': f'Ollama error: {str(e)}'
                }
        
        return {
            'success': False,
            'error': 'Max retries exceeded for Ollama'
        }
    
    def get_prompt(self, prompt_key: str, **kwargs) -> str:
        """
        Get a prompt template and format it with provided arguments
        
        Args:
            prompt_key: Key to identify the prompt in prompts dict
            **kwargs: Arguments to format the prompt template
            
        Returns:
            Formatted prompt string
        """
        try:
            prompt_template = self.prompts.get(prompt_key, "")
            if not prompt_template:
                raise ValueError(f"Prompt key '{prompt_key}' not found")
            
            # Format the prompt with provided kwargs
            return prompt_template.format(**kwargs)
        except Exception as e:
            print(f"Error getting prompt '{prompt_key}': {e}")
            return ""
    
    def parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse JSON from LLM response (handles markdown code blocks)
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Parsed JSON dict or None if parsing fails
        """
        try:
            # Try direct JSON parsing first
            return json.loads(response_text)
        except:
            pass
        
        try:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try to find any JSON object in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except:
            pass
        
        return None
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model availability status"""
        return {
            'gemini_available': self.gemini_model is not None,
            'ollama_available': self.ollama_available,
            'primary_model': self.config.PRIMARY_MODEL,
            'fallback_model': self.config.FALLBACK_MODEL
        }

