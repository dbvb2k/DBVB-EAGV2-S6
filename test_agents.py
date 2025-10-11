#!/usr/bin/env python3
"""
Test script for Law Case Finder - Agent Orchestration Testing

This script tests the core functionality of the Law Case Finder system
by using LLM-driven orchestration to determine which agents to call next,
passing the output of each function to the next one in the sequence.
"""

import requests
import json
import time
import os
import sys
import google.generativeai as genai
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables from server/.env file
load_dotenv('server/.env')

# Windows Color Support
if sys.platform == "win32":
    try:
        import ctypes
        from ctypes import wintypes
        
        # Windows color constants
        class WindowsColors:
            BLACK = 0
            BLUE = 1
            GREEN = 2
            CYAN = 3
            RED = 4
            MAGENTA = 5
            YELLOW = 6
            WHITE = 7
            GRAY = 8
            LIGHT_BLUE = 9
            LIGHT_GREEN = 10
            LIGHT_CYAN = 11
            LIGHT_RED = 12
            LIGHT_MAGENTA = 13
            LIGHT_YELLOW = 14
            BRIGHT_WHITE = 15
        
        # Map our colors to Windows colors
        COLOR_MAP = {
            'ORCHESTRATOR': WindowsColors.MAGENTA,
            'LEGAL_EXTRACTOR': WindowsColors.BLUE,
            'BRIEF_GENERATOR': WindowsColors.GREEN,
            'CITATION_NORMALIZER': WindowsColors.YELLOW,
            'CASE_RETRIEVER': WindowsColors.CYAN,
            'COMPARATOR': WindowsColors.RED,
            'SUCCESS': WindowsColors.GREEN,
            'ERROR': WindowsColors.RED,
            'WARNING': WindowsColors.YELLOW,
            'INFO': WindowsColors.BLUE,
            'RESET': WindowsColors.WHITE
        }
        
        def set_color(color_code):
            """Set Windows console color"""
            try:
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
                kernel32.SetConsoleTextAttribute(handle, color_code)
            except:
                pass
        
        def windows_colored_print(text, color_name='RESET', bold=False):
            """Print text with Windows color formatting"""
            try:
                color_code = COLOR_MAP.get(color_name, WindowsColors.WHITE)
                if bold:
                    color_code |= 8  # Make it bright
                set_color(color_code)
                print(text)
                set_color(WindowsColors.WHITE)  # Reset to white
            except:
                print(text)
        
        WINDOWS_COLORS = True
        
    except ImportError:
        WINDOWS_COLORS = False
else:
    WINDOWS_COLORS = False

# ANSI Color Codes for Unix/Linux/Mac
class Colors:
    # Agent Colors
    ORCHESTRATOR = '\033[95m'  # Magenta
    LEGAL_EXTRACTOR = '\033[94m'  # Blue
    BRIEF_GENERATOR = '\033[92m'  # Green
    CITATION_NORMALIZER = '\033[93m'  # Yellow
    CASE_RETRIEVER = '\033[96m'  # Cyan
    COMPARATOR = '\033[91m'  # Red
    
    # Status Colors
    SUCCESS = '\033[92m'  # Green
    ERROR = '\033[91m'  # Red
    WARNING = '\033[93m'  # Yellow
    INFO = '\033[94m'  # Blue
    
    # Formatting
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'  # Reset to default

