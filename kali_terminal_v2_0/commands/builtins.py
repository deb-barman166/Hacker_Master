"""
commands/builtins.py — Built-in shell commands (v2.0 Masterpiece).

Enhanced from v1 with many new builtins and cybersecurity features.
"""

import os
import sys
import platform
import subprocess
import socket
import random
import time
import shutil
import re
from datetime import datetime

from ui.theme import Colors

C = Colors


# ─────────────────────────────────────────────────────────────────────────
# cd — Change Directory
# ─────────────────────────────────────────────────────────────────────────
def cmd_cd(args: list, state: dict, terminal=None) -> int:
    """Change directory. Supports: cd, cd ~, cd .., cd -, cd /path."""
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
        print(C.error(f"cd: {args[0] if args else ''}: No such file or directory"))
        return 1
    except PermissionError:
        print(C.error(f"cd: {args[0] if args else ''}: Permission denied"))
        return 1
    except NotADirectoryError:
        print(C.error(f"cd: {args[0] if args else ''}: Not a directory"))
        return 1


# ─────────────────────────────────────────────────────────────────────────
# clear — Clear Screen
# ─────────────────────────────────────────────────────────────────────────
def cmd_clear(args: list, state: dict, terminal=None) -> int:
    """Clear the terminal screen."""
    os.system("clear" if os.name != "nt" else "cls")
    return 0


# ─────────────────────────────────────────────────────────────────────────
# history — Command History
# ─────────────────────────────────────────────────────────────────────────
def cmd_history(args: list, state: dict, terminal=None) -> int:
    """Show/search command history."""
    hist = state.get("history", [])

    if args and args[0] == "-c":
        state["history"] = []
        print(C.success("History cleared."))
        return 0

    if args and args[0] == "-s":
        pattern = " ".join(args[1:])
        if not pattern:
            print(C.error("history -s: pattern required"))
            return 1
        matches = [(i+1, h) for i, h in enumerate(hist) if pattern.lower() in h.lower()]
        if not matches:
            print(C.info(f"No matches for '{pattern}'"))
            return 0
        print(f"\n{C.BLUE}{'─'*60}{C.RESET}")
        print(f"  {C.BOLD}{C.WHITE}History search: '{pattern}' ({len(matches)} matches){C.RESET}")
        print(f"{C.BLUE}{'─'*60}{C.RESET}")
        for num, cmd in matches:
            print(f"  {C.GRAY}{num:5d}{C.RESET}  {C.CYAN}{cmd}{C.RESET}")
        print(f"{C.BLUE}{'─'*60}{C.RESET}\n")
        return 0

    n = 20
    if args:
        try:
            n = int(args[0])
        except ValueError:
            print(C.error(f"history: invalid count: {args[0]}"))
            return 1

    entries = hist[-n:]
    if not entries:
        print(C.info("No history yet."))
        return 0

    start = max(1, len(hist) - n + 1)
    print(f"\n{C.BLUE}{'─'*60}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}Command History (last {min(n, len(hist))} of {len(hist)}){C.RESET}")
    print(f"{C.BLUE}{'─'*60}{C.RESET}")
    for i, cmd in enumerate(entries, start=start):
        print(f"  {C.GRAY}{i:5d}{C.RESET}  {C.CYAN}{cmd}{C.RESET}")
    print(f"{C.BLUE}{'─'*60}{C.RESET}\n")
    return 0


# ─────────────────────────────────────────────────────────────────────────
# cheatsheet — Linux Command Quick Reference (Enhanced)
# ─────────────────────────────────────────────────────────────────────────
CHEATSHEET = {
    "FILE OPERATIONS": [
        ("ls -la", "List all files with details"),
        ("ls -lh", "Human-readable sizes"),
        ("pwd", "Print current directory"),
        ("cd /path", "Change directory"),
        ("mkdir -p a/b/c", "Create nested directories"),
        ("rm -rf dir/", "Remove directory recursively"),
        ("cp -r src/ dst/", "Copy directory recursively"),
        ("find / -name '*.py'", "Find files by name"),
    ],
    "NETWORKING": [
        ("nmap -sV host", "Service version scan"),
        ("nmap -p- host", "Full port scan"),
        ("curl -I http://site", "HTTP headers only"),
        ("ping -c 4 host", "Ping 4 times"),
        ("netstat -tulnp", "Listening ports"),
    ],
    "SECURITY": [
        ("nmap -A host", "Aggressive scan"),
        ("sqlmap -u 'url'", "SQL injection test"),
        ("hydra -l user -P pass.txt ssh host", "SSH brute force"),
        ("john hash.txt", "Password cracker"),
        ("hashcat -m 0 hash.txt", "GPU hash cracker"),
    ],
}


