"""
commands/builtins.py — Built-in Shell Commands for Kali Terminal v1.0

Commands (beyond v2):
  cd, clear, history, sysinfo, cheatsheet, tips, help   ← inherited
  theme [name]           — Switch / list themes
  alias [name=cmd]       — Manage persistent aliases
  bookmark [add|go|del]  — Named directory bookmarks
  note [add|list|del]    — In-terminal notes
  todo [add|done|del|ls] — TODO task manager
  tree [path] [depth]    — Colored directory tree
  monitor                — Live system monitor (updates every 1s)
  matrix                 — Matrix rain animation
  weather [city]         — ASCII weather (wttr.in)
  calc <expr>            — Python-powered calculator
  about                  — Show terminal info
  plugins                — List loaded plugins
  set [key] [value]      — Manage terminal preferences
"""

import os
import sys
import shutil
import platform
import subprocess
import time
import random
import math
from datetime import datetime

from ui.theme   import Colors, THEMES, apply_theme, get_active_theme
from utils.config import (
    load_aliases, save_aliases, load_bookmarks, save_bookmarks,
    load_notes, add_note, delete_note,
    load_todos, add_todo, complete_todo, delete_todo,
    load_prefs, save_prefs, set_pref, save_theme,
)
from utils.formatters import table, bar, tree_view

C = Colors


# ════════════════════════════════════════════════════════════════════
#  cd
# ════════════════════════════════════════════════════════════════════

def cmd_cd(args: list, state: dict) -> int:
    prev_dir = state.get("prev_dir", os.getcwd())

    if not args:
        target = os.path.expanduser("~")
    elif args[0] == "-":
        target = prev_dir
        print(C.paint(target, C.CYAN))
    else:
        target = os.path.expanduser(args[0])
        if not os.path.isabs(target):
            target = os.path.join(state["cwd"], target)
        target = os.path.normpath(target)

    try:
        state["prev_dir"] = state["cwd"]
        os.chdir(target)
        state["cwd"] = os.getcwd()
        return 0
    except FileNotFoundError:
        print(C.error(f"cd: {args[0]}: No such file or directory"))
        return 1
    except PermissionError:
        print(C.error(f"cd: {args[0]}: Permission denied"))
        return 1
    except NotADirectoryError:
        print(C.error(f"cd: {args[0]}: Not a directory"))
        return 1


# ════════════════════════════════════════════════════════════════════
#  clear
# ════════════════════════════════════════════════════════════════════

def cmd_clear(args: list, state: dict) -> int:
    os.system("clear" if os.name != "nt" else "cls")
    return 0


# ════════════════════════════════════════════════════════════════════
#  history
# ════════════════════════════════════════════════════════════════════

def cmd_history(args: list, state: dict) -> int:
    hist = state.get("history", [])

    if args and args[0] == "-c":
        state["history"] = []
        print(C.success("History cleared."))
        return 0

    if args and args[0] == "--grep" and len(args) > 1:
        pattern = args[1].lower()
        hist = [h for h in hist if pattern in h.lower()]

    n = 20
    if args and args[0].isdigit():
        n = int(args[0])

    entries = hist[-n:]
    if not entries:
        print(C.info("No history yet."))
        return 0

    start = max(1, len(hist) - n + 1)
    rows  = [(C.paint(f"{i}", C.GRAY), C.paint(cmd, C.CYAN))
             for i, cmd in enumerate(entries, start=start)]
    print()
    print(table(rows, headers=["#", "COMMAND"], title=f"HISTORY (last {n})"))
    print()
    return 0


# ════════════════════════════════════════════════════════════════════
#  theme
# ════════════════════════════════════════════════════════════════════

def cmd_theme(args: list, state: dict) -> int:
    """theme [name] — Switch theme or list available themes."""
    if not args or args[0] == "list":
        current = get_active_theme()
        rows = []
        for name, t in THEMES.items():
            marker = C.paint(" ◀ ACTIVE", C.GREEN, bold=True) if name == current else ""
            rows.append((
                t["emoji"] + " " + name,
                t["name"],
                t["desc"] + marker
            ))
        print()
        print(table(rows, headers=["THEME", "NAME", "DESCRIPTION"],
                    title="AVAILABLE THEMES"))
        print(f"\n  Usage: {C.CYAN}theme <name>{C.RESET}   e.g. {C.CYAN}theme dracula{C.RESET}\n")
        return 0

    theme_name = args[0].lower()
    if apply_theme(theme_name):
        save_theme(theme_name)
        state["theme"] = theme_name
        t = THEMES[theme_name]
        print(f"\n  {t['emoji']}  Theme set to: {C.BOLD}{C.WHITE}{t['name']}{C.RESET}")
        print(f"  {C.GRAY}{t['desc']}{C.RESET}\n")
    else:
        print(C.error(f"Unknown theme: {theme_name}"))
        print(f"  Available: {C.CYAN}{' | '.join(THEMES.keys())}{C.RESET}")
        return 1
    return 0


# ════════════════════════════════════════════════════════════════════
#  alias
# ════════════════════════════════════════════════════════════════════

