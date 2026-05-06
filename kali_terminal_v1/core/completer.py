"""
core/completer.py — Smart Tab Completer for Kali Terminal v1.0

Completes:
  • All commands on PATH
  • All built-in commands (with descriptions)
  • File / directory paths (absolute + relative + ~)
  • Bookmark names for `bookmark go`
  • Alias names
  • Theme names for `theme`
  • Subcommands for built-ins (todo add, note list, etc.)
"""

import os
from typing import Iterable

from prompt_toolkit.completion import Completer, Completion


# ── All built-in names + metadata ─────────────────────────────────────────────

BUILTIN_META: dict[str, str] = {
    # Navigation
    "cd":           "change directory",
    "tree":         "colored directory tree",
    "bookmark":     "named dir bookmarks",
    "bm":           "bookmark alias",
    # System
    "clear":        "clear screen",
    "cls":          "clear screen",
    "history":      "command history",
    "sysinfo":      "system info panel",
    "monitor":      "live system monitor",
    "calc":         "math calculator",
    "weather":      "ASCII weather",
    # Theme & Config
    "theme":        "switch theme",
    "alias":        "manage aliases",
    "set":          "terminal preferences",
    # Notes & Tasks
    "note":         "sticky notes",
    "notes":        "sticky notes",
    "todo":         "task manager",
    "todos":        "task manager",
    # Network
    "scan":         "TCP port scanner",
    "ping_sweep":   "ICMP ping sweep",
    "dns":          "DNS lookup",
    "myip":         "show all IPs",
    "banner_grab":  "grab service banner",
    "http_headers": "HTTP response headers",
    # Crypto
    "hash":         "hash text/file",
    "encode":       "encode text",
    "decode":       "decode text",
    "caesar":       "Caesar cipher",
    "xor":          "XOR encryption",
    "passgen":      "password generator",
    "pwdcheck":     "password strength",
    # Fun
    "matrix":       "matrix rain animation",
    "tips":         "pro-tips",
    "cheatsheet":   "command reference",
    "about":        "about this terminal",
    # AI
    "ai":           "AI cybersec assistant (Claude)",
    # Help
    "help":         "show all commands",
    "?":            "show all commands",
    "exit":         "quit terminal",
    "quit":         "quit terminal",
}

# Sub-command completions
SUBCOMMANDS: dict[str, list[str]] = {
    "theme":      ["kali", "dracula", "matrix", "ocean", "blood", "list"],
    "bookmark":   ["add", "go", "del", "list"],
    "bm":         ["add", "go", "del", "list"],
    "note":       ["add", "list", "del", "ls"],
    "notes":      ["add", "list", "del", "ls"],
    "todo":       ["add", "done", "del", "list", "clear", "ls"],
    "todos":      ["add", "done", "del", "list", "clear", "ls"],
    "hash":       ["md5", "sha1", "sha256", "sha512", "sha224", "sha384", "blake2b", "blake2s", "all"],
    "encode":     ["base64", "url", "hex", "binary", "html", "rot13", "morse"],
    "decode":     ["base64", "url", "hex", "binary", "html", "rot13", "morse"],
    "ai":         ["explain", "code", "ctf", "scan", "--setup"],
    "set":        ["show_git_branch", "show_time_in_prompt", "show_exit_code", "autocomplete", "vi_mode"],
    "history":    ["-c", "--grep"],
    "cheatsheet": ["FILE", "NETWORK", "CRYPTO", "SYSTEM", "GIT", "PYTHON"],
    "tips":       ["all"],
}

# Path command metadata
CMD_META: dict[str, str] = {
    "ls":       "list files",       "ll":      "list (long)",
    "pwd":      "print working dir","mkdir":   "make directory",
    "rm":       "remove",           "cp":      "copy",
    "mv":       "move/rename",      "touch":   "create file",
    "find":     "find files",       "locate":  "locate files",
    "cat":      "show file",        "less":    "pager",
    "head":     "first N lines",    "tail":    "last N lines",
    "grep":     "search text",      "awk":     "text processor",
    "sed":      "stream editor",    "sort":    "sort lines",
    "wc":       "word count",       "diff":    "compare files",
    "ps":       "process list",     "top":     "system monitor",
    "htop":     "interactive top",  "kill":    "kill process",
    "df":       "disk space",       "du":      "disk usage",
    "free":     "memory info",      "uname":   "kernel info",
    "ping":     "ping host",        "curl":    "HTTP client",
    "wget":     "download file",    "ssh":     "SSH client",
    "nmap":     "port scanner",     "nc":      "netcat",
    "python3":  "Python 3",         "pip":     "Python packages",
    "git":      "version control",  "vim":     "editor",
    "nano":     "editor",           "tar":     "archive",
    "zip":      "zip archive",      "unzip":   "unzip",
    "chmod":    "set permissions",  "chown":   "change owner",
    "ifconfig": "network ifaces",   "ip":      "IP config",
    "docker":   "containers",       "kubectl": "Kubernetes",
    "gcc":      "C compiler",       "make":    "build tool",
    "john":     "password cracker", "hydra":   "brute force",
    "sqlmap":   "SQL injection",    "nikto":   "web scanner",
    "dirb":     "dir brute force",  "gobuster":"dir brute force",
}


