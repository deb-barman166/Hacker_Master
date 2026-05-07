"""
commands/productivity.py — Productivity tools for KaliTerminal v2.

Commands:
  note     Quick notes (add/list/delete/search/clear)
  todo     To-do list (add/list/done/delete/clear)
  calc     Scientific calculator with history
  timer    Stopwatch / countdown timer
"""

import os
import math
import time
from datetime import datetime, timedelta

from ui.theme import Colors
from utils.config import (
    load_notes, save_notes, add_note, delete_note,
    load_todos, save_todos, add_todo, complete_todo, delete_todo,
)

C = Colors

# ══════════════════════════════════════════════════════════════════════════════
#  NOTE
# ══════════════════════════════════════════════════════════════════════════════

def cmd_note(args: list, state: dict) -> int:
    """
    note add <text> [#tag]   — add a note (tags with #)
    note list [tag]          — list notes (optionally filter by tag)
    note delete <id>         — delete note by ID
    note search <term>       — search notes
    note clear               — delete ALL notes (confirm)
    """
    if not args or args[0] == "list":
        tag = args[1] if len(args) > 1 else None
        return _note_list(tag)

    sub = args[0]

    if sub == "add":
        if len(args) < 2:
            print(C.error("Usage: note add <text> [#tag1 #tag2]"))
            return 1
        raw  = " ".join(args[1:])
        tags = [w[1:] for w in raw.split() if w.startswith("#")]
        text = " ".join(w for w in raw.split() if not w.startswith("#"))
        n    = add_note(text, tags)
        tag_str = "  " + " ".join(f"#{t}" for t in tags) if tags else ""
        print(C.success(f"Note #{n['id']} saved{tag_str}"))
        return 0

    if sub == "delete" and len(args) > 1:
        try:
            nid = int(args[1])
        except ValueError:
            print(C.error(f"Invalid ID: {args[1]}"))
            return 1
        if delete_note(nid):
            print(C.success(f"Note #{nid} deleted."))
        else:
            print(C.warn(f"Note #{nid} not found."))
        return 0

    if sub == "search" and len(args) > 1:
        term  = " ".join(args[1:]).lower()
        notes = [n for n in load_notes() if term in n["text"].lower()]
        if not notes:
            print(C.info(f"No notes matching '{term}'"))
            return 0
        _render_notes(notes, title=f"Notes — search: '{term}'")
        return 0

    if sub == "clear":
        print(C.warn("Delete ALL notes? [y/N] "), end="")
        if input().strip().lower() == "y":
            save_notes([])
            print(C.success("All notes cleared."))
        else:
            print(C.info("Cancelled."))
        return 0

    # Treat as implicit 'add'
    raw  = " ".join(args)
    tags = [w[1:] for w in raw.split() if w.startswith("#")]
    text = " ".join(w for w in raw.split() if not w.startswith("#"))
    n    = add_note(text, tags)
    print(C.success(f"Note #{n['id']} saved"))
    return 0


def _note_list(tag: str = None) -> int:
    notes = load_notes()
    if tag:
        notes = [n for n in notes if tag in n.get("tags", [])]
    if not notes:
        msg = f"No notes" + (f" with tag '#{tag}'" if tag else "")
        print(C.info(msg + ". Use: note add <text>"))
        return 0
    _render_notes(notes)
    return 0


def _render_notes(notes: list, title: str = None):
    t = title or f"Notes ({len(notes)})"
    print(C.header(t))
    for n in notes:
        date   = n.get("created", "")[:16]
        tags   = "  " + " ".join(f"{C.CYAN}#{t}{C.RESET}" for t in n.get("tags",[])) if n.get("tags") else ""
        print(f"  {C.YELLOW}#{n['id']:<4}{C.RESET}  "
              f"{C.WHITE}{n['text']}{C.RESET}{tags}  "
              f"{C.GRAY}{date}{C.RESET}")
    print()


# ══════════════════════════════════════════════════════════════════════════════
#  TODO
# ══════════════════════════════════════════════════════════════════════════════

PRIORITY_COLORS = {
    "critical": C.RED + C.BOLD,
    "high":     C.RED,
    "normal":   C.WHITE,
    "low":      C.GRAY,
}
PRIORITY_ICONS = {
    "critical": "🔴",
    "high":     "🟠",
    "normal":   "🟡",
    "low":      "⚪",
}


