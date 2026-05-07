"""
ui/banner.py — Masterpiece boot banner for KaliTerminal v2.

Features:
  - Animated dragon/skull ASCII art
  - Live system information panel
  - Full feature showcase
  - Theme-aware coloring
"""

import os
import sys
import time
import platform
import socket
import shutil
import subprocess
from datetime import datetime

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from ui.theme import Colors, get_logo_color

C = Colors

DRAGON_ART = r"""
    ██╗  ██╗ █████╗ ██╗     ██╗    ████████╗███████╗██████╗ ███╗   ███╗
    ██║ ██╔╝██╔══██╗██║     ██║    ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║
    █████╔╝ ███████║██║     ██║       ██║   █████╗  ██████╔╝██╔████╔██║
    ██╔═██╗ ██╔══██║██║     ██║       ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║
    ██║  ██╗██║  ██║███████╗██║       ██║   ███████╗██║  ██║██║ ╚═╝ ██║
    ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝       ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝
"""

SUBTITLE = "  ██████╗ ██╗   ██╗████████╗██╗  ██╗ ██████╗ ███╗   ██╗    ██╗   ██╗██████╗"

KALI_SKULL = [
    r"  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░",
    r"  ░  ██╗  ██╗ █████╗ ██╗     ██╗    ████████╗███████╗██████╗  ░",
    r"  ░  ██║ ██╔╝██╔══██╗██║     ██║    ╚══██╔══╝██╔════╝██╔══██╗ ░",
    r"  ░  █████╔╝ ███████║██║     ██║       ██║   █████╗  ██████╔╝  ░",
    r"  ░  ██╔═██╗ ██╔══██║██║     ██║       ██║   ██╔══╝  ██╔══██╗  ░",
    r"  ░  ██║  ██╗██║  ██║███████╗██║       ██║   ███████╗██║  ██║  ░",
    r"  ░  ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝       ╚═╝   ╚══════╝╚═╝  ╚═╝  ░",
    r"  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░",
]

VERSION_ART = [
    "  ██████╗ ██╗   ██╗████████╗██╗  ██╗ ██████╗ ███╗   ██╗     ██╗   ██╗██████╗",
    "  ██╔══██╗╚██╗ ██╔╝╚══██╔══╝██║  ██║██╔═══██╗████╗  ██║     ██║   ██║╚════██╗",
    "  ██████╔╝ ╚████╔╝    ██║   ███████║██║   ██║██╔██╗ ██║     ██║   ██║ █████╔╝",
    "  ██╔═══╝   ╚██╔╝     ██║   ██╔══██║██║   ██║██║╚██╗██║     ╚██╗ ██╔╝██╔═══╝",
    "  ██║        ██║      ██║   ██║  ██║╚██████╔╝██║ ╚████║      ╚████╔╝ ███████╗",
    "  ╚═╝        ╚═╝      ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝       ╚═══╝  ╚══════╝",
]


def _get_sys_info() -> dict:
    info = {}
    info["hostname"] = socket.gethostname()
    info["user"]     = os.environ.get("USER", os.environ.get("LOGNAME", "root"))
    info["os"]       = f"{platform.system()} {platform.release()}"
    info["python"]   = platform.python_version()
    info["date"]     = datetime.now().strftime("%a %d %b %Y  %H:%M:%S")
    info["arch"]     = platform.machine()
    info["shell"]    = "KaliTerm v2.0 — MASTERPIECE"

    # CPU
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "model name" in line:
                    info["cpu"] = line.split(":")[1].strip()
                    break
    except Exception:
        info["cpu"] = platform.processor() or "Unknown"

    if HAS_PSUTIL:
        vm = psutil.virtual_memory()
        info["ram"]      = f"{vm.used//(1024*1024)} MB / {vm.total//(1024*1024)} MB  ({vm.percent:.1f}%)"
        info["ram_pct"]  = vm.percent
        info["cpu_pct"]  = psutil.cpu_percent(interval=0.1)
        info["cores"]    = psutil.cpu_count(logical=True)
        info["cores_ph"] = psutil.cpu_count(logical=False)
        disk = psutil.disk_usage("/")
        info["disk"]     = f"{disk.used//(1024**3)} GB / {disk.total//(1024**3)} GB  ({disk.percent:.1f}%)"
        info["disk_pct"] = disk.percent
        # Network: primary IP
        try:
            addrs = psutil.net_if_addrs()
            for iface, addr_list in addrs.items():
                if iface == "lo":
                    continue
                for addr in addr_list:
                    if addr.family == socket.AF_INET:
                        info["local_ip"] = addr.address
                        break
                if "local_ip" in info:
                    break
        except Exception:
            pass
    else:
        info["ram"] = info["disk"] = "N/A (pip install psutil)"
        info["cpu_pct"] = info["ram_pct"] = info["disk_pct"] = 0
        info["cores"] = info["cores_ph"] = "?"

    info.setdefault("local_ip", "N/A")
    ts = shutil.get_terminal_size(fallback=(120, 24))
    info["term_size"] = f"{ts.columns} × {ts.lines}"

    return info


def _bar(pct: float, width: int = 25) -> str:
    filled = int(width * pct / 100)
    bar = "█" * filled + "░" * (width - filled)
    if pct < 50:
        color = C.GREEN
    elif pct < 80:
        color = C.YELLOW
    else:
        color = C.RED
    return f"{color}{bar}{C.RESET} {C.BOLD}{pct:.1f}%{C.RESET}"


