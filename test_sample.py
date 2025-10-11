#!/usr/bin/env python3
"""
Test script for Law Case Finder - MVP Testing

This script tests the core functionality of the Law Case Finder system
by sending sample legal text to the backend API endpoints.
"""

import requests
import json
import time
import os
import sys

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
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            status_log(f"✅ Health check passed: {data}", "success")
            return True
        else:
            status_log(f"❌ Health check failed with status {response.status_code}", "error")
            return False
    except requests.exceptions.RequestException as e:
        status_log(f"❌ Health check failed: {e}", "error")
        return False

def test_document_analysis():
    """Test the document analysis endpoint"""
    agent_log("Legal Extractor", "Starting document analysis...", status="info")
    try:
        payload = {"text": SAMPLE_LEGAL_TEXT}
        response = requests.post(
            f"{BASE_URL}/api/analyze-document",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            agent_log("Legal Extractor", "Document analysis successful!", status="success")
            
            # Print extracted information
            if data.get('success') and 'data' in data:
                extracted = data['data']['extracted_fields']
                colored_print(f"   📄 Case Name: {extracted.get('case_name', 'N/A')}", Colors.LEGAL_EXTRACTOR)
                colored_print(f"   🏛️ Court: {extracted.get('court', 'N/A')}", Colors.LEGAL_EXTRACTOR)
                colored_print(f"   📅 Date: {extracted.get('date', 'N/A')}", Colors.LEGAL_EXTRACTOR)
                colored_print(f"   ⚖️ Holdings: {len(extracted.get('holdings', []))} found", Colors.LEGAL_EXTRACTOR)
                colored_print(f"   💭 Reasoning: {len(extracted.get('reasoning', []))} points", Colors.LEGAL_EXTRACTOR)
                colored_print(f"   📚 Citations: {len(extracted.get('citations', []))} found", Colors.LEGAL_EXTRACTOR)
                colored_print(f"   🎯 Confidence: {data['data'].get('confidence_score', 0):.2f}", Colors.SUCCESS)
                return extracted
            else:
                agent_log("Legal Extractor", f"Analysis failed: {data.get('error', 'Unknown error')}", status="error")
                return None
        else:
            agent_log("Legal Extractor", f"Analysis failed with status {response.status_code}", status="error")
            try:
                error_data = response.json()
                colored_print(f"   Error: {error_data.get('error', 'Unknown error')}", Colors.ERROR)
            except:
                colored_print(f"   Response: {response.text}", Colors.ERROR)
            return None
            
    except requests.exceptions.RequestException as e:
        agent_log("Legal Extractor", f"Analysis failed: {e}", status="error")
        return None

def test_brief_generation(extracted_data):
    """Test the brief generation endpoint"""
    if not extracted_data:
        agent_log("Brief Generator", "Skipping brief generation - no extracted data available", status="warning")
        return None
        
    agent_log("Brief Generator", "Starting brief generation...", status="info")
    try:
        payload = {"extracted_data": extracted_data}
        response = requests.post(
            f"{BASE_URL}/api/generate-brief",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=45
        )
        
        if response.status_code == 200:
            data = response.json()
            agent_log("Brief Generator", "Brief generation successful!", status="success")
            
            if data.get('success') and 'data' in data:
                brief = data['data']['brief']
                colored_print(f"   📋 Issue: {brief.get('issue', 'N/A')[:100]}...", Colors.BRIEF_GENERATOR)
                colored_print(f"   📖 Facts: {brief.get('facts', 'N/A')[:100]}...", Colors.BRIEF_GENERATOR)
                colored_print(f"   ⚖️ Holding: {brief.get('holding', 'N/A')[:100]}...", Colors.BRIEF_GENERATOR)
                colored_print(f"   💭 Reasoning Points: {len(brief.get('reasoning', []))}", Colors.BRIEF_GENERATOR)
                colored_print(f"   📚 Key Citations: {len(brief.get('key_citations', []))}", Colors.BRIEF_GENERATOR)
                colored_print(f"   📊 Word Count: {brief.get('word_count', 0)}", Colors.BRIEF_GENERATOR)
                colored_print(f"   🎯 Confidence: {brief.get('confidence_score', 0)}%", Colors.SUCCESS)
                return brief
            else:
                agent_log("Brief Generator", f"Brief generation failed: {data.get('error', 'Unknown error')}", status="error")
                return None
        else:
            agent_log("Brief Generator", f"Brief generation failed with status {response.status_code}", status="error")
            try:
                error_data = response.json()
                colored_print(f"   Error: {error_data.get('error', 'Unknown error')}", Colors.ERROR)
            except:
                colored_print(f"   Response: {response.text}", Colors.ERROR)
            return None
            
    except requests.exceptions.RequestException as e:
        agent_log("Brief Generator", f"Brief generation failed: {e}", status="error")
        return None

def test_citation_normalization():
    """Test the citation normalization endpoint"""
    agent_log("Citation Normalizer", "Starting citation normalization...", status="info")
    
    sample_citations = [
        "Brown v. Board of Education, 347 U.S. 483 (1954)",
        "Plessy v. Ferguson, 163 U.S. 537 (1896)",
        "Sweatt v. Painter, 339 U.S. 629 (1950)"
    ]
    
    try:
        payload = {
            "citations": sample_citations,
            "format": "bluebook"
        }
        response = requests.post(
            f"{BASE_URL}/api/normalize-citations",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            agent_log("Citation Normalizer", "Citation normalization successful!", status="success")
            
            if data.get('success') and 'data' in data:
                normalized_data = data['data']['normalized_citations']
                colored_print(f"   📚 Processed {len(normalized_data)} citations", Colors.CITATION_NORMALIZER)
                
                # Display first 3 citations
                for i, citation in enumerate(normalized_data[:3]):
                    if isinstance(citation, dict):
                        colored_print(f"   {i+1}. {citation.get('normalized', 'N/A')}", Colors.CITATION_NORMALIZER)
                    else:
                        colored_print(f"   {i+1}. {citation}", Colors.CITATION_NORMALIZER)
                
                return normalized_data
            else:
                agent_log("Citation Normalizer", f"Citation normalization failed: {data.get('error', 'Unknown error')}", status="error")
                return None
        else:
            agent_log("Citation Normalizer", f"Citation normalization failed with status {response.status_code}", status="error")
            return None
            
    except requests.exceptions.RequestException as e:
        agent_log("Citation Normalizer", f"Citation normalization failed: {e}", status="error")
        return None

def test_config_endpoint():
    """Test the configuration endpoint"""
    status_log("\n⚙️ Testing configuration endpoint...", "info")
    try:
        response = requests.get(f"{BASE_URL}/api/config", timeout=5)
        if response.status_code == 200:
            data = response.json()
            status_log("✅ Configuration endpoint successful!", "success")
            colored_print(f"   🤖 Primary Model: {data.get('primary_model', 'N/A')}", Colors.INFO)
            colored_print(f"   🔄 Fallback Model: {data.get('fallback_model', 'N/A')}", Colors.INFO)
            colored_print(f"   📁 Max File Size: {data.get('max_file_size', 0)} bytes", Colors.INFO)
            colored_print(f"   📄 Allowed Extensions: {data.get('allowed_extensions', [])}", Colors.INFO)
            return data
        else:
            status_log(f"❌ Configuration failed with status {response.status_code}", "error")
            return None
    except requests.exceptions.RequestException as e:
        status_log(f"❌ Configuration failed: {e}", "error")
        return None

def test_orchestration():
    """Test the Master Orchestrator"""
    agent_log("Master Orchestrator", "Testing orchestration planning...", status="info")
    try:
        payload = {
            "user_request": "Analyze this legal document and generate a comprehensive brief with citations",
            "current_context": {
                "has_document": True,
                "document_type": "legal_case",
                "user_preferences": {"citation_format": "bluebook"}
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/orchestrate",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            agent_log("Master Orchestrator", "Orchestration planning successful!", status="success")
            
            if data.get('success') and 'data' in data:
                plan = data['data']['orchestration_plan']
                colored_print(f"   📋 Analysis: {plan.get('analysis', 'N/A')[:100]}...", Colors.INFO)
                colored_print(f"   🔄 Execution Sequence: {' → '.join(plan.get('execution_sequence', []))}", Colors.ORCHESTRATOR, bold=True)
                colored_print(f"   🎯 Confidence: {plan.get('confidence', 0):.2f}", Colors.SUCCESS)
                colored_print(f"   🤖 Model Used: {data['data'].get('model_used', 'N/A')}", Colors.INFO)
                
                # Show selected agents
                selected_agents = plan.get('selected_agents', [])
                colored_print(f"   📊 Selected Agents ({len(selected_agents)}):", Colors.INFO)
                for i, agent in enumerate(selected_agents, 1):
                    agent_id = agent.get('agent_id', 'N/A')
                    reason = agent.get('reason', 'N/A')[:50]
                    agent_color = {
                        'legal_extractor': Colors.LEGAL_EXTRACTOR,
                        'brief_generator': Colors.BRIEF_GENERATOR,
                        'citation_normalizer': Colors.CITATION_NORMALIZER,
                        'case_retriever': Colors.CASE_RETRIEVER,
                        'comparator': Colors.COMPARATOR
                    }.get(agent_id, Colors.INFO)
                    colored_print(f"      {i}. {agent_id}: {reason}...", agent_color)
                
                return plan
            else:
                agent_log("Master Orchestrator", f"Orchestration failed: {data.get('error', 'Unknown error')}", status="error")
                return None
        else:
            agent_log("Master Orchestrator", f"Orchestration failed with status {response.status_code}", status="error")
            try:
                error_data = response.json()
                colored_print(f"   Error: {error_data.get('detail', 'Unknown error')}", Colors.ERROR)
            except:
                colored_print(f"   Response: {response.text}", Colors.ERROR)
            return None
            
    except requests.exceptions.RequestException as e:
        agent_log("Master Orchestrator", f"Orchestration failed: {e}", status="error")
        return None

def main():
    """Run all tests"""
    colored_print("🚀 Starting Law Case Finder - Master Orchestrator", Colors.ORCHESTRATOR, bold=True)
    colored_print("=" * 50, Colors.ORCHESTRATOR)
    
    start_time = time.time()
    
    # Test 1: Health Check
    if not test_health_check():
        status_log("\n❌ Backend server is not running. Please start it with:", "error")
        colored_print("   cd server && python main.py", Colors.ERROR)
        return
    
    # Test 2: Configuration
    test_config_endpoint()
    
    # Test 3: Master Orchestrator
    colored_print("\n🧠 Master Orchestrator: Planning Agent Execution", Colors.ORCHESTRATOR, bold=True)
    orchestration_plan = test_orchestration()
    
    if orchestration_plan:
        execution_sequence = orchestration_plan.get('execution_sequence', [])
        
        # Execute agents based on orchestration plan
        extracted_data = None
        brief_data = None
        
        for agent_id in execution_sequence:
            if agent_id == 'legal_extractor':
                colored_print(f"\n🤖 Agent: Legal Extractor", Colors.LEGAL_EXTRACTOR, bold=True)
                extracted_data = test_document_analysis()
            elif agent_id == 'brief_generator' and extracted_data:
                colored_print(f"\n🤖 Agent: Brief Generator", Colors.BRIEF_GENERATOR, bold=True)
                brief_data = test_brief_generation(extracted_data)
            elif agent_id == 'citation_normalizer':
                colored_print(f"\n🤖 Agent: Citation Normalizer", Colors.CITATION_NORMALIZER, bold=True)
                test_citation_normalization()
            else:
                colored_print(f"\n🤖 Agent: {agent_id} (not implemented in test)", Colors.WARNING)
    else:
        # Fallback to original sequence if orchestration fails
        status_log("\n⚠️ Orchestration failed, using default sequence...", "warning")
        
        # Test 4: Document Analysis (Agent 1)
        colored_print("\n🤖 Agent 1: Document Analysis", Colors.LEGAL_EXTRACTOR, bold=True)
        extracted_data = test_document_analysis()
        
        if extracted_data:
            # Test 5: Brief Generation (Agent 2)
            colored_print("\n🤖 Agent 2: Brief Generator", Colors.BRIEF_GENERATOR, bold=True)
            brief_data = test_brief_generation(extracted_data)
            
            if brief_data:
                # Test 6: Citation Normalization (Agent 3)
                colored_print("\n🤖 Agent 3: Citation Normalizer", Colors.CITATION_NORMALIZER, bold=True)
                test_citation_normalization()
    
    # Summary
    end_time = time.time()
    colored_print("\n" + "=" * 50, Colors.ORCHESTRATOR)
    colored_print(f"🏁 Master Orchestrator completed all agent tasks in {end_time - start_time:.2f} seconds!", Colors.ORCHESTRATOR, bold=True)
    
    if extracted_data and brief_data:
        status_log("✅ All agents executed successfully!", "success")
        colored_print("\n📋 Next Steps:", Colors.INFO)
        colored_print("1. Install Chrome extension dependencies: cd extension && npm install", Colors.INFO)
        colored_print("2. Build Chrome extension: cd extension && npm run build", Colors.INFO)
        colored_print("3. Load extension in Chrome from extension/build folder", Colors.INFO)
        colored_print("4. Test with real legal documents", Colors.INFO)
    else:
        status_log("⚠️ Some agents may need configuration:", "warning")
        colored_print("1. Check if Gemini API key is set in server/.env", Colors.WARNING)
        colored_print("2. Ensure Ollama is installed and running (if using as fallback)", Colors.WARNING)
        colored_print("3. Check server logs for detailed error messages", Colors.WARNING)

if __name__ == "__main__":
    main()