def cmd_todo(args: list, state: dict) -> int:
    """
    todo add <task> [--priority low|normal|high|critical]
    todo list [all|done|pending]
    todo done <id>
    todo delete <id>
    todo clear
    """
    if not args or args[0] == "list":
        mode = args[1] if len(args) > 1 else "pending"
        return _todo_list(mode)

    sub = args[0]

    if sub == "add":
        if len(args) < 2:
            print(C.error("Usage: todo add <task> [--priority low|normal|high|critical]"))
            return 1
        priority = "normal"
        task_parts = []
        i = 1
        while i < len(args):
            if args[i] in ("--priority", "-p") and i+1 < len(args):
                priority = args[i+1]; i += 2
            elif args[i] in ("--critical", "--high", "--low"):
                priority = args[i][2:]; i += 1
            else:
                task_parts.append(args[i]); i += 1
        task = " ".join(task_parts)
        if not task:
            print(C.error("Task text cannot be empty."))
            return 1
        t = add_todo(task, priority)
        icon = PRIORITY_ICONS.get(priority, "🟡")
        print(C.success(f"TODO #{t['id']} added  {icon} [{priority}]: {task}"))
        return 0

    if sub == "done" and len(args) > 1:
        try:
            tid = int(args[1])
        except ValueError:
            print(C.error(f"Invalid ID: {args[1]}"))
            return 1
        if complete_todo(tid):
            print(C.success(f"TODO #{tid} marked as done! ✅"))
        else:
            print(C.warn(f"TODO #{tid} not found."))
        return 0

    if sub == "delete" and len(args) > 1:
        try:
            tid = int(args[1])
        except ValueError:
            print(C.error(f"Invalid ID: {args[1]}"))
            return 1
        if delete_todo(tid):
            print(C.success(f"TODO #{tid} deleted."))
        else:
            print(C.warn(f"TODO #{tid} not found."))
        return 0

    if sub == "clear":
        print(C.warn("Delete ALL todos? [y/N] "), end="")
        if input().strip().lower() == "y":
            save_todos([])
            print(C.success("All todos cleared."))
        return 0

    # Fallback: add
    task = " ".join(args)
    t    = add_todo(task, "normal")
    print(C.success(f"TODO #{t['id']} added."))
    return 0


def _todo_list(mode: str = "pending") -> int:
    todos = load_todos()
    if mode == "done":
        todos = [t for t in todos if t.get("done")]
    elif mode == "all":
        pass
    else:
        todos = [t for t in todos if not t.get("done")]

    if not todos:
        msgs = {
            "done":    "No completed todos.",
            "all":     "No todos. Use: todo add <task>",
            "pending": "All caught up! No pending todos. 🎉",
        }
        print(C.info(msgs.get(mode, "No todos.")))
        return 0

    # Sort by priority then id
    prio_rank = {"critical": 0, "high": 1, "normal": 2, "low": 3}
    todos.sort(key=lambda x: (prio_rank.get(x.get("priority","normal"), 2), x.get("id",0)))

    label = {"done": "Completed", "all": "All", "pending": "Pending"}.get(mode, "")
    print(C.header(f"TODO List — {label} ({len(todos)})"))

    for t in todos:
        done_str  = f"{C.GREEN}✅{C.RESET}" if t.get("done") else f"{C.GRAY}◻ {C.RESET}"
        prio      = t.get("priority", "normal")
        prio_clr  = PRIORITY_COLORS.get(prio, C.WHITE)
        icon      = PRIORITY_ICONS.get(prio, "🟡")
        date      = t.get("created","")[:10]
        comp_date = f"  → {t['completed'][:10]}" if t.get("completed") else ""
        print(f"  {done_str} {C.YELLOW}#{t['id']:<4}{C.RESET}  "
              f"{icon} {prio_clr}{t['task']}{C.RESET}  "
              f"{C.GRAY}{date}{comp_date}{C.RESET}")

    pending = sum(1 for t in load_todos() if not t.get("done"))
    done    = sum(1 for t in load_todos() if t.get("done"))
    print(f"\n  {C.GREEN}Done: {done}{C.RESET}  {C.YELLOW}Pending: {pending}{C.RESET}\n")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════

# Safe math namespace
MATH_NAMESPACE = {
    "__builtins__": {},
    "abs": abs, "round": round, "min": min, "max": max,
    "sum": sum, "pow": pow, "divmod": divmod,
    "int": int, "float": float, "hex": hex, "oct": oct, "bin": bin,
    # math module
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan, "atan2": math.atan2,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    "exp": math.exp, "log": math.log, "log2": math.log2, "log10": math.log10,
    "sqrt": math.sqrt, "ceil": math.ceil, "floor": math.floor,
    "factorial": math.factorial, "gcd": math.gcd,
    "pi": math.pi, "e": math.e, "tau": math.tau, "inf": math.inf,
    # IP/network helpers
    "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4,
}

_calc_history: list = []


def cmd_calc(args: list, state: dict) -> int:
    """
    calc <expression>   — Evaluate a mathematical expression
    calc                — Enter interactive calculator mode
    Examples:
      calc 2**32
      calc sqrt(2) * pi
      calc 4 * GB / MB
      calc sin(pi/6)
    """
    if not args:
        return _calc_interactive()

    expr = " ".join(args)
    return _calc_eval(expr)


