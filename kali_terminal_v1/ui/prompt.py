"""
ui/prompt.py — Git-Aware Two-Line Kali Prompt

Produces:
  ┌──(root㉿kali)-[~/path] ● [main*] ⏱ 12:34:56
  └─#

Git integration:
  • Shows current branch name
  • Dirty indicator (*) when uncommitted changes
  • Ahead/behind count vs remote

Time display: optional, configurable in prefs.
"""

import os
import socket
import subprocess
import datetime
from functools import lru_cache

from prompt_toolkit.formatted_text import FormattedText
from ui.theme import get_prompt_style


def _shorten_path(path: str, max_len: int = 35) -> str:
    """Shorten long paths for display."""
    home = os.path.expanduser("~")
    if path.startswith(home):
        path = "~" + path[len(home):]

    if len(path) > max_len:
        parts = path.split(os.sep)
        if len(parts) > 3:
            path = "…/" + "/".join(parts[-2:])
        else:
            path = "…" + path[-(max_len - 1):]

    return path


def _get_git_info(cwd: str) -> tuple[str, bool, int, int]:
    """
    Returns (branch_name, is_dirty, ahead_count, behind_count).
    Returns ("", False, 0, 0) if not in a git repo.
    """
    try:
        # Check if inside a git repo
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=cwd, capture_output=True, text=True, timeout=1
        )
        if result.returncode != 0:
            return "", False, 0, 0

        # Get branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd, capture_output=True, text=True, timeout=1
        )
        branch = branch_result.stdout.strip() or "HEAD"

        # Check dirty
        dirty_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd, capture_output=True, text=True, timeout=1
        )
        is_dirty = bool(dirty_result.stdout.strip())

        # Ahead/behind (best effort)
        ahead, behind = 0, 0
        try:
            ab_result = subprocess.run(
                ["git", "rev-list", "--left-right", "--count",
                 f"@{{u}}...HEAD"],
                cwd=cwd, capture_output=True, text=True, timeout=1
            )
            if ab_result.returncode == 0:
                parts = ab_result.stdout.strip().split()
                if len(parts) == 2:
                    behind, ahead = int(parts[0]), int(parts[1])
        except Exception:
            pass

        return branch, is_dirty, ahead, behind

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return "", False, 0, 0


def build_prompt(cwd: str, last_exit_code: int = 0,
                 show_time: bool = False,
                 show_git: bool = True) -> FormattedText:
    """Build the Kali-style two-line prompt with optional git + time."""

    user = os.environ.get("USER", os.environ.get("LOGNAME", "root"))
    host = socket.gethostname().split(".")[0]
    path_str = _shorten_path(cwd)

    is_root = False
    try:
        is_root = os.geteuid() == 0
    except AttributeError:
        pass

    prompt_char = "#" if is_root else "$"
    dot_ok  = last_exit_code == 0
    dot_cls = "class:dot-ok" if dot_ok else "class:dot-err"

    tokens = [
        # Line 1
        ("class:bracket",    "┌──("),
        ("class:user",       user),
        ("class:at",         "㉿"),
        ("class:host",       host),
        ("class:bracket",    ")-["),
        ("class:path",       path_str),
        ("class:bracket",    "]"),
        ("",                 " "),
        (dot_cls,            "●"),
    ]

    # Git branch indicator
    if show_git:
        branch, dirty, ahead, behind = _get_git_info(cwd)
        if branch:
            dirty_marker = "*" if dirty else ""
            git_str = f" [{branch}{dirty_marker}"
            if ahead:
                git_str += f"↑{ahead}"
            if behind:
                git_str += f"↓{behind}"
            git_str += "]"
            tokens.append(("class:git-branch", git_str))

    # Optional time
    if show_time:
        t = datetime.datetime.now().strftime("%H:%M:%S")
        tokens.append(("class:bracket", f" ⏱ {t}"))

    tokens.append(("", "\n"))

    # Line 2
    tokens += [
        ("class:bracket",    "└─"),
        ("class:prompt-end", prompt_char + " "),
    ]

    return FormattedText(tokens)


def get_style():
    """Return the current theme's prompt style."""
    return get_prompt_style()
