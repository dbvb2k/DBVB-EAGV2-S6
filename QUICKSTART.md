# Quick Start Guide - Law Case Finder

## ⚡ Get Started in 5 Minutes

### 1. Install Dependencies

```bash
# Install Python dependencies only
cd server
pip install -r requirements.txt
cd ..
```

**Note**: This project uses vanilla JavaScript for the Chrome extension - no Node.js or npm required!

**Optional npm scripts**: The root `package.json` is optional and only provides convenience commands:
```bash
npm run install  # Alternative to: cd server && pip install -r requirements.txt
npm run server   # Alternative to: cd server && python main.py
```

### 2. Configure API Keys

Edit `server/config.py`:

```python
class Config:
    # For Gemini (recommended)
    GEMINI_API_KEY = "your-gemini-api-key-here"
    GEMINI_MODEL = "gemini-2.0-flash-001"  # Correct model name
    
    # For Ollama (local alternative)
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_MODEL = "llama2"
    
    # Model priority
    PRIMARY_MODEL = 'gemini'  # or 'ollama'
    FALLBACK_MODEL = 'ollama'  # or 'gemini'
```

**Or create a `server/.env` file:**
```env
GEMINI_API_KEY=your-actual-api-key-here
GEMINI_MODEL=gemini-2.0-flash-001
PRIMARY_MODEL=gemini
FALLBACK_MODEL=ollama
```

### 3. Start the Server

```bash
cd server
python main.py
```

You should see:
```
🚀 Law Case Finder - 4-Layer Cognitive Architecture
📝 LLM interactions logged to: logs/llm_interactions_20251011_120000.log
🌐 Server running on: http://0.0.0.0:3002
🧠 Architecture: Perception → Memory → Decision → Action
```

### 4. Load the Chrome Extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension` folder from this project
5. Pin the extension to your toolbar

### 5. Configure Your Preferences

1. Click the Law Case Finder extension icon
2. Scroll down and click "⚙️ Settings" to expand
3. Configure your preferences:
   - **General**: Set language and verbosity level
   - **AI Model**: Choose Gemini or Ollama
   - **Citation**: Select format (Bluebook, APA, MLA, Chicago)
   - **Privacy**: Choose what to store
4. Click "💾 Save Preferences"

### 6. Analyze Your First Document

#### Option A: Upload a PDF
1. Click "📄 Upload File" tab
2. Drag and drop a legal PDF or click to browse
3. Wait for analysis (usually 10-30 seconds)
4. View extracted information with confidence scores

#### Option B: Paste Text
1. Click "📝 Paste Text" tab
2. Paste legal document text (min 100 characters)
3. Click "🔍 Analyze Text"
4. View extracted information

### 7. Generate a Brief

1. After document analysis, click "📝 Generate Brief"
2. Wait for brief generation (usually 15-45 seconds)
3. View the generated brief with:
   - Issue statement
   - Key facts
   - Court holding
   - Legal reasoning
   - Citations

### 8. Export or Start New Analysis

- **Export**: Use the export tab to download in various formats
- **New Analysis**: Click "← Upload New Document"

## 🎯 Common Use Cases

### Use Case 1: Quick Case Summary

**Goal**: Get a quick summary of a legal case

**Steps**:
1. Set verbosity to "Minimal" in Settings
2. Upload PDF or paste case text
3. Click "Generate Brief"
4. Get concise summary in 30 seconds

### Use Case 2: Detailed Legal Analysis

**Goal**: Deep analysis with all reasoning

**Steps**:
1. Set verbosity to "Detailed" in Settings
2. Enable "Auto-generate Brief"
3. Upload document
4. System automatically generates comprehensive brief

### Use Case 3: Citation Formatting

**Goal**: Convert citations to specific format

**Steps**:
1. Set citation format in Settings (e.g., "Bluebook")
2. Upload document with citations
3. System automatically normalizes all citations
4. View formatted citations in results

### Use Case 4: Multi-Language Analysis

**Goal**: Analyze documents in Spanish

**Steps**:
1. Set language to "Spanish" in Settings
2. Upload Spanish legal document
3. Get analysis in Spanish
4. Generate brief in Spanish

## 🧪 Testing the System

### Test 1: Preferences Persistence

