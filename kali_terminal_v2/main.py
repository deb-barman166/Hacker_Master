#!/usr/bin/env python3
"""
██╗  ██╗ █████╗ ██╗     ██╗    ████████╗███████╗██████╗ ███╗   ███╗
██║ ██╔╝██╔══██╗██║     ██║    ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║
█████╔╝ ███████║██║     ██║       ██║   █████╗  ██████╔╝██╔████╔██║
██╔═██╗ ██╔══██║██║     ██║       ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║
██║  ██╗██║  ██║███████╗██║       ██║   ███████╗██║  ██║██║ ╚═╝ ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝       ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝

                    PYTHON v2 — MASTERPIECE EDITION
              A Professional Cybersecurity Terminal Experience

Author  : KaliTerminal v2 Project
Python  : 3.9+
License : MIT

Usage:
    python main.py               normal boot
    python main.py --fast        skip banner animation
    python main.py --theme <n>   start with a specific theme
    python main.py --help        show this message
"""

import os
import sys

# ── Python version check ───────────────────────────────────────────────────────
if sys.version_info < (3, 9):
    print("❌  KaliTerminal v2 requires Python 3.9 or higher.")
    print(f"   Current version: {sys.version}")
    print("   Install from: https://www.python.org/downloads/")
    sys.exit(1)

# ── Ensure project root is in path ────────────────────────────────────────────
ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def check_dependencies() -> bool:
    """Check for required packages and offer to install missing ones."""
    required = {
        "prompt_toolkit": "prompt-toolkit>=3.0",
    }
    optional = {
        "psutil": "psutil",
    }

    missing_required = []
    missing_optional = []

    for mod, pkg in required.items():
        try:
            __import__(mod)
        except ImportError:
            missing_required.append(pkg)

    for mod, pkg in optional.items():
        try:
            __import__(mod)
        except ImportError:
            missing_optional.append(pkg)

    if missing_required:
        print("❌  Missing required packages:")
        for pkg in missing_required:
            print(f"   • {pkg}")
        print("\n   Install with:")
        print(f"   pip install {' '.join(missing_required)}")
        print("   OR: pip install -r requirements.txt\n")
        return False

    if missing_optional:
        print("⚠   Optional packages not installed (some features limited):")
        for pkg in missing_optional:
            print(f"   • {pkg}  (system stats, process monitor, network info)")
        print("   Install: pip install psutil\n")

    return True


def parse_args():
    """Simple argument parser (no argparse dependency)."""
    opts = {
        "fast":  False,
        "theme": None,
        "help":  False,
    }
    args = sys.argv[1:]
    i    = 0
    while i < len(args):
        a = args[i]
        if a in ("--fast", "-f"):
            opts["fast"] = True
        elif a in ("--help", "-h"):
            opts["help"] = True
        elif a in ("--theme", "-t") and i+1 < len(args):
            opts["theme"] = args[i+1]; i += 1
        i += 1
    return opts


def main():
    opts = parse_args()

    if opts["help"]:
        print(__doc__)
        sys.exit(0)

    if not check_dependencies():
        sys.exit(1)

    # ── Import after dependency check ──────────────────────────────────────
    from core.terminal import KaliTerminal
    from ui.theme      import set_theme

    # ── Apply CLI theme override ───────────────────────────────────────────
    if opts["theme"]:
        try:
            set_theme(opts["theme"])
        except ValueError as e:
            print(f"⚠  {e}. Using default 'kali' theme.")

    # ── Apply fast-banner flag to prefs for this session ──────────────────
    if opts["fast"]:
        from utils.config import set_pref
        # Temporarily, not persistently
        os.environ["KALI_FAST_BANNER"] = "1"

    # ── Boot terminal ──────────────────────────────────────────────────────
    terminal = KaliTerminal()

    if opts["fast"]:
        terminal.state["prefs"]["fast_banner"] = True

    try:
        terminal.run()
    except KeyboardInterrupt:
        print("\n")
    except Exception as e:
        print(f"\n\033[38;5;196m[FATAL] Unexpected error: {e}\033[0m")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