def cmd_cheatsheet(args: list, state: dict, terminal=None) -> int:
    """Print the Linux command cheatsheet, optionally filtered by topic."""
    filter_term = args[0].upper() if args else None

    sections_shown = 0
    for section, rows in CHEATSHEET.items():
        if filter_term and filter_term not in section.upper():
            continue
        sections_shown += 1
        print(f"\n{C.RED}{C.BOLD}  >> {section}{C.RESET}")
        print(f"  {C.BLUE}{'─'*65}{C.RESET}")
        for item in rows:
            if isinstance(item, tuple):
                cmd_str, desc = item
            else:
                cmd_str, desc = item, ""
            print(f"  {C.CYAN}{cmd_str:<42}{C.RESET}{C.GRAY}{desc}{C.RESET}")

    if sections_shown == 0:
        avail = ", ".join(CHEATSHEET.keys())
        print(C.warn(f"No section matching '{args[0]}'. Available: {avail}"))
        return 1
    print()
    return 0


# ─────────────────────────────────────────────────────────────────────────
# tips — Random Linux Tips
# ─────────────────────────────────────────────────────────────────────────
TIPS = [
    "Use 'history -s pattern' to search your command history.",
    "Use '!!' to repeat the last command.",
    "Use '!$' to reuse the last argument of the previous command.",
    "Press Ctrl+R to search command history interactively.",
    "Use 'alias ll=ls -la' to create a shortcut command.",
    "Use 'time command' to measure how long a command takes.",
    "Use 'nohup command &' to run a command immune to hangups.",
]


def cmd_tips(args: list, state: dict, terminal=None) -> int:
    """Show a random Linux pro-tip."""
    tip = random.choice(TIPS)
    print(f"\n{C.YELLOW}{C.BOLD}[*] Linux Pro Tip:{C.RESET}")
    print(f"  {C.WHITE}{tip}{C.RESET}\n")
    return 0


# ─────────────────────────────────────────────────────────────────────────
# theme — Switch terminal theme
# ─────────────────────────────────────────────────────────────────────────
def cmd_theme(args: list, state: dict, terminal=None) -> int:
    """Switch the terminal color theme."""
    if not args:
        from core.config import get_config
        current = get_config().theme
        print(C.info(f"Current theme: {C.BOLD}{current}{C.RESET}"))
        print(C.info("Use 'theme-list' to see available themes."))
        return 0

    theme_name = args[0].lower()
    from ui.theme import set_theme
    try:
        set_theme(theme_name)
        if terminal:
            terminal.config.set("theme", theme_name)
            terminal.config.save()
        print(C.success(f"Theme changed to '{theme_name}'."))
    except ValueError as e:
        print(C.error(str(e)))
        return 1
    return 0


def cmd_theme_list(args: list, state: dict, terminal=None) -> int:
    """List all available themes."""
    from ui.themes import THEMES
    from core.config import get_config
    current = get_config().theme

    print(f"\n{C.BLUE}{'='*55}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}AVAILABLE THEMES{C.RESET}")
    print(f"{C.BLUE}{'='*55}{C.RESET}")
    for key, theme in THEMES.items():
        marker = C.paint(" <-- ACTIVE", C.GREEN, bold=True) if key == current else ""
        print(f"  {C.CYAN}{key:<15}{C.RESET} {C.WHITE}{theme['name']}{C.RESET}{marker}")
    print(f"{C.BLUE}{'='*55}{C.RESET}")
    print(f"  {C.GRAY}Usage: theme <name>{C.RESET}\n")
    return 0


