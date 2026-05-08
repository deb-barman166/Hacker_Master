"""
ui/banner.py — Enhanced boot banner for Kali Terminal v2.0 Masterpiece.

Features:
  - Animated boot sequence
  - Live system information
  - Feature showcase
  - Theme-aware coloring
  - ASCII art logo
"""

import os
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

from ui.theme import Colors

C = Colors


KALI_LOGO = r"""
    ██╗  ██╗ ██████╗ ████████╗ █████╗     ███████╗██╗███╗   ██╗ ██████╗ ██╗███╗   ██╗ ██████╗
    ██║ ██╔╝██╔═══██╗╚══██╔══╝██╔══██╗    ██╔════╝██║████╗  ██║██╔════╝ ██║████╗  ██║██╔════╝
    █████╔╝ ██║   ██║   ██║   ███████║    ███████╗██║██╔██╗ ██║██║  ███╗██║██╔██╗ ██║██║  ███╗
    ██╔═██╗ ██║   ██║   ██║   ██╔══██║    ╚════██║██║██║╚██╗██║██║   ██║██║██║╚██╗██║██║   ██║
    ██║  ██╗╚██████╔╝   ██║   ██║  ██║    ███████║██║██║ ╚████║╚██████╔╝██║██║ ╚████║╚██████╔╝
    ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝    ╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚═════╝
                                    L I N U X   T E R M I N A L   v 2 . 0
                                Professional Cybersecurity Framework with AI
"""


KALI_LOGO_V2 = r"""
    ╔═══════════════════════════════════════════════════════════════════════════════════════╗
    ║                                                                                       ║
    ║   ██╗  ██╗ ██████╗ ████████╗ ██████╗     ███████╗██╗███╗   ██╗ ██████╗ ██╗███╗   ██╗  ║
    ║   ██║ ██╔╝██╔═══██╗╚══██╔══╝██╔═══██╗    ██╔════╝██║████╗  ██║██╔════╝ ██║████╗  ██║  ║
    ║   █████╔╝ ██║   ██║   ██║   ██║   ██║    ███████╗██║██╔██╗ ██║██║  ███╗██║██╔██╗ ██║  ║
    ║   ██╔═██╗ ██║   ██║   ██║   ██║   ██║    ╚════██║██║██║╚██╗██║██║   ██║██║██║╚██╗██║  ║
    ║   ██║  ██╗╚██████╔╝   ██║   ╚██████╔╝    ███████║██║██║ ╚████║╚██████╔╝██║██║ ╚████║  ║
    ║   ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝     ╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝  ║
    ║                                                                                       ║
    ║                        L I N U X   T E R M I N A L   v 2 . 0                           ║
    ║              Professional Cybersecurity Framework with AI Integration                 ║
    ╚═══════════════════════════════════════════════════════════════════════════════════════╝
"""


def _get_sys_info() -> dict:
    """Collect live system information."""
    info = {}
    info["hostname"] = socket.gethostname()
    info["user"] = os.environ.get("USER", os.environ.get("LOGNAME", "root"))
    info["os"] = platform.system() + " " + platform.release()
    info["python"] = platform.python_version()
    info["shell"] = "KaliTerm v2.0 Masterpiece"
    info["date"] = datetime.now().strftime("%a %b %d %H:%M:%S %Y")
    info["arch"] = platform.machine()

    # CPU info
    try:
        cpu_out = subprocess.check_output(
            ["cat", "/proc/cpuinfo"], text=True, stderr=subprocess.DEVNULL
        )
        for line in cpu_out.splitlines():
            if "model name" in line:
                info["cpu"] = line.split(":")[1].strip()
                break
        else:
            info["cpu"] = platform.processor() or "Unknown"
    except Exception:
        info["cpu"] = platform.processor() or "Unknown"

    # Hardware stats
    if HAS_PSUTIL:
        vm = psutil.virtual_memory()
        info["ram"] = f"{vm.used // (1024*1024)}MB / {vm.total // (1024*1024)}MB ({vm.percent}%)"
        info["cpu_pct"] = f"{psutil.cpu_percent(interval=0.1):.1f}%"
        info["cores"] = str(psutil.cpu_count(logical=True))
        try:
            disk = psutil.disk_usage("/")
            info["disk"] = f"{disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB ({disk.percent}%)"
        except:
            info["disk"] = "N/A"
    else:
        info["ram"] = info["cpu_pct"] = info["cores"] = info["disk"] = "N/A"

    ts = shutil.get_terminal_size(fallback=(100, 24))
    info["term_size"] = f"{ts.columns}x{ts.lines}"

    return info


