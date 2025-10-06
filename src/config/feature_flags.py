"""
Backend feature flags configuration system.
Allows runtime control of UI features and functionality.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from threading import Lock

from .logging import get_logger

logger = get_logger(__name__)


class FeatureFlags:
    """
    Manages feature flags for the application.
    Features can be toggled at runtime and persist across sessions.
    """
    
    # Default feature flag values
    DEFAULT_FLAGS = {
        # Sidebar Features
        "SHOW_RELATED_DOCUMENTS": False,       # Shows related documents from search results
        "SHOW_PERSONALIZED_QUESTIONS": False,  # Shows personalized question generator
        "SHOW_GENERAL_TOPICS": False,          # Shows general topic exploration buttons
        
        # Core Features
        "SHOW_SESSION_WINDOW": True,           # Shows session ID and clear button
        "SHOW_LANGUAGE_SELECTOR": True,        # Shows language dropdown in UI
        "SHOW_FEATURE_TOGGLE_PANEL": True,     # Shows admin feature toggle panel
        
        # Advanced Features
        "ENABLE_LANGUAGE_DETECTION": True,     # Auto-detect query language
        "ENABLE_MULTILINGUAL_RESPONSES": True, # Respond in detected language
        "ENABLE_WEB_SEARCH": False,           # Enable web search capabilities
        "ENABLE_ADVANCED_ANALYTICS": False,    # Enable usage analytics
        
        # Debug Features
        "SHOW_DEBUG_INFO": False,              # Show debug information in UI
        "ENABLE_VERBOSE_LOGGING": False,       # Enable verbose API logging
    }
    
    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize feature flags.
        
        Args:
            config_file: Optional path to persistent config file
        """
        self._lock = Lock()
        self._flags = self.DEFAULT_FLAGS.copy()
        
        # Set config file path
        if config_file:
            self.config_file = config_file
        else:
            # Default to data directory
            from .settings import settings
            self.config_file = settings.DATA_DIR / "feature_flags.json"
        
        # Load saved configuration if exists
        self._load_config()
    
    def _load_config(self):
        """Load feature flags from persistent storage."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    saved_flags = json.load(f)
                    # Merge with defaults (in case new flags were added)
                    for key, value in saved_flags.items():
                        if key in self._flags:
                            self._flags[key] = value
                logger.info(f"Loaded feature flags from {self.config_file}")
            else:
                # If no config exists, try to copy from default config in repo
                default_config = Path(__file__).parent / "default_feature_flags.json"
                if default_config.exists():
                    # Ensure directory exists
                    self.config_file.parent.mkdir(parents=True, exist_ok=True)
                    # Copy default config
                    with open(default_config, 'r') as src:
                        default_flags = json.load(src)
                        for key, value in default_flags.items():
                            if key in self._flags:
                                self._flags[key] = value
                    # Save to persistent location
                    self._save_config()
                    logger.info(f"Initialized feature flags from default config")
                else:
                    logger.info(f"No saved config found, using hardcoded defaults")
        except Exception as e:
            logger.error(f"Failed to load feature flags: {e}")
    
    def _save_config(self):
        """Save current feature flags to persistent storage."""
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self._flags, f, indent=2)
            logger.info(f"Saved feature flags to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save feature flags: {e}")
    
    def get(self, flag_name: str, default: Any = None) -> Any:
        """
        Get a feature flag value.
        
        Args:
            flag_name: Name of the feature flag
            default: Default value if flag doesn't exist
            
        Returns:
            Feature flag value
        """
        with self._lock:
            return self._flags.get(flag_name, default)
    
    def set(self, flag_name: str, value: Any) -> bool:
        """
        Set a feature flag value.
        
        Args:
            flag_name: Name of the feature flag
            value: New value for the flag
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if flag_name in self._flags:
                old_value = self._flags[flag_name]
                self._flags[flag_name] = value
                logger.info(f"Feature flag '{flag_name}' changed from {old_value} to {value}")
                self._save_config()
                return True
            else:
                logger.warning(f"Attempted to set unknown feature flag: {flag_name}")
                return False
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all feature flags.
        
        Returns:
            Dictionary of all feature flags
        """
        with self._lock:
            return self._flags.copy()
    
    def update_multiple(self, updates: Dict[str, Any]) -> Dict[str, bool]:
        """
        Update multiple feature flags at once.
        
        Args:
            updates: Dictionary of flag updates
            
        Returns:
            Dictionary of update results (flag_name -> success)
        """
        results = {}
        with self._lock:
            for flag_name, value in updates.items():
                if flag_name in self._flags:
                    self._flags[flag_name] = value
                    results[flag_name] = True
                    logger.info(f"Updated feature flag '{flag_name}' to {value}")
                else:
                    results[flag_name] = False
                    logger.warning(f"Unknown feature flag: {flag_name}")
            
            # Save once after all updates
            if any(results.values()):
                self._save_config()
        
        return results
    
    def reset_to_defaults(self):
        """Reset all feature flags to default values."""
        with self._lock:
            self._flags = self.DEFAULT_FLAGS.copy()
            self._save_config()
            logger.info("Reset all feature flags to defaults")
    
    def is_sidebar_enabled(self) -> bool:
        """Check if any sidebar feature is enabled."""
        return (
            self.get("SHOW_RELATED_DOCUMENTS", False) or
            self.get("SHOW_PERSONALIZED_QUESTIONS", False) or
            self.get("SHOW_GENERAL_TOPICS", False)
        )
    
    def get_frontend_config(self) -> Dict[str, Any]:
        """
        Get feature configuration for frontend.
        Includes metadata about each feature.
        
        Returns:
            Feature configuration with metadata
        """
        # Feature metadata for UI
        feature_metadata = {
            "SHOW_RELATED_DOCUMENTS": {
                "label": "Related Documents",
                "description": "Show related documents in sidebar",
                "category": "sidebar",
                "requiresRestart": False
            },
            "SHOW_PERSONALIZED_QUESTIONS": {
                "label": "Personalized Questions",
                "description": "Show personalized question generator",
                "category": "sidebar",
                "requiresRestart": False
            },
            "SHOW_GENERAL_TOPICS": {
                "label": "General Topics",
                "description": "Show general topic exploration",
                "category": "sidebar",
                "requiresRestart": False
            },
            "SHOW_SESSION_WINDOW": {
                "label": "Session Window",
                "description": "Show session ID and controls",
                "category": "core",
                "requiresRestart": False
            },
            "SHOW_FEATURE_TOGGLE_PANEL": {
                "label": "Feature Toggle Panel",
                "description": "Show admin feature control panel",
                "category": "admin",
                "requiresRestart": False
            },
            "ENABLE_LANGUAGE_DETECTION": {
                "label": "Auto Language Detection",
                "description": "Automatically detect query language",
                "category": "language",
                "requiresRestart": False
            },
            "ENABLE_MULTILINGUAL_RESPONSES": {
                "label": "Multilingual Responses",
                "description": "Respond in user's language",
                "category": "language",
                "requiresRestart": False
            },
            "ENABLE_WEB_SEARCH": {
                "label": "Web Search",
                "description": "Enable web search capabilities",
                "category": "advanced",
                "requiresRestart": True
            },
            "ENABLE_ADVANCED_ANALYTICS": {
                "label": "Advanced Analytics",
                "description": "Track usage analytics",
                "category": "advanced",
                "requiresRestart": True
            },
            "SHOW_DEBUG_INFO": {
                "label": "Debug Info",
                "description": "Show debug information in UI",
                "category": "debug",
                "requiresRestart": False
            },
            "ENABLE_VERBOSE_LOGGING": {
                "label": "Verbose Logging",
                "description": "Enable detailed API logging",
                "category": "debug",
                "requiresRestart": False
            }
        }
        
        # Build configuration with current values and metadata
        config = {}
        for flag_name, metadata in feature_metadata.items():
            config[flag_name] = {
                **metadata,
                "value": self.get(flag_name, False),
                "default": self.DEFAULT_FLAGS.get(flag_name, False)
            }
        
        return {
            "flags": config,
            "categories": {
                "sidebar": "Sidebar Features",
                "core": "Core Features",
                "admin": "Admin Features",
                "language": "Language Features",
                "advanced": "Advanced Features",
                "debug": "Debug Features"
            }
        }


# Global feature flags instance
feature_flags = FeatureFlags()