# ── PATH command cache ─────────────────────────────────────────────────────────

_PATH_COMMANDS: list[str] | None = None


def _load_path_commands() -> list[str]:
    commands: set[str] = set()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        try:
            for name in os.listdir(directory):
                full = os.path.join(directory, name)
                if os.access(full, os.X_OK) and os.path.isfile(full):
                    commands.add(name)
        except (PermissionError, FileNotFoundError):
            pass
    return sorted(commands)


def get_path_commands() -> list[str]:
    global _PATH_COMMANDS
    if _PATH_COMMANDS is None:
        _PATH_COMMANDS = _load_path_commands()
    return _PATH_COMMANDS


# ── Main Completer ─────────────────────────────────────────────────────────────

class KaliCompleter(Completer):
    """Context-aware smart completer for Kali Terminal v1.0."""

    def __init__(self, cwd_getter, state_getter=None):
        self._cwd   = cwd_getter
        self._state = state_getter or (lambda: {})

    def get_completions(self, document, complete_event) -> Iterable[Completion]:
        text  = document.text_before_cursor
        words = text.split()
        word  = document.get_word_before_cursor(WORD=True)

        # ── First word: complete command names ────────────────────────────────
        is_first = (
            len(words) == 0
            or (len(words) == 1 and not text.endswith(" "))
        )
        if is_first:
            all_cmds = (
                list(BUILTIN_META.keys())
                + get_path_commands()
                + list(self._state().get("aliases", {}).keys())
            )
            seen = set()
            for cmd in sorted(set(all_cmds)):
                if cmd.startswith(word) and cmd not in seen:
                    seen.add(cmd)
                    meta = BUILTIN_META.get(cmd) or CMD_META.get(cmd, "")
                    yield Completion(
                        cmd,
                        start_position=-len(word),
                        display_meta=meta,
                    )
            return

        # ── Second word: subcommand completions for known commands ────────────
        first_cmd = words[0]
        is_second  = len(words) == 1 or (len(words) == 2 and not text.endswith(" "))

        if first_cmd in SUBCOMMANDS and is_second:
            for sub in SUBCOMMANDS[first_cmd]:
                if sub.startswith(word):
                    yield Completion(sub, start_position=-len(word))
            return

        # ── Bookmark names for `bookmark go` / `bm go` ───────────────────────
        if first_cmd in ("bookmark", "bm") and len(words) >= 2 and words[1] in ("go", "del"):
            bookmarks = self._state().get("bookmarks", {})
            for name in sorted(bookmarks):
                if name.startswith(word):
                    path = bookmarks[name]
                    yield Completion(name, start_position=-len(word),
                                     display_meta=path)
            return

        # ── Theme names for `theme` ───────────────────────────────────────────
        if first_cmd == "theme" and len(words) >= 2:
            from ui.theme import THEMES
            for name in THEMES:
                if name.startswith(word):
                    desc = THEMES[name].get("desc", "")[:30]
                    yield Completion(name, start_position=-len(word),
                                     display_meta=desc)
            return

        # ── Flag completions ──────────────────────────────────────────────────
        if word.startswith("-"):
            return  # Skip for now — too command-specific

        # ── File/directory path completion ────────────────────────────────────
        yield from self._path_completions(word)

    def _path_completions(self, prefix: str) -> Iterable[Completion]:
        """Complete file and directory paths."""
        expanded = os.path.expanduser(prefix)

        if os.path.isabs(expanded):
            base_dir = os.path.dirname(expanded)
            partial  = os.path.basename(expanded)
        else:
            cwd      = self._cwd()
            full     = os.path.join(cwd, expanded)
            base_dir = os.path.dirname(full)
            partial  = os.path.basename(full)

        try:
            entries = os.listdir(base_dir or ".")
        except (PermissionError, FileNotFoundError):
            return

        for name in sorted(entries):
            if not name.startswith(partial):
                continue

            full_path = os.path.join(base_dir, name)
            is_dir    = os.path.isdir(full_path)

            if os.path.isabs(expanded):
                completion = os.path.join(os.path.dirname(expanded), name)
            else:
                import os.path as osp
                rel = osp.relpath(full_path, self._cwd())
                completion = rel

            if is_dir:
                completion += "/"

            try:
                stat = os.stat(full_path)
                size = stat.st_size
                if size >= 1024**2:
                    meta = f"{size//(1024**2)}MB"
                elif size >= 1024:
                    meta = f"{size//1024}KB"
                else:
                    meta = f"{size}B"
                if is_dir:
                    meta = "dir"
            except Exception:
                meta = "dir" if is_dir else ""

            yield Completion(
                completion,
                start_position=-len(prefix),
                display=name + ("/" if is_dir else ""),
                display_meta=meta,
            )
