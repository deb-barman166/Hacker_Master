"""
commands/system_tools.py — System monitoring and analysis tools (v2.0 Masterpiece).

Commands:
  - disk-usage: Enhanced disk usage analyzer
  - proc-monitor: Interactive process monitor
  - sysinfo-enhanced: Full system information
"""

import os
import sys
import platform
import shutil
from datetime import datetime

from ui.theme import Colors

C = Colors


def cmd_disk_usage(args: list, state: dict, terminal=None) -> int:
    """Enhanced disk usage analyzer. Usage: disk-usage [path]"""
    target = args[0] if args else "."
    if not os.path.isabs(target):
        target = os.path.join(state.get("cwd", os.getcwd()), target)

    if not os.path.isdir(target):
        print(C.error(f"Not a directory: {target}"))
        return 1

    try:
        import psutil
    except ImportError:
        print(C.error("Requires psutil: pip install psutil"))
        return 1

    print(f"\n{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}DISK USAGE ANALYZER: {target}{C.RESET}")
    print(f"{C.BLUE}{'='*70}{C.RESET}")

    disk = psutil.disk_usage(target)
    bar_width = 50
    filled = int(bar_width * disk.percent / 100)
    bar = f"{C.GREEN}{'█' * filled}{C.RESET}{C.DIM}{'░' * (bar_width - filled)}{C.RESET}"

    def fmt_size(n):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} PB"

    print(f"\n  {C.CYAN}Total{C.RESET}:   {fmt_size(disk.total)}")
    print(f"  {C.CYAN}Used{C.RESET}:    {fmt_size(disk.used)} ({disk.percent:.1f}%)")
    print(f"  {C.CYAN}Free{C.RESET}:    {fmt_size(disk.free)}")
    print(f"  {bar} {disk.percent:.1f}%")

    print(f"\n  {C.YELLOW}{C.BOLD}Disk Partitions:{C.RESET}")
    partitions = psutil.disk_partitions()
    for part in partitions:
        try:
            usage = psutil.disk_usage(part.mountpoint)
            print(f"  {C.CYAN}{part.device or 'N/A':<20}{C.RESET} "
                  f"{C.WHITE}{part.mountpoint:<20}{C.RESET} "
                  f"{C.GREEN}{fmt_size(usage.total):<10}{C.RESET} "
                  f"{C.YELLOW}{usage.percent:>5.1f}%{C.RESET} ")
        except Exception:
            pass

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def cmd_proc_monitor(args: list, state: dict, terminal=None) -> int:
    """Process monitor. Usage: proc-monitor [top|search|kill]"""
    subcmd = args[0] if args else "top"

    try:
        import psutil
    except ImportError:
        print(C.error("Requires psutil: pip install psutil"))
        return 1

    if subcmd == "top":
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
            try:
                info = p.info
                procs.append(info)
            except:
                pass

        procs.sort(key=lambda p: p.get('cpu_percent', 0) or 0, reverse=True)

        print(f"\n{C.BLUE}{'='*80}{C.RESET}")
        print(f"  {C.BOLD}{C.WHITE}TOP PROCESSES BY CPU{C.RESET}")
        print(f"{C.BLUE}{'='*80}{C.RESET}")
        print(f"  {C.BOLD}{C.GRAY}{'PID':<8}{'USER':<15}{'CPU%':>8}{'MEM%':>8}{'NAME'}{C.RESET}")

        for p in procs[:15]:
            cpu = p.get('cpu_percent', 0) or 0
            mem = p.get('memory_percent', 0) or 0
            user = (p.get('username') or 'N/A')[:14]
            name = (p.get('name') or 'unknown')[:30]
            cpu_color = C.RED if cpu > 50 else C.YELLOW if cpu > 20 else C.GREEN

            print(f"  {C.CYAN}{p['pid']:<8}{C.RESET}{C.WHITE}{user:<15}{C.RESET}"
                  f"{cpu_color}{cpu:>7.1f}%{C.RESET} {C.CYAN}{mem:>7.1f}%{C.RESET} {C.WHITE}{name}{C.RESET}")

        print(f"{C.BLUE}{'='*80}{C.RESET}\n")

    elif subcmd == "search" and len(args) > 1:
        name = " ".join(args[1:])
        matches = []
        for p in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                info = p.info
                if name.lower() in (info.get('name') or '').lower():
                    matches.append(info)
            except:
                pass

        if matches:
            print(f"\n  {C.YELLOW}Processes matching '{name}':{C.RESET}")
            for p in matches[:20]:
                cmd = ' '.join(p.get('cmdline') or [])[:60]
                print(f"  {C.CYAN}{p['pid']:<8}{C.RESET} {C.WHITE}{p['name']}{C.RESET}")
                if cmd:
                    print(f"  {C.GRAY}         {cmd}{C.RESET}")
        else:
            print(C.info(f"No processes matching '{name}'"))

    else:
        print(C.info("Usage: proc-monitor [top|search|kill]"))
        print(C.info("  proc-monitor top         # Top processes"))
        print(C.info("  proc-monitor search name # Find processes"))

    return 0


def cmd_sysinfo_enhanced(args: list, state: dict, terminal=None) -> int:
    """Enhanced system information panel."""
    try:
        import psutil
        has_psutil = True
    except ImportError:
        has_psutil = False

    print(f"\n{C.BLUE}{'='*65}{C.RESET}")
    print(f"  {C.RED}{C.BOLD}KALI TERMINAL v2.0 — SYSTEM INFORMATION{C.RESET}")
    print(f"{C.BLUE}{'='*65}{C.RESET}")

    def row(label, value, color=C.WHITE):
        pad = 50 - len(label) - len(str(value))
        print(f"{C.BLUE}|{C.RESET}  {C.CYAN}{label:<16}{C.RESET}: {color}{value}{C.RESET}{' ' * max(0,pad)}{C.BLUE}|{C.RESET}")

    row("Hostname", socket.gethostname())
    row("OS", platform.system() + " " + platform.release(), C.GREEN)
    row("Python", platform.python_version(), C.GREEN)
    row("Shell", "KaliTerm v2.0 Masterpiece", C.MAGENTA)
    row("Session", f"{time.time() - state.get('start_time', time.time()):.0f}s", C.YELLOW)
    row("Commands", str(state.get("cmd_count", 0)))
    row("Datetime", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), C.YELLOW)

    if has_psutil:
        vm = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=0.2)
        disk = psutil.disk_usage("/")

        def bar(pct, w=16):
            f = int(w * pct / 100)
            c = C.GREEN if pct < 60 else C.YELLOW if pct < 85 else C.RED
            return f"{c}{'█' * f}{C.RESET}{'░' * (w - f)}"

        row("CPU Usage", f"{bar(cpu_pct)} {cpu_pct:.1f}%")
        row("RAM Used", f"{bar(vm.percent)} {vm.percent:.1f}%")
        row("RAM Total", f"{vm.total // (1024**2)} MB")
        row("Disk Used", f"{bar(disk.percent)} {disk.percent:.1f}%")
        row("Disk Free", f"{disk.free // (1024**3)} GB", C.GREEN)

    print(f"{C.BLUE}{'='*65}{C.RESET}\n")
    return 0


# Import socket for sysinfo
import socket