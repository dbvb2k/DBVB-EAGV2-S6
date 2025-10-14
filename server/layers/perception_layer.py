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
                print(f"  → Configuring Gemini with API key (length: {len(self.config.GEMINI_API_KEY)})...")
                genai.configure(api_key=self.config.GEMINI_API_KEY)
                self.gemini_model = genai.GenerativeModel(self.config.GEMINI_MODEL)
                print(f"  ✓ Gemini model initialized: {self.config.GEMINI_MODEL}")
            else:
                print(f"  ⚠ No Gemini API key found - Gemini will not be available")
                self.gemini_model = None
            
            # Ollama setup (no API key needed)
            print(f"  → Checking Ollama availability at {self.config.OLLAMA_BASE_URL}...")
            self.ollama_available, self.available_ollama_model = self._check_ollama_availability()
            if self.ollama_available:
                print(f"  ✓ Ollama is available: {self.available_ollama_model}")
            else:
                print(f"  ⚠ Ollama is not available")
            
            # Summary
            models_available = []
            if self.gemini_model:
                models_available.append("Gemini")
            if self.ollama_available:
                models_available.append("Ollama")
            
            if models_available:
                print(f"  ✓ Available models: {', '.join(models_available)}")
            else:
                print(f"  ❌ WARNING: No LLM models available! Please configure at least one model.")
            
        except Exception as e:
            print(f"  ❌ Perception Layer model setup error: {e}")
            import traceback
            traceback.print_exc()
            self.gemini_model = None
            self.ollama_available = False
            self.available_ollama_model = None
    
    def _check_ollama_availability(self) -> tuple[bool, str]:
        """Check if Ollama is available and has the required model
        
        Returns:
            tuple: (is_available, model_name)
        """
        try:
            # First check if Ollama is running
            response = requests.get(f"{self.config.OLLAMA_BASE_URL}/api/tags", timeout=5)
            if response.status_code != 200:
                return False, None
            
            # Check if the required model is available
            models_data = response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]
            
            # Check for exact match or partial match (e.g., 'llama3:8b' matches 'llama3')
            required_model = self.config.OLLAMA_MODEL
            model_found = False
            found_model = None
            
            for model_name in available_models:
                if (model_name == required_model or 
                    model_name.startswith(required_model.split(':')[0]) or
                    required_model.startswith(model_name.split(':')[0])):
                    model_found = True
                    found_model = model_name
                    print(f"  ✓ Found Ollama model: {model_name} (required: {required_model})")
                    break
            
            if not model_found:
                print(f"  ⚠ Ollama running but required model '{required_model}' not found")
                print(f"  Available models: {available_models}")
                # Use the first available model as fallback
                if available_models:
                    found_model = available_models[0]
                    print(f"  → Using fallback model: {found_model}")
                    return True, found_model
                else:
                    return False, None
            
            return True, found_model
        except Exception as e:
            print(f"  ⚠ Ollama availability check failed: {e}")
            return False, None
    
    def process_with_llm(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        preferred_model: str = None,
        temperature: float = 0.7,
        max_retries: int = 2,
        detail_level: str = 'summary'
    ) -> Dict[str, Any]:
        """
        Process a prompt with the LLM using preferred model with fallback
        
        Args:
            prompt: The prompt to send to the LLM
            context: Additional context for the prompt
            preferred_model: Preferred model ('gemini' or 'ollama')
            temperature: Temperature for generation
            max_retries: Maximum number of retries
            detail_level: 'summary' or 'detailed' for logging verbosity
            
        Returns:
            Dict with success status, response text, and metadata
        """
        start_time = time.time()
        
        # Log based on detail level
        if detail_level == 'detailed':
            print(f"  🧠 [Perception Layer] LLM Processing - Starting")
            print(f"  [Perception] Preferred model: {preferred_model}")
            print(f"  [Perception] Gemini available: {self.gemini_model is not None}")
            print(f"  [Perception] Ollama available: {self.ollama_available}")
            print(f"  [Perception] Config PRIMARY_MODEL: {self.config.PRIMARY_MODEL}")
        else:
            print(f"  🧠 [Perception Layer] LLM Processing - Starting")
        
        # Determine model priority
        if preferred_model:
            primary = preferred_model
            fallback = 'ollama' if preferred_model == 'gemini' else 'gemini'
        else:
            primary = self.config.PRIMARY_MODEL
            fallback = self.config.FALLBACK_MODEL
        
        print(f"  [Perception] Using primary: {primary}, fallback: {fallback}")
        
        # Try primary model
        if primary == 'gemini' and self.gemini_model:
            if detail_level == 'detailed':
                print(f"  [Perception] Attempting Gemini...")
            result = self._process_with_gemini(prompt, temperature, max_retries)
            if result['success']:
                result['model_used'] = 'gemini'
                result['processing_time'] = time.time() - start_time
                print(f"  ✅ [Perception Layer] LLM Processing - Completed (Gemini)")
                return result
            else:
                print(f"  [Perception] Gemini failed: {result.get('error', 'Unknown error')}")
        
        if primary == 'ollama' and self.ollama_available:
            if detail_level == 'detailed':
                print(f"  [Perception] Attempting Ollama...")
            result = self._process_with_ollama(prompt, temperature, max_retries)
            if result['success']:
                result['model_used'] = 'ollama'
                result['processing_time'] = time.time() - start_time
                print(f"  ✅ [Perception Layer] LLM Processing - Completed (Ollama)")
                return result
            else:
                print(f"  [Perception] Ollama failed: {result.get('error', 'Unknown error')}")
        
        # Try fallback model
        print(f"  [Perception] Primary failed or unavailable, trying fallback...")
        if fallback == 'gemini' and self.gemini_model:
            print(f"  [Perception] Attempting Gemini (fallback)...")
            result = self._process_with_gemini(prompt, temperature, max_retries)
            if result['success']:
                result['model_used'] = 'gemini (fallback)'
                result['processing_time'] = time.time() - start_time
                return result
            else:
                print(f"  [Perception] Gemini fallback failed: {result.get('error', 'Unknown error')}")
        
        if fallback == 'ollama' and self.ollama_available:
            print(f"  [Perception] Attempting Ollama (fallback)...")
            result = self._process_with_ollama(prompt, temperature, max_retries)
            if result['success']:
                result['model_used'] = 'ollama (fallback)'
                result['processing_time'] = time.time() - start_time
                return result
            else:
                print(f"  [Perception] Ollama fallback failed: {result.get('error', 'Unknown error')}")
        
        # No model available
        print(f"  [Perception] ❌ ERROR: No LLM models available!")
        print(f"  [Perception] Debug info:")
        print(f"    - Primary: {primary}, Available: {primary == 'gemini' and self.gemini_model or primary == 'ollama' and self.ollama_available}")
        print(f"    - Fallback: {fallback}, Available: {fallback == 'gemini' and self.gemini_model or fallback == 'ollama' and self.ollama_available}")
        print(f"    - self.gemini_model: {self.gemini_model}")
        print(f"    - self.ollama_available: {self.ollama_available}")
        
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
        print(f"  [Perception] Gemini processing - Model: {self.config.GEMINI_MODEL}")
        
        for attempt in range(max_retries):
            try:
                generation_config = {
                    "temperature": float(temperature),
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 8192,
                }
                
                print(f"  [Perception] Gemini generation config: {generation_config}")
                
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                print(f"  [Perception] Gemini response received: {bool(response.text)}")
                
                if not response.text:
                    print(f"  [Perception] Gemini empty response")
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
        print(f"  [Perception] Ollama processing - Model: {self.available_ollama_model}")
        
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": self.available_ollama_model,  # Use the actual available model
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": float(temperature)
                    }
                }
                
                print(f"  [Perception] Ollama request payload: {payload}")
                
                response = requests.post(
                    f"{self.config.OLLAMA_BASE_URL}/api/generate",
                    json=payload,
                    timeout=120
                )
                
                print(f"  [Perception] Ollama response status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"  [Perception] Ollama HTTP error: {response.status_code} - {response.text}")
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
                available_keys = list(self.prompts.keys())
                error_msg = f"Prompt key '{prompt_key}' not found in system prompts.\n"
                error_msg += f"Available keys: {available_keys}\n"
                error_msg += f"Total prompts loaded: {len(self.prompts)}"
                print(f"❌ ERROR: {error_msg}")
                raise ValueError(error_msg)
            
            # Format the prompt with provided kwargs
            return prompt_template.format(**kwargs)
        except KeyError as e:
            print(f"❌ ERROR: Missing template variable in prompt '{prompt_key}': {e}")
            print(f"   Required variables: {e}")
            print(f"   Provided variables: {list(kwargs.keys())}")
            raise
        except Exception as e:
            print(f"❌ ERROR getting prompt '{prompt_key}': {e}")
            raise
    
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

