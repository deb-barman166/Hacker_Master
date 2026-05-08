"""
commands/productivity.py — Productivity tools (v2.0 Masterpiece).

Commands:
  - notes: Quick note manager
  - todo: Task manager
  - plugins: Plugin management
  - save-session/load-session: Session management
  - calendar: Simple calendar
  - reminders: Reminder system
"""

import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

from ui.theme import Colors

C = Colors


# ─────────────────────────────────────────────────────────────────────────
# Notes
# ─────────────────────────────────────────────────────────────────────────
def cmd_notes(args: list, state: dict, terminal=None) -> int:
    """Quick note manager. Usage: notes [add|list|show|delete] [text|id]"""
    notes_file = Path.home() / ".config" / "kali_terminal" / "notes.json"
    notes_file.parent.mkdir(parents=True, exist_ok=True)

    # Load notes
    if notes_file.exists():
        try:
            notes = json.loads(notes_file.read_text())
        except:
            notes = []
    else:
        notes = []

    if not args or args[0] == "list":
        if not notes:
            print(C.info("No notes yet. Use 'notes add <text>' to create one."))
            return 0

        print(f"\n{C.BLUE}{'='*60}{C.RESET}")
        print(f"  {C.BOLD}{C.WHITE}NOTES ({len(notes)}){C.RESET}")
        print(f"{C.BLUE}{'='*60}{C.RESET}")
        for i, note in enumerate(notes, 1):
            timestamp = datetime.fromtimestamp(note.get("time", 0)).strftime("%Y-%m-%d %H:%M")
            print(f"  {C.CYAN}[{i}]{C.RESET} {C.WHITE}{note['text'][:50]}{C.RESET} {C.GRAY}({timestamp}){C.RESET}")
        print(f"{C.BLUE}{'='*60}{C.RESET}\n")

    elif args[0] == "add" and len(args) > 1:
        text = " ".join(args[1:])
        notes.append({"text": text, "time": time.time()})
        notes_file.write_text(json.dumps(notes, indent=2))
        print(C.success(f"Note added: {text[:50]}..."))

    elif args[0] == "show" and len(args) > 1:
        try:
            idx = int(args[1]) - 1
            if 0 <= idx < len(notes):
                note = notes[idx]
                timestamp = datetime.fromtimestamp(note.get("time", 0)).strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n  {C.YELLOW}Note #{idx + 1}{C.RESET}")
                print(f"  {C.GRAY}Created: {timestamp}{C.RESET}")
                print(f"  {C.WHITE}{note['text']}{C.RESET}\n")
            else:
                print(C.error(f"Note #{args[1]} not found"))
        except ValueError:
            print(C.error("Invalid note ID"))

    elif args[0] == "delete" and len(args) > 1:
        try:
            idx = int(args[1]) - 1
            if 0 <= idx < len(notes):
                deleted = notes.pop(idx)
                notes_file.write_text(json.dumps(notes, indent=2))
                print(C.success(f"Deleted: {deleted['text'][:50]}..."))
            else:
                print(C.error(f"Note #{args[1]} not found"))
        except ValueError:
            print(C.error("Invalid note ID"))

    else:
        print(C.info("Usage: notes [add|list|show|delete] [text|id]"))

    return 0


