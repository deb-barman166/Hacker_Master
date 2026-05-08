"""
core/config.py — Configuration management for Kali Terminal v2.0 Masterpiece.

Handles loading, saving, and accessing configuration settings.
"""

import os
import json
from pathlib import Path


# Default configuration
DEFAULT_CONFIG = {
    "theme": "kali",
    "prompt_style": "kali",
    "show_banner": True,
    "show_tips": True,
    "auto_suggest": True,
    "complete_while_typing": True,
    "mouse_support": False,
    "history_duplicates": "ignore",
    "prompt_max_path": 40,
    "log_commands": False,
    "ai_backend": "none",
    "ai_model": "",
    "startup_commands": [],
    "color_scheme": "default",
}


# Config file location
CONFIG_DIR = Path.home() / ".config" / "kali_terminal"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history"
LOG_FILE = CONFIG_DIR / "commands.log"
SESSIONS_DIR = CONFIG_DIR / "sessions"


class Config:
    """Configuration manager with JSON persistence."""

    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.data = DEFAULT_CONFIG.copy()
        self._load()

    def _load(self):
        """Load configuration from file."""
        if self.config_path and os.path.isfile(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
                    return
            except Exception as e:
                print(f"Warning: Could not load config: {e}")

        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception:
                pass

    def save(self):
        """Save configuration to file."""
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")

    def get(self, key: str, default=None):
        """Get a configuration value."""
        return self.data.get(key, default)

    def set(self, key: str, value):
        """Set a configuration value."""
        self.data[key] = value

    @property
    def theme(self):
        """Get current theme."""
        return self.data.get("theme", "kali")

    @theme.setter
    def theme(self, value):
        """Set current theme."""
        self.data["theme"] = value

    def reset(self):
        """Reset to default configuration."""
        self.data = DEFAULT_CONFIG.copy()
        self.save()


# Global config instance
_config = None


def get_config(config_path: str = None) -> Config:
    """Get or create the global configuration instance."""
    global _config
    if _config is None or config_path:
        _config = Config(config_path)
    return _config


# Initialize directories
def init_dirs():
    """Initialize required directories."""
    for directory in [CONFIG_DIR, SESSIONS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


init_dirs()