def print_banner(fast: bool = False):
    """Print the full v2 masterpiece boot banner."""
    info     = _get_sys_info()
    logo_clr = get_logo_color()
    w        = max(shutil.get_terminal_size(fallback=(120, 24)).columns, 90)
    delay    = 0.0 if fast else 0.005

    def ln(text=""):
        print(text)
        if delay:
            time.sleep(delay)

    ln(f"\n{C.BLUE}{'═' * w}{C.RESET}")

    # Big ASCII logo
    for line in VERSION_ART:
        ln(f"{logo_clr}{C.BOLD}{line}{C.RESET}")

    ln(f"{C.BLUE}{'═' * w}{C.RESET}")

    # ── Left: system info | Right: stats ──────────────────────────────────
    separator = f"  {C.BLUE}│{C.RESET}  "

    def row(label: str, value: str, val_color: str = None):
        vc = val_color or C.WHITE
        print(f"  {C.CYAN}{label:<16}{C.RESET}: {vc}{value}{C.RESET}")

    ln()
    row("  Shell",    info["shell"],             C.CYAN)
    row("  Host",     info["hostname"],           C.GREEN)
    row("  User",     info["user"],               C.RED + C.BOLD)
    row("  OS",       info["os"],                 C.WHITE)
    row("  Arch",     info["arch"],               C.YELLOW)
    row("  Python",   info["python"],             C.GREEN)
    row("  Local IP", info["local_ip"],           C.CYAN)
    row("  Date",     info["date"],               C.YELLOW)
    row("  Terminal", info["term_size"],           C.GRAY)
    ln()

    # CPU / RAM / Disk bars
    cpu_bar  = _bar(float(info["cpu_pct"]))
    ram_bar  = _bar(float(info["ram_pct"]))
    disk_bar = _bar(float(info["disk_pct"]))

    print(f"  {C.CYAN}{'CPU':<8}{C.RESET} {cpu_bar}   {C.GRAY}{info.get('cores','?')} cores{C.RESET}")
    print(f"  {C.CYAN}{'RAM':<8}{C.RESET} {ram_bar}   {C.GRAY}{info['ram']}{C.RESET}")
    print(f"  {C.CYAN}{'Disk':<8}{C.RESET} {disk_bar}   {C.GRAY}{info['disk']}{C.RESET}")
    ln()

    ln(f"{C.BLUE}{'═' * w}{C.RESET}")

    # ── Feature tags ──────────────────────────────────────────────────────
    FEATURES = [
        ("7 THEMES",      C.MAGENTA),
        ("AI DUAL-MODE",  C.RED + C.BOLD),
        ("OLLAMA LOCAL",  C.GREEN),
        ("MULTI-API KEY", C.CYAN),
        ("PORT SCAN",     C.YELLOW),
        ("DNS LOOKUP",    C.BLUE),
        ("SSL CHECK",     C.MAGENTA),
        ("HTTP HEADERS",  C.GREEN),
        ("WHOIS",         C.CYAN),
        ("GEO-IP",        C.ORANGE),
        ("HASH TOOLS",    C.RED),
        ("ENCODE/DECODE", C.YELLOW),
        ("JWT DECODE",    C.MAGENTA),
        ("PASS GEN",      C.GREEN),
        ("PASS AUDIT",    C.CYAN),
        ("VULN SEARCH",   C.RED),
        ("PROC MONITOR",  C.YELLOW),
        ("DISK USAGE",    C.BLUE),
        ("ALIASES",       C.MAGENTA),
        ("BOOKMARKS",     C.GREEN),
        ("NOTES",         C.CYAN),
        ("TODO LIST",     C.ORANGE),
        ("CALCULATOR",    C.YELLOW),
        ("PIPE SUPPORT",  C.BLUE),
        ("HISTORY",       C.MAGENTA),
        ("TAB COMPLETE",  C.GREEN),
        ("VI MODE",       C.CYAN),
        ("PLUGIN SYS",    C.RED),
        ("SESSION SAVE",  C.YELLOW),
        ("CHEAT SHEET",   C.BLUE),
    ]

    tag_line = "  "
    for label, color in FEATURES:
        tag_line += f"{color}[{C.BOLD}{label}{C.RESET}{color}]{C.RESET} "
    print(tag_line)

    ln(f"\n{C.BLUE}{'═' * w}{C.RESET}")

    # ── Quick-start tips ──────────────────────────────────────────────────
    tips = [
        (f"{C.CYAN}help{C.RESET}", "   full command reference"),
        (f"{C.CYAN}ai on{C.RESET}", "  enable AI assistant"),
        (f"{C.CYAN}theme-list{C.RESET}", " browse themes"),
        (f"{C.CYAN}cheatsheet{C.RESET}", " security quick-ref"),
        (f"{C.CYAN}Ctrl+L{C.RESET}", " clear  |  {C.CYAN}Ctrl+D{C.RESET} exit"),
    ]
    tip_str = "  "
    for cmd, desc in tips:
        tip_str += f" {cmd}{C.GRAY}{desc}{C.RESET}  {C.BLUE}│{C.RESET}"
    print(tip_str)

    ln(f"\n{C.BLUE}{'═' * w}{C.RESET}\n")
