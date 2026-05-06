"""
utils/config.py — Persistent Configuration & State Manager

Manages:
  • Theme preference
  • Aliases (persistent across sessions)
  • Bookmarks (named directory shortcuts)
  • Notes
  • TODO list
  • Custom keybindings
  • Terminal preferences

All data stored in ~/.kali_terminal/ directory as JSON files.
"""

import os
import json
import datetime
from pathlib import Path


# ── Config directory ───────────────────────────────────────────────────────────
CONFIG_DIR  = Path.home() / ".kali_terminal"
THEME_FILE  = CONFIG_DIR / "theme.json"
ALIAS_FILE  = CONFIG_DIR / "aliases.json"
BOOK_FILE   = CONFIG_DIR / "bookmarks.json"
NOTES_FILE  = CONFIG_DIR / "notes.json"
TODO_FILE   = CONFIG_DIR / "todos.json"
PREFS_FILE  = CONFIG_DIR / "prefs.json"
HIST_FILE   = Path.home() / ".kali_terminal_history"


def _ensure_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _load(path: Path, default):
    try:
        if path.exists():
            with open(path) as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return default


def _save(path: Path, data) -> bool:
    _ensure_dir()
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except OSError:
        return False


# ══════════════════════════════════════════════════════════════════════
#  Theme
# ══════════════════════════════════════════════════════════════════════

def load_theme() -> str:
    data = _load(THEME_FILE, {"theme": "kali"})
    return data.get("theme", "kali")


def save_theme(theme_name: str):
    _save(THEME_FILE, {"theme": theme_name})


# ══════════════════════════════════════════════════════════════════════
#  Aliases
# ══════════════════════════════════════════════════════════════════════

def load_aliases() -> dict:
    """Load persistent aliases. Returns {name: command} dict."""
    return _load(ALIAS_FILE, {})


def save_aliases(aliases: dict) -> bool:
    return _save(ALIAS_FILE, aliases)


# ══════════════════════════════════════════════════════════════════════
#  Bookmarks
# ══════════════════════════════════════════════════════════════════════

def load_bookmarks() -> dict:
    """Load bookmarks. Returns {name: path} dict."""
    return _load(BOOK_FILE, {})


def save_bookmarks(bookmarks: dict) -> bool:
    return _save(BOOK_FILE, bookmarks)


# ══════════════════════════════════════════════════════════════════════
#  Notes
# ══════════════════════════════════════════════════════════════════════

def load_notes() -> list:
    """Load notes. Returns list of {id, text, timestamp} dicts."""
    return _load(NOTES_FILE, [])


def save_notes(notes: list) -> bool:
    return _save(NOTES_FILE, notes)


def add_note(text: str) -> dict:
    notes = load_notes()
    note = {
        "id":        len(notes) + 1,
        "text":      text,
        "timestamp": datetime.datetime.now().isoformat(),
        "tags":      [],
    }
    notes.append(note)
    save_notes(notes)
    return note


def delete_note(note_id: int) -> bool:
    notes = load_notes()
    original_len = len(notes)
    notes = [n for n in notes if n.get("id") != note_id]
    if len(notes) < original_len:
        # Re-number
        for i, n in enumerate(notes, start=1):
            n["id"] = i
        save_notes(notes)
        return True
    return False


# ══════════════════════════════════════════════════════════════════════
#  TODO List
# ══════════════════════════════════════════════════════════════════════

def load_todos() -> list:
    """Load todos. Returns list of {id, task, done, priority, created} dicts."""
    return _load(TODO_FILE, [])


def save_todos(todos: list) -> bool:
    return _save(TODO_FILE, todos)


def add_todo(task: str, priority: str = "normal") -> dict:
    todos = load_todos()
    todo = {
        "id":       len(todos) + 1,
        "task":     task,
        "done":     False,
        "priority": priority,  # low / normal / high
        "created":  datetime.datetime.now().isoformat(),
        "completed": None,
    }
    todos.append(todo)
    save_todos(todos)
    return todo


def complete_todo(todo_id: int) -> bool:
    todos = load_todos()
    for t in todos:
        if t.get("id") == todo_id:
            t["done"] = True
            t["completed"] = datetime.datetime.now().isoformat()
            save_todos(todos)
            return True
    return False


def delete_todo(todo_id: int) -> bool:
    todos = load_todos()
    original_len = len(todos)
    todos = [t for t in todos if t.get("id") != todo_id]
    if len(todos) < original_len:
        for i, t in enumerate(todos, start=1):
            t["id"] = i
        save_todos(todos)
        return True
    return False


# ══════════════════════════════════════════════════════════════════════
#  Preferences
# ══════════════════════════════════════════════════════════════════════

DEFAULT_PREFS = {
    "show_git_branch":     True,
    "show_exit_code":      True,
    "show_time_in_prompt": False,
    "autocomplete":        True,
    "mouse_support":       False,
    "vi_mode":             False,
    "welcome_tips":        True,
    "recording":           False,
    "record_file":         None,
    "anthropic_api_key":   None,
}


def load_prefs() -> dict:
    stored = _load(PREFS_FILE, {})
    return {**DEFAULT_PREFS, **stored}


def save_prefs(prefs: dict) -> bool:
    return _save(PREFS_FILE, prefs)


def get_pref(key: str):
    return load_prefs().get(key, DEFAULT_PREFS.get(key))


def set_pref(key: str, value) -> bool:
    prefs = load_prefs()
    prefs[key] = value
    return save_prefs(prefs)
