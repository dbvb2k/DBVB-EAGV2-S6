# Law Case Finder - 4-Layer Cognitive Architecture

## Overview

This project has been refactored to follow a **4-Layer Cognitive Architecture** that mimics human cognitive processing for AI-powered legal analysis.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│              Chrome Extension (Frontend)                │
│                    popup.js + UI                        │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP API
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    main.py                              │
│              (Pure Orchestrator)                        │
│         Coordinates all cognitive layers                │
└──┬─────────────────┬────────────────┬─────────────────┬─┘
   │                 │                │                 │
   ▼                 ▼                ▼                 ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ LAYER 1  │  │ LAYER 2  │  │ LAYER 3  │  │ LAYER 4  │
│Perception│  │  Memory  │  │ Decision │  │  Action  │
│          │  │          │  │          │  │          │
│ LLM      │  │User Prefs│  │Orchestr. │  │Task Exec.│
│Management│  │  Context │  │  Planning│  │  Agents  │
│          │  │  Storage │  │          │  │          │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

## The 4 Cognitive Layers

### Layer 1: Perception Layer (`perception_layer.py`)

**Purpose**: Handle all interactions with Language Models (LLMs)

**Responsibilities**:
- Manage multiple LLM providers (Gemini Flash 2.0, Ollama)
- Handle model switching and fallback logic
- Process prompts and parse responses
- Format prompts using centralized templates
- Track model availability and status

**Key Methods**:
- `process_with_llm()` - Main LLM interaction method
- `get_prompt()` - Load and format prompts from central configuration
- `parse_json_response()` - Parse structured JSON from LLM outputs
- `get_model_status()` - Check availability of models

### Layer 2: Memory Layer (`memory_layer.py`)

**Purpose**: Store and retrieve user preferences, context, and session state

**Responsibilities**:
- Persistent storage of user preferences (server-side)
- Session context management
- Analysis history tracking
- Preference validation and schema management

**Preference Categories**:
1. **General Settings**: Output format, language, verbosity level
2. **LLM Settings**: Model selection, temperature, fallback options
3. **Citation Settings**: Format (Bluebook/APA/MLA/Chicago), normalization
4. **Integration Settings**: Legal API configurations, export options
5. **Privacy Settings**: Data storage policies

**Key Methods**:
- `get_preferences()` - Retrieve user preferences
- `update_preferences()` - Save preference changes
- `get_session_context()` - Get current session state
- `get_preference_schema()` - Get UI configuration schema

### Layer 3: Decision Layer (`decision_layer.py`)

**Purpose**: Orchestrate agent execution and determine optimal processing flow

**Responsibilities**:
- Analyze user requests to determine required agents
- Create execution plans with agent sequences
- Validate execution plans for dependencies
- Implement conditional logic (e.g., skip citation normalization if no citations)
- Provide rule-based fallback when LLM is unavailable

**Available Agents**:
1. **legal_extractor** - Extract structured legal information
2. **brief_generator** - Generate comprehensive legal briefs
3. **citation_normalizer** - Normalize citations to standard formats
4. **case_retriever** - Find similar cases (future)
5. **comparator** - Compare cases (future)

**Key Methods**:
- `decide_execution_plan()` - Create optimal execution plan
- `validate_execution_plan()` - Check plan for errors
- `should_execute_agent()` - Conditional agent execution logic

### Layer 4: Action Layer (`action_layer.py`)

**Purpose**: Execute specific tasks (extraction, generation, normalization)

**Responsibilities**:
- Legal document extraction
- Legal brief generation
- Citation normalization
- Task validation and quality checking
- Data enhancement and formatting

**Key Methods**:
- `extract_legal_information()` - Extract from documents
- `generate_legal_brief()` - Generate briefs from extracted data
- `normalize_citations()` - Normalize citation formats
- `validate_extraction()` - Validate extracted data
- `validate_brief()` - Validate generated briefs

## Centralized Prompts

All system prompts are stored in `prompts/system_prompts.json`:

```json
{
  "orchestration": "...",
  "legal_extraction": "...",
  "brief_generation": "...",
  "citation_analysis": "...",
  ...
}
```

**Benefits**:
- Easy to edit without code changes
- Version control for prompt improvements
- Consistent prompt formatting
- Support for multiple languages

## User Preferences System

### Server-Side Storage

Preferences are stored in `server/data/user_preferences.json` and persist across sessions.

### Preference Categories

1. **General Settings**
   - Output format (plain_text, pdf, markdown)
   - Language (en, es, fr, de, pt, zh, ja)
   - Verbosity level (minimal, standard, detailed)
   - Auto-generate brief

2. **LLM Settings**
   - Primary model (gemini, ollama)
   - Fallback model
   - Temperature (creativity)
   - Enable fallback

3. **Citation Settings**
   - Format (bluebook, apa, mla, chicago)
   - Include citations in brief
   - Auto-normalize citations

4. **Integration Settings**
   - Legal API integrations (CourtListener, Caselaw Access)
   - Export destinations (Local, Google Drive, Dropbox)

5. **Privacy Settings**
   - Store documents
   - Store analysis results
   - Anonymize data

### Chrome Extension Integration

The Settings panel in the extension:
- Loads preferences from server on startup
- Saves changes back to server
- Falls back to local storage if server unavailable
- Provides reset to defaults functionality

## API Endpoints

### Preference Management
- `GET /api/preferences` - Get all preferences or by category
- `POST /api/preferences` - Update preferences
- `DELETE /api/preferences` - Reset to defaults
- `GET /api/preferences/schema` - Get preference schema for UI