def colored_print(text, color=Colors.RESET, bold=False):
    """Print text with color formatting"""
    if WINDOWS_COLORS:
        # Use Windows color system
        color_name = 'RESET'
        if color == Colors.ORCHESTRATOR:
            color_name = 'ORCHESTRATOR'
        elif color == Colors.LEGAL_EXTRACTOR:
            color_name = 'LEGAL_EXTRACTOR'
        elif color == Colors.BRIEF_GENERATOR:
            color_name = 'BRIEF_GENERATOR'
        elif color == Colors.CITATION_NORMALIZER:
            color_name = 'CITATION_NORMALIZER'
        elif color == Colors.CASE_RETRIEVER:
            color_name = 'CASE_RETRIEVER'
        elif color == Colors.COMPARATOR:
            color_name = 'COMPARATOR'
        elif color == Colors.SUCCESS:
            color_name = 'SUCCESS'
        elif color == Colors.ERROR:
            color_name = 'ERROR'
        elif color == Colors.WARNING:
            color_name = 'WARNING'
        elif color == Colors.INFO:
            color_name = 'INFO'
        
        windows_colored_print(text, color_name, bold)
    else:
        # Use ANSI colors for Unix/Linux/Mac
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            prefix = Colors.BOLD if bold else ""
            print(f"{prefix}{color}{text}{Colors.RESET}")
        else:
            # Fallback: use simple formatting without colors
            if bold:
                print(f"**{text}**")
            else:
                print(text)

def agent_log(agent_name, message, color=None, status="info"):
    """Log message for a specific agent with appropriate coloring"""
    if color is None:
        color_map = {
            "Master Orchestrator": Colors.ORCHESTRATOR,
            "Legal Extractor": Colors.LEGAL_EXTRACTOR,
            "Brief Generator": Colors.BRIEF_GENERATOR,
            "Citation Normalizer": Colors.CITATION_NORMALIZER,
            "Case Retriever": Colors.CASE_RETRIEVER,
            "Comparator": Colors.COMPARATOR
        }
        color = color_map.get(agent_name, Colors.INFO)
    
    status_color = {
        "success": Colors.SUCCESS,
        "error": Colors.ERROR,
        "warning": Colors.WARNING,
        "info": Colors.INFO
    }.get(status, Colors.INFO)
    
    colored_print(f"🤖 {agent_name}: {message}", color, bold=True)

def status_log(message, status="info"):
    """Log status messages with appropriate coloring"""
    status_color = {
        "success": Colors.SUCCESS,
        "error": Colors.ERROR,
        "warning": Colors.WARNING,
        "info": Colors.INFO
    }.get(status, Colors.INFO)
    
    colored_print(message, status_color)

