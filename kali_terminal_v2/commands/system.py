"""
commands/system.py — System monitoring tools for KaliTerminal v2.

Commands:
  disk-usage      Visual disk usage analyzer (tree view)
  proc-monitor    Process monitor (top/search/kill/tree)
"""

import os
import sys
import signal
import time
import subprocess

from ui.theme import Colors

C = Colors


# ══════════════════════════════════════════════════════════════════════════════
#  DISK USAGE
# ══════════════════════════════════════════════════════════════════════════════

def cmd_disk_usage(args: list, state: dict) -> int:
    """
    disk-usage [path] [options]
    Options:
      --depth <n>     max depth (default: 2)
      --top <n>       show top N entries by size (default: 20)
      --sort size|name  sort order (default: size)
    """
    try:
        import psutil
        has_psutil = True
    except ImportError:
        has_psutil = False

    path    = args[0] if args and not args[0].startswith("-") else state.get("cwd", os.getcwd())
    depth   = 2
    top     = 20
    sort_by = "size"

    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--depth", "-d") and i+1 < len(args):
            depth = int(args[i+1]); i += 2
        elif a in ("--top", "-t") and i+1 < len(args):
            top = int(args[i+1]); i += 2
        elif a in ("--sort", "-s") and i+1 < len(args):
            sort_by = args[i+1]; i += 2
        else:
            i += 1

    if not os.path.isabs(path):
        path = os.path.join(state.get("cwd", os.getcwd()), path)

    path = os.path.normpath(path)
    if not os.path.exists(path):
        print(C.error(f"Path not found: {path}"))
        return 1

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}DISK USAGE: {path}{C.RESET}")
    print(f"{C.BLUE}{'═'*65}{C.RESET}\n")

    # ── Filesystem overview ────────────────────────────────────────────────
    if has_psutil:
        import psutil
        try:
            disk = psutil.disk_usage(path)
            total = disk.total
            used  = disk.used
            free  = disk.free
            pct   = disk.percent
            bar   = C.progress_bar(pct, width=30)
            print(f"  {C.CYAN}Filesystem{C.RESET}")
            print(f"    Total : {_fmt_size(total)}")
            print(f"    Used  : {_fmt_size(used)}  {bar}")
            print(f"    Free  : {_fmt_size(free)}")
            print()
        except Exception:
            pass

    # ── Directory tree sizes ───────────────────────────────────────────────
    entries = []
    try:
        _walk_sizes(path, depth, 0, entries)
    except PermissionError:
        print(C.warn("Some directories required elevated privileges."))

    # Sort
    if sort_by == "name":
        entries.sort(key=lambda x: x[1].lower())
    else:
        entries.sort(key=lambda x: -x[0])

    # Find max size for bar scaling
    max_sz = max((e[0] for e in entries), default=1) or 1

    # Display
    print(f"  {C.BOLD}{C.GRAY}{'SIZE':<12}{'USAGE BAR':<35}{'PATH'}{C.RESET}")
    print(f"  {C.BLUE}{'─'*65}{C.RESET}")

    shown = 0
    for size, rel_path, is_dir in entries[:top]:
        bar_len  = int(30 * size / max_sz)
        bar_str  = "█" * bar_len + "░" * (30 - bar_len)
        icon     = "📁" if is_dir else "📄"
        sz_str   = _fmt_size(size)
        clr      = C.CYAN if is_dir else C.WHITE
        bar_clr  = C.GREEN if size < max_sz * 0.3 else C.YELLOW if size < max_sz * 0.7 else C.RED
        print(f"  {C.YELLOW}{sz_str:<12}{C.RESET}"
              f"{bar_clr}{bar_str}{C.RESET}  "
              f"{clr}{icon} {rel_path}{C.RESET}")
        shown += 1

    if len(entries) > top:
        print(f"  {C.GRAY}... and {len(entries)-top} more items{C.RESET}")

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}\n")
    return 0


def _walk_sizes(path: str, max_depth: int, cur_depth: int, out: list):
    """Recursively collect (size, rel_path, is_dir) tuples."""
    try:
        entries = os.scandir(path)
    except (PermissionError, NotADirectoryError):
        return

    base = os.path.dirname(path)

    for entry in entries:
        try:
            if entry.is_dir(follow_symlinks=False):
                size    = _dir_size(entry.path)
                rel     = os.path.relpath(entry.path, os.path.dirname(path))
                out.append((size, rel, True))
                if cur_depth < max_depth:
                    _walk_sizes(entry.path, max_depth, cur_depth+1, out)
            else:
                size = entry.stat(follow_symlinks=False).st_size
                rel  = os.path.relpath(entry.path, os.path.dirname(path))
                out.append((size, rel, False))
        except (PermissionError, OSError):
            continue


