#!/usr/bin/env python3
"""
Test script for Law Case Finder - 4-Layer Cognitive Architecture Testing

This script tests the new 4-layer cognitive architecture:
1. Perception Layer - LLM interactions and model management
2. Memory Layer - User preferences and context storage
3. Decision Layer - Intelligent orchestration and agent sequencing
4. Action Layer - Task execution (extraction, generation, normalization)

Tests include:
- Individual layer functionality
- End-to-end document analysis flow
- User preference management
- Agent orchestration with the Decision Layer
- Session management
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
        
        # Enable ANSI escape sequences in Windows console
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        
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
                # Handle potential Unicode errors gracefully
                try:
                    print(text)
                except UnicodeEncodeError:
                    # Remove emojis but keep the text
                    safe_text = text.encode('ascii', errors='replace').decode('ascii')
                    print(safe_text)
                set_color(WindowsColors.WHITE)  # Reset to white
            except Exception as e:
                # Fallback without colors
                try:
                    print(text)
                except UnicodeEncodeError:
                    print(text.encode('ascii', errors='replace').decode('ascii'))
        
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

class CognitiveArchitectureTester:
    """
    Tester for the 4-layer cognitive architecture
    Tests individual layers and end-to-end flows
    """
    
    def __init__(self):
        self.base_url = "http://localhost:3002"
        self.gemini_api_key = os.getenv('GEMINI_API_KEY', '')
        
        # Test preferences for different scenarios
        self.test_preferences = {
            'minimal': {
                'general': {
                    'language': 'en',
                    'verbosity_level': 'minimal',
                    'auto_generate_brief': False
                },
                'citation': {
                    'format': 'bluebook'
                }
            },
            'detailed': {
                'general': {
                    'language': 'en',
                    'verbosity_level': 'detailed',
                    'auto_generate_brief': True
                },
                'citation': {
                    'format': 'apa'
                }
            }
        }

    
    def test_memory_layer(self) -> bool:
        """Test Memory Layer - Preferences and session management"""
        colored_print("\n🧠 Testing Memory Layer (Preferences & Context)", Colors.INFO, bold=True)
        colored_print("=" * 60, Colors.INFO)
        
        try:
            # Test 1: Get current preferences
            colored_print("\n1️⃣ Getting current preferences...", Colors.INFO)
            response = requests.get(f"{self.base_url}/api/preferences")
            if response.status_code == 200:
                prefs = response.json()
                status_log(f"✅ Retrieved preferences: {len(prefs.get('preferences', {}))} categories", "success")
            else:
                status_log(f"❌ Failed to get preferences: {response.status_code}", "error")
                return False
            
            # Test 2: Update preferences
            colored_print("\n2️⃣ Updating preferences (test mode)...", Colors.INFO)
            test_update = {
                'category': 'general',
                'updates': {
                    'verbosity_level': 'detailed',
                    'language': 'en'
                }
            }
            response = requests.post(
                f"{self.base_url}/api/preferences",
                json=test_update,
                headers={"Content-Type": "application/json"}
            )
            if response.status_code == 200:
                status_log("✅ Preferences updated successfully", "success")
            else:
                status_log(f"❌ Failed to update preferences: {response.status_code}", "error")
                return False
            
            # Test 3: Get preference schema
            colored_print("\n3️⃣ Getting preference schema...", Colors.INFO)
            response = requests.get(f"{self.base_url}/api/preferences/schema")
            if response.status_code == 200:
                schema = response.json()
                categories = len(schema.get('schema', {}))
                status_log(f"✅ Retrieved preference schema: {categories} categories", "success")
            else:
                status_log(f"❌ Failed to get schema: {response.status_code}", "error")
                return False
            
            # Test 4: Session management
            colored_print("\n4️⃣ Testing session management...", Colors.INFO)
            response = requests.get(f"{self.base_url}/api/session")
            if response.status_code == 200:
                session = response.json()
                status_log(f"✅ Session retrieved: {session.get('success', False)}", "success")
            else:
                status_log(f"⚠️ Session endpoint returned: {response.status_code}", "warning")
            
            colored_print("\n✅ Memory Layer tests passed!", Colors.SUCCESS, bold=True)
            return True
            
        except Exception as e:
            status_log(f"❌ Memory Layer test failed: {e}", "error")
            return False
    
    def test_decision_layer(self, document_text: str) -> bool:
        """Test Decision Layer - Orchestration and planning"""
        colored_print("\n🎯 Testing Decision Layer (Orchestration)", Colors.ORCHESTRATOR, bold=True)
        colored_print("=" * 60, Colors.ORCHESTRATOR)
        
        try:
            # Test orchestration endpoint
            colored_print("\n1️⃣ Requesting execution plan from Decision Layer...", Colors.INFO)
            
            orchestration_request = {
                'user_request': 'Analyze this legal document and generate a comprehensive brief',
                'current_context': {
                    'has_document': True,
                    'document_length': len(document_text)
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/orchestrate",
                json=orchestration_request,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    plan = data.get('data', {}).get('orchestration_plan', {})
                    status_log(f"✅ Orchestration plan received", "success")
                    
                    # Display plan details
                    colored_print(f"\n   📋 Analysis: {plan.get('analysis', 'N/A')}", Colors.ORCHESTRATOR)
                    
                    agents = plan.get('selected_agents', [])
                    colored_print(f"\n   🤖 Selected Agents ({len(agents)}):", Colors.INFO)
                    for agent in agents:
                        colored_print(f"      • {agent.get('agent_id')}: {agent.get('reason')}", Colors.ORCHESTRATOR)
                    
                    sequence = plan.get('execution_sequence', [])
                    colored_print(f"\n   🔄 Execution Sequence: {' → '.join(sequence)}", Colors.SUCCESS)
                    
                    colored_print(f"   🎯 Confidence: {plan.get('confidence', 0):.2f}", Colors.SUCCESS)
                    
                    validation = data.get('data', {}).get('validation_result', {})
                    if validation.get('is_valid'):
                        status_log("   ✅ Plan validation: PASSED", "success")
                    else:
                        status_log(f"   ⚠️ Plan validation issues: {validation.get('errors', [])}", "warning")
                    
                    colored_print("\n✅ Decision Layer tests passed!", Colors.SUCCESS, bold=True)
                    return True
                else:
                    status_log(f"❌ Orchestration failed: {data.get('error')}", "error")
                    return False
            else:
                status_log(f"❌ Decision Layer failed: {response.status_code}", "error")
                return False
                
        except Exception as e:
            status_log(f"❌ Decision Layer test failed: {e}", "error")
            return False

    
    def test_action_layer(self, document_text: str) -> Dict[str, Any]:
        """Test Action Layer - Task execution (extraction, generation, normalization)"""
        colored_print("\n⚡ Testing Action Layer (Task Execution)", Colors.INFO, bold=True)
        colored_print("=" * 60, Colors.INFO)
        
        results = {}
        
        try:
            # Test 1: Document extraction
            colored_print("\n1️⃣ Testing Legal Extraction...", Colors.LEGAL_EXTRACTOR, bold=True)
            response = requests.post(
                f"{self.base_url}/api/analyze-document",
                json={'text': document_text},
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    extracted = data.get('data', {}).get('extracted_fields', {})
                    results['extraction'] = extracted
                    
                    status_log(f"✅ Extraction successful", "success")
                    colored_print(f"   📄 Case: {extracted.get('case_name', 'N/A')}", Colors.LEGAL_EXTRACTOR)
                    colored_print(f"   🏛️ Court: {extracted.get('court', 'N/A')}", Colors.LEGAL_EXTRACTOR)
                    colored_print(f"   📅 Date: {extracted.get('date', 'N/A')}", Colors.LEGAL_EXTRACTOR)
                    colored_print(f"   📚 Citations: {len(extracted.get('citations', []))}", Colors.LEGAL_EXTRACTOR)
                else:
                    status_log(f"❌ Extraction failed: {data.get('error')}", "error")
                    return results
            else:
                status_log(f"❌ Extraction endpoint failed: {response.status_code}", "error")
                return results
            
            # Test 2: Brief generation
            colored_print("\n2️⃣ Testing Brief Generation...", Colors.BRIEF_GENERATOR, bold=True)
            response = requests.post(
                f"{self.base_url}/api/generate-brief",
                json={'extracted_data': extracted},
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    brief = data.get('data', {}).get('brief', {})
                    results['brief'] = brief
                    
                    status_log(f"✅ Brief generation successful", "success")
                    colored_print(f"   📋 Issue: {brief.get('issue', 'N/A')[:80]}...", Colors.BRIEF_GENERATOR)
                    colored_print(f"   📊 Word Count: {brief.get('word_count', 0)}", Colors.BRIEF_GENERATOR)
                    colored_print(f"   🎯 Confidence: {brief.get('confidence_score', 0)}%", Colors.SUCCESS)
                else:
                    status_log(f"⚠️ Brief generation failed: {data.get('error')}", "warning")
            else:
                status_log(f"⚠️ Brief endpoint failed: {response.status_code}", "warning")
            
            # Test 3: Citation normalization
            citations = extracted.get('citations', [])
            if citations:
                colored_print("\n3️⃣ Testing Citation Normalization...", Colors.CITATION_NORMALIZER, bold=True)
                response = requests.post(
                    f"{self.base_url}/api/normalize-citations",
                    json={'citations': citations},
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        normalized = data.get('data', {}).get('normalized_citations', [])
                        results['citations'] = normalized
                        
                        status_log(f"✅ Citation normalization successful", "success")
                        colored_print(f"   📚 Processed: {len(normalized)} citations", Colors.CITATION_NORMALIZER)
                        if normalized:
                            colored_print(f"   Format: {normalized[0].get('format', 'N/A')}", Colors.CITATION_NORMALIZER)
                    else:
                        status_log(f"⚠️ Citation normalization failed", "warning")
                else:
                    status_log(f"⚠️ Citation endpoint failed: {response.status_code}", "warning")
            else:
                colored_print("\n3️⃣ Skipping citation test (no citations found)", Colors.INFO)
            
            colored_print("\n✅ Action Layer tests completed!", Colors.SUCCESS, bold=True)
            return results
            
        except Exception as e:
            status_log(f"❌ Action Layer test failed: {e}", "error")
            return results

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

def test_cognitive_architecture():
    """Test the complete 4-layer cognitive architecture"""
    colored_print("\n🧠 Testing 4-Layer Cognitive Architecture", Colors.ORCHESTRATOR, bold=True)
    colored_print("=" * 80, Colors.ORCHESTRATOR)
    colored_print("\nArchitecture: Perception → Memory → Decision → Action", Colors.INFO)
    colored_print("=" * 80, Colors.ORCHESTRATOR)
    
    start_time = time.time()
    
    # Initialize tester
    tester = CognitiveArchitectureTester()
    
    # Test each layer
    test_results = {
        'memory': False,
        'decision': False,
        'action': False
    }
    
    # Layer 1: Perception Layer (tested implicitly through other layers)
    colored_print("\n🎨 Perception Layer: Tested through all LLM interactions", Colors.INFO)
    
    # Layer 2: Memory Layer
    test_results['memory'] = tester.test_memory_layer()
    
    # Layer 3: Decision Layer
    if test_results['memory']:
        test_results['decision'] = tester.test_decision_layer(SAMPLE_LEGAL_TEXT)
    
    # Layer 4: Action Layer
    if test_results['decision']:
        action_results = tester.test_action_layer(SAMPLE_LEGAL_TEXT)
        test_results['action'] = bool(action_results)
    
    # Summary
    end_time = time.time()
    colored_print("\n" + "=" * 80, Colors.ORCHESTRATOR)
    colored_print(f"🏁 4-Layer Architecture Test completed in {end_time - start_time:.2f} seconds!", Colors.ORCHESTRATOR, bold=True)
    colored_print("=" * 80, Colors.ORCHESTRATOR)
    
    colored_print(f"\n📊 Test Results:", Colors.INFO, bold=True)
    for layer, passed in test_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        color = Colors.SUCCESS if passed else Colors.ERROR
        colored_print(f"   {layer.upper()} Layer: {status}", color)
    
    all_passed = all(test_results.values())
    if all_passed:
        colored_print("\n🎉 All cognitive layers working correctly!", Colors.SUCCESS, bold=True)
        colored_print("\n📋 System Status:", Colors.INFO, bold=True)
        colored_print("   ✅ Perception Layer: LLM interactions functional", Colors.SUCCESS)
        colored_print("   ✅ Memory Layer: Preferences stored server-side", Colors.SUCCESS)
        colored_print("   ✅ Decision Layer: Intelligent orchestration active", Colors.SUCCESS)
        colored_print("   ✅ Action Layer: Task execution operational", Colors.SUCCESS)
        
        colored_print("\n🚀 Next Steps:", Colors.INFO)
        colored_print("   1. Test with your own legal documents", Colors.INFO)
        colored_print("   2. Configure preferences in the Chrome extension", Colors.INFO)
        colored_print("   3. Try different citation formats and verbosity levels", Colors.INFO)
        colored_print("   4. Monitor server logs for LLM interactions", Colors.INFO)
    else:
        colored_print("\n⚠️ Some tests failed. Please check:", Colors.WARNING, bold=True)
        colored_print("   1. Ensure server is running: python server/main.py", Colors.WARNING)
        colored_print("   2. Check Gemini API key in server/.env or config.py", Colors.WARNING)
        colored_print("   3. Review server logs in server/logs/", Colors.WARNING)
        colored_print("   4. Verify Python dependencies are installed", Colors.WARNING)
    
    return all_passed

def main():
    """Run the 4-layer cognitive architecture tests"""
    colored_print("\n" + "=" * 80, Colors.ORCHESTRATOR, bold=True)
    colored_print("🧠 LAW CASE FINDER - 4-LAYER COGNITIVE ARCHITECTURE TEST", Colors.ORCHESTRATOR, bold=True)
    colored_print("=" * 80, Colors.ORCHESTRATOR, bold=True)
    
    colored_print("\nTesting Layers:", Colors.INFO)
    colored_print("   1. Perception Layer  - LLM interactions and model management", Colors.INFO)
    colored_print("   2. Memory Layer      - User preferences and context storage", Colors.INFO)
    colored_print("   3. Decision Layer    - Intelligent orchestration and planning", Colors.INFO)
    colored_print("   4. Action Layer      - Task execution (extract, generate, normalize)", Colors.INFO)
    
    colored_print("\n" + "=" * 80, Colors.ORCHESTRATOR)
    
    # Test 1: Health Check
    if not test_health_check():
        colored_print("\n" + "=" * 80, Colors.ERROR)
        status_log("\n❌ Backend server is not running!", "error")
        colored_print("\nTo start the server:", Colors.INFO, bold=True)
        colored_print("   cd server", Colors.INFO)
        colored_print("   python main.py", Colors.INFO)
        colored_print("\nOr use npm script (if installed):", Colors.INFO)
        colored_print("   npm run server", Colors.INFO)
        colored_print("\n" + "=" * 80, Colors.ERROR)
        return
    
    # Test 2: 4-Layer Cognitive Architecture
    success = test_cognitive_architecture()
    
    # Final summary
    colored_print("\n" + "=" * 80, Colors.ORCHESTRATOR, bold=True)
    if success:
        colored_print("🎉 ALL TESTS PASSED - System is fully operational!", Colors.SUCCESS, bold=True)
    else:
        colored_print("⚠️  SOME TESTS FAILED - Review output above for details", Colors.WARNING, bold=True)
    colored_print("=" * 80, Colors.ORCHESTRATOR, bold=True)

if __name__ == "__main__":
    main()