class AgentOrchestrator:
    """
    LLM-driven orchestrator that decides which agent to call next
    based on the current state and previous outputs
    """
    
    def __init__(self):
        self.base_url = "http://localhost:3002"
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', '')
        self.gemini_model = None
        self._setup_gemini()
        
        # Available agents and their capabilities
        self.available_agents = {
            'legal_extractor': {
                'name': 'Legal Extractor',
                'endpoint': '/api/analyze-document',
                'description': 'Extracts structured legal information from documents',
                'input_required': ['document_text'],
                'output_provides': ['case_name', 'court', 'date', 'facts', 'legal_issues', 'holdings', 'reasoning', 'citations', 'disposition']
            },
            'brief_generator': {
                'name': 'Brief Generator',
                'endpoint': '/api/generate-brief',
                'description': 'Generates comprehensive legal briefs from extracted data',
                'input_required': ['extracted_data'],
                'output_provides': ['issue', 'facts', 'holding', 'reasoning', 'key_citations', 'word_count', 'confidence_score']
            },
            'citation_normalizer': {
                'name': 'Citation Normalizer',
                'endpoint': '/api/normalize-citations',
                'description': 'Normalizes citations to standard formats',
                'input_required': ['citations'],
                'output_provides': ['normalized_citations', 'format_used', 'total_processed']
            }
        }
        
        # Orchestration prompt template
        self.orchestration_prompt = """
You are an AI orchestrator for a legal analysis system. Based on the current state and previous outputs, determine which agent should be called next.

AVAILABLE AGENTS:
{available_agents}

CURRENT STATE:
- User Request: {user_request}
- Completed Steps: {completed_steps}
- Available Data: {available_data}
- Previous Output: {previous_output}

INSTRUCTIONS:
1. Analyze what has been accomplished so far
2. Determine what the next logical step should be
3. Select the appropriate agent to call next
4. Provide reasoning for your decision
5. Consider dependencies (e.g., brief_generator needs extracted_data from legal_extractor)

RESPONSE FORMAT (JSON):
{{
    "next_agent": "agent_id",
    "reasoning": "Why this agent should be called next",
    "input_data": {{
        "key": "value"
    }},
    "is_complete": false,
    "confidence": 0.95
}}

IMPORTANT RULES:
- Always start with legal_extractor for document analysis
- brief_generator requires extracted_data from legal_extractor
- citation_normalizer can run after legal_extractor or brief_generator
- Set is_complete to true when all necessary analysis is done
- Provide specific input_data for the next agent call

INPUT DATA FORMATS (MUST FOLLOW EXACTLY):
- legal_extractor: {{"text": "document_text_content"}}  # MUST use "text" key, NOT "document_text"
- brief_generator: {{"extracted_data": {{"case_name": "...", "facts": "...", etc.}}}}
- citation_normalizer: {{"citations": ["citation1", "citation2", ...]}}

CRITICAL: For legal_extractor, the input_data MUST have a "text" key containing the document text, NOT "document_text"
"""

    def _setup_gemini(self):
        """Setup Gemini model for orchestration"""
        try:
            if self.gemini_api_key:
                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
                agent_log("Agent Orchestrator", "Gemini model initialized successfully from server/.env", status="success")
            else:
                agent_log("Agent Orchestrator", "No Gemini API key found in server/.env, using fallback logic", status="warning")
        except Exception as e:
            agent_log("Agent Orchestrator", f"Failed to setup Gemini: {e}", status="error")

    def decide_next_agent(self, user_request: str, completed_steps: List[str], 
                         available_data: Dict[str, Any], previous_output: Any = None) -> Dict[str, Any]:
        """
        Use LLM to decide which agent to call next
        
        Args:
            user_request: Original user request
            completed_steps: List of completed agent steps
            available_data: Data available from previous steps
            previous_output: Output from the last executed agent
            
        Returns:
            Dict with next agent decision and reasoning
        """
        try:
            if not self.gemini_model:
                return self._fallback_decision(user_request, completed_steps, available_data)
            
            # Format available agents for prompt
            agents_info = "\n".join([
                f"- {agent_id}: {info['description']} (requires: {', '.join(info['input_required'])})"
                for agent_id, info in self.available_agents.items()
            ])
            
            # Prepare prompt
            prompt = self.orchestration_prompt.format(
                available_agents=agents_info,
                user_request=user_request,
                completed_steps=', '.join(completed_steps) if completed_steps else 'None',
                available_data=json.dumps(available_data, indent=2),
                previous_output=json.dumps(previous_output, indent=2) if previous_output else 'None'
            )
            
            # Get LLM response
            response = self.gemini_model.generate_content(prompt)
            
            if not response.text:
                return self._fallback_decision(user_request, completed_steps, available_data)
            
            # Parse JSON response
            try:
                # Extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    decision = json.loads(json_str)
                else:
                    decision = json.loads(response.text)
                
                # Validate decision
                if 'next_agent' not in decision:
                    return self._fallback_decision(user_request, completed_steps, available_data)
                
                agent_log("Agent Orchestrator", f"LLM decided: {decision['next_agent']} - {decision.get('reasoning', 'No reasoning provided')}", status="success")
                return decision
                
            except json.JSONDecodeError:
                agent_log("Agent Orchestrator", "Failed to parse LLM response, using fallback", status="warning")
                return self._fallback_decision(user_request, completed_steps, available_data)
                
        except Exception as e:
            agent_log("Agent Orchestrator", f"LLM orchestration failed: {e}", status="error")
            return self._fallback_decision(user_request, completed_steps, available_data)

    def _fallback_decision(self, user_request: str, completed_steps: List[str], 
                          available_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback decision logic when LLM is not available"""
        if not completed_steps:
            return {
                "next_agent": "legal_extractor",
                "reasoning": "Starting with document analysis",
                "input_data": {"text": available_data.get('document_text', '')},
                "is_complete": False,
                "confidence": 0.8
            }
        
        if 'legal_extractor' in completed_steps and 'brief_generator' not in completed_steps:
            return {
                "next_agent": "brief_generator",
                "reasoning": "Extraction complete, generating brief",
                "input_data": {"extracted_data": available_data.get('extracted_data', {})},
                "is_complete": False,
                "confidence": 0.8
            }
        
        if 'brief_generator' in completed_steps and 'citation_normalizer' not in completed_steps:
            return {
                "next_agent": "citation_normalizer",
                "reasoning": "Brief generated, normalizing citations",
                "input_data": {"citations": available_data.get('citations', [])},
                "is_complete": False,
                "confidence": 0.8
            }
        
        return {
            "next_agent": None,
            "reasoning": "All necessary steps completed",
            "input_data": {},
            "is_complete": True,
            "confidence": 0.9
        }

    def call_agent(self, agent_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a specific agent with the provided input data
        
        Args:
            agent_id: ID of the agent to call
            input_data: Input data for the agent
            
        Returns:
            Response from the agent
        """
        if agent_id not in self.available_agents:
            return {
                'success': False,
                'error': f'Unknown agent: {agent_id}'
            }
        
        agent_info = self.available_agents[agent_id]
        endpoint = f"{self.base_url}{agent_info['endpoint']}"
        
        try:
            agent_log(agent_info['name'], f"Calling {agent_info['name']}...", status="info")
            
            # Fix input data format for legal_extractor if needed
            if agent_id == 'legal_extractor' and 'document_text' in input_data and 'text' not in input_data:
                agent_log(agent_info['name'], "Fixing input data format: document_text -> text", status="warning")
                input_data['text'] = input_data.pop('document_text')
            
            # Debug: Print input data for legal_extractor
            if agent_id == 'legal_extractor':
                agent_log(agent_info['name'], f"Input data keys: {list(input_data.keys())}", status="info")
                if 'text' in input_data:
                    text_length = len(input_data['text']) if input_data['text'] else 0
                    agent_log(agent_info['name'], f"Text length: {text_length} characters", status="info")
            
            response = requests.post(
                endpoint,
                json=input_data,
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                agent_log(agent_info['name'], f"{agent_info['name']} completed successfully!", status="success")
                return {
                    'success': True,
                    'data': data,
                    'agent_id': agent_id
                }
            else:
                agent_log(agent_info['name'], f"{agent_info['name']} failed with status {response.status_code}", status="error")
                try:
                    error_data = response.json()
                    agent_log(agent_info['name'], f"Error details: {error_data}", status="error")
                except:
                    agent_log(agent_info['name'], f"Error response: {response.text}", status="error")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text}",
                    'agent_id': agent_id
                }
                
        except requests.exceptions.RequestException as e:
            agent_log(agent_info['name'], f"{agent_info['name']} failed: {e}", status="error")
            return {
                'success': False,
                'error': str(e),
                'agent_id': agent_id
            }

