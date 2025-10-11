import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    
    # Server Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    PORT = int(os.getenv('PORT', 3001))
    
    # AI Model Configuration
    PRIMARY_MODEL = os.getenv('PRIMARY_MODEL', 'gemini')
    FALLBACK_MODEL = os.getenv('FALLBACK_MODEL', 'ollama')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.0-flash')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama2')
    
    # Legal Database Configuration
    ENABLE_CASE_RETRIEVAL = os.getenv('ENABLE_CASE_RETRIEVAL', 'false').lower() == 'true'
    LEGAL_DB_URL = os.getenv('LEGAL_DB_URL', '')
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'static/uploads'
    ALLOWED_EXTENSIONS = {'pdf', 'txt'}
