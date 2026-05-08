"""
core/completer.py — Tab completion for Kali Terminal v2.0 Masterpiece.
"""

from prompt_toolkit.completion import Completer, Completion, PathCompleter
from prompt_toolkit.completion.word_completer import WordCompleter
import os
import shlex


class KaliCompleter(Completer):
    """Tab completer for Kali Terminal."""

    def __init__(self, cwd_getter=None, alias_getter=None):
        self.cwd_getter = cwd_getter or (lambda: os.getcwd())
        self.alias_getter = alias_getter or (lambda: [])

        # Built-in commands
        self.commands = [
            # Navigation
            "cd", "pwd", "ls", "ll", "la",
            # Display
            "clear", "cls", "history", "help", "cheatsheet", "tips",
            # System
            "sysinfo", "services", "uptime", "whoami",
            # Calculator/Timer
            "calc", "timer", "stopwatch",
            # Themes
            "theme", "theme-list", "colors-demo",
            # Aliases
            "alias", "unalias", "aliases",
            # Environment
            "export", "unset", "source",
            # Network
            "ip-info", "netstat-enhanced", "port-scan", "subnet-calc",
            "dns-lookup", "whois", "traceroute", "ping-sweep",
            # Crypto
            "hash", "encode", "decode", "rot13", "caesar",
            "hash-identify", "hash-crack", "ssl-check",
            # Security
            "password-gen", "random-uuid", "random-mac", "sanitize",
            "cypher", "decypher", "base64-img",
            # Forensics
            "hexdump", "strings", "file-analysis", "entropy", "xor-data", "binwalk",
            # Web
            "http-headers", "http-post", "sql-test", "xss-test",
            "dir-scan", "subdomain-enum", "cert-check",
            # AI
            "ai-enable", "ai-disable", "ai-config", "ai", "ai-explain",
            "ai-analyze", "ai-help",
            # System Tools
            "disk-usage", "proc-monitor",
            # Text
            "json-format", "json-minify", "yaml-convert", "markdown",
            "ascii-table", "regex-test",
            # Productivity
            "notes", "todo", "plugins", "save-session", "load-session",
            "lsessions", "calendar", "reminders",
            # Fun
            "matrix", "quote", "man-pages",
        ]

        # Network-related completions
        self.network_commands = [
            "nmap", "nikto", "dirb", "gobuster", "hydra",
            "sqlmap", "burpsuite", "wireshark", "tcpdump",
            "ping", "traceroute", "nslookup", "dig",
            "curl", "wget", "netstat", "ss", "ifconfig", "ip",
        ]

        self.command_completer = WordCompleter(
            self.commands + self.network_commands,
            ignore_case=True
        )
        self.path_completer = PathCompleter()

    def get_completions(self, document, complete_event):
        """Generate completions based on current text."""
        text = document.text_before_cursor
        cwd = self.cwd_getter()

        # Handle command completion
        if not text or text.endswith(" "):
            if text:
                cmd = text.strip().split()[0] if text.strip() else ""
                # Show command completions
                for cmd_name in self.commands:
                    if cmd_name.startswith(cmd.lower()):
                        yield Completion(
                            cmd_name,
                            start_position=-len(cmd) if cmd else 0
                        )
            return

        # Parse current input
        try:
            parts = shlex.split(text)
        except ValueError:
            parts = text.split()

        # Complete command name
        if len(parts) == 1:
            cmd = parts[0]
            for cmd_name in self.commands + self.network_commands:
                if cmd_name.startswith(cmd.lower()):
                    yield Completion(
                        cmd_name,
                        start_position=-len(cmd)
                    )

        # Complete file paths
        elif len(parts) > 1:
            last_part = parts[-1]
            if last_part.startswith("-"):
                return

            # Path completion
            if "/" in last_part or "~" in last_part:
                for completion in self.path_completer.get_completions(document, complete_event):
                    yield completion

            # Complete option flags for specific commands
            cmd = parts[0].lower()
            if cmd == "theme":
                themes = ["kali", "hacker", "matrix", "cyberpunk", "nord", "dracula", "monokai"]
                for theme in themes:
                    if theme.startswith(last_part.lower()):
                        yield Completion(theme, start_position=-len(last_part))

            elif cmd == "hash":
                algos = ["md5", "sha1", "sha256", "sha512", "all"]
                for algo in algos:
                    if algo.startswith(last_part.lower()):
                        yield Completion(algo, start_position=-len(last_part))

            elif cmd == "encode":
                formats = ["base64", "url", "hex", "html", "unicode", "binary", "octal"]
                for fmt in formats:
                    if fmt.startswith(last_part.lower()):
                        yield Completion(fmt, start_position=-len(last_part))

            elif cmd == "decode":
                formats = ["base64", "url", "hex", "html", "unicode", "binary", "octal"]
                for fmt in formats:
                    if fmt.startswith(last_part.lower()):
                        yield Completion(fmt, start_position=-len(last_part))

        # Complete aliases
        for alias in self.alias_getter():
            if alias.startswith(parts[-1] if parts else ""):
                yield Completion(alias, start_position=-len(parts[-1] if parts else ""))