def _dir_size(path: str) -> int:
    """Get total size of a directory."""
    total = 0
    try:
        for dirpath, dirs, files in os.walk(path, followlinks=False):
            for f in files:
                try:
                    fp = os.path.join(dirpath, f)
                    total += os.stat(fp).st_size
                except (PermissionError, OSError):
                    pass
    except PermissionError:
        pass
    return total


def _fmt_size(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


# ══════════════════════════════════════════════════════════════════════════════
#  PROC MONITOR
# ══════════════════════════════════════════════════════════════════════════════

def cmd_proc_monitor(args: list, state: dict) -> int:
    """
    proc-monitor              — top 20 processes by CPU
    proc-monitor top [n]      — top N processes by CPU+RAM
    proc-monitor search <term>— search by name/cmdline
    proc-monitor kill <pid>   — kill a process
    proc-monitor tree         — process tree
    """
    try:
        import psutil
    except ImportError:
        print(C.error("psutil required: pip install psutil"))
        return 1

    sub = args[0] if args else "top"

    if sub == "top":
        n = int(args[1]) if len(args) > 1 and args[1].isdigit() else 20
        return _proc_top(n)

    if sub == "search" and len(args) > 1:
        term = " ".join(args[1:])
        return _proc_search(term)

    if sub == "kill" and len(args) > 1:
        return _proc_kill(args[1:], state)

    if sub == "tree":
        return _proc_tree()

    # Default: treat as search if not a keyword
    if sub not in ("top", "search", "kill", "tree"):
        return _proc_search(sub)

    return _proc_top(20)


def _proc_top(n: int) -> int:
    try:
        import psutil
    except ImportError:
        return 1

    procs = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent",
                                   "status", "username", "cmdline"]):
        try:
            info = p.info
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Second pass for accurate CPU%
    time.sleep(0.2)
    for p in psutil.process_iter(["pid", "name", "cpu_percent"]):
        try:
            for proc in procs:
                if proc["pid"] == p.pid:
                    proc["cpu_percent"] = p.cpu_percent()
        except Exception:
            pass

    procs.sort(key=lambda x: (x.get("cpu_percent") or 0) + (x.get("memory_percent") or 0) * 2,
               reverse=True)

    # Header
    print(f"\n{C.BLUE}{'═'*80}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}PROCESS MONITOR  —  Top {n}{C.RESET}")
    try:
        import psutil
        vm   = psutil.virtual_memory()
        cpu  = psutil.cpu_percent(interval=0.1)
        disk = psutil.disk_io_counters()
        print(f"  {C.GRAY}CPU: {cpu:.1f}%  RAM: {vm.percent:.1f}%  "
              f"({vm.used//(1024**2)}MB/{vm.total//(1024**2)}MB){C.RESET}")
    except Exception:
        pass
    print(f"{C.BLUE}{'═'*80}{C.RESET}\n")

    hdr = f"  {C.BOLD}{C.GRAY}{'PID':<8}{'USER':<12}{'CPU%':<8}{'MEM%':<8}{'STATUS':<12}NAME{C.RESET}"
    print(hdr)
    print(f"  {C.BLUE}{'─'*75}{C.RESET}")

    for p in procs[:n]:
        pid    = p.get("pid", 0)
        name   = (p.get("name") or "?")[:20]
        cpu    = p.get("cpu_percent") or 0.0
        mem    = p.get("memory_percent") or 0.0
        status = (p.get("status") or "?")[:10]
        user   = (p.get("username") or "?")[:10]

        cpu_clr = C.RED if cpu > 50 else C.YELLOW if cpu > 10 else C.GREEN
        mem_clr = C.RED if mem > 20 else C.YELLOW if mem > 5 else C.WHITE

        print(f"  {C.CYAN}{pid:<8}{C.RESET}"
              f"{C.GRAY}{user:<12}{C.RESET}"
              f"{cpu_clr}{cpu:<8.1f}{C.RESET}"
              f"{mem_clr}{mem:<8.2f}{C.RESET}"
              f"{C.GRAY}{status:<12}{C.RESET}"
              f"{C.WHITE}{name}{C.RESET}")

    print(f"\n{C.BLUE}{'═'*80}{C.RESET}\n")
    print(f"  {C.GRAY}Commands: proc-monitor search <name>  |  proc-monitor kill <pid>  |  proc-monitor tree{C.RESET}\n")
    return 0


