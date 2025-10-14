"""
Law Case Finder - Main Orchestrator
====================================

This is the main orchestrator that coordinates the 4 cognitive layers:
1. Perception Layer - LLM interactions and model management
2. Memory Layer - User preferences and context storage
3. Decision Layer - Agent orchestration and execution planning
4. Action Layer - Task execution (extraction, generation, normalization)

All Chrome extension requests come through this orchestrator.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
import traceback
import logging
import json
from datetime import datetime
from pathlib import Path

# Import configuration
from config import Config

# Import cognitive layers
from layers import PerceptionLayer, MemoryLayer, DecisionLayer, ActionLayer

# Import utilities
from utils.pdf_processor import PDFProcessor
from utils.response_formatter import ResponseFormatter

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Enable CORS for Chrome extension
CORS(app, origins=["chrome-extension://*", "http://localhost:*"])

# ========== LOGGING SETUP ==========

_llm_logger = None
_log_file = None


def setup_llm_logging():
    """Setup logging for LLM input/output with timestamped files (singleton pattern)"""
    global _llm_logger, _log_file
    
    if _llm_logger is not None:
        return _llm_logger, _log_file
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/llm_interactions_{timestamp}.log"
    
    os.makedirs("logs", exist_ok=True)
    
    _llm_logger = logging.getLogger('llm_interactions')
    _llm_logger.setLevel(logging.INFO)
    _llm_logger.handlers.clear()
    
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    _llm_logger.addHandler(file_handler)
    _llm_logger.addHandler(console_handler)
    
    _log_file = log_filename
    _llm_logger.info(f"LLM logging initialized. Log file: {log_filename}")
    
    return _llm_logger, _log_file


def log_llm_interaction(layer_name, interaction_type, data, model_used=None, task=None):
    """Log LLM input/output interactions with layer information"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_entry = {
        "timestamp": timestamp,
        "layer": layer_name,
        "task": task,
        "interaction_type": interaction_type,
        "model_used": model_used,
        "data": data
    }
    
    if task:
        llm_logger.info(f"[{layer_name}: {task}] {interaction_type.upper()}: {log_entry}")
    else:
        llm_logger.info(f"[{layer_name}] {interaction_type.upper()}: {log_entry}")


# Initialize LLM logging
llm_logger, log_file = setup_llm_logging()

# ========== COGNITIVE LAYERS INITIALIZATION ==========

# Load system prompts
# Get the directory where main.py is located
script_dir = Path(__file__).parent
prompts_file = script_dir / "prompts" / "system_prompts.json"

if not prompts_file.exists():
    # Try alternative paths
    alt_paths = [
        Path("server/prompts/system_prompts.json"),
        Path("prompts/system_prompts.json")
    ]
    for alt_path in alt_paths:
        if alt_path.exists():
            prompts_file = alt_path
            break

try:
    with open(prompts_file, 'r', encoding='utf-8') as f:
        system_prompts = json.load(f)
    print(f"✓ Loaded system prompts from {prompts_file}")
    
    # Validate prompts
    required_prompts = ['legal_extraction', 'brief_generation', 'orchestration']
    missing_prompts = [p for p in required_prompts if p not in system_prompts]
    if missing_prompts:
        print(f"⚠ Warning: Missing required prompts: {missing_prompts}")
    else:
        print(f"✓ Validated {len(system_prompts)} system prompts")
        
except Exception as e:
    print(f"❌ ERROR: Could not load prompts file: {e}")
    print(f"   Tried path: {prompts_file}")
    print(f"   File exists: {prompts_file.exists()}")
    print(f"   Current working directory: {Path.cwd()}")
    print(f"\n⚠️  System will use empty prompts - API calls may fail!")
    system_prompts = {}

# Initialize cognitive layers
print("🧠 Initializing Cognitive Layers...")

try:
    # Create config instance
    config = Config()
    
    # Debug: Show config values
    print(f"  Config - API Key Present: {'YES' if config.GEMINI_API_KEY else 'NO'}")
    print(f"  Config - Primary Model: {config.PRIMARY_MODEL}")
    print(f"  Config - Gemini Model: {config.GEMINI_MODEL}")
    print(f"  Config - Ollama URL: {config.OLLAMA_BASE_URL}")
    
    # 1. Perception Layer (LLM interactions)
    perception_layer = PerceptionLayer(config, system_prompts)
    print("✓ Perception Layer initialized")
    
    # 2. Memory Layer (preferences and context)
    # Use relative path since we're running from server dir
    data_path = "data" if Path("data").exists() else "server/data"
    memory_layer = MemoryLayer(storage_path=data_path)
    print("✓ Memory Layer initialized")
    
    # 3. Decision Layer (orchestration)
    decision_layer = DecisionLayer(perception_layer, memory_layer)
    print("✓ Decision Layer initialized")
    
    # 4. Action Layer (task execution)
    action_layer = ActionLayer(perception_layer, memory_layer)
    print("✓ Action Layer initialized")
    
    print("✅ All Cognitive Layers initialized successfully")
    
