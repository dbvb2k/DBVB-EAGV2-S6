# Troubleshooting Guide - Law Case Finder

## 🔥 Common Issues and Solutions

### Issue 1: "No LLM models available" Error

**Symptoms:**
```
'error': 'LLM processing failed: No LLM models available'
```

**Causes & Solutions:**

#### A. Wrong Gemini Model Name ⭐ MOST COMMON
**Problem:** Using incorrect model name like `gemini-2.0-flash-002` or `gemini-2.0-flash-exp`

**Solution:**
Update your `server/.env` file:
```env
# WRONG ❌
GEMINI_MODEL=gemini-2.0-flash-002
GEMINI_MODEL=gemini-2.0-flash-exp

# CORRECT ✅
GEMINI_MODEL=gemini-2.0-flash-001
# OR use stable version
GEMINI_MODEL=gemini-1.5-flash
```

**Valid Gemini Model Names (as of Oct 2024):**
- `gemini-2.0-flash-001` ← Recommended (newest, fast)
- `gemini-1.5-flash` ← Stable alternative
- `gemini-1.5-pro` ← More powerful, slower
- `gemini-1.0-pro` ← Older, still works

**How to verify:**
```bash
# Test your API key and model name
curl -H 'Content-Type: application/json' \
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}' \
  "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-001:generateContent?key=YOUR_API_KEY"
```

#### B. API Key Not Loaded
**Problem:** `.env` file not being read

**Solution:**
1. Ensure `.env` is in `server/` directory
2. Verify file contains:
   ```env
   GEMINI_API_KEY=AIza...your-actual-key
   ```
3. Restart server to reload config
4. Check startup output for: `Config - API Key Present: YES`

#### C. Server Running Old Code
**Problem:** Server cached old configuration

**Solution:**
1. Stop server completely (Ctrl+C)
2. Wait 2 seconds
3. Restart: `python main.py`
4. Verify you see: `✓ Available models: Gemini, Ollama`

---

### Issue 2: Windows Color Encoding Errors

**Symptoms:**
```
UnicodeEncodeError: 'charmap' codec can't encode character
```

**Solution:**
Already fixed in latest `test_agents.py` with:
```python
# Enable ANSI escape sequences in Windows console
kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
```

If still having issues, run in PowerShell or use Windows Terminal instead of CMD.

---

### Issue 3: Preferences Not Saving

**Symptoms:**
- Settings reset after browser reload
- Error when clicking "Save Preferences"

**Solutions:**

#### A. Server Not Running
Ensure Flask server is running on port 3002

#### B. CORS Issues
Check browser console (F12). If you see CORS errors, verify in `server/main.py`:
```python
CORS(app, origins=["chrome-extension://*", "http://localhost:*"])
```

#### C. Data Directory Missing
```bash
mkdir -p server/data/sessions
```

---

### Issue 4: Extension Not Loading in Chrome

**Symptoms:**
- Can't find extension in Chrome
- Extension shows errors

**Solutions:**

#### A. Wrong Folder Selected
- Go to `chrome://extensions/`
- Click "Load unpacked"
- Select the `extension` folder (NOT `extension/public`)

#### B. Manifest Errors
Check browser console for manifest errors. Verify `extension/manifest.json` is valid JSON.

#### C. Permissions
Ensure manifest has:
```json
"permissions": ["activeTab", "storage", "scripting"],
"host_permissions": ["http://localhost:3002/*"]
```

---

### Issue 5: PDF Upload Not Working

**Symptoms:**
- PDF uploads fail
- "File processing failed" error

**Solutions:**

#### A. Missing Dependencies
```bash
pip install PyPDF2 pdfplumber
```

#### B. Large File Size
Default limit is 16MB. Edit `server/config.py`:
```python
MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB
```

#### C. Corrupted PDF
Try with a different PDF or use text paste instead.

---

### Issue 6: Ollama Not Available

**Symptoms:**
```
⚠ Ollama is not available
```

**Solutions:**

#### A. Ollama Not Running
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start Ollama
ollama serve
```

#### B. Wrong Port
Update `server/.env`:
```env
OLLAMA_BASE_URL=http://localhost:11434
```

#### C. Model Not Pulled
```bash
# Pull the model
ollama pull llama2