# ─────────────────────────────────────────────────────────────────────────
# calc — Built-in Calculator
# ─────────────────────────────────────────────────────────────────────────
def cmd_calc(args: list, state: dict, terminal=None) -> int:
    """Evaluate a mathematical expression."""
    if not args:
        print(C.info("Usage: calc <expression>"))
        print(C.info("Examples: calc 2+2, calc 'sin(3.14)', calc '2**10'"))
        print(C.info("Supports: +, -, *, /, **, (), sin, cos, tan, sqrt, log, pi, e"))
        return 0

    expr = " ".join(args)
    allowed_names = {
        "sin": __import__("math").sin,
        "cos": __import__("math").cos,
        "tan": __import__("math").tan,
        "sqrt": __import__("math").sqrt,
        "log": __import__("math").log,
        "pi": __import__("math").pi,
        "e": __import__("math").e,
        "abs": abs, "round": round, "int": int, "float": float,
        "pow": pow, "max": max, "min": min,
    }

    try:
        expr = expr.replace("^", "**")
        result = eval(expr, {"__builtins__": {}}, allowed_names)
        print(f"\n  {C.CYAN}{expr}{C.RESET} {C.YELLOW}={C.RESET} {C.GREEN}{C.BOLD}{result}{C.RESET}\n")
    except ZeroDivisionError:
        print(C.error("Division by zero"))
        return 1
    except Exception as e:
        print(C.error(f"Invalid expression: {e}"))
        return 1
    return 0


