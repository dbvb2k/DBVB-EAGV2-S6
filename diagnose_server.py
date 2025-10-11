#!/usr/bin/env python3
"""
Diagnostic script for Law Case Finder server
Checks configuration, prompts, layers, and API connectivity
"""

import sys
import os
from pathlib import Path
import json

def print_header(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_status(item, status, details=""):
    symbols = {"✓": "✓", "✗": "✗", "⚠": "⚠"}
    symbol = symbols.get(status, status)
    color_codes = {"✓": "\033[92m", "✗": "\033[91m", "⚠": "\033[93m"}
    reset = "\033[0m"
    
    if sys.platform == "win32":
        # Windows doesn't always support ANSI colors
        print(f"{symbol} {item}")
    else:
        color = color_codes.get(status, "")
        print(f"{color}{symbol}{reset} {item}")
    
    if details:
        print(f"  → {details}")

def check_python_version():
    """Check Python version"""
    print_header("Python Environment")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major >= 3 and version.minor >= 8:
        print_status(f"Python version: {version_str}", "✓", "Compatible (3.8+)")
        return True
    else:
        print_status(f"Python version: {version_str}", "✗", "Need Python 3.8+")
        return False

def check_dependencies():
    """Check required Python packages"""
    print_header("Dependencies")
    
    required_packages = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS',
        'google.generativeai': 'Google Generative AI',
        'requests': 'Requests'
    }
    
    all_good = True
    for import_name, display_name in required_packages.items():
        try:
            __import__(import_name)
            print_status(display_name, "✓", "Installed")
        except ImportError:
            print_status(display_name, "✗", "Missing - run: pip install -r server/requirements.txt")
            all_good = False
    
    return all_good

def check_directory_structure():
    """Check project directory structure"""
    print_header("Directory Structure")
    
    required_dirs = [
        'server',
        'server/layers',
        'server/prompts',
        'server/data',
        'server/utils',
        'extension'
    ]
    
    all_good = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print_status(dir_path, "✓", "Exists")
        else:
            print_status(dir_path, "✗", "Missing")
            all_good = False
    
    return all_good

def check_prompts_file():
    """Check system prompts file"""
    print_header("System Prompts")
    
    # Try multiple possible locations
    possible_paths = [
        Path("server/prompts/system_prompts.json"),
        Path("prompts/system_prompts.json")
    ]
    
    prompts_file = None
    for path in possible_paths:
        if path.exists():
            prompts_file = path
            break
    
    if not prompts_file:
        print_status("system_prompts.json", "✗", "File not found in expected locations")
        print(f"  Tried paths:")
        for path in possible_paths:
            print(f"    - {path.absolute()}")
        return False, None
    
    print_status(f"system_prompts.json", "✓", f"Found at: {prompts_file}")
    
    try:
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts = json.load(f)
        
        required_prompts = ['legal_extraction', 'brief_generation', 'orchestration']
        found_prompts = [p for p in required_prompts if p in prompts]
        missing_prompts = [p for p in required_prompts if p not in prompts]
        
        print_status(f"Total prompts loaded: {len(prompts)}", "✓")
        print_status(f"Required prompts: {len(found_prompts)}/{len(required_prompts)}", 
                    "✓" if len(found_prompts) == len(required_prompts) else "✗")
        
        if missing_prompts:
            print_status(f"Missing prompts", "✗", f"{missing_prompts}")
            return False, prompts
        
        return True, prompts
        
    except json.JSONDecodeError as e:
        print_status("system_prompts.json", "✗", f"Invalid JSON: {e}")
        return False, None
    except Exception as e:
        print_status("system_prompts.json", "✗", f"Error loading: {e}")
        return False, None