### Document Analysis
- `POST /api/analyze-document` - Analyze legal document
- `POST /api/generate-brief` - Generate legal brief
- `POST /api/normalize-citations` - Normalize citations

### Orchestration
- `POST /api/orchestrate` - Get execution plan

### Session Management
- `GET /api/session` - Get session state
- `POST /api/session` - Save session
- `DELETE /api/session` - Clear session

### System
- `GET /health` - Health check with layer status
- `GET /api/config` - Get system configuration

## Data Flow Example

### Document Analysis Flow

1. **User Action**: Upload PDF in Chrome extension
2. **Extension**: Send file to `POST /api/analyze-document`
3. **main.py**: 
   - Extract text from PDF (if needed)
   - Load user preferences from Memory Layer
   - Call Action Layer to extract legal information
4. **Action Layer**:
   - Get extraction prompt from Perception Layer
   - Call Perception Layer to process with LLM
   - Parse and validate response
   - Enhance extracted data
5. **main.py**: Format and return response to extension
6. **Extension**: Display results with confidence scores

### Brief Generation Flow

1. **User Action**: Click "Generate Brief" button
2. **Extension**: Send extracted data to `POST /api/generate-brief`
3. **main.py**:
   - Load user preferences (citation format, verbosity, etc.)
   - Call Action Layer to generate brief
4. **Action Layer**:
   - Get brief generation prompt from Perception Layer
   - Format prompt with user preferences
   - Call Perception Layer to process with LLM
   - Enhance brief with metadata
   - Normalize citations if requested
5. **main.py**: Format and return brief
6. **Extension**: Display brief in formatted view

## Benefits of This Architecture

### 1. Separation of Concerns
Each layer has a single, well-defined responsibility

### 2. Flexibility
- Easy to swap LLM providers
- Simple to add new agents
- Straightforward preference additions

### 3. Maintainability
- Centralized prompt management
- Clear data flow
- Isolated testing of each layer

### 4. User Experience
- Persistent preferences
- Configurable behavior
- Transparent processing

### 5. Scalability
- Independent layer scaling
- Easy to add new cognitive layers
- Support for multiple LLM providers

## File Structure

```
server/
├── main.py                 # Main orchestrator
├── config.py              # Configuration
├── layers/                # 4 Cognitive Layers
│   ├── __init__.py
│   ├── perception_layer.py   # LLM interactions
│   ├── memory_layer.py       # Preferences & context
│   ├── decision_layer.py     # Orchestration
│   └── action_layer.py       # Task execution
├── prompts/               # Centralized prompts
│   └── system_prompts.json
├── data/                  # User data storage
│   ├── user_preferences.json
│   └── sessions/
├── agents/                # Legacy agents (deprecated)
│   ├── legal_extractor.py
│   ├── brief_generator.py
│   └── citation_normalizer.py
├── utils/
│   ├── pdf_processor.py
│   └── response_formatter.py
└── logs/                  # LLM interaction logs

extension/
├── popup.html            # UI with Settings panel
├── popup.js              # Frontend logic with preference management
├── popup.css             # Styling with new settings styles
├── background.js         # Service worker
└── manifest.json         # Extension manifest
```

## Migration Notes

### From Old Architecture

The previous architecture had:
- Individual agents with embedded LLM logic
- No centralized prompt management
- Client-side only preferences
- Tight coupling between agents

### To New Architecture

Now we have:
- **Separation**: Perception layer handles all LLM interactions
- **Centralization**: All prompts in `system_prompts.json`
- **Persistence**: Server-side preference storage
- **Flexibility**: Easy to modify any layer independently

### Backward Compatibility

The API endpoints remain compatible with the old extension code, but now use the new 4-layer architecture internally.

## Testing the System

### 1. Test Preferences
```python
# In Python console or test file
from layers import MemoryLayer

memory = MemoryLayer()

# Get preferences
prefs = memory.get_preferences()
print(prefs)

# Update preferences
memory.update_preferences('general', {'language': 'es'})

# Reset preferences
memory.reset_preferences()
```

### 2. Test Perception Layer
```python
from layers import PerceptionLayer
import json

# Load prompts
with open('server/prompts/system_prompts.json') as f:
    prompts = json.load(f)

perception = PerceptionLayer(Config(), prompts)

# Test LLM call
result = perception.process_with_llm(
    prompt="Explain legal precedent",
    preferred_model="gemini"
)
print(result)
```

### 3. Test Full Flow
1. Start the server: `python server/main.py`
2. Load extension in Chrome
3. Open Settings panel and modify preferences
4. Click "Save Preferences"
5. Upload a legal document
6. Verify extraction uses your preferences (language, verbosity)
7. Generate brief with custom citation format

## Future Enhancements

1. **Learning Layer**: Capture user feedback to improve over time
2. **Case Retriever**: Integration with legal databases
3. **Comparator Agent**: Case comparison functionality
4. **Multi-language**: Full support for multiple languages
5. **Advanced Analytics**: Usage patterns and accuracy tracking

## Troubleshooting

### Preferences Not Saving
- Check server logs for errors
- Verify `server/data/` directory exists
- Check browser console for API errors

### LLM Not Responding
- Check `perception_layer.get_model_status()`
- Verify API keys in `config.py`
- Check logs in `server/logs/`

### Extraction Quality Issues
- Adjust verbosity level in preferences
- Modify prompts in `system_prompts.json`
- Check LLM temperature settings

## Conclusion

This 4-layer cognitive architecture provides a robust, maintainable, and extensible foundation for AI-powered legal analysis. Each layer operates independently while working together seamlessly to deliver a superior user experience.

