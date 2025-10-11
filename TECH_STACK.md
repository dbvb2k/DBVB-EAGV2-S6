# Tech Stack - Law Case Finder

## 🎯 Core Technologies

### Backend
- **Language**: Python 3.8+
- **Framework**: Flask (REST API)
- **LLM Integration**: 
  - Google Gemini Flash 2.0 (primary)
  - Ollama (local alternative)
- **PDF Processing**: PyPDF2 / pdfplumber
- **Data Storage**: JSON files (server-side)

### Frontend (Chrome Extension)
- **Language**: Vanilla JavaScript (ES6+)
- **UI**: HTML5 + CSS3
- **Build Tools**: **NONE** - Pure JavaScript!
- **No Dependencies**: No webpack, no babel, no npm packages

### Architecture
- **Pattern**: 4-Layer Cognitive Architecture
- **Layers**: Perception → Memory → Decision → Action
- **Communication**: REST API (JSON)

## 📦 Required Dependencies

### Python Packages (see `server/requirements.txt`)
```
flask>=2.3.0
flask-cors>=4.0.0
google-generativeai>=0.3.0
requests>=2.31.0
PyPDF2>=3.0.0
python-dotenv>=1.0.0
```

### System Requirements
- **Python**: 3.8 or higher
- **pip**: Python package manager
- **Chrome**: Version 88+ (for extension)

### Optional
- **Ollama**: For local LLM (privacy-focused alternative)
- **npm**: Only for convenience scripts (completely optional)

## 🚫 What's NOT Used

- ❌ Node.js (not required)
- ❌ npm packages for extension (vanilla JS)
- ❌ React/Vue/Angular (pure JavaScript)
- ❌ Webpack/Babel/Vite (no build process)
- ❌ TypeScript (plain JavaScript)
- ❌ jQuery (native DOM APIs)
- ❌ Bootstrap (custom CSS)

## 📁 File Structure

```
project/
├── server/                      # Python Flask backend
│   ├── main.py                  # Flask orchestrator
│   ├── requirements.txt         # Python dependencies
│   ├── layers/                  # Cognitive layers (Python)
│   ├── prompts/                 # JSON prompts
│   └── data/                    # JSON data storage
│
├── extension/                   # Chrome extension
│   ├── popup.html               # Pure HTML
│   ├── popup.css                # Pure CSS
│   ├── popup.js                 # Vanilla JavaScript
│   ├── background.js            # Service worker (JS)
│   ├── content.js               # Content script (JS)
│   └── manifest.json            # Extension config
│
└── package.json                 # Optional convenience scripts

```

## 🛠️ Development Tools

### Required
1. **Python 3.8+**: Download from python.org
2. **pip**: Comes with Python
3. **Code Editor**: VS Code, PyCharm, or any editor
4. **Chrome Browser**: For testing extension

### Optional
1. **Git**: For version control
2. **Postman/Insomnia**: For API testing
3. **Python virtual environment**: For isolation
4. **Chrome DevTools**: For debugging

## 🚀 Quick Start Commands

### Option 1: Direct (Recommended)
```bash
# Install Python dependencies
cd server
pip install -r requirements.txt

# Start server
python main.py

# Load extension in Chrome
# Go to chrome://extensions/
# Enable Developer Mode
# Click "Load unpacked" → select 'extension' folder
```

### Option 2: With npm convenience scripts (Optional)
```bash
# Install (if you have npm installed)
npm run install

# Start server
npm run server
```

## 🔧 Configuration

### API Keys (Required for LLMs)

#### Gemini API Key
1. Visit: https://makersuite.google.com/app/apikey
2. Create an API key
3. Add to `server/config.py`:
   ```python
   GEMINI_API_KEY = "your-api-key-here"
   ```

#### Ollama (Optional - Local LLM)
1. Install: https://ollama.ai/
2. Pull model: `ollama pull llama2`
3. Verify: `ollama list`
4. Config in `server/config.py`:
   ```python
   OLLAMA_BASE_URL = "http://localhost:11434"
   OLLAMA_MODEL = "llama2"
   ```

## 📊 Why Vanilla JavaScript?

### Advantages
1. **Zero Build Time**: Instant development
2. **No Dependencies**: No npm packages to maintain
3. **Smaller Size**: ~50KB total (vs ~2MB+ with frameworks)
4. **Better Performance**: Native APIs are faster
5. **Easier Debugging**: No source maps needed
6. **Chrome Native**: Perfect for extensions
7. **Long-term Stability**: No framework updates needed

### Disadvantages (and why they don't matter here)
1. ❌ No JSX → ✅ We use templates in HTML
2. ❌ No state management → ✅ Simple state in class
3. ❌ Manual DOM updates → ✅ Straightforward for this scale
4. ❌ No hot reload → ✅ Chrome extension reload is instant

## 🧪 Testing

### Backend Testing
```bash
cd server
python -m pytest tests/
```

### Frontend Testing
1. Load extension in Chrome
2. Open DevTools (F12)
3. Check Console for errors
4. Test all features manually

### API Testing
```bash
# Health check
curl http://localhost:3002/health

# Test preferences
curl http://localhost:3002/api/preferences
```

## 📚 Learning Resources

### Python + Flask
- Flask Documentation: https://flask.palletsprojects.com/
- Python.org: https://www.python.org/

### Vanilla JavaScript
- MDN Web Docs: https://developer.mozilla.org/
- JavaScript.info: https://javascript.info/

### Chrome Extensions
- Chrome Extension Docs: https://developer.chrome.com/docs/extensions/

### LLMs
- Google Gemini: https://ai.google.dev/
- Ollama: https://ollama.ai/

## 💡 Tips

1. **Virtual Environment**: Use venv for Python isolation
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. **Chrome DevTools**: Essential for debugging
   - F12 to open
   - Inspect extension popup
   - Check Network tab for API calls

3. **Hot Reload**: Chrome extensions
   - Click reload button in chrome://extensions/
   - Or use "Reload" keyboard shortcut

4. **API Testing**: Test endpoints directly
   ```python
   import requests
   r = requests.get('http://localhost:3002/health')
   print(r.json())
   ```

## 🆘 Troubleshooting

### "npm command not found"
- **Solution**: npm is optional! Use Python commands directly
- Or install Node.js if you want convenience scripts

### "Module not found" (Python)
- **Solution**: Install requirements: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.8+)

### Extension won't load
- **Solution**: Check manifest.json is valid
- Make sure you selected the 'extension' folder
- Check Chrome console for errors

### LLM not responding
- **Solution**: Check API key in config.py
- Verify network connection
- Check server logs in `server/logs/`

## 🎓 Best Practices

1. **Python Virtual Environment**: Always use one
2. **API Keys**: Never commit to git (use .env)
3. **Chrome DevTools**: Use for debugging
4. **Server Logs**: Check for errors
5. **Preferences**: Save often in extension
6. **Backups**: Export important analyses

## 📈 Performance

### Current Metrics
- **Extension Size**: ~50KB
- **Load Time**: <100ms
- **API Response**: 1-5 seconds (LLM processing)
- **Memory Usage**: ~50MB (extension)
- **Server Memory**: ~200MB (Python + Flask)

### Optimization Tips
1. Use minimal verbosity for faster responses
2. Choose Ollama for local, faster processing
3. Cache common analyses
4. Batch process multiple documents

---

**Summary**: Simple Python backend + Vanilla JavaScript frontend = Fast, maintainable, and easy to understand! 🚀

