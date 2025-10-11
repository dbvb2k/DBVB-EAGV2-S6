# Law Case Finder - Setup Guide

This guide will help you set up and run the Law Case Finder Chrome extension with its Python backend server.

## Prerequisites

- **Python 3.8+** installed on your system
- **Node.js 16+** and npm installed
- **Google Chrome** browser
- **Git** (for cloning the repository)

## Quick Start

### 1. Install Dependencies

```bash
# Install all dependencies (backend and extension)
npm run install:all
```

Or install manually:

```bash
# Backend dependencies
cd server
pip install -r requirements.txt

# Extension dependencies  
cd ../extension
npm install

cd ..
```

### 2. Configure Environment Variables

Create a `.env` file in the `server/` directory:

```bash
# server/.env
GEMINI_API_KEY=your_gemini_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
FLASK_ENV=development
FLASK_DEBUG=True
PORT=3001
PRIMARY_MODEL=gemini
FALLBACK_MODEL=ollama
```

**Getting a Gemini API Key:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Create a new API key
4. Copy the key to your `.env` file

### 3. Start the Backend Server

```bash
# Start the Python FastAPI server
npm run server:dev

# Or manually:
cd server
python main.py
```

The server will start on `http://localhost:3001`

### 4. Build and Install Chrome Extension

```bash
# Extension is ready to load (no build needed)
npm run extension:build

# Or manually:
cd extension
npm run build
```

**Load Extension in Chrome:**
1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Select the `extension/public` folder
5. The extension icon should appear in your toolbar

### 5. Test the Setup

```bash
# Run the test script to verify everything works
python test_sample.py
```

## Detailed Setup Instructions

### Backend Server Setup

1. **Python Environment Setup:**
   ```bash
   # Create virtual environment (recommended)
   python -m venv law-case-finder-env
   
   # Activate virtual environment
   # Windows:
   law-case-finder-env\Scripts\activate
   # macOS/Linux:
   source law-case-finder-env/bin/activate
   
   # Install dependencies
   cd server
   pip install -r requirements.txt
   ```

2. **AI Model Configuration:**

   **Option A: Gemini (Cloud-based, Recommended)**
   - Get API key from Google AI Studio
   - Add to `.env` file
   - Set `PRIMARY_MODEL=gemini`

   **Option B: Ollama (Local, Privacy-focused)**
   - Install Ollama from [ollama.ai](https://ollama.ai)
   - Pull a model: `ollama pull llama2`
   - Start Ollama service
   - Set `PRIMARY_MODEL=ollama`

3. **Start Server:**
   ```bash
   # Development mode (with auto-reload)
   python app.py
   
   # Or using Flask CLI
   flask run --debug --port=3001
   ```

### Chrome Extension Setup

1. **Install Dependencies:**
   ```bash
   cd extension
   npm install
   ```

2. **Build Extension:**
   ```bash
   # Production build
   npm run build
   
   # Development build with watching
   npm run dev
   ```

3. **Load in Chrome:**
   - Navigate to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select `extension/build` folder

## Testing

### Automated Testing

```bash
# Test backend API endpoints
python test_sample.py
```

### Manual Testing

1. **Test Backend:**
   - Visit `http://localhost:3001/health`
   - Should return server status

2. **Test Extension:**
   - Click extension icon in Chrome
   - Upload a PDF or paste legal text
   - Verify analysis and brief generation

### Sample Legal Documents

Test with these types of documents:
- Court judgments and opinions
- Legal case documents
- Tribunal decisions
- Administrative rulings

## Troubleshooting

### Common Issues

**1. "Backend server not accessible"**
- Ensure Python server is running on port 3001
- Check firewall settings
- Verify no other service is using port 3001

**2. "No available AI models"**
- Check Gemini API key in `.env` file
- Verify Ollama is installed and running
- Check server logs for model loading errors

**3. "Extension not loading"**
- Ensure `extension/build` folder exists
- Check Chrome developer console for errors
- Verify manifest.json is valid

**4. "PDF processing failed"**
- Check file size (max 16MB)
- Ensure file is a valid PDF
- Try with a text file instead

**5. "CORS errors"**
- Backend includes CORS headers for Chrome extensions
- If issues persist, check browser console

### Debug Mode

Enable detailed logging:

1. **Backend Debug:**
   ```bash
   # Set debug mode in .env
   FLASK_DEBUG=True
   
   # Check server logs
   tail -f server.log
   ```

2. **Extension Debug:**
   - Open Chrome DevTools
   - Go to Extensions tab
   - Click "Inspect views: popup"

### Performance Issues

**Slow Analysis:**
- Check AI model response times
- Consider using Gemini for faster processing
- Reduce document size if very large

**Memory Issues:**
- Monitor Python memory usage
- Consider processing documents in chunks
- Restart server if memory usage is high

## Development

### Project Structure

```
law-case-finder/
├── server/                 # Python Flask backend
│   ├── agents/            # AI agents
│   ├── utils/             # Utilities
│   ├── app.py             # Main server
│   └── requirements.txt   # Python dependencies
├── extension/             # Chrome extension
│   ├── src/               # React source code
│   ├── public/            # Static files
│   └── build/             # Built extension
├── test_sample.py         # Test script
└── package.json           # Project configuration
```

### Making Changes

**Backend Changes:**
- Edit files in `server/`
- Server auto-reloads in debug mode
- Test with `python test_sample.py`

**Extension Changes:**
- Edit files in `extension/src/`
- Run `npm run build` to rebuild
- Reload extension in Chrome

### Adding New Features

1. **New AI Agent:**
   - Create in `server/agents/`
   - Add to main app.py
   - Create API endpoint

2. **New UI Component:**
   - Create in `extension/src/components/`
   - Import in App.tsx
   - Update types.ts if needed

## Production Deployment

### Backend Deployment

**Using Docker:**
```dockerfile
# Dockerfile (create in server/)
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:3001", "app:app"]
```

**Using Cloud Services:**
- Deploy to Heroku, AWS, Google Cloud, etc.
- Update extension API URLs
- Configure environment variables

### Extension Distribution

**Chrome Web Store:**
1. Create developer account
2. Package extension
3. Submit for review
4. Publish when approved

**Enterprise Distribution:**
- Use Chrome Enterprise policies
- Deploy via Group Policy
- Manage through Admin Console

## Security Considerations

- **API Keys:** Never commit API keys to version control
- **HTTPS:** Use HTTPS in production
- **Input Validation:** Backend validates all inputs
- **File Uploads:** Scanned for malicious content
- **Privacy:** Documents not stored permanently without consent

## Legal Disclaimer

This tool is for educational and research purposes only. It does not constitute legal advice and should not be relied upon for legal decisions. Always consult with qualified legal professionals for legal matters.

## Support

For issues and questions:
1. Check this setup guide
2. Review troubleshooting section
3. Check project documentation
4. Create an issue on the project repository

## License

MIT License - see LICENSE file for details