def _proc_search(term: str) -> int:
    try:
        import psutil
    except ImportError:
        return 1

    print(f"\n{C.BLUE}{'═'*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}PROCESS SEARCH: '{term}'{C.RESET}")
    print(f"{C.BLUE}{'═'*70}{C.RESET}\n")

    found = []
    for p in psutil.process_iter(["pid", "name", "cmdline", "cpu_percent",
                                   "memory_percent", "status", "username"]):
        try:
            info  = p.info
            name  = (info.get("name") or "").lower()
            cmd   = " ".join(info.get("cmdline") or []).lower()
            if term.lower() in name or term.lower() in cmd:
                found.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if not found:
        print(C.warn(f"No processes matching '{term}'"))
        return 0

    print(f"  {C.GRAY}Found {len(found)} process(es){C.RESET}\n")

    for p in found:
        pid  = p.get("pid", 0)
        name = p.get("name", "?")
        cmd  = " ".join(p.get("cmdline") or [])[:60]
        cpu  = p.get("cpu_percent") or 0.0
        mem  = p.get("memory_percent") or 0.0
        user = p.get("username", "?")

        print(f"  {C.CYAN}PID  {C.RESET}: {C.GREEN}{pid}{C.RESET}")
        print(f"  {C.CYAN}Name {C.RESET}: {C.WHITE}{name}{C.RESET}")
        print(f"  {C.CYAN}User {C.RESET}: {user}")
        print(f"  {C.CYAN}CMD  {C.RESET}: {C.GRAY}{cmd}{C.RESET}")
        print(f"  {C.CYAN}CPU% {C.RESET}: {cpu:.1f}   {C.CYAN}MEM%{C.RESET}: {mem:.2f}")
        print()

    print(f"{C.BLUE}{'═'*70}{C.RESET}\n")
    return 0


def _proc_kill(args: list, state: dict) -> int:
    try:
        import psutil
    except ImportError:
        return 1

    if not args:
        print(C.error("Usage: proc-monitor kill <pid> [signal]"))
        return 1

    try:
        pid = int(args[0])
    except ValueError:
        print(C.error(f"Invalid PID: {args[0]}"))
        return 1

    sig = signal.SIGTERM
    if len(args) > 1:
        sig_map = {
            "SIGTERM": signal.SIGTERM, "SIGKILL": signal.SIGKILL,
            "SIGHUP": signal.SIGHUP,   "SIGINT": signal.SIGINT,
            "9": signal.SIGKILL,       "15": signal.SIGTERM,
        }
        sig = sig_map.get(args[1].upper(), signal.SIGTERM)

    try:
        import psutil
        p = psutil.Process(pid)
        pname = p.name()
        print(C.warn(f"Kill PID {pid} ({pname}) with {sig.name}? [y/N] "), end="")
        confirm = input().strip().lower()
        if confirm != "y":
            print(C.info("Cancelled."))
            return 0
        p.send_signal(sig)
        print(C.success(f"Signal {sig.name} sent to PID {pid} ({pname})"))
    except psutil.NoSuchProcess:
        print(C.error(f"PID {pid} not found."))
        return 1
    except psutil.AccessDenied:
        print(C.error(f"Access denied — try with sudo."))
        return 1

    return 0


def _proc_tree() -> int:
    """Show process tree using pstree if available, else build manually."""
    # Try system pstree first
    for cmd in [["pstree", "-p"], ["pstree"]]:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                print(f"\n{C.BLUE}{'═'*70}{C.RESET}")
                print(f"  {C.BOLD}{C.WHITE}PROCESS TREE{C.RESET}")
                print(f"{C.BLUE}{'═'*70}{C.RESET}\n")
                for line in res.stdout.splitlines()[:60]:
                    print(f"  {C.WHITE}{line}{C.RESET}")
                print(f"\n{C.BLUE}{'═'*70}{C.RESET}\n")
                return 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # Manual tree via psutil
    try:
        import psutil
    except ImportError:
        return 1

    print(f"\n{C.BLUE}{'═'*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}PROCESS TREE{C.RESET}")
    print(f"{C.BLUE}{'═'*70}{C.RESET}\n")

    procs = {p.pid: p for p in psutil.process_iter(["pid", "ppid", "name"])}
    children: dict = {}
    for pid, p in procs.items():
        try:
            ppid = p.info["ppid"]
            children.setdefault(ppid, []).append(pid)
        except Exception:
            pass

    def _print_tree(pid: int, indent: str = "", last: bool = True):
        try:
            p    = procs.get(pid)
            name = p.info["name"] if p else "?"
            connector = "└─ " if last else "├─ "
            print(f"  {C.GRAY}{indent}{connector}{C.RESET}{C.CYAN}{pid}{C.RESET} {C.WHITE}{name}{C.RESET}")
            kids = children.get(pid, [])
            ext  = "   " if last else "│  "
            for i, kid in enumerate(kids[:10]):
                _print_tree(kid, indent + ext, i == len(kids) - 1)
        except Exception:
            pass

    # Start from init/PID 1
    _print_tree(1)
    print(f"\n{C.BLUE}{'═'*70}{C.RESET}\n")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  Registry
# ══════════════════════════════════════════════════════════════════════════════

SYS_CMDS: dict = {
    "disk-usage":    cmd_disk_usage,
    "du-enhanced":   cmd_disk_usage,
    "proc-monitor":  cmd_proc_monitor,
    "ps-enhanced":   cmd_proc_monitor,
}
