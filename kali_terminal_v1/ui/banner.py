"""
ui/banner.py — Epic Boot Banner for Kali Terminal v1.0

Features:
  • Animated fake-boot loading sequence
  • ASCII Kali logo with gradient colors
  • Live system stats (CPU, RAM, Disk, Network)
  • Session welcome with random hacker quote
  • Feature pills display
"""

import os
import sys
import time
import random
import platform
import socket
import shutil
import datetime
import subprocess

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from ui.theme import Colors, get_active_theme, THEMES

C = Colors

# ── ASCII Art ─────────────────────────────────────────────────────────────────

KALI_LOGO = [
    r"  ██╗  ██╗ █████╗ ██╗      ██╗",
    r"  ██║ ██╔╝██╔══██╗██║      ██║",
    r"  █████╔╝ ███████║██║      ██║",
    r"  ██╔═██╗ ██╔══██║██║      ██║",
    r"  ██║  ██╗██║  ██║███████╗ ██║",
    r"  ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═╝",
    r"",
    r"   ──── TERMINAL  v1.0.0 ────",
]

DRAGON = [
    r"       .---.        .----------",
    r"      /     \  __  /    ------",
    r"     / /     \(  )/    -----",
    r"    //////   ' \/`   ---",
    r"   //// / // :    : ---",
    r"  // /   /  /`    '--",
    r" // /        //..\\",
    r"",
]

HACKER_QUOTES = [
    "\"The quieter you become, the more you are able to hear.\"  — Kali motto",
    "\"Hack the planet.\"  — Hackers (1995)",
    "\"With great power comes great responsibility.\"  — Uncle Ben",
    "\"Security is not a product, it is a process.\"  — Bruce Schneier",
    "\"The only truly secure system is one that is powered off.\"  — Gene Spafford",
    "\"In God we trust. All others we monitor.\"  — NSA",
    "\"Information is the oxygen of the modern age.\"  — Ronald Reagan",
    "\"Every system is broken. Find the break.\"  — Anonymous",
    "\"The art of war teaches us to rely not on the likelihood of the enemy not coming.\"",
    "\"Privacy is not something that I'm merely entitled to, it's an absolute prerequisite.\"",
]

# ── Boot sequence messages ─────────────────────────────────────────────────────

BOOT_MSGS = [
    ("Initializing kernel modules",         "OK"),
    ("Loading network stack",               "OK"),
    ("Starting Python runtime",             "OK"),
    ("Mounting filesystem",                 "OK"),
    ("Loading color engine",                "OK"),
    ("Applying theme",                      "OK"),
    ("Initializing tab completion",         "OK"),
    ("Loading persistent aliases",          "OK"),
    ("Loading bookmarks",                   "OK"),
    ("Connecting to AI subsystem",          "OK"),
    ("Starting command executor",           "OK"),
    ("Terminal ready",                      "OK"),
]