def _calc_eval(expr: str) -> int:
    # Preprocess: replace ^ with **, comma with dot
    expr = expr.replace("^", "**").replace(",", "")

    try:
        result = eval(expr, MATH_NAMESPACE)  # noqa: S307
    except ZeroDivisionError:
        print(C.error("Division by zero."))
        return 1
    except Exception as e:
        print(C.error(f"Invalid expression: {e}"))
        return 1

    _calc_history.append((expr, result))

    # Format result
    if isinstance(result, float):
        if result == int(result) and abs(result) < 1e15:
            result_str = str(int(result))
        else:
            result_str = f"{result:.10g}"
    elif isinstance(result, int) and abs(result) > 1_000_000:
        result_str = f"{result:,}"
    else:
        result_str = str(result)

    print(f"  {C.CYAN}{expr}{C.RESET}  {C.GRAY}={C.RESET}  {C.GREEN}{C.BOLD}{result_str}{C.RESET}")

    # Extra representations for integers
    if isinstance(result, int) and 0 <= result < 2**64:
        print(f"  {C.GRAY}  hex: {hex(result)}   bin: {bin(result)}   oct: {oct(result)}{C.RESET}")

    return 0


def _calc_interactive() -> int:
    """Interactive calculator REPL."""
    print(f"\n{C.BLUE}{'═'*50}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}CALCULATOR{C.RESET}  {C.GRAY}(type 'exit' to quit){C.RESET}")
    print(f"  {C.GRAY}Supports: +,-,*,/,**,sqrt,sin,cos,pi,e,log,KB,GB…{C.RESET}")
    print(f"{C.BLUE}{'═'*50}{C.RESET}\n")

    while True:
        try:
            raw = input(f"  {C.CYAN}calc❯{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw or raw in ("exit", "quit", "q"):
            break

        if raw in ("history", "hist"):
            if not _calc_history:
                print(C.info("No history yet."))
            for expr, res in _calc_history[-10:]:
                print(f"  {C.GRAY}{expr}{C.RESET} = {C.GREEN}{res}{C.RESET}")
            continue

        _calc_eval(raw)

    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  TIMER
# ══════════════════════════════════════════════════════════════════════════════

_timer_start: float = None
_timer_laps:  list  = []


def cmd_timer(args: list, state: dict) -> int:
    """
    timer start          — start the stopwatch
    timer stop / lap     — show elapsed time
    timer countdown <s>  — countdown N seconds
    """
    global _timer_start, _timer_laps

    sub = args[0] if args else "start"

    if sub == "start":
        _timer_start = time.time()
        _timer_laps  = []
        print(C.success("Stopwatch started. Use 'timer lap' or 'timer stop'."))
        return 0

    if sub in ("stop", "lap"):
        if _timer_start is None:
            print(C.warn("Timer not running. Use 'timer start'."))
            return 0
        elapsed = time.time() - _timer_start
        lap_n   = len(_timer_laps) + 1
        _timer_laps.append(elapsed)
        action = "Stopped" if sub == "stop" else f"Lap #{lap_n}"
        print(f"  {C.CYAN}{action}{C.RESET}: {C.BOLD}{C.GREEN}{_fmt_duration(elapsed)}{C.RESET}")
        if sub == "stop":
            _timer_start = None
        return 0

    if sub == "countdown" and len(args) > 1:
        return _countdown(args[1:])

    if sub == "status":
        if _timer_start is None:
            print(C.info("Timer is not running."))
        else:
            elapsed = time.time() - _timer_start
            print(f"  {C.CYAN}Elapsed{C.RESET}: {C.GREEN}{_fmt_duration(elapsed)}{C.RESET}")
        return 0

    # Default: show status
    if _timer_start is not None:
        elapsed = time.time() - _timer_start
        print(f"  {C.CYAN}Elapsed{C.RESET}: {C.GREEN}{_fmt_duration(elapsed)}{C.RESET}")
    else:
        print(C.info("Timer not running. Use 'timer start'."))
    return 0


def _countdown(args: list) -> int:
    """Blocking countdown in terminal."""
    try:
        secs = int(args[0])
    except ValueError:
        print(C.error(f"Invalid seconds: {args[0]}"))
        return 1

    secs = min(max(secs, 1), 86400)
    total = secs

    print(f"\n  {C.CYAN}Countdown: {secs}s{C.RESET}  (Ctrl+C to cancel)\n")
    try:
        while secs > 0:
            pct = (total - secs) * 100 // total
            bar = C.progress_bar(pct, width=25)
            sys_stdout_write = __import__("sys").stdout.write
            sys_stdout_write(f"\r  {bar}  {C.BOLD}{_fmt_duration(secs)}{C.RESET} remaining   ")
            __import__("sys").stdout.flush()
            time.sleep(1)
            secs -= 1
        print(f"\r  {C.GREEN}{C.BOLD}{'Time\'s up! ✅':^50}{C.RESET}")
    except KeyboardInterrupt:
        print(f"\n  {C.YELLOW}Countdown cancelled.{C.RESET}")

    return 0


def _fmt_duration(secs: float) -> str:
    secs = int(secs)
    h, r = divmod(secs, 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


# ══════════════════════════════════════════════════════════════════════════════
#  Registry
# ══════════════════════════════════════════════════════════════════════════════

PROD_CMDS: dict = {
    "note":   cmd_note,
    "notes":  cmd_note,
    "todo":   cmd_todo,
    "todos":  cmd_todo,
    "calc":   cmd_calc,
    "timer":  cmd_timer,
    "stopwatch": cmd_timer,
}