# Configuration
BASE_URL = "http://localhost:3002"
SAMPLE_LEGAL_TEXT = """
Brown v. Board of Education of Topeka, 347 U.S. 483 (1954)

SUPREME COURT OF THE UNITED STATES

Facts:
The case consolidated several legal challenges to racial segregation in public schools. 
Linda Brown, an African American student, was denied admission to her local elementary 
school in Topeka, Kansas, because of her race and was required to attend a segregated 
school farther from her home.

Issue:
Does the segregation of children in public schools solely on the basis of race, even 
though the physical facilities and other "tangible" factors may be equal, deprive the 
children of the minority group of equal educational opportunities?

Holding:
The Supreme Court held unanimously that racial segregation in public schools violates 
the Equal Protection Clause of the Fourteenth Amendment. The Court declared that 
"separate educational facilities are inherently unequal."

Reasoning:
1. Education is a fundamental right that must be available to all on equal terms.
2. Segregation generates a feeling of inferiority that affects children's motivation to learn.
3. The "separate but equal" doctrine established in Plessy v. Ferguson (1896) has no place 
   in the field of public education.
4. Psychological and sociological studies demonstrate the harmful effects of segregation on children.

Citations:
- Plessy v. Ferguson, 163 U.S. 537 (1896)
- Fourteenth Amendment to the U.S. Constitution
- Sweatt v. Painter, 339 U.S. 629 (1950)
- McLaurin v. Oklahoma State Regents, 339 U.S. 637 (1950)

Disposition:
The Court reversed the lower court's decision and ordered the desegregation of public schools.
"""