def _get_sys_info() -> dict:
    """Collect live system information."""
    info = {}
    info["hostname"] = socket.gethostname()
    info["user"]     = os.environ.get("USER", os.environ.get("LOGNAME", "root"))
    info["os"]       = platform.system() + " " + platform.release()
    info["python"]   = platform.python_version()
    info["arch"]     = platform.machine()
    info["date"]     = datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y")
    info["uptime"]   = _get_uptime()
    info["theme"]    = THEMES.get(get_active_theme(), {}).get("name", "Kali Dark")

    # CPU model
    try:
        out = subprocess.check_output(["cat", "/proc/cpuinfo"], text=True,
                                      stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            if "model name" in line:
                info["cpu"] = line.split(":")[1].strip()[:40]
                break
        else:
            info["cpu"] = platform.processor()[:40] or "Unknown"
    except Exception:
        info["cpu"] = platform.processor()[:40] or "Unknown"

    if HAS_PSUTIL:
        import psutil
        vm = psutil.virtual_memory()
        info["ram_total"] = f"{vm.total // (1024**2)} MB"
        info["ram_used"]  = f"{vm.used  // (1024**2)} MB"
        info["ram_pct"]   = vm.percent
        info["cores"]     = str(psutil.cpu_count(logical=True))
        info["cpu_pct"]   = psutil.cpu_percent(interval=0.1)
        disk = psutil.disk_usage("/")
        info["disk_total"] = f"{disk.total // (1024**3)} GB"
        info["disk_used"]  = f"{disk.used  // (1024**3)} GB"
        info["disk_pct"]   = disk.percent
        # IP
        try:
            net = psutil.net_if_addrs()
            for iface, addrs in net.items():
                for addr in addrs:
                    if addr.family == 2 and not addr.address.startswith("127."):
                        info["ip"] = addr.address
                        info["iface"] = iface
                        break
                if "ip" in info:
                    break
        except Exception:
            pass
        if "ip" not in info:
            info["ip"] = "127.0.0.1"
            info["iface"] = "lo"
    else:
        info["ram_total"] = "N/A"
        info["ram_used"]  = "N/A"
        info["ram_pct"]   = 0
        info["cores"]     = "N/A"
        info["cpu_pct"]   = 0
        info["disk_total"] = "N/A"
        info["disk_used"]  = "N/A"
        info["disk_pct"]   = 0
        info["ip"]        = "N/A"
        info["iface"]     = "N/A"

    return info


def _get_uptime() -> str:
    try:
        with open("/proc/uptime") as f:
            secs = float(f.read().split()[0])
        h = int(secs // 3600)
        m = int((secs % 3600) // 60)
        return f"{h}h {m}m"
    except Exception:
        return "N/A"


def _mini_bar(pct: float, w: int = 18) -> str:
    filled = int(w * pct / 100)
    if pct < 50:
        color = C.TRUE_GREEN
    elif pct < 80:
        color = C.YELLOW
    else:
        color = C.TRUE_RED
    return f"{color}{'█'*filled}{'░'*(w-filled)}{C.RESET}"


def _boot_animation():
    """Simulate a Kali boot sequence."""
    width = shutil.get_terminal_size(fallback=(100, 24)).columns

    print(f"\n{C.BLUE}{'─'*width}{C.RESET}")
    print(f"  {C.BOLD}{C.RED}[ KALI TERMINAL v1.0.0 BOOT SEQUENCE ]{C.RESET}")
    print(f"{C.BLUE}{'─'*width}{C.RESET}\n")

    for msg, status in BOOT_MSGS:
        dots = "." * (40 - len(msg))
        sys.stdout.write(
            f"  {C.CYAN}►{C.RESET} {C.WHITE}{msg}{C.GRAY}{dots}{C.RESET}"
        )
        sys.stdout.flush()
        time.sleep(0.03)
        sys.stdout.write(
            f"  [{C.GREEN}{C.BOLD}{status}{C.RESET}]\n"
        )
        sys.stdout.flush()

    print(f"\n{C.BLUE}{'─'*width}{C.RESET}\n")


def print_banner(animated: bool = True):
    """Print the full Kali boot banner."""
    info  = _get_sys_info()
    width = shutil.get_terminal_size(fallback=(100, 24)).columns
    width = max(width, 85)

    if animated:
        _boot_animation()

    # ── Main header bar ───────────────────────────────────────────────────────
    print(f"{C.BLUE}{'═'*width}{C.RESET}")

    # ── Logo side ─────────────────────────────────────────────────────────────
    theme_emoji = THEMES.get(get_active_theme(), {}).get("emoji", "🐉")

    logo_lines = [
        f"  {C.RED}{C.BOLD}{line}{C.RESET}" for line in KALI_LOGO
    ]
    dragon_lines = [
        f"  {C.BLUE}{C.DIM}{line}{C.RESET}" for line in DRAGON
    ]

    # ── Info panel ────────────────────────────────────────────────────────────
    cpu_bar  = _mini_bar(info["cpu_pct"])
    ram_bar  = _mini_bar(info["ram_pct"])
    disk_bar = _mini_bar(info["disk_pct"])

    def R(label, val, color=C.WHITE):
        return (
            f"  {C.BLUE}{label:<10}{C.RESET}: {color}{val}{C.RESET}"
        )

    info_lines = [
        f"  {C.GRAY}{'─'*42}{C.RESET}",
        R("OS",      info["os"],        C.GREEN),
        R("Host",    info["hostname"],   C.CYAN),
        R("User",    info["user"],       C.RED + C.BOLD),
        R("Shell",   f"KaliTerm v1.0  {theme_emoji} [{info['theme']}]", C.CYAN),
        R("Python",  info["python"],     C.GREEN),
        R("Arch",    info["arch"],       C.WHITE),
        R("CPU",     info["cpu"][:36],   C.WHITE),
        R("Cores",   info["cores"],      C.WHITE),
        R("Uptime",  info["uptime"],     C.YELLOW),
        f"  {C.GRAY}{'─'*42}{C.RESET}",
        f"  {C.BLUE}{'CPU':<10}{C.RESET}: {cpu_bar} {C.CYAN}{info['cpu_pct']:.1f}%{C.RESET}",
        f"  {C.BLUE}{'RAM':<10}{C.RESET}: {ram_bar} {C.CYAN}{info['ram_used']}/{info['ram_total']}{C.RESET}",
        f"  {C.BLUE}{'Disk':<10}{C.RESET}: {disk_bar} {C.CYAN}{info['disk_used']}/{info['disk_total']}{C.RESET}",
        R("IP",      f"{info['ip']} ({info['iface']})", C.GREEN),
        R("Date",    info["date"],       C.YELLOW),
        f"  {C.GRAY}{'─'*42}{C.RESET}",
    ]

    # Merge logo + dragon + info
    left_lines  = logo_lines + dragon_lines
    right_lines = info_lines

    max_rows = max(len(left_lines), len(right_lines))
    left_lines  += [""] * (max_rows - len(left_lines))
    right_lines += [""] * (max_rows - len(right_lines))

    for l, r in zip(left_lines, right_lines):
        l_clean = len(l.replace(C.RED, "").replace(C.BLUE, "").replace(
                   C.BOLD, "").replace(C.DIM, "").replace(C.RESET, "").replace(C.WHITE,""))
        # Just print them side by side
        print(f"{l:<38}{r}")

    # ── Feature pills ─────────────────────────────────────────────────────────
    pills = [
        ("🤖 AI ASSISTANT",    C.MAGENTA),
        ("🎨 MULTI-THEME",     C.BLUE),
        ("🔒 CRYPTO SUITE",    C.GREEN),
        ("🌐 NET SCANNER",     C.CYAN),
        ("📌 BOOKMARKS",       C.YELLOW),
        ("📝 NOTES & TODO",    C.ORANGE),
        ("💾 PERSISTENT",      C.RED),
        ("🌀 MATRIX MODE",     C.TRUE_GREEN),
    ]
    pill_str = "\n  "
    for label, color in pills:
        pill_str += f"{color}[{C.BOLD} {label} {C.RESET}{color}]{C.RESET}  "
    print(pill_str)

    # ── Random quote ──────────────────────────────────────────────────────────
    quote = random.choice(HACKER_QUOTES)
    print(f"\n  {C.DIM}{C.ITALIC}{quote}{C.RESET}")

    # ── Bottom border + help line ──────────────────────────────────────────────
    print(f"\n{C.BLUE}{'═'*width}{C.RESET}")
    print(
        f"  {C.GRAY}Type {C.CYAN}help{C.GRAY} for commands · "
        f"{C.CYAN}ai <question>{C.GRAY} for AI help · "
        f"{C.CYAN}theme <name>{C.GRAY} to switch theme · "
        f"{C.CYAN}exit{C.GRAY} to quit{C.RESET}\n"
    )
