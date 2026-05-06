#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║       ██╗  ██╗ █████╗ ██╗     ██╗    ████████╗███████╗██████╗       ║
║       ██║ ██╔╝██╔══██╗██║     ██║    ╚══██╔══╝██╔════╝██╔══██╗      ║
║       █████╔╝ ███████║██║     ██║       ██║   █████╗  ██████╔╝      ║
║       ██╔═██╗ ██╔══██║██║     ██║       ██║   ██╔══╝  ██╔══██╗      ║
║       ██║  ██╗██║  ██║███████╗██║       ██║   ███████╗██║  ██║      ║
║       ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝       ╚═╝   ╚══════╝╚═╝  ╚═╝      ║
║                                                                      ║
║              LINUX TERMINAL SIMULATOR — VERSION 1.0.0               ║
║         Python-Powered · AI-Enhanced · Hacker-Grade Terminal         ║
╚══════════════════════════════════════════════════════════════════════╝

 KALI TERMINAL v1.0.0 — Entry Point
 Built with Python · AI · Power · Style

 Features:
   ▸ AI Assistant (Claude-powered cybersecurity help)
   ▸ Multi-Theme Engine (Kali / Dracula / Matrix / Ocean / Blood)
   ▸ Persistent Aliases, Bookmarks, Notes, TODO
   ▸ Python Network Scanner & Tools
   ▸ Crypto Suite (Hash / Encode / Decode / Cipher)
   ▸ Git-aware Prompt with Branch + Dirty Status
   ▸ Smart Tab Completion with Metadata
   ▸ Session Recording & Replay
   ▸ Plugin Architecture
   ▸ Matrix Rain Animation
   ▸ Live System Monitoring
   ▸ And 20+ more features...
"""

import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.terminal import KaliTerminal


def main():
    terminal = KaliTerminal()
    terminal.run()


if __name__ == "__main__":
    main()