def cmd_alias(args: list, state: dict) -> int:
    """alias [name=command] — Manage persistent aliases."""
    aliases = state.get("aliases", {})

    # List aliases
    if not args:
        if not aliases:
            print(C.info("No aliases defined. Use: alias name='command'"))
            return 0
        rows = [(C.paint(k, C.CYAN), C.paint(v, C.WHITE)) for k, v in sorted(aliases.items())]
        print()
        print(table(rows, headers=["ALIAS", "COMMAND"], title="ALIASES"))
        print()
        return 0

    # Remove alias
    if args[0] == "--del" or args[0] == "-d":
        if len(args) < 2:
            print(C.error("Usage: alias --del <name>"))
            return 1
        name = args[1]
        if name in aliases:
            del aliases[name]
            state["aliases"] = aliases
            save_aliases(aliases)
            print(C.success(f"Alias '{name}' removed."))
        else:
            print(C.warn(f"Alias '{name}' not found."))
            return 1
        return 0

    # Add alias: alias ll='ls -la'  OR  alias ll ls -la
    raw = " ".join(args)
    if "=" in raw:
        name, _, cmd = raw.partition("=")
        name = name.strip()
        cmd  = cmd.strip().strip("'\"")
    elif len(args) >= 2:
        name = args[0]
        cmd  = " ".join(args[1:])
    else:
        # Show single alias
        name = args[0]
        if name in aliases:
            print(f"  {C.CYAN}{name}{C.RESET} = {C.WHITE}{aliases[name]!r}{C.RESET}")
        else:
            print(C.warn(f"Alias '{name}' not found."))
        return 0

    aliases[name] = cmd
    state["aliases"] = aliases
    save_aliases(aliases)
    print(C.success(f"Alias set: {name} → {cmd}"))
    return 0


# ════════════════════════════════════════════════════════════════════
#  bookmark
# ════════════════════════════════════════════════════════════════════

def cmd_bookmark(args: list, state: dict) -> int:
    """
    bookmark           — List bookmarks
    bookmark add [name] — Add current dir (or named)
    bookmark go <name>  — cd to bookmark
    bookmark del <name> — Remove bookmark
    """
    bookmarks = state.get("bookmarks", {})

    if not args or args[0] == "list":
        if not bookmarks:
            print(C.info("No bookmarks. Use: bookmark add [name]"))
            return 0
        rows = [(C.paint(k, C.CYAN), C.paint(v, C.WHITE)) for k, v in sorted(bookmarks.items())]
        print()
        print(table(rows, headers=["NAME", "PATH"], title="📌 BOOKMARKS"))
        print(f"\n  Use {C.CYAN}bookmark go <name>{C.RESET} to jump to a bookmark.\n")
        return 0

    subcmd = args[0]

    if subcmd == "add":
        name = args[1] if len(args) > 1 else os.path.basename(state["cwd"]) or "home"
        path = state["cwd"]
        bookmarks[name] = path
        state["bookmarks"] = bookmarks
        save_bookmarks(bookmarks)
        print(C.success(f"Bookmark '{name}' → {path}"))

    elif subcmd == "go":
        if len(args) < 2:
            print(C.error("Usage: bookmark go <name>"))
            return 1
        name = args[1]
        if name not in bookmarks:
            print(C.error(f"Bookmark '{name}' not found."))
            available = ", ".join(bookmarks.keys()) or "(none)"
            print(f"  Available: {C.CYAN}{available}{C.RESET}")
            return 1
        path = bookmarks[name]
        return cmd_cd([path], state)

    elif subcmd in ("del", "rm", "remove"):
        if len(args) < 2:
            print(C.error("Usage: bookmark del <name>"))
            return 1
        name = args[1]
        if name in bookmarks:
            del bookmarks[name]
            state["bookmarks"] = bookmarks
            save_bookmarks(bookmarks)
            print(C.success(f"Bookmark '{name}' removed."))
        else:
            print(C.warn(f"Bookmark '{name}' not found."))
            return 1
    else:
        print(C.error(f"Unknown subcommand: {subcmd}"))
        print(f"  Usage: {C.CYAN}bookmark [list|add|go|del]{C.RESET}")
        return 1

    return 0


# ════════════════════════════════════════════════════════════════════
#  note
# ════════════════════════════════════════════════════════════════════

def cmd_note(args: list, state: dict) -> int:
    """
    note           — List all notes
    note add <text> — Add a note
    note del <id>   — Delete note by ID
    """
    if not args or args[0] == "list" or args[0] == "ls":
        notes = load_notes()
        if not notes:
            print(C.info("No notes. Use: note add <your note>"))
            return 0
        rows = []
        for n in notes:
            ts = n.get("timestamp", "")[:16].replace("T", " ")
            rows.append((
                C.paint(str(n["id"]), C.CYAN),
                C.paint(n["text"][:50], C.WHITE),
                C.paint(ts, C.GRAY),
            ))
        print()
        print(table(rows, headers=["ID", "NOTE", "TIMESTAMP"], title="📝 NOTES"))
        print()
        return 0

    if args[0] == "add":
        if len(args) < 2:
            print(C.error("Usage: note add <text>"))
            return 1
        text = " ".join(args[1:])
        n = add_note(text)
        print(C.success(f"Note #{n['id']} saved."))
        return 0

    if args[0] in ("del", "rm", "delete"):
        if len(args) < 2:
            print(C.error("Usage: note del <id>"))
            return 1
        try:
            nid = int(args[1])
        except ValueError:
            print(C.error("ID must be a number"))
            return 1
        if delete_note(nid):
            print(C.success(f"Note #{nid} deleted."))
        else:
            print(C.warn(f"Note #{nid} not found."))
            return 1
        return 0

    # Treat bare args as "add"
    text = " ".join(args)
    n = add_note(text)
    print(C.success(f"Note #{n['id']} saved."))
    return 0


