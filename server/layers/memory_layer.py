"""
Memory Layer - User Preferences and Context Management

This layer handles storage and retrieval of user preferences,
session context, and analysis history.
"""

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path


class MemoryLayer:
    """
    Memory Layer handles user preferences, session state, and context management
    """
    
    # Default preferences structure
    DEFAULT_PREFERENCES = {
        "general": {
            "output_format": "plain_text",  # plain_text, pdf, markdown
            "language": "en",  # en, es, fr, de, etc.
            "verbosity_level": "standard",  # minimal, standard, detailed
            "auto_generate_brief": False,
            "save_analysis_history": True
        },
        "llm": {
            "primary_model": "gemini",  # gemini, ollama
            "fallback_model": "ollama",
            "temperature": 0.7,
            "max_tokens": 8192,
            "enable_fallback": True
        },
        "citation": {
            "format": "bluebook",  # bluebook, apa, mla, chicago
            "include_citations_in_brief": True,
            "normalize_citations": True
        },
        "integration": {
            "legal_apis": {
                "courtlistener_enabled": False,
                "courtlistener_api_key": "",
                "caselaw_access_enabled": False,
                "caselaw_access_api_key": ""
            },
            "export_destinations": {
                "local_download": True,
                "google_drive": False,
                "dropbox": False
            }
        },
        "privacy": {
            "store_documents": False,
            "store_analysis_results": True,
            "anonymize_data": False
        }
    }
    
    def __init__(self, storage_path: str = "server/data"):
        """
        Initialize Memory Layer
        
        Args:
            storage_path: Path to store user data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.preferences_file = self.storage_path / "user_preferences.json"
        self.sessions_dir = self.storage_path / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize preferences
        self.preferences = self._load_preferences()
        
        # Current session context
        self.current_session = {
            "session_id": self._generate_session_id(),
            "started_at": datetime.now().isoformat(),
            "context": {},
            "history": []
        }
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
    
    def _load_preferences(self) -> Dict[str, Any]:
        """Load user preferences from file"""
        if self.preferences_file.exists():
            try:
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    loaded_prefs = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_preferences(self.DEFAULT_PREFERENCES.copy(), loaded_prefs)
            except Exception as e:
                print(f"Error loading preferences: {e}")
                return self.DEFAULT_PREFERENCES.copy()
        else:
            # Create default preferences file
            self._save_preferences(self.DEFAULT_PREFERENCES)
            return self.DEFAULT_PREFERENCES.copy()
    
    def _merge_preferences(self, defaults: Dict, loaded: Dict) -> Dict:
        """Recursively merge loaded preferences with defaults"""
        for key, value in loaded.items():
            if key in defaults:
                if isinstance(value, dict) and isinstance(defaults[key], dict):
                    defaults[key] = self._merge_preferences(defaults[key], value)
                else:
                    defaults[key] = value
        return defaults
    
    def _save_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Save preferences to file"""
        try:
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving preferences: {e}")
            return False
    
    def get_preferences(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user preferences
        
        Args:
            category: Optional category to filter (general, llm, citation, integration, privacy)
            
        Returns:
            Preferences dict or category dict
        """
        if category:
            return self.preferences.get(category, {})
        return self.preferences.copy()
    
    def update_preferences(
        self,
        category: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update user preferences
        
        Args:
            category: Category to update (general, llm, citation, integration, privacy)
            updates: Dictionary of updates to apply
            
        Returns:
            Updated preferences dict with success status
        """
        try:
            if category not in self.preferences:
                return {
                    'success': False,
                    'error': f'Invalid category: {category}'
                }
            
            # Update preferences
            if isinstance(self.preferences[category], dict):
                self.preferences[category].update(updates)
            else:
                self.preferences[category] = updates
            
            # Save to file
            if self._save_preferences(self.preferences):
                return {
                    'success': True,
                    'preferences': self.preferences[category]
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to save preferences'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error updating preferences: {str(e)}'
            }
    
    def reset_preferences(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Reset preferences to defaults
        
        Args:
            category: Optional category to reset, or None to reset all
            
        Returns:
            Result dict with success status
        """
        try:
            if category:
                if category in self.DEFAULT_PREFERENCES:
                    self.preferences[category] = self.DEFAULT_PREFERENCES[category].copy()
                else:
                    return {
                        'success': False,
                        'error': f'Invalid category: {category}'
                    }
            else:
                self.preferences = self.DEFAULT_PREFERENCES.copy()
            
            if self._save_preferences(self.preferences):
                return {
                    'success': True,
                    'preferences': self.preferences
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to save preferences'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error resetting preferences: {str(e)}'
            }
    
    def get_session_context(self) -> Dict[str, Any]:
        """Get current session context"""
        return self.current_session['context'].copy()
    
    def update_session_context(self, updates: Dict[str, Any]) -> None:
        """
        Update current session context
        
        Args:
            updates: Dictionary of context updates
        """
        self.current_session['context'].update(updates)
    
    def add_to_session_history(self, event: Dict[str, Any]) -> None:
        """
        Add an event to session history
        
        Args:
            event: Event dictionary with type, data, timestamp
        """
        event['timestamp'] = datetime.now().isoformat()
        self.current_session['history'].append(event)
    
    def get_session_history(self) -> List[Dict[str, Any]]:
        """Get current session history"""
        return self.current_session['history'].copy()
    
    def save_session(self) -> bool:
        """Save current session to file"""
        try:
            session_file = self.sessions_dir / f"{self.current_session['session_id']}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_session, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving session: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a previous session
        
        Args:
            session_id: Session ID to load
            
        Returns:
            Session dict or None if not found
        """
        try:
            session_file = self.sessions_dir / f"{session_id}.json"
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"Error loading session: {e}")
            return None
    
    def list_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent sessions
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of session metadata
        """
        try:
            sessions = []
            session_files = sorted(
                self.sessions_dir.glob("session_*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            for session_file in session_files[:limit]:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                    sessions.append({
                        'session_id': session_data.get('session_id'),
                        'started_at': session_data.get('started_at'),
                        'history_count': len(session_data.get('history', []))
                    })
            
            return sessions
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []
    
    def clear_session(self) -> None:
        """Clear current session and start new one"""
        self.current_session = {
            "session_id": self._generate_session_id(),
            "started_at": datetime.now().isoformat(),
            "context": {},
            "history": []
        }
    
    def get_preference_schema(self) -> Dict[str, Any]:
        """Get the schema/structure of preferences for UI generation"""
        return {
            "general": {
                "label": "General Settings",
                "icon": "⚙️",
                "fields": {
                    "output_format": {
                        "label": "Output Format",
                        "type": "select",
                        "options": ["plain_text", "pdf", "markdown"],
                        "default": "plain_text"
                    },
                    "language": {
                        "label": "Language",
                        "type": "select",
                        "options": ["en", "es", "fr", "de", "pt", "zh", "ja"],
                        "default": "en"
                    },
                    "verbosity_level": {
                        "label": "Verbosity Level",
                        "type": "select",
                        "options": ["minimal", "standard", "detailed"],
                        "default": "standard"
                    },
                    "auto_generate_brief": {
                        "label": "Auto-generate Brief",
                        "type": "boolean",
                        "default": False
                    },
                    "save_analysis_history": {
                        "label": "Save Analysis History",
                        "type": "boolean",
                        "default": True
                    }
                }
            },
            "llm": {
                "label": "AI Model Settings",
                "icon": "🤖",
                "fields": {
                    "primary_model": {
                        "label": "Primary Model",
                        "type": "select",
                        "options": ["gemini", "ollama"],
                        "default": "gemini"
                    },
                    "fallback_model": {
                        "label": "Fallback Model",
                        "type": "select",
                        "options": ["ollama", "gemini"],
                        "default": "ollama"
                    },
                    "temperature": {
                        "label": "Temperature",
                        "type": "number",
                        "min": 0.0,
                        "max": 2.0,
                        "step": 0.1,
                        "default": 0.7
                    },
                    "enable_fallback": {
                        "label": "Enable Fallback Model",
                        "type": "boolean",
                        "default": True
                    }
                }
            },
            "citation": {
                "label": "Citation Settings",
                "icon": "📚",
                "fields": {
                    "format": {
                        "label": "Citation Format",
                        "type": "select",
                        "options": ["bluebook", "apa", "mla", "chicago"],
                        "default": "bluebook"
                    },
                    "include_citations_in_brief": {
                        "label": "Include Citations in Brief",
                        "type": "boolean",
                        "default": True
                    },
                    "normalize_citations": {
                        "label": "Normalize Citations",
                        "type": "boolean",
                        "default": True
                    }
                }
            },
            "integration": {
                "label": "Integration Settings",
                "icon": "🔗",
                "fields": {
                    "legal_apis": {
                        "label": "Legal API Integrations",
                        "type": "object",
                        "fields": {
                            "courtlistener_enabled": {
                                "label": "Enable CourtListener API",
                                "type": "boolean",
                                "default": False
                            },
                            "caselaw_access_enabled": {
                                "label": "Enable Caselaw Access API",
                                "type": "boolean",
                                "default": False
                            }
                        }
                    }
                }
            },
            "privacy": {
                "label": "Privacy Settings",
                "icon": "🔒",
                "fields": {
                    "store_documents": {
                        "label": "Store Uploaded Documents",
                        "type": "boolean",
                        "default": False
                    },
                    "store_analysis_results": {
                        "label": "Store Analysis Results",
                        "type": "boolean",
                        "default": True
                    },
                    "anonymize_data": {
                        "label": "Anonymize Stored Data",
                        "type": "boolean",
                        "default": False
                    }
                }
            }
        }