# ─────────────────────────────────────────────────────────────────────────
# help — Main Help Screen (Enhanced)
# ─────────────────────────────────────────────────────────────────────────
def cmd_help(args: list, state: dict, terminal=None) -> int:
    """Show comprehensive help for all built-in commands."""
    print(f"""
{C.BLUE}{'='*75}{C.RESET}
{C.BLUE}|{C.RESET}  {C.RED}{C.BOLD}KALI TERMINAL v2.0 MASTERPIECE — COMMAND REFERENCE{C.RESET}{' '*17}{C.BLUE}|{C.RESET}
{C.BLUE}{'='*75}{C.RESET}

{C.YELLOW}{C.BOLD}NAVIGATION:{C.RESET}
  {C.CYAN}cd [path]{C.RESET}       Change directory (~, -, ..)
  {C.CYAN}pwd{C.RESET}            Print working directory
  {C.CYAN}ls, ll, la{C.RESET}     List directory contents

{C.YELLOW}{C.BOLD}NETWORK TOOLS:{C.RESET}
  {C.CYAN}ip-info{C.RESET}        Network interface information
  {C.CYAN}port-scan <host>{C.RESET} TCP port scanner
  {C.CYAN}subnet-calc <IP/CIDR>{C.RESET} Subnet calculator
  {C.CYAN}dns-lookup <domain>{C.RESET} DNS lookup
  {C.CYAN}whois <domain>{C.RESET} WHOIS lookup
  {C.CYAN}traceroute <host>{C.RESET} Traceroute utility
  {C.CYAN}ping-sweep <network>{C.RESET} Ping sweep

{C.YELLOW}{C.BOLD}CRYPTOGRAPHY:{C.RESET}
  {C.CYAN}hash <file>{C.RESET}    Calculate file hash (MD5, SHA1, SHA256, etc.)
  {C.CYAN}encode <text>{C.RESET}  Encode text (base64, url, hex, html, unicode)
  {C.CYAN}decode <text>{C.RESET}  Decode text
  {C.CYAN}rot13 <text>{C.RESET}   ROT13 cipher
  {C.CYAN}caesar <text> <shift>{C.RESET} Caesar cipher
  {C.CYAN}hash-identify <hash>{C.RESET} Identify hash type
  {C.CYAN}ssl-check <host>{C.RESET} SSL/TLS certificate checker

{C.YELLOW}{C.BOLD}WEB SECURITY:{C.RESET}
  {C.CYAN}http-headers <url>{C.RESET} Fetch HTTP headers
  {C.CYAN}http-post <url> <data>{C.RESET} Send POST request
  {C.CYAN}sql-test <url>{C.RESET} Basic SQL injection test
  {C.CYAN}xss-test <url>{C.RESET} XSS payload generator
  {C.CYAN}dir-scan <url>{C.RESET} Directory scanner
  {C.CYAN}cert-check <host>{C.RESET} SSL certificate checker

{C.YELLOW}{C.BOLD}FORENSICS:{C.RESET}
  {C.CYAN}hexdump <file>{C.RESET} Hex dump of file
  {C.CYAN}strings <file>{C.RESET} Extract strings from binary
  {C.CYAN}file-analysis <file>{C.RESET} Comprehensive file analysis
  {C.CYAN}entropy <file>{C.RESET} Calculate file entropy
  {C.CYAN}xor-data <file> <key>{C.RESET} XOR data with key
  {C.CYAN}binwalk <file>{C.RESET} Analyze binary for embedded files

{C.YELLOW}{C.BOLD}AI INTEGRATION:{C.RESET}
  {C.CYAN}ai-enable [backend]{C.RESET} Enable AI (ollama, openai, anthropic, gemini)
  {C.CYAN}ai-disable{C.RESET}      Disable AI
  {C.CYAN}ai <prompt>{C.RESET}     Chat with AI
  {C.CYAN}ai-explain <concept>{C.RESET} Get explanation
  {C.CYAN}ai-analyze <type>{C.RESET} Analyze with AI
  {C.CYAN}ai-help{C.RESET}        AI help and setup

{C.YELLOW}{C.BOLD}SECURITY:{C.RESET}
  {C.CYAN}password-gen [length]{C.RESET} Generate secure passwords
  {C.CYAN}random-uuid [count]{C.RESET} Generate UUIDs
  {C.CYAN}random-mac [count]{C.RESET} Generate MAC addresses
  {C.CYAN}cypher <text> <key>{C.RESET} Encrypt text
  {C.CYAN}decypher <text> <key>{C.RESET} Decrypt text

{C.YELLOW}{C.BOLD}SYSTEM:{C.RESET}
  {C.CYAN}sysinfo{C.RESET}        Full system information
  {C.CYAN}disk-usage [path]{C.RESET} Disk usage analyzer
  {C.CYAN}proc-monitor{C.RESET}   Process monitor

{C.YELLOW}{C.BOLD}CUSTOMIZATION:{C.RESET}
  {C.CYAN}theme <name>{C.RESET}  Switch color theme
  {C.CYAN}theme-list{C.RESET}    List available themes
  {C.CYAN}alias name=cmd{C.RESET} Create command alias
  {C.CYAN}history{C.RESET}       Command history

{C.YELLOW}{C.BOLD}PRODUCTIVITY:{C.RESET}
  {C.CYAN}calc <expr>{C.RESET}     Math calculator
  {C.CYAN}cheatsheet [topic]{C.RESET} Command reference
  {C.CYAN}tips{C.RESET}          Random Linux tips
  {C.CYAN}matrix{C.RESET}        Matrix rain effect
  {C.CYAN}quote{C.RESET}         Random hacker quote

{C.BLUE}{'='*75}{C.RESET}
{C.BLUE}|{C.RESET}  {C.GRAY}All Linux commands work: ls, grep, nmap, curl, git, python3, ...{C.RESET}    {C.BLUE}|{C.RESET}
{C.BLUE}|{C.RESET}  {C.GRAY}Tab=complete  Up/Down=history  Ctrl+R=search  Ctrl+L=clear{C.RESET}          {C.BLUE}|{C.RESET}
{C.BLUE}{'='*75}{C.RESET}
""")


# ─────────────────────────────────────────────────────────────────────────
# Dispatch Table
# ─────────────────────────────────────────────────────────────────────────
BUILTINS = {
    "cd": cmd_cd,
    "clear": cmd_clear,
    "cls": cmd_clear,
    "history": cmd_history,
    "cheatsheet": cmd_cheatsheet,
    "tips": cmd_tips,
    "help": cmd_help,
    "theme": cmd_theme,
    "theme-list": cmd_theme_list,
    "calc": cmd_calc,
}