# ════════════════════════════════════════════════════════════════════
#  todo
# ════════════════════════════════════════════════════════════════════

def cmd_todo(args: list, state: dict) -> int:
    """
    todo                      — List all tasks
    todo add <task> [--high]  — Add task
    todo done <id>            — Mark as done
    todo del <id>             — Delete task
    todo clear                — Remove all done tasks
    """
    if not args or args[0] in ("list", "ls"):
        todos = load_todos()
        if not todos:
            print(C.info("No tasks. Use: todo add <task>"))
            return 0

        pending  = [t for t in todos if not t["done"]]
        done_t   = [t for t in todos if t["done"]]

        if pending:
            rows = []
            for t in pending:
                pri_map = {"high": C.paint("HIGH", C.RED, bold=True),
                           "low":  C.paint("LOW",  C.GRAY),
                           "normal": C.paint("NORM", C.WHITE)}
                pri = pri_map.get(t.get("priority","normal"), t.get("priority",""))
                rows.append((C.paint(str(t["id"]), C.CYAN), C.paint(t["task"][:50], C.WHITE), pri))
            print()
            print(table(rows, headers=["ID", "TASK", "PRIORITY"], title="📋 TODO — PENDING"))

        if done_t:
            rows = []
            for t in done_t:
                rows.append((
                    C.paint(str(t["id"]), C.GRAY),
                    C.paint(t["task"][:50], C.DIM + C.GRAY),
                    C.paint("DONE ✔", C.GREEN)
                ))
            print()
            print(table(rows, headers=["ID", "TASK", "STATUS"], title="✅ DONE"))
        print()
        return 0

    subcmd = args[0]

    if subcmd == "add":
        if len(args) < 2:
            print(C.error("Usage: todo add <task> [--high|--low]"))
            return 1
        priority = "normal"
        task_args = [a for a in args[1:] if a not in ("--high","--low","--normal")]
        if "--high" in args: priority = "high"
        if "--low"  in args: priority = "low"
        task = " ".join(task_args)
        t = add_todo(task, priority)
        print(C.success(f"Task #{t['id']} added: {task}"))
        return 0

    if subcmd == "done":
        if len(args) < 2:
            print(C.error("Usage: todo done <id>"))
            return 1
        try:
            tid = int(args[1])
        except ValueError:
            print(C.error("ID must be a number"))
            return 1
        if complete_todo(tid):
            print(C.success(f"Task #{tid} marked as done! ✔"))
        else:
            print(C.warn(f"Task #{tid} not found."))
            return 1
        return 0

    if subcmd in ("del", "rm", "delete"):
        if len(args) < 2:
            print(C.error("Usage: todo del <id>"))
            return 1
        try:
            tid = int(args[1])
        except ValueError:
            print(C.error("ID must be a number"))
            return 1
        if delete_todo(tid):
            print(C.success(f"Task #{tid} deleted."))
        else:
            print(C.warn(f"Task #{tid} not found."))
            return 1
        return 0

    if subcmd == "clear":
        todos = load_todos()
        remaining = [t for t in todos if not t["done"]]
        removed   = len(todos) - len(remaining)
        from utils.config import save_todos
        for i, t in enumerate(remaining, start=1):
            t["id"] = i
        save_todos(remaining)
        print(C.success(f"Cleared {removed} completed task(s)."))
        return 0

    print(C.error(f"Unknown subcommand: {subcmd}"))
    print(f"  Usage: {C.CYAN}todo [list|add|done|del|clear]{C.RESET}")
    return 1


# ════════════════════════════════════════════════════════════════════
#  sysinfo
# ════════════════════════════════════════════════════════════════════