1. Change all settings in the Settings panel
2. Click "Save Preferences"
3. Close and reopen the extension
4. Verify settings are remembered

### Test 2: Model Fallback

1. Set primary model to "Gemini"
2. Set fallback to "Ollama"
3. If Gemini is unavailable, system auto-switches to Ollama
4. Check console for "using fallback model" message

### Test 3: End-to-End Flow

1. Upload a PDF legal document
2. Verify extraction completes successfully
3. Generate brief
4. Check citations are normalized
5. Export to PDF/text

## 🐛 Troubleshooting

### Problem: Server Won't Start

**Solution**:
```bash
# Check if port 3002 is in use
netstat -an | grep 3002

# Kill process if needed
kill -9 $(lsof -t -i:3002)

# Or change port in config.py
```

### Problem: Extension Not Loading

**Solution**:
- Check Chrome console (F12) for errors
- Verify `manifest.json` is valid
- Try reloading extension in `chrome://extensions/`

### Problem: Preferences Not Saving

**Solution**:
- Check server logs for errors
- Verify `server/data/` directory exists:
  ```bash
  mkdir -p server/data/sessions
  ```
- Check browser console for API errors

### Problem: LLM Not Responding

**Solution**:
```bash
# Test Gemini API key
curl -H "Content-Type: application/json" \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=YOUR_API_KEY"

# Test Ollama (if using)
curl http://localhost:11434/api/tags
```

### Problem: Poor Extraction Quality

**Solution**:
- Increase verbosity level in Settings
- Try different LLM model
- Check document quality (OCR text may need cleanup)
- Edit prompts in `server/prompts/system_prompts.json`

## 📊 Monitor System Activity

### View Agent Console

1. Expand the "🖥️ Agent Console" at bottom of extension
2. See real-time agent activity:
   - Agent execution sequence
   - Success/failure status
   - Processing times
   - Model used

### Check Server Logs

```bash
# View latest log file
tail -f server/logs/llm_interactions_*.log

# Search for errors
grep ERROR server/logs/*.log

# Monitor in real-time
python -c "import time; [print(open('server/logs/' + sorted(os.listdir('server/logs'))[-1]).read()) or time.sleep(1) for _ in range(100)]"
```

## 🎓 Advanced Usage

### Custom Prompts

Edit `server/prompts/system_prompts.json`:

```json
{
  "legal_extraction": "Your custom extraction prompt here...",
  "brief_generation": "Your custom brief prompt here..."
}
```

Restart server to apply changes.

### API Integration

Use the REST API directly:

```python
import requests

# Analyze document
response = requests.post('http://localhost:3002/api/analyze-document', 
    json={'text': 'Your legal text here...'})
data = response.json()

# Generate brief
response = requests.post('http://localhost:3002/api/generate-brief',
    json={'extracted_data': data['data']})
brief = response.json()
```

### Batch Processing

```python
import glob
import requests

# Process all PDFs in a folder
for pdf_file in glob.glob('legal_docs/*.pdf'):
    with open(pdf_file, 'rb') as f:
        files = {'file': f}
        response = requests.post('http://localhost:3002/api/analyze-document', 
                               files=files)
        print(f"Processed: {pdf_file}")
```

## 🚀 Next Steps

1. Read [ARCHITECTURE.md](server/ARCHITECTURE.md) for deep dive
2. Explore [SETUP.md](SETUP.md) for advanced configuration
3. Customize prompts in `server/prompts/system_prompts.json`
4. Try different citation formats
5. Test with your own legal documents

## 💡 Tips

- **Faster Analysis**: Use "Minimal" verbosity for quick summaries
- **Better Quality**: Use "Detailed" verbosity + Gemini model
- **Privacy**: Disable document storage in Privacy Settings
- **Consistency**: Save preferences after configuration
- **Debugging**: Enable console logging for troubleshooting

## 📚 Additional Resources

- [Full Architecture Documentation](server/ARCHITECTURE.md)
- [Setup Guide](SETUP.md)
- [API Documentation](#) (Coming soon)
- [Prompt Engineering Guide](#) (Coming soon)

## 🆘 Getting Help

If you encounter issues:

1. Check troubleshooting section above
2. Review server logs in `server/logs/`
3. Check browser console (F12)
4. Verify API keys and configuration
5. Test with sample documents first

---

**Happy Legal Analysis! ⚖️**