def print_banner():
    """Print the full Kali v2 boot banner."""
    info = _get_sys_info()
    width = shutil.get_terminal_size(fallback=(100, 24)).columns
    width = max(width, 90)

    # ── Top border ─────────────────────────────────────────────────────────
    print(f"\n{C.RED}{C.BOLD}{'═' * width}{C.RESET}")

    # ── ASCII Logo ─────────────────────────────────────────────────────────
    print(f"{C.RED}{C.BOLD}")
    print("    ██╗  ██╗ ██████╗ ████████╗ █████╗     ███████╗██╗███╗   ██╗ ██████╗ ██╗███╗   ██╗")
    print("    ██║ ██╔╝██╔═══██╗╚══██╔══╝██╔══██╗    ██╔════╝██║████╗  ██║██╔════╝ ██║████╗  ██║")
    print("    █████╔╝ ██║   ██║   ██║   ███████║    ███████╗██║██╔██╗ ██║██║  ███╗██║██╔██╗ ██║")
    print("    ██╔═██╗ ██║   ██║   ██║   ██╔══██║    ╚════██║██║██║╚██╗██║██║   ██║██║██║╚██╗██║")
    print("    ██║  ██╗╚██████╔╝   ██║   ██║  ██║    ███████║██║██║ ╚████║╚██████╔╝██║██║ ╚████║")
    print("    ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝    ╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝")
    print(f"{C.RESET}")

    print(f"  {C.CYAN}{C.BOLD}LINUX TERMINAL v2.0 — Professional Cybersecurity Framework with AI Integration{C.RESET}")

    print(f"{C.RED}{C.BOLD}{'═' * width}{C.RESET}")

    # ── System Info Panel ──────────────────────────────────────────────────
    def row(label, value, color=C.WHITE):
        pad = max(0, 52 - len(label) - len(str(value)))
        print(f"{C.BLUE}│{C.RESET}  {C.CYAN}{label:<18}{C.RESET}: {color}{value}{C.RESET}{' ' * pad}{C.BLUE}│{C.RESET}")

    print(f"{C.BLUE}│{C.RESET}  {C.RED}{C.BOLD}SYSTEM INFORMATION — v2.0 MASTERPIECE{C.RESET}{' ' * 30}{C.BLUE}│{C.RESET}")
    print(f"{C.BLUE}├{C.RESET}{'─' * (width - 2)}{C.BLUE}┤{C.RESET}")

    row("Hostname", info["hostname"])
    row("User", info["user"], C.GREEN)
    row("OS", info["os"], C.GREEN)
    row("Kernel", platform.version()[:35] + "...", C.GRAY)
    row("Arch", info["arch"], C.YELLOW)
    row("Shell", info["shell"], C.CYAN)
    row("Python", info["python"], C.GREEN)
    row("CPU", info.get("cpu", "N/A")[:35], C.WHITE)
    row("Cores", info["cores"])
    row("CPU Load", info["cpu_pct"])
    row("RAM", info["ram"])
    row("Disk", info["disk"])
    row("Terminal", info["term_size"])
    row("Date", info["date"], C.YELLOW)

    print(f"{C.BLUE}├{C.RESET}{'─' * (width - 2)}{C.BLUE}┤{C.RESET}")

    # ── AI Features ───────────────────────────────────────────────────────
    print(f"{C.BLUE}│{C.RESET}  {C.MAGENTA}{C.BOLD}AI INTEGRATION{C.RESET}{' ' * 45}{C.BLUE}│{C.RESET}")
    print(f"{C.BLUE}├{C.RESET}{'─' * (width - 2)}{C.BLUE}┤{C.RESET}")

    row("Ollama (Local)", "llama3.2, mistral, codellama", C.GREEN)
    row("OpenAI", "GPT-4, GPT-4-Turbo, GPT-3.5", C.GREEN)
    row("Anthropic", "Claude 3 Opus, Sonnet, Haiku", C.GREEN)
    row("Google", "Gemini Pro, Gemini Ultra", C.GREEN)

    print(f"{C.BLUE}├{C.RESET}{'─' * (width - 2)}{C.BLUE}┤{C.RESET}")

    # ── Feature Showcase ──────────────────────────────────────────────────
    print(f"{C.BLUE}│{C.RESET}  {C.YELLOW}{C.BOLD}FEATURES — 100+ Commands{C.RESET}{' ' * 42}{C.BLUE}│{C.RESET}")
    print(f"{C.BLUE}├{C.RESET}{'─' * (width - 2)}{C.BLUE}┤{C.RESET}")

    features_col1 = [
        ("NETWORK", "port-scan, subnet-calc, dns-lookup"),
        ("CRYPTO", "hash, encode/decode, hash-identify"),
        ("WEB", "http-headers, dir-scan, sql-test"),
        ("FORENSICS", "hexdump, strings, entropy, binwalk"),
        ("PASSWORD", "password-gen, random-uuid/mac"),
    ]

    features_col2 = [
        ("AI CHAT", "ai, ai-explain, ai-analyze"),
        ("RECON", "traceroute, ping-sweep, whois"),
        ("SSL/TLS", "ssl-check, cert-check"),
        ("ENCRYPTION", "cypher, decypher, rot13, caesar"),
        ("ANALYSIS", "file-analysis, xor-data"),
    ]

    for (cat1, desc1), (cat2, desc2) in zip(features_col1, features_col2):
        print(f"{C.BLUE}│{C.RESET}  {C.RED}{cat1:<12}{C.RESET}{C.WHITE}{desc1:<28}{C.RESET}  {C.RED}{cat2:<12}{C.RESET}{C.WHITE}{desc2:<28}{C.RESET}{C.BLUE}│{C.RESET}")

    print(f"{C.BLUE}├{C.RESET}{'─' * (width - 2)}{C.BLUE}┤{C.RESET}")

    # ── Quick Commands ────────────────────────────────────────────────────
    quick_commands = [
        ("help", "Show all commands"),
        ("ai-help", "AI assistance"),
        ("sysinfo", "System information"),
        ("cheatsheet", "Command reference"),
        ("theme-list", "Color themes"),
    ]

    print(f"{C.BLUE}│{C.RESET}  {C.CYAN}{C.BOLD}Quick Start:{C.RESET}", end="")
    for cmd, desc in quick_commands:
        print(f" {C.GREEN}{cmd}{C.RESET}({C.GRAY}{desc}{C.RESET})", end="  ")
    print(f"{' ' * max(0, width - 100)}{C.BLUE}│{C.RESET}")

    print(f"{C.RED}{C.BOLD}{'═' * width}{C.RESET}")

    print(f"\n  {C.GRAY}Type {C.CYAN}help{C.RESET} for commands | {C.CYAN}ai-help{C.RESET} for AI assistance | {C.CYAN}cheatsheet{C.RESET} for reference{C.RESET}\n")