"""
core/session_manager.py — Session management for Kali Terminal v2.0 Masterpiece.
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime


class Session:
    """Represents a saved terminal session."""

    def __init__(self, name: str, cwd: str, history: list, env_vars: dict, aliases: dict, timestamp: float = None):
        self.name = name
        self.cwd = cwd
        self.history = history
        self.env_vars = env_vars
        self.aliases = aliases
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> dict:
        """Convert session to dictionary."""
        return {
            "name": self.name,
            "cwd": self.cwd,
            "history": self.history,
            "env_vars": self.env_vars,
            "aliases": self.aliases,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Create session from dictionary."""
        return cls(
            name=data["name"],
            cwd=data["cwd"],
            history=data["history"],
            env_vars=data.get("env_vars", {}),
            aliases=data.get("aliases", {}),
            timestamp=data.get("timestamp", time.time()),
        )


class SessionManager:
    """Manages terminal session saving and loading."""

    def __init__(self, terminal):
        self.terminal = terminal
        self.sessions_dir = Path.home() / ".config" / "kali_terminal" / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def save_session(self, name: str = None) -> bool:
        """Save current session."""
        if not name:
            name = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        session = Session(
            name=name,
            cwd=self.terminal.state["cwd"],
            history=self.terminal.state["history"],
            env_vars=self.terminal.state["env_vars"],
            aliases=self.terminal.aliases.aliases,
        )

        try:
            filepath = self.sessions_dir / f"{name}.json"
            with open(filepath, "w") as f:
                json.dump(session.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save session: {e}")
            return False

    def load_session(self, name: str) -> bool:
        """Load a saved session."""
        try:
            filepath = self.sessions_dir / f"{name}.json"
            if not filepath.exists():
                print(f"Session not found: {name}")
                return False

            with open(filepath, "r") as f:
                data = json.load(f)

            session = Session.from_dict(data)

            # Restore session state
            self.terminal.state["cwd"] = session.cwd
            self.terminal.state["history"] = session.history
            self.terminal.state["env_vars"] = session.env_vars
            self.terminal.aliases.aliases = session.aliases

            try:
                os.chdir(session.cwd)
            except:
                pass

            return True

        except Exception as e:
            print(f"Failed to load session: {e}")
            return False

    def list_sessions(self) -> list:
        """List all saved sessions."""
        sessions = []
        for filepath in self.sessions_dir.glob("*.json"):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                sessions.append({
                    "name": data["name"],
                    "cwd": data["cwd"],
                    "history_count": len(data.get("history", [])),
                    "timestamp": data.get("timestamp", 0),
                })
            except:
                pass

        return sorted(sessions, key=lambda s: s["timestamp"], reverse=True)

    def delete_session(self, name: str) -> bool:
        """Delete a saved session."""
        filepath = self.sessions_dir / f"{name}.json"
        if filepath.exists():
            filepath.unlink()
            return True
        return False