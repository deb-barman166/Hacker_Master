"""
utils/config.py — Persistent configuration manager for KaliTerminal v2.

Stores everything in ~/.kali_terminal_v2/ as JSON files:
  prefs.json    — user preferences (theme, AI mode, api keys, etc.)
  aliases.json  — custom command aliases
  bookmarks.json— named directory shortcuts
  notes.json    — quick notes
  todos.json    — to-do list
  history.json  — command history (backup)
"""

import os
import json
import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
CONFIG_DIR    = Path.home() / ".kali_terminal_v2"
PREFS_FILE    = CONFIG_DIR / "prefs.json"
ALIAS_FILE    = CONFIG_DIR / "aliases.json"
BOOKMARK_FILE = CONFIG_DIR / "bookmarks.json"
NOTES_FILE    = CONFIG_DIR / "notes.json"
TODO_FILE     = CONFIG_DIR / "todos.json"
HIST_FILE     = Path.home() / ".kali_v2_history"

# ── Default preferences ────────────────────────────────────────────────────────
DEFAULT_PREFS = {
    # UI
    "theme":               "kali",
    "show_git":            True,
    "show_venv":           True,
    "show_time_prompt":    False,
    "show_exit_code":      True,
    "vi_mode":             False,
    "mouse_support":       False,
    "complete_while_type": True,
    # AI
    "ai_enabled":          False,
    "ai_mode":             "off",        # "off" | "local" | "cloud"
    "ai_local_url":        "http://localhost:11434",
    "ai_local_model":      "llama3.2",
    "ai_cloud_provider":   "anthropic",  # anthropic|openai|gemini|groq|mistral|cohere
    "ai_cloud_model":      "",           # auto-selected per provider
    # API Keys (stored locally, never sent anywhere except chosen provider)
    "anthropic_key":       "",
    "openai_key":          "",
    "gemini_key":          "",
    "groq_key":            "",
    "mistral_key":         "",
    "cohere_key":          "",
    # Session
    "welcome_tips":        True,
    "fast_banner":         False,
    "recording":           False,
    "record_file":         "",
    # Security
    "safe_mode":           False,        # warn before dangerous ops
}

# ── Internal helpers ───────────────────────────────────────────────────────────

def _ensure():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _load(path: Path, default):
    try:
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return default


def _save(path: Path, data) -> bool:
    _ensure()
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except OSError:
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  Preferences
# ══════════════════════════════════════════════════════════════════════════════

def load_prefs() -> dict:
    stored = _load(PREFS_FILE, {})
    return {**DEFAULT_PREFS, **stored}


def save_prefs(prefs: dict) -> bool:
    return _save(PREFS_FILE, prefs)


def get_pref(key: str, default=None):
    prefs = load_prefs()
    return prefs.get(key, DEFAULT_PREFS.get(key, default))


def set_pref(key: str, value) -> bool:
    prefs = load_prefs()
    prefs[key] = value
    return save_prefs(prefs)


# ══════════════════════════════════════════════════════════════════════════════
#  Aliases
# ══════════════════════════════════════════════════════════════════════════════

def load_aliases() -> dict:
    return _load(ALIAS_FILE, {})


def save_aliases(aliases: dict) -> bool:
    return _save(ALIAS_FILE, aliases)


# ══════════════════════════════════════════════════════════════════════════════
#  Bookmarks
# ══════════════════════════════════════════════════════════════════════════════

def load_bookmarks() -> dict:
    return _load(BOOKMARK_FILE, {})


def save_bookmarks(bm: dict) -> bool:
    return _save(BOOKMARK_FILE, bm)


# ══════════════════════════════════════════════════════════════════════════════
#  Notes
# ══════════════════════════════════════════════════════════════════════════════

def load_notes() -> list:
    return _load(NOTES_FILE, [])


def save_notes(notes: list) -> bool:
    return _save(NOTES_FILE, notes)


def add_note(text: str, tags: list = None) -> dict:
    notes = load_notes()
    note = {
        "id":        len(notes) + 1,
        "text":      text,
        "tags":      tags or [],
        "created":   datetime.datetime.now().isoformat(),
    }
    notes.append(note)
    save_notes(notes)
    return note


def delete_note(note_id: int) -> bool:
    notes = load_notes()
    new   = [n for n in notes if n.get("id") != note_id]
    if len(new) < len(notes):
        for i, n in enumerate(new, 1):
            n["id"] = i
        save_notes(new)
        return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
#  TODO
# ══════════════════════════════════════════════════════════════════════════════

def load_todos() -> list:
    return _load(TODO_FILE, [])


def save_todos(todos: list) -> bool:
    return _save(TODO_FILE, todos)


def add_todo(task: str, priority: str = "normal") -> dict:
    todos = load_todos()
    todo = {
        "id":        len(todos) + 1,
        "task":      task,
        "done":      False,
        "priority":  priority,      # low | normal | high | critical
        "created":   datetime.datetime.now().isoformat(),
        "completed": None,
    }
    todos.append(todo)
    save_todos(todos)
    return todo


def complete_todo(todo_id: int) -> bool:
    todos = load_todos()
    for t in todos:
        if t.get("id") == todo_id:
            t["done"]      = True
            t["completed"] = datetime.datetime.now().isoformat()
            save_todos(todos)
            return True
    return False


def delete_todo(todo_id: int) -> bool:
    todos = load_todos()
    new   = [t for t in todos if t.get("id") != todo_id]
    if len(new) < len(todos):
        for i, t in enumerate(new, 1):
            t["id"] = i
        save_todos(new)
        return True
    return False