except Exception as e:
    print(f"❌ Error initializing cognitive layers: {e}")
    traceback.print_exc()
    raise

# Initialize utilities
pdf_processor = PDFProcessor()
response_formatter = ResponseFormatter()

# ========== HELPER FUNCTIONS ==========


def is_valid_file(filename):
    """Check if file extension is allowed"""
    if not filename:
        return False
    
    valid_extensions = app.config.get('ALLOWED_EXTENSIONS', ['pdf', 'txt'])
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in valid_extensions


# ========== API ENDPOINTS ==========

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    model_status = perception_layer.get_model_status()
    
    return jsonify({
        "status": "healthy",
        "version": "2.0.0",
        "architecture": "4-layer cognitive system",
        "layers": {
            "perception": "active",
            "memory": "active",
            "decision": "active",
            "action": "active"
        },
        "models": model_status
    })


@app.route('/api/preferences', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_preferences():
    """
    Manage user preferences
    GET: Retrieve preferences
    POST/PUT: Update preferences
    DELETE: Reset preferences
    """
    try:
        if request.method == 'GET':
            # Get preferences
            category = request.args.get('category')
            preferences = memory_layer.get_preferences(category)
            
            return jsonify({
                'success': True,
                'preferences': preferences
            })
        
        elif request.method in ['POST', 'PUT']:
            # Update preferences
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
            
            category = data.get('category')
            updates = data.get('updates', {})
            
            if not category:
                return jsonify({"error": "Category is required"}), 400
            
            result = memory_layer.update_preferences(category, updates)
            
            if result['success']:
                return jsonify(result)
            else:
                return jsonify(result), 400
        
        elif request.method == 'DELETE':
            # Reset preferences
            category = request.args.get('category')
            result = memory_layer.reset_preferences(category)
            
            if result['success']:
                return jsonify(result)
            else:
                return jsonify(result), 400
    
    except Exception as e:
        return jsonify({"error": f"Preference management failed: {str(e)}"}), 500


@app.route('/api/preferences/schema', methods=['GET'])
def get_preference_schema():
    """Get the preference schema for UI generation"""
    try:
        schema = memory_layer.get_preference_schema()
        return jsonify({
            'success': True,
            'schema': schema
        })
    except Exception as e:
        return jsonify({"error": f"Schema retrieval failed: {str(e)}"}), 500


@app.route('/api/analyze-document', methods=['POST'])
def analyze_document():
    """
    Main endpoint for document analysis
    Uses Decision Layer to determine optimal execution plan
    """
    try:
        text_content = ""
        
        # Handle file upload
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:
                print(f"Processing file: {file.filename}")
                
                if not is_valid_file(file.filename):
                    return jsonify({
                        "error": "Invalid file type. Only PDF and TXT files are allowed."
                    }), 400
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
                    file.save(temp_file.name)
                    temp_file_path = temp_file.name
                
                try:
                    if file.filename.lower().endswith('.txt'):
                        with open(temp_file_path, 'r', encoding='utf-8') as f:
                            text_content = f.read()
                    else:
                        text_content = pdf_processor.extract_text(temp_file_path)
                except Exception as e:
                    return jsonify({"error": f"File processing failed: {str(e)}"}), 400
                finally:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
        
        # Handle text input from JSON data
        elif request.is_json:
            data = request.get_json()
            text_content = data.get('text', '')
        
        # Handle text input from form data
        elif 'text' in request.form:
            text_content = request.form['text']
        
        else:
            return jsonify({"error": "No file or text provided"}), 400
        
        if not text_content or len(text_content.strip()) < 100:
            return jsonify({"error": "Document content is too short or empty (minimum 100 characters)"}), 400
        
        # Get user preferences
        preferences = memory_layer.get_preferences()
        
        # Get detail level from preferences
        detail_level = preferences.get('general', {}).get('verbosity_level', 'standard')
        # Map verbosity level to detail level
        detail_level_map = {'minimal': 'summary', 'standard': 'summary', 'detailed': 'detailed'}
        detail_level = detail_level_map.get(detail_level, 'summary')
        
        # Update session context
        memory_layer.update_session_context({
            'has_document': True,
            'document_length': len(text_content)
        })
        
        # Log LLM input
        log_llm_interaction("Action Layer", "input", {
            "text_length": len(text_content),
            "text_preview": text_content[:200] + "..." if len(text_content) > 200 else text_content
        }, task="Legal Extraction")
        
        # Use Action Layer to extract legal information
        try:
            print(f"⚡ [Action Layer] Starting legal extraction...")
            extraction_result = action_layer.extract_legal_information(
                document_text=text_content,
                preferences=preferences,
                detail_level=detail_level
            )
            print(f"✅ [Action Layer] Legal extraction completed")
        except Exception as e:
            error_msg = f"Action Layer extraction error: {str(e)}"
            print(f"❌ ERROR: {error_msg}")
            traceback.print_exc()
            return jsonify({"error": error_msg}), 500
        
        # Log LLM output
        log_llm_interaction("Action Layer", "output", extraction_result, 
                           extraction_result.get('model_used', 'unknown'), task="Legal Extraction")
        
        if not extraction_result['success']:
            error_detail = extraction_result.get('error', 'Unknown error')
            print(f"❌ Extraction failed: {error_detail}")
            return jsonify({
                "error": f"Failed to extract legal information: {error_detail}"
            }), 500
        
        # Add to session history
        memory_layer.add_to_session_history({
            'type': 'document_analysis',
            'result': 'success',
            'data': {
                'document_length': len(text_content),
                'confidence': extraction_result.get('confidence', 0)
            }
        })
        
        # Format response
        response = response_formatter.format_extraction_response(extraction_result)
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Unexpected error in document analysis: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/api/generate-brief', methods=['POST'])
def generate_brief():
    """
    Generate legal brief from extracted information
    Uses Action Layer for brief generation
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        extracted_data = data.get('extracted_data')
        
        if not extracted_data:
            return jsonify({"error": "No extracted data provided"}), 400
        
        # Get user preferences
        preferences = memory_layer.get_preferences()
        
        # Get detail level from preferences
        detail_level = preferences.get('general', {}).get('verbosity_level', 'standard')
        # Map verbosity level to detail level
        detail_level_map = {'minimal': 'summary', 'standard': 'summary', 'detailed': 'detailed'}
        detail_level = detail_level_map.get(detail_level, 'summary')
        
        # Log LLM input
        log_llm_interaction("Action Layer", "input", {
            "extracted_data_keys": list(extracted_data.keys()) if isinstance(extracted_data, dict) else "Not a dict"
        }, task="Brief Generation")
        
        # Use Action Layer to generate brief
        print(f"⚡ [Action Layer] Starting brief generation...")
        brief_result = action_layer.generate_legal_brief(
            extracted_data=extracted_data,
            preferences=preferences,
            detail_level=detail_level
        )
        print(f"✅ [Action Layer] Brief generation completed")
        
        # Log LLM output
        log_llm_interaction("Action Layer", "output", brief_result, 
                           brief_result.get('model_used', 'unknown'), task="Brief Generation")
        
        if not brief_result['success']:
            return jsonify({
                "error": f"Failed to generate brief: {brief_result.get('error', 'Unknown error')}"
            }), 500
        
        # Normalize citations if requested
        citations = []
        if isinstance(extracted_data, dict):
            citations = extracted_data.get('citations', [])
        
        citation_result = {'success': True, 'data': {'normalized_citations': [], 'format': 'bluebook', 'total_processed': 0}}
        
        if citations and preferences.get('citation', {}).get('normalize_citations', True):
            citation_result = action_layer.normalize_citations(
                citations=citations,
                preferences=preferences
            )
        
        # Add to session history
        memory_layer.add_to_session_history({
            'type': 'brief_generation',
            'result': 'success',
            'data': {
                'word_count': brief_result.get('data', {}).get('word_count', 0),
                'confidence': brief_result.get('data', {}).get('confidence_score', 0)
            }
        })
        
        # Format response
        response = response_formatter.format_brief_response(brief_result, citation_result)
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Unexpected error in brief generation: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/api/normalize-citations', methods=['POST'])
def normalize_citations():
    """
    Normalize citations to specified format
    Uses Action Layer for citation normalization
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        citations = data.get('citations', [])
        
        if not citations:
            return jsonify({
                "success": True,
                "data": {
                    "normalized_citations": [],
                    "total_processed": 0
                }
            })
        
        # Get user preferences
        preferences = memory_layer.get_preferences()
        
        # Log LLM input
        log_llm_interaction("Action Layer", "input", {
            "citations_count": len(citations),
            "citations_preview": citations[:3] if len(citations) > 3 else citations
        }, task="Citation Normalization")
        
        # Use Action Layer to normalize citations
        print(f"⚡ [Action Layer] Starting citation normalization...")
        result = action_layer.normalize_citations(
            citations=citations,
            preferences=preferences
        )
        print(f"✅ [Action Layer] Citation normalization completed")
        
        # Log LLM output
        log_llm_interaction("Action Layer", "output", result, 
                           result.get('model_used', 'rule-based'), task="Citation Normalization")
        
        return jsonify(response_formatter.format_citation_response(result))
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/api/orchestrate', methods=['POST'])
def orchestrate_agents():
    """
    Use Decision Layer to determine optimal agent execution sequence
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        user_request = data.get('user_request')
        current_context = data.get('current_context', {})
        
        if not user_request:
            return jsonify({"error": "User request is required"}), 400
        
        # Get user preferences for detail level
        preferences = memory_layer.get_preferences()
        detail_level = preferences.get('general', {}).get('verbosity_level', 'standard')
        # Map verbosity level to detail level
        detail_level_map = {'minimal': 'summary', 'standard': 'summary', 'detailed': 'detailed'}
        detail_level = detail_level_map.get(detail_level, 'summary')
        
        # Log LLM input
        log_llm_interaction("Decision Layer", "input", {
            "user_request": user_request,
            "current_context": current_context
        }, task="Orchestration Planning")
        
        # Get execution plan from Decision Layer
        print(f"🎯 [Decision Layer] Starting orchestration planning...")
        orchestration_result = decision_layer.decide_execution_plan(
            user_request=user_request,
            context=current_context,
            detail_level=detail_level
        )
        print(f"✅ [Decision Layer] Orchestration planning completed")
        
        # Log LLM output
        log_llm_interaction("Decision Layer", "output", orchestration_result, 
                           orchestration_result.get('model_used', 'unknown'), task="Orchestration Planning")
        
        if not orchestration_result['success']:
            return jsonify({
                "error": f"Orchestration failed: {orchestration_result.get('error', 'Unknown error')}"
            }), 500
        
        # Format response
        response_data = {
            'orchestration_plan': orchestration_result.get('plan', {}),
            'validation_result': orchestration_result.get('validation', {}),
            'model_used': orchestration_result.get('model_used', 'unknown'),
            'processing_time': orchestration_result.get('processing_time', 0)
        }
        
        return jsonify({
            'success': True,
            'data': response_data,
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0'
        })
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500


@app.route('/api/session', methods=['GET', 'POST', 'DELETE'])
def manage_session():
    """
    Manage session state
    GET: Get current session
    POST: Save session
    DELETE: Clear session
    """
    try:
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'session': {
                    'context': memory_layer.get_session_context(),
                    'history': memory_layer.get_session_history()
                }
            })
        
        elif request.method == 'POST':
            saved = memory_layer.save_session()
            return jsonify({
                'success': saved,
                'message': 'Session saved' if saved else 'Failed to save session'
            })
        
        elif request.method == 'DELETE':
            memory_layer.clear_session()
            return jsonify({
                'success': True,
                'message': 'Session cleared'
            })
    
    except Exception as e:
        return jsonify({"error": f"Session management failed: {str(e)}"}), 500


@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current configuration for frontend"""
    try:
        preferences = memory_layer.get_preferences()
        model_status = perception_layer.get_model_status()
        
        return jsonify({
            'architecture': '4-layer cognitive system',
            'version': '2.0.0',
            'preferences': preferences,
            'models': model_status,
            'max_file_size': getattr(Config, 'MAX_CONTENT_LENGTH', 16777216),
            'allowed_extensions': list(getattr(Config, 'ALLOWED_EXTENSIONS', {'pdf', 'txt'}))
        })
    except Exception as e:
        return jsonify({"error": f"Configuration error: {str(e)}"}), 500


# ========== MAIN ==========

if __name__ == "__main__":
    # Only show startup message once (not on Flask debug restarts)
    if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print("=" * 70)
        print("🚀 Law Case Finder - 4-Layer Cognitive Architecture")
        print("=" * 70)
        print(f"📝 LLM interactions logged to: {log_file}")
        print(f"🌐 Server running on: http://0.0.0.0:3002")
        print(f"🔧 Debug mode: {Config.FLASK_DEBUG}")
        print(f"🧠 Architecture: Perception → Memory → Decision → Action")
        print("=" * 70)
    
    app.run(
        host="0.0.0.0",
        port=3002,
        debug=Config.FLASK_DEBUG
    )