# Verify
ollama list
```

---

### Issue 7: Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'layers'
ImportError: cannot import name 'PerceptionLayer'
```

**Solutions:**

#### A. Running from Wrong Directory
```bash
# Must run from project root or server directory
cd server
python main.py
```

#### B. Missing __init__.py
Verify `server/layers/__init__.py` exists

#### C. Python Path Issues
```bash
# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/server"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;%cd%\server  # Windows CMD
```

---

### Issue 8: Prompt Loading Errors

**Symptoms:**
```
Prompt key 'legal_extraction' not found
```

**Solutions:**

#### A. Missing Prompts File
Verify file exists:
```bash
ls server/prompts/system_prompts.json
```

#### B. Invalid JSON
Validate JSON syntax:
```bash
python -c "import json; json.load(open('server/prompts/system_prompts.json'))"
```

#### C. Missing Prompt Keys
Check file contains required prompts:
- `legal_extraction`
- `brief_generation`
- `orchestration`

---

### Issue 9: Tests Failing

**Symptoms:**
```
❌ ACTION Layer: FAILED
```

**Solutions:**

#### A. Server Not Running
Start server first:
```bash
cd server
python main.py
```

#### B. Wrong Port
Update `test_agents.py`:
```python
self.base_url = "http://localhost:3002"  # Match server port
```

#### C. Firewall Blocking
Allow Python through Windows Firewall

---

### Issue 10: Slow Performance

**Symptoms:**
- Extraction takes > 30 seconds
- Brief generation very slow

**Solutions:**

#### A. Use Faster Model
In preferences, set:
- Model: Gemini (faster than Ollama)
- Verbosity: Minimal

#### B. Reduce Temperature
Lower temperature = faster, more deterministic:
```env
# In preferences or .env
TEMPERATURE=0.1
```

#### C. Local Ollama
For privacy + speed, use Ollama with a smaller model:
```bash
ollama pull phi  # Smaller, faster model
```

---

## 🔍 Debugging Tools

### 1. Diagnostic Script
```bash
python diagnose_server.py
```
Checks all system components.

### 2. Server Logs
```bash
# View latest log
ls -lt server/logs/*.log | head -1

# Monitor in real-time
tail -f server/logs/llm_interactions_*.log
```

### 3. Test Individual Layers
```bash
cd server
python -c "
from layers import PerceptionLayer, MemoryLayer
from config import Config
import json

# Load prompts
with open('prompts/system_prompts.json') as f:
    prompts = json.load(f)

# Test Perception
perception = PerceptionLayer(Config(), prompts)
print('Gemini:', perception.gemini_model)
print('Ollama:', perception.ollama_available)

# Test Memory
memory = MemoryLayer()
print('Preferences:', memory.get_preferences('general'))
"
```

### 4. Test API Endpoints
```bash
# Health check
curl http://localhost:3002/health

# Get preferences
curl http://localhost:3002/api/preferences

# Test extraction
curl -X POST http://localhost:3002/api/analyze-document \
  -H "Content-Type: application/json" \
  -d '{"text":"Your legal text here..."}'
```

---

## 📞 Getting Help

If issues persist after trying solutions above:

1. **Check server startup output** - Look for ERROR or WARNING messages
2. **Review server logs** - Check `server/logs/` for detailed errors
3. **Browser console** - F12 in Chrome, check for JavaScript errors
4. **Run diagnostic** - `python diagnose_server.py`
5. **Verify API key** - Test with curl command above

---

## 💡 Pro Tips

1. **Always restart server** after config changes
2. **Check server terminal** for real-time error messages
3. **Use diagnostic script** before asking for help
4. **Test with sample text** before uploading PDFs
5. **Check LLM model names** - they change frequently!

---

## 📋 Quick Checklist

When something doesn't work, check:

- [ ] Server is running (`python server/main.py`)
- [ ] API key is configured in `server/.env`
- [ ] Model name is correct (`gemini-2.0-flash-001`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Extension loaded in Chrome
- [ ] Port 3002 is not blocked
- [ ] `server/prompts/system_prompts.json` exists
- [ ] `server/data/` directory exists

---

**Most issues are solved by restarting the server or fixing the model name!** 🚀

