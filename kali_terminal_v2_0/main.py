"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║     ██╗  ██╗ █████╗ ██╗     ██╗    ██████╗ ██████╗ ██████╗ ██╗   ██╗██╗      ║
║     ██║ ██╔╝██╔══██╗██║     ██║    ██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝██║      ║
║     █████╔╝ ███████║██║     ██║    ██████╔╝██████╔╝██████╔╝ ╚████╔╝ ██║      ║
║     ██╔═██╗ ██╔══██║██║     ██║    ██╔══██╗██╔══██╗██╔══██╗  ╚██╔╝  ██║      ║
║     ██║  ██╗██║  ██║███████╗██║    ██║  ██║██║  ██║██║  ██║   ██║   ███████╗ ║
║     ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚══════╝ ║
║                                                                               ║
║           KALI LINUX TERMINAL SIMULATOR — v2.0 MASTERPIECE                    ║
║           Professional Cybersecurity Framework with AI Integration            ║
║           Built with Python · 34 Years Experience · Plugin Architecture       ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Entry point — boots the terminal engine with full feature set.
Supports local AI (Ollama) and cloud AI (API keys).
"""

import sys
import os
import argparse

# Ensure we can import from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.terminal import KaliTerminal


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Kali Linux Terminal v2.0 Masterpiece",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--no-banner", "-nb",
        action="store_true",
        help="Skip displaying the boot banner"
    )
    parser.add_argument(
        "--theme", "-t",
        default="kali",
        choices=["kali", "hacker", "matrix", "cyberpunk", "nord", "dracula", "monokai"],
        help="Set initial color theme (default: kali)"
    )
    parser.add_argument(
        "--ai-backend", "-a",
        choices=["ollama", "openai", "anthropic", "gemini", "none"],
        default="none",
        help="Set AI backend (default: none)"
    )
    parser.add_argument(
        "--ai-model", "-m",
        default=None,
        help="Specify AI model to use"
    )
    parser.add_argument(
        "--config", "-c",
        default=None,
        help="Path to custom configuration file"
    )
    parser.add_argument(
        "--command", "-cmd",
        nargs="*",
        help="Execute command(s) and exit"
    )
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Display version information"
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()

    if args.version:
        print("""
╔═══════════════════════════════════════════════════════════════╗
║   Kali Terminal v2.0 Masterpiece                              ║
║   Professional Cybersecurity Framework                         ║
║   Built with Python · AI-Powered · Plugin Architecture        ║
╚═══════════════════════════════════════════════════════════════╝
        """)
        return

    # Initialize and run terminal
    terminal = KaliTerminal(
        show_banner=not args.no_banner,
        theme=args.theme,
        ai_backend=args.ai_backend,
        ai_model=args.ai_model,
        config_path=args.config
    )

    # Execute single commands if provided
    if args.command:
        for cmd in args.command:
            terminal._dispatch(cmd)
        return

    terminal.run()


if __name__ == "__main__":
    main()