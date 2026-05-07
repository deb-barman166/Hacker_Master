"""
core/completer.py — Smart tab completion for KaliTerminal v2.

Completes:
  - Built-in commands
  - Files and directories (relative & absolute)
  - ~/ paths
  - Command sub-arguments where known
  - History-based suggestions
"""

import os
from prompt_toolkit.completion import Completer, Completion


# All built-in commands — populated by terminal on init
_KNOWN_COMMANDS: list[str] = []


def register_commands(cmds: list[str]):
    global _KNOWN_COMMANDS
    _KNOWN_COMMANDS = sorted(cmds)


class KaliCompleter(Completer):
    def __init__(self, cwd_getter):
        self._cwd = cwd_getter

    # ── Main entry ────────────────────────────────────────────────────────

    def get_completions(self, document, complete_event):
        text   = document.text_before_cursor
        word   = document.get_word_before_cursor(WORD=True)
        parts  = text.split()
        cwd    = self._cwd()

        # ── Empty line or just whitespace → all commands ──────────────────
        if not parts or (len(parts) == 1 and not text.endswith(" ")):
            prefix = parts[0] if parts else ""
            yield from self._complete_commands(prefix)
            return

        # ── First word complete → files/dirs for args ─────────────────────
        cmd   = parts[0]
        arg   = word  # the fragment being completed

        # Path-ish: absolute, ~, or contains /
        if arg.startswith("/") or arg.startswith("~") or "/" in arg:
            yield from self._complete_path(arg, cwd)
            return

        # ── Command-specific sub-completions ──────────────────────────────
        subs = _SUBCOMMANDS.get(cmd)
        if subs and len(parts) == 2 and not text.endswith(" "):
            yield from (
                Completion(s[len(arg):], display=s)
                for s in subs if s.startswith(arg)
            )
            return

        # ── Default: files + dirs ─────────────────────────────────────────
        yield from self._complete_path(arg, cwd)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _complete_commands(self, prefix: str):
        for cmd in _KNOWN_COMMANDS:
            if cmd.startswith(prefix):
                yield Completion(cmd[len(prefix):], display=cmd,
                                 display_meta="command")

    def _complete_path(self, fragment: str, cwd: str):
        """Complete filesystem paths."""
        # Expand ~
        expanded = os.path.expanduser(fragment)

        if os.path.isabs(expanded):
            base_dir  = os.path.dirname(expanded)
            name_part = os.path.basename(expanded)
        else:
            # Relative: interpret from cwd
            joined    = os.path.join(cwd, expanded)
            base_dir  = os.path.dirname(joined)
            name_part = os.path.basename(joined)

        try:
            entries = os.listdir(base_dir or cwd)
        except (PermissionError, FileNotFoundError):
            return

        for entry in sorted(entries):
            if entry.startswith(".") and not name_part.startswith("."):
                continue
            if not entry.startswith(name_part):
                continue

            full = os.path.join(base_dir, entry)
            is_dir = os.path.isdir(full)
            suffix = "/" if is_dir else ""

            # Calculate what to insert after the current fragment
            if os.path.isabs(expanded):
                display_path = os.path.join(base_dir, entry) + suffix
                to_insert    = display_path[len(fragment):]
            else:
                to_insert    = entry[len(name_part):] + suffix
                display_path = entry + suffix

            meta = "dir" if is_dir else "file"
            yield Completion(
                to_insert,
                display=display_path,
                display_meta=meta,
                start_position=0,
            )


# ── Sub-command hints per command ─────────────────────────────────────────────
_SUBCOMMANDS: dict[str, list[str]] = {
    "ai":         ["on", "off", "mode", "setup", "key", "explain",
                   "code", "ctf", "scan", "models", "chat", "status"],
    "theme":      ["kali", "matrix", "cyberpunk", "dracula",
                   "midnight", "blood", "ocean"],
    "theme-list": [],
    "port-scan":  [],
    "dns-lookup": ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"],
    "ssl-check":  [],
    "http-headers": [],
    "whois":      [],
    "ip-geo":     [],
    "hash":       ["md5", "sha1", "sha256", "sha512", "sha3_256", "all"],
    "encode":     ["base64", "url", "hex", "binary", "rot13"],
    "decode":     ["base64", "url", "hex", "binary", "rot13"],
    "jwt-decode": [],
    "password-gen": ["--no-special", "--no-ambiguous", "--pin", "--passphrase"],
    "password-audit": [],
    "vuln-search": [],
    "proc-monitor": ["top", "search", "kill", "tree"],
    "disk-usage": [],
    "note":       ["add", "list", "delete", "search", "clear"],
    "todo":       ["add", "list", "done", "delete", "clear", "high", "critical"],
    "alias":      ["list", "add", "remove"],
    "bookmark":   ["add", "go", "list", "remove"],
    "set":        ["show_git", "show_time", "vi_mode", "safe_mode",
                   "complete_while_type", "fast_banner"],
    "calc":       [],
    "timer":      ["start", "stop", "lap"],
    "cheatsheet": ["nmap", "sqlmap", "burp", "metasploit", "wireshark",
                   "hydra", "john", "hashcat", "gobuster", "curl", "netcat"],
    "help":       [],
    "history":    ["clear", "search"],
    "cd":         [],
    "export":     [],
}
