# Law Case Finder - AI-Powered Legal Analysis Chrome Extension

An intelligent Chrome extension that uses Agentic AI orchestration to analyze legal documents, extract key information, and generate comprehensive legal briefs.

## Features

- 📄 PDF upload and text extraction
- 🔍 Legal issue and fact extraction
- 📋 Automated brief generation
- 📊 Citation analysis and normalization
- 🌳 Visual precedence tree (coming soon)
- 📤 Export in multiple citation formats

## Architecture

### 🧠 4-Layer Cognitive Architecture

This system uses a sophisticated 4-layer cognitive architecture:

1. **Perception Layer** - LLM interactions and model management (Gemini Flash 2.0 + Ollama)
2. **Memory Layer** - User preferences, context storage, and session management
3. **Decision Layer** - Intelligent orchestration and agent sequencing
4. **Action Layer** - Task execution (extraction, brief generation, normalization)

See [ARCHITECTURE.md](server/ARCHITECTURE.md) for detailed documentation.

### Chrome Extension
- **Vanilla JavaScript** (ES6+) - No build tools required!
- Settings panel with server-side preference sync
- Real-time agent console for transparency
- Responsive UI with drag-and-drop support

### Backend Server
- **Python 3.8+** with Flask REST API
- Cognitive layer orchestration
- PDF processing with text extraction
- Centralized prompt management (JSON-based)
- Server-side user preference storage

### Tech Stack
- **Backend**: Python 3.8+, Flask, Google Gemini API / Ollama
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **No Build Tools**: Pure JavaScript - just load and run!

📘 See [TECH_STACK.md](TECH_STACK.md) for complete technical details.

## Setup

1. **Install Python dependencies:**
   ```bash
   cd server
   pip install -r requirements.txt
   ```

2. **Configure API keys:**
   - Edit `server/config.py` and add your Gemini API key
   - Or set up Ollama for local LLM

3. **Start the server:**
   ```bash
   cd server
   python main.py
   ```

4. **Load extension in Chrome:**
   - Open Chrome and navigate to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" and select the `extension` folder

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

## Development

### Project Structure
```
├── extension/                    # Chrome extension
│   ├── popup.html               # UI with Settings panel
│   ├── popup.js                 # Frontend with preference sync
│   ├── popup.css                # Modern styling
│   ├── background.js            # Service worker
│   └── manifest.json            # Extension configuration
├── server/                       # Backend server
│   ├── main.py                  # Main orchestrator (coordinates layers)
│   ├── config.py                # Configuration
│   ├── layers/                  # 4 Cognitive Layers ⭐
│   │   ├── perception_layer.py  # LLM interactions
│   │   ├── memory_layer.py      # Preferences & context
│   │   ├── decision_layer.py    # Orchestration & planning
│   │   └── action_layer.py      # Task execution
│   ├── prompts/                 # Centralized prompts
│   │   └── system_prompts.json  # All system prompts
│   ├── data/                    # User data storage
│   │   ├── user_preferences.json
│   │   └── sessions/
│   ├── agents/                  # Legacy agents (kept for reference)
│   ├── utils/                   # Utilities
│   └── logs/                    # LLM interaction logs
├── ARCHITECTURE.md               # Detailed architecture docs
└── SETUP.md                     # Setup instructions
```

### AI Capabilities

#### Current Features
1. **Legal Extractor** - Extracts structured data from legal documents (case name, facts, issues, holdings, reasoning, citations)
2. **Brief Generator** - Creates comprehensive legal briefs with configurable verbosity
3. **Citation Normalizer** - Standardizes citations (Bluebook, APA, MLA, Chicago)
4. **Intelligent Orchestration** - Automatically determines optimal agent execution sequence

#### Coming Soon
5. **Case Retriever** - Finds similar cases and precedents from legal databases
6. **Comparator Agent** - Compares cases and highlights similarities/differences
7. **Multi-language Support** - Analysis in Spanish, French, German, Portuguese

### User Preferences

The system now includes comprehensive user preference management:

#### General Settings
- Output format (Plain Text, PDF, Markdown)
- Language selection (English, Spanish, French, German, Portuguese)
- Verbosity level (Minimal, Standard, Detailed)
- Auto-generate brief option

#### AI Model Settings
- Primary model selection (Gemini/Ollama)
- Fallback model configuration
- Temperature control for creativity
- Automatic fallback on failure

#### Citation Settings
- Citation format (Bluebook, APA, MLA, Chicago)
- Include citations in brief
- Auto-normalize citations

#### Privacy Settings
- Store analysis results
- Document storage policy
- Data anonymization options

All preferences are stored server-side and persist across sessions.

## Configuration

### Required
- **Python 3.12+**
- **pip** (Python package manager)

### LLM Providers (choose one or both)
- **Gemini Flash 2.0** (cloud-based, recommended)
  - Get API key: https://makersuite.google.com/app/apikey
- **Ollama** (local, privacy-focused)
  - Install: https://ollama.ai/

## Privacy & Security

- No permanent storage of user documents without consent
- Clear disclaimers about legal advice limitations
- Source attribution for all generated content

## License

MIT License - see LICENSE file for details