def cmd_sysinfo(args: list, state: dict) -> int:
    """Live system information dashboard."""
    try:
        import psutil
        has_psutil = True
    except ImportError:
        has_psutil = False

    import socket

    def row(label, value, color=C.WHITE):
        clean_val = str(value)
        pad = 48 - len(label) - len(clean_val)
        return (
            f"{C.BLUE}║{C.RESET}  {C.CYAN}{label:<18}{C.RESET}: "
            f"{color}{value}{C.RESET}{' '*max(0,pad)}{C.BLUE}║{C.RESET}"
        )

    print(f"\n{C.BLUE}╔{'═'*52}╗{C.RESET}")
    print(f"{C.BLUE}║{C.RESET}  {C.RED}{C.BOLD} KALI TERMINAL v1.0 — SYSTEM MONITOR {C.RESET}{'':14}{C.BLUE}║{C.RESET}")
    print(f"{C.BLUE}╠{'═'*52}╣{C.RESET}")
    print(row("Hostname",   socket.gethostname()))
    print(row("OS",         platform.system() + " " + platform.release(), C.GREEN))
    print(row("Kernel",     platform.version()[:32] + "…", C.GRAY))
    print(row("Arch",       platform.machine(), C.YELLOW))
    print(row("Python",     platform.python_version(), C.GREEN))
    print(row("Theme",      THEMES.get(get_active_theme(),{}).get("name","—"), C.MAGENTA))
    print(row("CWD",        state.get("cwd","?")[:35], C.CYAN))
    print(row("DateTime",   datetime.now().strftime("%Y-%m-%d %H:%M:%S"), C.YELLOW))

    if has_psutil:
        import psutil
        vm   = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        cpu_pct  = psutil.cpu_percent(interval=0.3)
        cpu_freq = psutil.cpu_freq()

        print(f"{C.BLUE}╠{'═'*52}╣{C.RESET}")
        print(row("CPU Usage",  f"{bar(cpu_pct, 14)} {cpu_pct:.1f}%"))
        print(row("CPU Cores",  str(psutil.cpu_count(logical=True))))
        if cpu_freq:
            print(row("CPU Freq",   f"{cpu_freq.current:.0f} MHz"))
        print(row("RAM Used",   f"{bar(vm.percent, 14)} {vm.percent:.1f}%"))
        print(row("RAM Total",  f"{vm.total//(1024**2)} MB"))
        print(row("Disk Used",  f"{bar(disk.percent, 14)} {disk.percent:.1f}%"))
        print(row("Disk Free",  f"{disk.free//(1024**3)} GB free", C.GREEN))

        print(f"{C.BLUE}╠{'═'*52}╣{C.RESET}")
        net = psutil.net_if_addrs()
        net_io = psutil.net_io_counters(pernic=True)
        for iface, addrs in list(net.items())[:4]:
            for addr in addrs:
                if addr.family == 2:
                    io = net_io.get(iface)
                    sent = f"{(io.bytes_sent//(1024**2))}MB↑" if io else ""
                    recv = f"{(io.bytes_recv//(1024**2))}MB↓" if io else ""
                    print(row(f"IP ({iface})", f"{addr.address}  {sent} {recv}", C.GREEN))

        procs = len(psutil.pids())
        print(row("Processes",  str(procs), C.WHITE))
        uptime_secs = time.time() - psutil.boot_time()
        h = int(uptime_secs // 3600)
        m = int((uptime_secs % 3600) // 60)
        print(row("Uptime",     f"{h}h {m}m", C.YELLOW))

    print(f"{C.BLUE}╚{'═'*52}╝{C.RESET}\n")
    return 0


# ════════════════════════════════════════════════════════════════════
#  monitor (live)
# ════════════════════════════════════════════════════════════════════

def cmd_monitor(args: list, state: dict) -> int:
    """Live system monitor — updates every second. Press Ctrl+C to exit."""
    try:
        import psutil
    except ImportError:
        print(C.error("psutil required: pip install psutil"))
        return 1

    print(f"  {C.GRAY}Live monitor — Ctrl+C to exit{C.RESET}\n")
    try:
        while True:
            os.system("clear")
            print(f"{C.BLUE}{'═'*60}{C.RESET}")
            print(f"  {C.BOLD}{C.RED}KALI LIVE MONITOR{C.RESET}  "
                  f"{C.GRAY}{datetime.now().strftime('%H:%M:%S')}{C.RESET}")
            print(f"{C.BLUE}{'═'*60}{C.RESET}\n")

            cpu_pcts = psutil.cpu_percent(interval=None, percpu=True)
            for i, pct in enumerate(cpu_pcts):
                label = f"CPU{i:<3}"
                b = bar(pct, width=30)
                print(f"  {C.CYAN}{label}{C.RESET} {b}")

            vm   = psutil.virtual_memory()
            swap = psutil.swap_memory()
            disk = psutil.disk_usage("/")
            print()
            print(f"  {C.CYAN}{'RAM':<4}{C.RESET} {bar(vm.percent, 30)}  "
                  f"{vm.used//(1024**2)}/{vm.total//(1024**2)} MB")
            print(f"  {C.CYAN}{'SWAP':<4}{C.RESET} {bar(swap.percent, 30)}  "
                  f"{swap.used//(1024**2)}/{swap.total//(1024**2)} MB")
            print(f"  {C.CYAN}{'DISK':<4}{C.RESET} {bar(disk.percent, 30)}  "
                  f"{disk.used//(1024**3)}/{disk.total//(1024**3)} GB")

            # Top 5 processes
            print(f"\n  {C.BOLD}{C.WHITE}TOP PROCESSES{C.RESET}")
            procs = sorted(psutil.process_iter(["pid","name","cpu_percent","memory_percent"]),
                           key=lambda p: p.info.get("cpu_percent",0) or 0, reverse=True)[:5]
            for p in procs:
                name = (p.info.get("name","?") or "?")[:20]
                cpu  = p.info.get("cpu_percent") or 0
                mem  = p.info.get("memory_percent") or 0
                pid  = p.info.get("pid", 0)
                print(f"  {C.GRAY}{pid:<7}{C.RESET}{C.CYAN}{name:<22}{C.RESET}"
                      f"CPU:{C.YELLOW}{cpu:5.1f}%{C.RESET}  MEM:{C.GREEN}{mem:5.1f}%{C.RESET}")

            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{C.info('Monitor stopped.')}\n")
    return 0


# ════════════════════════════════════════════════════════════════════
#  matrix
# ════════════════════════════════════════════════════════════════════

def cmd_matrix(args: list, state: dict) -> int:
    """Matrix digital rain animation. Press Ctrl+C to exit."""
    cols, rows = shutil.get_terminal_size(fallback=(80, 24))
    chars = list("ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789")

    GREEN_BRIGHT = "\033[38;5;46m"
    GREEN_DIM    = "\033[38;5;22m"
    WHITE        = "\033[97m"

    # Column state: each col has a "drop" at some y position
    drops = [random.randint(-rows, 0) for _ in range(cols)]

    print("\033[?25l", end="")   # hide cursor
    os.system("clear")
    try:
        while True:
            for col in range(cols):
                y = drops[col]
                if 0 <= y < rows:
                    ch = random.choice(chars)
                    # Head: bright white
                    sys.stdout.write(f"\033[{y+1};{col+1}H{WHITE}{ch}{C.RESET}")
                    # Trail: fade out
                    for trail in range(1, 6):
                        ty = y - trail
                        if 0 <= ty < rows:
                            faded = random.choice(chars)
                            sys.stdout.write(f"\033[{ty+1};{col+1}H{GREEN_DIM}{faded}{C.RESET}")
                    # Erase tail
                    tail_y = y - 8
                    if 0 <= tail_y < rows:
                        sys.stdout.write(f"\033[{tail_y+1};{col+1}H {C.RESET}")

                drops[col] += 1
                if drops[col] > rows + 8:
                    drops[col] = random.randint(-rows, 0)

            sys.stdout.flush()
            time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        os.system("clear")
        print("\033[?25h", end="")   # show cursor
        print(f"\n{C.GREEN}Welcome back to reality.{C.RESET}\n")
    return 0


# ════════════════════════════════════════════════════════════════════
#  tree
# ════════════════════════════════════════════════════════════════════

def cmd_tree(args: list, state: dict) -> int:
    """tree [path] [--depth N] — Colored directory tree."""
    target = state["cwd"]
    depth  = 3

    i = 0
    while i < len(args):
        if args[i] in ("--depth", "-d") and i + 1 < len(args):
            try:
                depth = int(args[i+1])
            except ValueError:
                pass
            i += 2
        else:
            p = os.path.expanduser(args[i])
            if not os.path.isabs(p):
                p = os.path.join(state["cwd"], p)
            target = p
            i += 1

    if not os.path.isdir(target):
        print(C.error(f"Not a directory: {target}"))
        return 1

    name = C.paint(os.path.basename(target) or target, C.BLUE, bold=True) + "/"
    print(f"\n{name}")
    lines = tree_view(target, max_depth=depth)
    for line in lines:
        print(line)

    total_files = sum(1 for _ in lines if not _.endswith("/"))
    print(f"\n{C.GRAY}{len(lines)} entries{C.RESET}\n")
    return 0


# ════════════════════════════════════════════════════════════════════
#  calc
# ════════════════════════════════════════════════════════════════════

def cmd_calc(args: list, state: dict) -> int:
    """
    calc <expression> — Safe Python math evaluator.
    Supports: +,-,*,/,**,%, sqrt, sin, cos, log, pi, e, abs, round, hex, bin
    """
    if not args:
        print(C.error("Usage: calc <expression>   e.g. calc 2**10  or  calc sqrt(144)"))
        return 1

    expr = " ".join(args)

    # Safe evaluation context
    safe_globals = {
        "__builtins__": {},
        "abs": abs, "round": round, "max": max, "min": min,
        "int": int, "float": float, "hex": hex, "bin": bin, "oct": oct,
        "sqrt":  math.sqrt,  "log":   math.log,   "log2":  math.log2,
        "log10": math.log10, "exp":   math.exp,    "pow":   math.pow,
        "sin":   math.sin,   "cos":   math.cos,    "tan":   math.tan,
        "asin":  math.asin,  "acos":  math.acos,   "atan":  math.atan,
        "atan2": math.atan2, "floor": math.floor,  "ceil":  math.ceil,
        "pi":    math.pi,    "e":     math.e,
        "inf":   math.inf,   "tau":   math.tau,
        "factorial": math.factorial,
    }

    try:
        result = eval(expr, safe_globals, {})
        print(f"\n  {C.CYAN}{expr}{C.RESET}  =  {C.GREEN}{C.BOLD}{result}{C.RESET}\n")
        if isinstance(result, int) and abs(result) < 2**32:
            print(f"  {C.GRAY}HEX: {hex(result)}  BIN: {bin(result)}  OCT: {oct(result)}{C.RESET}\n")
    except ZeroDivisionError:
        print(C.error("Division by zero"))
        return 1
    except (SyntaxError, NameError, TypeError) as e:
        print(C.error(f"Invalid expression: {e}"))
        return 1
    except Exception as e:
        print(C.error(f"Error: {e}"))
        return 1
    return 0


# ════════════════════════════════════════════════════════════════════
#  weather
# ════════════════════════════════════════════════════════════════════

def cmd_weather(args: list, state: dict) -> int:
    """weather [city] — ASCII weather from wttr.in"""
    city = "+".join(args) if args else ""
    url  = f"https://wttr.in/{city}?T"

    print(f"\n{C.GRAY}Fetching weather...{C.RESET}\n")
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "5", url],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout:
            # Print first 20 lines of weather
            for line in result.stdout.splitlines()[:24]:
                print(f"  {line}")
        else:
            print(C.warn("Could not fetch weather. Check your internet connection."))
            return 1
    except FileNotFoundError:
        print(C.warn("curl not found. Install curl or check your PATH."))
        return 1
    print()
    return 0


# ════════════════════════════════════════════════════════════════════
#  set (preferences)
# ════════════════════════════════════════════════════════════════════

def cmd_set(args: list, state: dict) -> int:
    """set [key] [value] — Get/set terminal preferences."""
    prefs = load_prefs()

    if not args:
        rows = [(C.paint(k, C.CYAN), C.paint(str(v), C.WHITE))
                for k, v in sorted(prefs.items())]
        print()
        print(table(rows, headers=["PREFERENCE", "VALUE"], title="⚙  PREFERENCES"))
        print()
        return 0

    if len(args) == 1:
        key = args[0]
        val = prefs.get(key, "(not set)")
        print(f"  {C.CYAN}{key}{C.RESET} = {C.WHITE}{val}{C.RESET}")
        return 0

    key   = args[0]
    value = args[1]

    # Type coercion
    if value.lower() == "true":    value = True
    elif value.lower() == "false": value = False
    elif value.isdigit():          value = int(value)

    set_pref(key, value)
    state["prefs"] = load_prefs()
    print(C.success(f"Set {key} = {value}"))
    return 0


# ════════════════════════════════════════════════════════════════════
#  about
# ════════════════════════════════════════════════════════════════════

def cmd_about(args: list, state: dict) -> int:
    """Show information about Kali Terminal."""
    lines = [
        f"{C.RED}{C.BOLD}KALI TERMINAL v1.0.0{C.RESET}",
        f"{C.GRAY}────────────────────────────────────────{C.RESET}",
        f"  {C.CYAN}Author    {C.RESET}: Built for elite hackers & learners",
        f"  {C.CYAN}Engine    {C.RESET}: Pure Python (no binary deps)",
        f"  {C.CYAN}Themes    {C.RESET}: Kali · Dracula · Matrix · Ocean · Blood",
        f"  {C.CYAN}Features  {C.RESET}:",
        f"    {C.GREEN}▸{C.RESET} AI Assistant (Claude-powered)",
        f"    {C.GREEN}▸{C.RESET} TCP Port Scanner & Ping Sweep",
        f"    {C.GREEN}▸{C.RESET} DNS Lookup & HTTP Header Inspector",
        f"    {C.GREEN}▸{C.RESET} Hash Engine (MD5/SHA/BLAKE2)",
        f"    {C.GREEN}▸{C.RESET} Encode/Decode (Base64/Hex/Binary/Morse)",
        f"    {C.GREEN}▸{C.RESET} Caesar/XOR Cipher + Password Generator",
        f"    {C.GREEN}▸{C.RESET} Persistent Aliases, Bookmarks, Notes, TODO",
        f"    {C.GREEN}▸{C.RESET} Live System Monitor (CPU/RAM/Disk/Net)",
        f"    {C.GREEN}▸{C.RESET} Matrix Rain Animation",
        f"    {C.GREEN}▸{C.RESET} Git-Aware Prompt",
        f"    {C.GREEN}▸{C.RESET} Tree View, Calculator, Weather",
        f"    {C.GREEN}▸{C.RESET} Smart Tab Completion",
        f"    {C.GREEN}▸{C.RESET} Session Persistence",
        f"  {C.GRAY}────────────────────────────────────────{C.RESET}",
        f"  {C.YELLOW}Config dir: {C.CYAN}~/.kali_terminal/{C.RESET}",
    ]

    print()
    for line in lines:
        print(f"  {line}")
    print()
    return 0


# ════════════════════════════════════════════════════════════════════
#  tips
# ════════════════════════════════════════════════════════════════════

TIPS = [
    "Use `!!` to repeat the last command.",
    "Use `!$` to reuse the last argument of the previous command.",
    "Press `Ctrl+R` to search command history interactively.",
    "`man command` opens the manual page for any command.",
    "Use `Ctrl+A` to jump to beginning, `Ctrl+E` to end of line.",
    "`watch -n 2 command` runs a command every 2 seconds.",
    "`xargs` converts stdin to arguments: find . -name '*.py' | xargs wc -l",
    "Use `tee` to write output to a file AND stdout: cmd | tee output.txt",
    "Use `screen` or `tmux` for persistent terminal sessions over SSH.",
    "`lsof -i :8080` shows what's using port 8080.",
    "Use `strace cmd` to trace all system calls a program makes.",
    "`dmesg | tail` shows recent kernel messages.",
    "Use curly braces: `cp file.txt{,.bak}` copies to file.txt.bak",
    "Try `nmap -sV <host>` to detect service versions.",
    "Use `grep -r` to search recursively through directories.",
    "Python one-liner server: `python3 -m http.server 8080`",
    "`alias ll='ls -la --color=auto'` creates a quick directory list shortcut.",
    "Use `set show_git_branch true` to enable git branch in the prompt.",
    "Try `scan <host> 1 65535` for a full TCP port scan.",
    "Use `bookmark add work` to save your current directory as 'work'.",
    "`todo add --high Fix the buffer overflow` adds a high-priority task.",
    "Use `passgen 32` to generate a 32-character secure password.",
    "`hash all secret123` shows MD5, SHA1, SHA256, SHA512 all at once.",
    "Try `theme matrix` for the hacker aesthetic. `theme dracula` for style.",
    "Use `encode morse Hello World` to translate to Morse code.",
]


def cmd_tips(args: list, state: dict) -> int:
    """Show a random pro-tip, or `tips all` to list all."""
    if args and args[0] == "all":
        print(f"\n{C.BOLD}{C.BLUE}[ ALL PRO TIPS ]{C.RESET}\n")
        for i, tip in enumerate(TIPS, start=1):
            print(f"  {C.GRAY}{i:2d}.{C.RESET} {C.WHITE}{tip}{C.RESET}")
        print()
        return 0
    tip = random.choice(TIPS)
    print(f"\n  {C.YELLOW}💡 Pro Tip:{C.RESET}  {C.WHITE}{tip}{C.RESET}\n")
    return 0


# ════════════════════════════════════════════════════════════════════
#  cheatsheet (upgraded)
# ════════════════════════════════════════════════════════════════════

CHEATSHEET = {
    "FILE": [
        ("ls -la",              "List all files with details"),
        ("find / -name '*.py'", "Find files by name"),
        ("stat file",           "File metadata + timestamps"),
        ("chmod 755 script.sh", "Set executable permissions"),
        ("ln -s target link",   "Create symbolic link"),
        ("rsync -av src/ dst/", "Sync directories"),
        ("dd if=/dev/zero of=file bs=1M count=100", "Create file of size 100MB"),
    ],
    "NETWORK": [
        ("scan <host>",             "KaliTerm: TCP port scan"),
        ("ping_sweep 192.168.1.0/24", "KaliTerm: Ping sweep"),
        ("dns <domain> MX",         "KaliTerm: DNS MX records"),
        ("myip",                    "KaliTerm: Show all IPs"),
        ("banner_grab <host> 22",   "KaliTerm: Grab service banner"),
        ("http_headers <url>",      "KaliTerm: HTTP response headers"),
        ("nmap -sV -p- <host>",     "Full service scan"),
        ("curl -I https://site.com","HTTP head request"),
        ("ss -tulnp",               "Listening ports + programs"),
        ("ip route show",           "Show routing table"),
        ("tcpdump -i eth0",         "Live packet capture"),
        ("nc -lvp 4444",            "Listen on port 4444"),
    ],
    "CRYPTO": [
        ("hash sha256 <text>",       "KaliTerm: SHA256 hash"),
        ("hash all <text>",          "KaliTerm: All hash algos"),
        ("encode base64 <text>",     "KaliTerm: Base64 encode"),
        ("decode base64 <text>",     "KaliTerm: Base64 decode"),
        ("passgen 32",               "KaliTerm: 32-char password"),
        ("pwdcheck <password>",      "KaliTerm: Password strength"),
        ("caesar 13 <text>",         "KaliTerm: ROT13/Caesar"),
        ("openssl enc -aes-256-cbc", "AES encrypt a file"),
        ("gpg --symmetric file",     "GPG symmetric encrypt"),
    ],
    "SYSTEM": [
        ("ps aux | grep <name>",    "Find process by name"),
        ("kill -9 <PID>",           "Force kill process"),
        ("lsof -i :<port>",         "What's using this port?"),
        ("strace -p <PID>",         "Trace syscalls of process"),
        ("ulimit -a",               "Show resource limits"),
        ("systemctl status <svc>",  "Check service status"),
        ("journalctl -f",           "Follow system journal"),
        ("crontab -e",              "Edit cron jobs"),
        ("df -h && du -sh /*",      "Disk space by directory"),
    ],
    "GIT": [
        ("git log --oneline --graph","Visual branch log"),
        ("git stash pop",            "Apply stashed changes"),
        ("git diff HEAD~1",          "Diff vs last commit"),
        ("git blame file",           "Who wrote each line?"),
        ("git bisect start",         "Binary search for bug commit"),
        ("git rebase -i HEAD~3",     "Interactive rebase last 3"),
        ("git cherry-pick <hash>",   "Apply specific commit"),
        ("git reflog",               "History of HEAD changes"),
    ],
    "PYTHON": [
        ("python3 -m venv .venv",        "Create virtual env"),
        ("python3 -m http.server 8080",  "Quick HTTP server"),
        ("python3 -m json.tool file.json","Pretty-print JSON"),
        ("python3 -c 'import this'",     "The Zen of Python"),
        ("pip show <package>",           "Package info"),
        ("pip list --outdated",          "Outdated packages"),
        ("python3 -m pdb script.py",     "Debug with pdb"),
        ("python3 -m timeit 'code'",     "Benchmark code"),
    ],
}


def cmd_cheatsheet(args: list, state: dict) -> int:
    """cheatsheet [section] — Linux/Kali command reference."""
    filter_term = args[0].upper() if args else None

    shown = 0
    for section, rows in CHEATSHEET.items():
        if filter_term and filter_term not in section.upper():
            continue
        shown += 1
        print(f"\n  {C.RED}{C.BOLD}▶ {section}{C.RESET}")
        print(f"  {C.BLUE}{'─'*62}{C.RESET}")
        for cmd_str, desc in rows:
            cmd_col  = C.paint(f"  {cmd_str:<42}", C.CYAN)
            desc_col = C.paint(desc, C.GRAY)
            print(f"{cmd_col}{desc_col}")

    if shown == 0:
        avail = " | ".join(CHEATSHEET.keys())
        print(C.warn(f"No section '{args[0]}'. Available: {avail}"))
        return 1
    print()
    return 0


# ════════════════════════════════════════════════════════════════════
#  help
# ════════════════════════════════════════════════════════════════════

def cmd_help(args: list, state: dict) -> int:
    """Show all built-in commands."""
    cmds = [
        ("NAVIGATION", [
            ("cd [path]",           "Change directory (supports ~, -, ..)"),
            ("tree [path] [-d N]",  "Colored directory tree"),
            ("bookmark [add|go|del]","Named directory bookmarks"),
        ]),
        ("SYSTEM", [
            ("sysinfo",             "Full system info panel"),
            ("monitor",             "Live system monitor (Ctrl+C to stop)"),
            ("history [N]",         "Show last N commands"),
            ("clear / cls",         "Clear the screen"),
            ("calc <expr>",         "Python-powered calculator"),
            ("weather [city]",      "ASCII weather"),
        ]),
        ("THEME & CONFIG", [
            ("theme [name]",        "Switch theme: kali|dracula|matrix|ocean|blood"),
            ("alias [name=cmd]",    "Manage persistent aliases"),
            ("set [key] [value]",   "Manage terminal preferences"),
        ]),
        ("NOTES & TASKS", [
            ("note [add|list|del]", "In-terminal sticky notes"),
            ("todo [add|done|del]", "TODO task manager"),
        ]),
        ("NETWORK TOOLS", [
            ("scan <host> [ports]", "TCP port scanner with service detection"),
            ("ping_sweep <subnet>", "ICMP ping sweep e.g. ping_sweep 192.168.1.0/24"),
            ("dns <domain> [type]", "DNS lookup (A, MX, TXT, NS, CNAME...)"),
            ("myip",                "Show all network interfaces + external IP"),
            ("banner_grab <h> <p>", "Grab service banner via TCP"),
            ("http_headers <url>",  "Inspect HTTP response headers"),
        ]),
        ("CRYPTO SUITE", [
            ("hash <algo> <text>",  "Hash: md5|sha1|sha256|sha512|blake2b|all"),
            ("encode <method> <t>", "Encode: base64|url|hex|binary|html|morse"),
            ("decode <method> <t>", "Decode the above"),
            ("caesar <n> <text>",   "Caesar cipher (--brute for all 26)"),
            ("xor <key> <hex>",     "XOR a hex string with a key"),
            ("passgen [len]",       "Generate secure random password"),
            ("pwdcheck <pwd>",      "Analyze password strength"),
        ]),
        ("FUN", [
            ("matrix",              "Matrix digital rain animation"),
            ("tips [all]",          "Random Linux pro-tip"),
            ("cheatsheet [topic]",  "Quick command reference"),
            ("about",               "About this terminal"),
        ]),
        ("AI", [
            ("ai <question>",       "Ask the built-in AI assistant (Claude)"),
            ("ai --setup <key>",    "Set your Anthropic API key"),
        ]),
    ]

    print(f"\n{C.BLUE}╔{'═'*66}╗{C.RESET}")
    print(f"{C.BLUE}║{C.RESET}  {C.RED}{C.BOLD}  KALI TERMINAL v1.0 — COMMAND REFERENCE{C.RESET}{'':26}{C.BLUE}║{C.RESET}")
    print(f"{C.BLUE}╠{'═'*66}╣{C.RESET}")

    for section_name, section_cmds in cmds:
        print(f"{C.BLUE}║{C.RESET}  {C.YELLOW}{C.BOLD}{section_name}{C.RESET}")
        for cmd_str, desc in section_cmds:
            c   = C.paint(f"    {cmd_str:<30}", C.CYAN)
            d   = C.paint(desc, C.WHITE)
            pad = 66 - 4 - 30 - len(desc) - 2
            print(f"{C.BLUE}║{C.RESET}{c}{d}{' '*max(0,pad)}{C.BLUE}║{C.RESET}")
        print(f"{C.BLUE}╠{'═'*66}╣{C.RESET}")

    print(f"{C.BLUE}║{C.RESET}  {C.GRAY}All real Linux commands work too (ls, grep, nmap, curl, git…)      {C.BLUE}║{C.RESET}")
    print(f"{C.BLUE}║{C.RESET}  {C.GRAY}Tab completion · ↑↓ history · Ctrl+C cancel · Ctrl+D exit         {C.BLUE}║{C.RESET}")
    print(f"{C.BLUE}╚{'═'*66}╝{C.RESET}\n")
    return 0


# ════════════════════════════════════════════════════════════════════
#  Dispatch Table
# ════════════════════════════════════════════════════════════════════

BUILTINS: dict = {
    # Navigation
    "cd":           cmd_cd,
    "tree":         cmd_tree,
    "bookmark":     cmd_bookmark,
    "bm":           cmd_bookmark,

    # System
    "clear":        cmd_clear,
    "cls":          cmd_clear,
    "history":      cmd_history,
    "sysinfo":      cmd_sysinfo,
    "monitor":      cmd_monitor,
    "calc":         cmd_calc,
    "weather":      cmd_weather,

    # Theme & Config
    "theme":        cmd_theme,
    "alias":        cmd_alias,
    "set":          cmd_set,

    # Notes & Tasks
    "note":         cmd_note,
    "notes":        cmd_note,
    "todo":         cmd_todo,
    "todos":        cmd_todo,

    # Fun
    "matrix":       cmd_matrix,
    "tips":         cmd_tips,
    "cheatsheet":   cmd_cheatsheet,
    "help":         cmd_help,
    "about":        cmd_about,
    "?":            cmd_help,
}