# ─────────────────────────────────────────────────────────────────────────
# Todo
# ─────────────────────────────────────────────────────────────────────────
def cmd_todo(args: list, state: dict, terminal=None) -> int:
    """Task manager. Usage: todo [add|list|done|delete] [task|id]"""
    todo_file = Path.home() / ".config" / "kali_terminal" / "todo.json"
    todo_file.parent.mkdir(parents=True, exist_ok=True)

    if todo_file.exists():
        try:
            todos = json.loads(todo_file.read_text())
        except:
            todos = []
    else:
        todos = []

    if not args or args[0] == "list":
        if not todos:
            print(C.info("No tasks. Use 'todo add <task>' to create one."))
            return 0

        print(f"\n{C.BLUE}{'='*60}{C.RESET}")
        print(f"  {C.BOLD}{C.WHITE}TASKS ({len(todos)}){C.RESET}")
        print(f"{C.BLUE}{'='*60}{C.RESET}")
        for i, todo in enumerate(todos, 1):
            status = f"{C.GREEN}[x]{C.RESET}" if todo.get("done") else f"{C.RED}[ ]{C.RESET}"
            text = todo["text"] if todo.get("done") else f"{C.WHITE}{todo['text']}{C.RESET}"
            print(f"  {C.CYAN}[{i}]{C.RESET} {status} {text}")
        print(f"{C.BLUE}{'='*60}{C.RESET}\n")

    elif args[0] == "add" and len(args) > 1:
        text = " ".join(args[1:])
        todos.append({"text": text, "done": False, "time": time.time()})
        todo_file.write_text(json.dumps(todos, indent=2))
        print(C.success(f"Task added: {text}"))

    elif args[0] == "done" and len(args) > 1:
        try:
            idx = int(args[1]) - 1
            if 0 <= idx < len(todos):
                todos[idx]["done"] = True
                todo_file.write_text(json.dumps(todos, indent=2))
                print(C.success(f"Task completed: {todos[idx]['text']}"))
            else:
                print(C.error(f"Task #{args[1]} not found"))
        except ValueError:
            print(C.error("Invalid task ID"))

    elif args[0] == "delete" and len(args) > 1:
        try:
            idx = int(args[1]) - 1
            if 0 <= idx < len(todos):
                deleted = todos.pop(idx)
                todo_file.write_text(json.dumps(todos, indent=2))
                print(C.success(f"Deleted: {deleted['text']}"))
            else:
                print(C.error(f"Task #{args[1]} not found"))
        except ValueError:
            print(C.error("Invalid task ID"))

    else:
        print(C.info("Usage: todo [add|list|done|delete] [task|id]"))

    return 0


# ─────────────────────────────────────────────────────────────────────────
# Plugins
# ─────────────────────────────────────────────────────────────────────────
def cmd_plugins(args: list, state: dict, terminal=None) -> int:
    """Plugin management. Usage: plugins [list|load|unload] [name]"""
    if not terminal:
        print(C.error("Terminal context not available"))
        return 1

    if not args or args[0] == "list":
        plugins = terminal.plugins.list_plugins()
        if not plugins:
            print(C.info("No plugins loaded"))
            return 0

        print(f"\n{C.BLUE}{'='*60}{C.RESET}")
        print(f"  {C.BOLD}{C.WHITE}PLUGINS ({len(plugins)}){C.RESET}")
        print(f"{C.BLUE}{'='*60}{C.RESET}")
        for name, enabled in plugins:
            status = f"{C.GREEN}active{C.RESET}" if enabled else f"{C.RED}inactive{C.RESET}"
            print(f"  {C.CYAN}{name:<30}{C.RESET} {status}")
        print(f"{C.BLUE}{'='*60}{C.RESET}\n")

    elif args[0] == "load" and len(args) > 1:
        if terminal.plugins.enable_plugin(args[1]):
            print(C.success(f"Plugin '{args[1]}' loaded"))
        else:
            print(C.error(f"Plugin '{args[1]}' not found"))

    elif args[0] == "unload" and len(args) > 1:
        if terminal.plugins.disable_plugin(args[1]):
            print(C.success(f"Plugin '{args[1]}' unloaded"))
        else:
            print(C.error(f"Plugin '{args[1]}' not found"))

    else:
        print(C.info("Usage: plugins [list|load|unload] [name]"))

    return 0


# ─────────────────────────────────────────────────────────────────────────
# Session Management
# ─────────────────────────────────────────────────────────────────────────
def cmd_save_session(args: list, state: dict, terminal=None) -> int:
    """Save current session. Usage: save-session [name]"""
    if not terminal:
        print(C.error("Terminal context not available"))
        return 1

    name = args[0] if args else None
    if terminal.sessions.save_session(name):
        print(C.success(f"Session saved: {name or 'default'}"))
    else:
        print(C.error("Failed to save session"))
        return 1
    return 0


def cmd_load_session(args: list, state: dict, terminal=None) -> int:
    """Load a saved session. Usage: load-session <name>"""
    if not terminal:
        print(C.error("Terminal context not available"))
        return 1

    if not args:
        print(C.error("Session name required"))
        return 1

    if terminal.sessions.load_session(args[0]):
        print(C.success(f"Session loaded: {args[0]}"))
    else:
        print(C.error(f"Session '{args[0]}' not found"))
        return 1
    return 0