def test_health_check():
    """Test the health check endpoint"""
    status_log("🔍 Testing health check endpoint...", "info")
    colored_print("="*60, Colors.INFO)

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            status_log(f"✅ Health check passed: {data}", "success")
            colored_print("="*60, Colors.INFO)
            return True
        else:
            status_log(f"❌ Health check failed with status {response.status_code}", "error")
            return False
    except requests.exceptions.RequestException as e:
        status_log(f"❌ Health check failed: {e}", "error")
        return False

def test_agent_orchestration():
    """Test the LLM-driven agent orchestration"""
    colored_print("🚀 Starting LLM-Driven Agent Orchestration Test", Colors.ORCHESTRATOR, bold=True)
    colored_print("=" * 60, Colors.ORCHESTRATOR)
    
    start_time = time.time()
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator()
    
    # Initial state
    user_request = "Analyze this legal document and generate a comprehensive brief with normalized citations"
    completed_steps = []
    available_data = {
        'document_text': SAMPLE_LEGAL_TEXT
    }
    previous_output = None
    
    step_count = 0
    max_steps = 10  # Prevent infinite loops
    
    while step_count < max_steps:
        step_count += 1
        
        colored_print(f"\n🔄 Step {step_count}: Deciding next agent...", Colors.INFO, bold=True)
        
        # Get LLM decision
        decision = orchestrator.decide_next_agent(
            user_request=user_request,
            completed_steps=completed_steps,
            available_data=available_data,
            previous_output=previous_output
        )
        
        # Display decision
        colored_print(f"   🎯 Decision: {decision['next_agent']}", Colors.ORCHESTRATOR, bold=True)
        colored_print(f"   💭 Reasoning: {decision['reasoning']}", Colors.INFO)
        colored_print(f"   📊 Confidence: {decision['confidence']:.2f}", Colors.SUCCESS)
        
        # Check if we're done
        if decision['is_complete'] or not decision['next_agent']:
            colored_print("\n✅ Orchestration complete!", Colors.SUCCESS, bold=True)
            break
        
        # Call the next agent
        colored_print(f"\n🤖 Executing: {decision['next_agent']}", Colors.INFO, bold=True)
        
        agent_result = orchestrator.call_agent(
            agent_id=decision['next_agent'],
            input_data=decision['input_data']
        )
        
        if agent_result['success']:
            # Update state
            completed_steps.append(decision['next_agent'])
            previous_output = agent_result['data']
            
            # Extract relevant data for next steps
            if decision['next_agent'] == 'legal_extractor':
                extracted_data = agent_result['data'].get('data', {}).get('extracted_fields', {})
                available_data['extracted_data'] = extracted_data
                available_data['citations'] = extracted_data.get('citations', [])
                
                # Display extraction results
                colored_print(f"   📄 Case Name: {extracted_data.get('case_name', 'N/A')}", Colors.LEGAL_EXTRACTOR)
                colored_print(f"   🏛️ Court: {extracted_data.get('court', 'N/A')}", Colors.LEGAL_EXTRACTOR)
                colored_print(f"   📅 Date: {extracted_data.get('date', 'N/A')}", Colors.LEGAL_EXTRACTOR)
                colored_print(f"   ⚖️ Holdings: {len(extracted_data.get('holdings', []))} found", Colors.LEGAL_EXTRACTOR)
                colored_print(f"   💭 Reasoning: {len(extracted_data.get('reasoning', []))} points", Colors.LEGAL_EXTRACTOR)
                colored_print(f"   📚 Citations: {len(extracted_data.get('citations', []))} found", Colors.LEGAL_EXTRACTOR)
                
            elif decision['next_agent'] == 'brief_generator':
                brief_data = agent_result['data'].get('data', {}).get('brief', {})
                available_data['brief'] = brief_data
                
                # Display brief results
                colored_print(f"   📋 Issue: {brief_data.get('issue', 'N/A')[:100]}...", Colors.BRIEF_GENERATOR)
                colored_print(f"   📖 Facts: {brief_data.get('facts', 'N/A')[:100]}...", Colors.BRIEF_GENERATOR)
                colored_print(f"   ⚖️ Holding: {brief_data.get('holding', 'N/A')[:100]}...", Colors.BRIEF_GENERATOR)
                colored_print(f"   💭 Reasoning Points: {len(brief_data.get('reasoning', []))}", Colors.BRIEF_GENERATOR)
                colored_print(f"   📚 Key Citations: {len(brief_data.get('key_citations', []))}", Colors.BRIEF_GENERATOR)
                colored_print(f"   📊 Word Count: {brief_data.get('word_count', 0)}", Colors.BRIEF_GENERATOR)
                colored_print(f"   🎯 Confidence: {brief_data.get('confidence_score', 0)}%", Colors.SUCCESS)
                
            elif decision['next_agent'] == 'citation_normalizer':
                citation_data = agent_result['data'].get('data', {}).get('normalized_citations', [])
                available_data['normalized_citations'] = citation_data
                
                # Display citation results
                colored_print(f"   📚 Processed {len(citation_data)} citations", Colors.CITATION_NORMALIZER)
                for i, citation in enumerate(citation_data[:3]):
                    if isinstance(citation, dict):
                        colored_print(f"   {i+1}. {citation.get('normalized', 'N/A')}", Colors.CITATION_NORMALIZER)
                    else:
                        colored_print(f"   {i+1}. {citation}", Colors.CITATION_NORMALIZER)
        else:
            agent_log("Orchestrator", f"Agent {decision['next_agent']} failed: {agent_result['error']}", status="error")
            break
    
    # Summary
    end_time = time.time()
    colored_print("\n" + "=" * 60, Colors.ORCHESTRATOR)
    colored_print(f"🏁 LLM-Driven Orchestration completed in {end_time - start_time:.2f} seconds!", Colors.ORCHESTRATOR, bold=True)
    
    colored_print(f"\n📊 Execution Summary:", Colors.INFO, bold=True)
    colored_print(f"   🔄 Total Steps: {step_count}", Colors.INFO)
    colored_print(f"   ✅ Completed Agents: {', '.join(completed_steps)}", Colors.SUCCESS)
    colored_print(f"   📄 Data Available: {list(available_data.keys())}", Colors.INFO)
    
    if completed_steps:
        status_log("✅ LLM-driven orchestration test completed successfully!", "success")
        colored_print("\n📋 Next Steps:", Colors.INFO)
        colored_print("1. Review the orchestration decisions made by the LLM", Colors.INFO)
        colored_print("2. Analyze the data flow between agents", Colors.INFO)
        colored_print("3. Test with different legal documents", Colors.INFO)
        colored_print("4. Fine-tune the orchestration prompts if needed", Colors.INFO)
    else:
        status_log("⚠️ Orchestration test may need configuration:", "warning")
        colored_print("1. Check if Gemini API key is set in server/.env file", Colors.WARNING)
        colored_print("2. Ensure backend server is running", Colors.WARNING)
        colored_print("3. Check server logs for detailed error messages", Colors.WARNING)

def main():
    """Run the LLM-driven agent orchestration test"""
    # Test 1: Health Check
    if not test_health_check():
        status_log("\n❌ Backend server is not running. Please start it with:", "error")
        colored_print("   cd server && python main.py", Colors.ERROR)
        return
    
    # Test 2: LLM-Driven Agent Orchestration
    test_agent_orchestration()

if __name__ == "__main__":
    main()