def check_cognitive_layers():
    """Check if cognitive layers can be imported"""
    print_header("Cognitive Layers")
    
    try:
        sys.path.insert(0, 'server')
        from layers import PerceptionLayer, MemoryLayer, DecisionLayer, ActionLayer
        print_status("Import layers", "✓", "All layers can be imported")
        
        # Try to instantiate with dummy config
        from config import Config
        
        # Check if we can load prompts
        prompts_ok, prompts = check_prompts_file()
        if prompts_ok:
            try:
                perception = PerceptionLayer(Config(), prompts)
                print_status("PerceptionLayer", "✓", "Can be instantiated")
            except Exception as e:
                print_status("PerceptionLayer", "✗", f"Error: {e}")
                return False
            
            try:
                memory = MemoryLayer(storage_path="server/data")
                print_status("MemoryLayer", "✓", "Can be instantiated")
            except Exception as e:
                print_status("MemoryLayer", "✗", f"Error: {e}")
                return False
            
            try:
                decision = DecisionLayer(perception, memory)
                print_status("DecisionLayer", "✓", "Can be instantiated")
            except Exception as e:
                print_status("DecisionLayer", "✗", f"Error: {e}")
                return False
            
            try:
                action = ActionLayer(perception, memory)
                print_status("ActionLayer", "✓", "Can be instantiated")
            except Exception as e:
                print_status("ActionLayer", "✗", f"Error: {e}")
                return False
        
        return True
        
    except ImportError as e:
        print_status("Import layers", "✗", f"Import error: {e}")
        return False
    except Exception as e:
        print_status("Cognitive layers", "✗", f"Error: {e}")
        return False

def check_api_keys():
    """Check for API keys"""
    print_header("API Configuration")
    
    try:
        sys.path.insert(0, 'server')
        from config import Config
        config = Config()
        
        if hasattr(config, 'GEMINI_API_KEY') and config.GEMINI_API_KEY:
            key_preview = config.GEMINI_API_KEY[:8] + "..." if len(config.GEMINI_API_KEY) > 8 else "***"
            print_status("Gemini API Key", "✓", f"Configured ({key_preview})")
        else:
            print_status("Gemini API Key", "⚠", "Not configured - LLM features may not work")
        
        if hasattr(config, 'OLLAMA_BASE_URL'):
            print_status("Ollama URL", "✓", f"{config.OLLAMA_BASE_URL}")
        
        return True
        
    except Exception as e:
        print_status("Config", "✗", f"Error: {e}")
        return False

def check_server_running():
    """Check if server is running"""
    print_header("Server Status")
    
    try:
        import requests
        response = requests.get("http://localhost:3002/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_status("Server", "✓", "Running on http://localhost:3002")
            print_status("Architecture", "✓", data.get('architecture', 'Unknown'))
            
            layers = data.get('layers', {})
            for layer_name, status in layers.items():
                print_status(f"  {layer_name} layer", "✓" if status == "active" else "✗", status)
            
            return True
        else:
            print_status("Server", "✗", f"Unexpected status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_status("Server", "✗", "Not running - start with: python server/main.py")
        return False
    except Exception as e:
        print_status("Server", "✗", f"Error: {e}")
        return False

def main():
    """Run all diagnostic checks"""
    print("\n" + "=" * 70)
    print("  🔍 LAW CASE FINDER - DIAGNOSTIC CHECK")
    print("=" * 70)
    print("\n  Checking system configuration and dependencies...")
    
    results = {}
    results['python'] = check_python_version()
    results['dependencies'] = check_dependencies()
    results['structure'] = check_directory_structure()
    results['prompts'] = check_prompts_file()[0]
    results['layers'] = check_cognitive_layers()
    results['api_keys'] = check_api_keys()
    results['server'] = check_server_running()
    
    # Summary
    print_header("Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    if passed == total:
        print(f"\n  🎉 All checks passed ({passed}/{total})!")
        print(f"\n  ✓ System is properly configured")
        print(f"  ✓ Ready to analyze legal documents")
    else:
        print(f"\n  ⚠️  {total - passed} check(s) failed ({passed}/{total} passed)")
        print(f"\n  Please fix the issues above before using the system.")
        
        print(f"\n  Common fixes:")
        print(f"    1. Install dependencies: pip install -r server/requirements.txt")
        print(f"    2. Start server: python server/main.py")
        print(f"    3. Check API keys in server/config.py")
    
    print("\n" + "=" * 70 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