def cmd_lsessions(args: list, state: dict, terminal=None) -> int:
    """List saved sessions."""
    if not terminal:
        print(C.error("Terminal context not available"))
        return 1

    sessions = terminal.sessions.list_sessions()
    if not sessions:
        print(C.info("No saved sessions"))
        return 0

    print(f"\n{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}SAVED SESSIONS ({len(sessions)}){C.RESET}")
    print(f"{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.GRAY}{'Name':<25}{'CWD':<25}{'Commands'}{C.RESET}")

    for s in sessions:
        cwd = s.get('cwd', '')[:22]
        ts = datetime.fromtimestamp(s.get('timestamp', 0)).strftime("%Y-%m-%d %H:%M")
        print(f"  {C.CYAN}{s['name']:<25}{C.RESET}{C.GRAY}{cwd:<25}{s.get('history_count', 0):>8}{C.RESET}")
        print(f"  {C.GRAY}   Last saved: {ts}{C.RESET}")

    print(f"{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


# ─────────────────────────────────────────────────────────────────────────
# Calendar
# ─────────────────────────────────────────────────────────────────────────
def cmd_calendar(args: list, state: dict, terminal=None) -> int:
    """Simple calendar display. Usage: calendar [month] [year]"""
    import calendar

    now = datetime.now()
    month = now.month
    year = now.year

    if args:
        try:
            month = int(args[0])
        except ValueError:
            month = now.month
    if len(args) > 1:
        try:
            year = int(args[1])
        except ValueError:
            year = now.year

    cal = calendar.TextCalendar(firstweekday=6)
    output = cal.formatmonth(year, month)

    print(f"\n{C.BLUE}{'='*40}{C.RESET}")
    print(f"{C.BOLD}{C.WHITE}  {calendar.month_name[month]} {year}{C.RESET}")
    print(f"{C.BLUE}{'='*40}{C.RESET}")
    print(output)
    return 0


# ─────────────────────────────────────────────────────────────────────────
# Reminders
# ─────────────────────────────────────────────────────────────────────────
def cmd_reminders(args: list, state: dict, terminal=None) -> int:
    """Reminder system. Usage: reminders [add|list|clear] [text|minutes]"""
    reminders_file = Path.home() / ".config" / "kali_terminal" / "reminders.json"
    reminders_file.parent.mkdir(parents=True, exist_ok=True)

    if reminders_file.exists():
        try:
            reminders = json.loads(reminders_file.read_text())
        except:
            reminders = []
    else:
        reminders = []

    if not args or args[0] == "list":
        if not reminders:
            print(C.info("No reminders. Use 'reminders add <minutes> <text>'"))
            return 0

        print(f"\n{C.BLUE}{'='*60}{C.RESET}")
        print(f"  {C.BOLD}{C.WHITE}REMINDERS ({len(reminders)}){C.RESET}")
        print(f"{C.BLUE}{'='*60}{C.RESET}")

        now = time.time()
        for i, rem in enumerate(reminders, 1):
            target = rem.get("time", 0)
            remaining = max(0, target - now)
            mins = int(remaining // 60)

            if remaining > 0:
                status = f"{C.YELLOW}In {mins} min{C.RESET}"
            else:
                status = f"{C.RED}READY{C.RESET}"

            print(f"  {C.CYAN}[{i}]{C.RESET} {C.WHITE}{rem['text']}{C.RESET} {status}")

        print(f"{C.BLUE}{'='*60}{C.RESET}\n")

    elif args[0] == "add" and len(args) > 2:
        try:
            mins = int(args[1])
            text = " ".join(args[2:])
            reminder_time = time.time() + (mins * 60)
            reminders.append({"text": text, "time": reminder_time})
            reminders_file.write_text(json.dumps(reminders, indent=2))
            print(C.success(f"Reminder set for {mins} minutes: {text}"))
        except ValueError:
            print(C.error("Invalid minutes value"))

    elif args[0] == "clear":
        reminders = []
        reminders_file.write_text(json.dumps(reminders, indent=2))
        print(C.success("All reminders cleared"))

    else:
        print(C.info("Usage: reminders [add|list|clear] [minutes] [text]"))

    return 0