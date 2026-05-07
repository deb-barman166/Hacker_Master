"""
ui/prompt.py — Dynamic prompt builder for KaliTerminal v2.

Renders: user@host:path [git] [venv] [AI] [exit_code] ❯
All segments are theme-aware via prompt_toolkit FormattedText.
"""

import os
import subprocess
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from ui.theme import get_prompt_style, get_theme
from ui.themes import THEMES


def _get_git_branch(cwd: str) -> str:
    """Return current git branch or '' if not in a repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd, capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            # Check dirty
            dirty = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=cwd, capture_output=True, text=True, timeout=2
            )
            suffix = "*" if dirty.stdout.strip() else ""
            return f"{branch}{suffix}"
    except Exception:
        pass
    return ""


def _get_venv() -> str:
    """Return active venv name or ''."""
    venv = os.environ.get("VIRTUAL_ENV", "")
    if venv:
        return os.path.basename(venv)
    conda = os.environ.get("CONDA_DEFAULT_ENV", "")
    if conda and conda != "base":
        return f"conda:{conda}"
    return ""


def _shorten_path(cwd: str, max_len: int = 35) -> str:
    """Shorten path for display: ~/projects/foo/bar/baz → ~/…/bar/baz."""
    home = os.path.expanduser("~")
    if cwd.startswith(home):
        cwd = "~" + cwd[len(home):]
    if len(cwd) <= max_len:
        return cwd
    parts = cwd.split(os.sep)
    while len("/".join(parts)) > max_len and len(parts) > 3:
        parts.pop(1)
        parts[1] = "…"
    return "/".join(parts)


def build_prompt(
    cwd: str,
    last_exit: int = 0,
    ai_enabled: bool = False,
    ai_mode: str = "off",
    vi_mode: str = "insert",
    show_time: bool = False,
) -> FormattedText:
    """
    Build the full prompt as FormattedText for prompt_toolkit.

    Format:
      [time] user@host:path [git] [venv] [AI] ❯
    """
    fragments = []

    # ── Optional timestamp ────────────────────────────────────────────────
    if show_time:
        import time
        ts = time.strftime("%H:%M:%S")
        fragments += [
            ("class:prompt.sep", "["),
            ("class:prompt.git", ts),
            ("class:prompt.sep", "] "),
        ]

    # ── user@host ─────────────────────────────────────────────────────────
    user = os.environ.get("USER", os.environ.get("LOGNAME", "root"))
    host = os.uname().nodename if hasattr(os, "uname") else "kali"
    fragments += [
        ("class:prompt.user",   user),
        ("class:prompt.at",     "@"),
        ("class:prompt.host",   host),
        ("class:prompt.sep",    ":"),
    ]

    # ── path ──────────────────────────────────────────────────────────────
    fragments.append(("class:prompt.path", _shorten_path(cwd)))

    # ── git branch ────────────────────────────────────────────────────────
    branch = _get_git_branch(cwd)
    if branch:
        dirty = branch.endswith("*")
        color = "class:prompt.git"
        fragments += [
            ("class:prompt.sep", " ("),
            (color, f" {branch}"),
            ("class:prompt.sep", ")"),
        ]

    # ── venv ──────────────────────────────────────────────────────────────
    venv = _get_venv()
    if venv:
        fragments += [
            ("class:prompt.sep", " ["),
            ("class:prompt.git", f"env:{venv}"),
            ("class:prompt.sep", "]"),
        ]

    # ── AI mode indicator ─────────────────────────────────────────────────
    if ai_enabled:
        mode_label = {"local": "🤖LOCAL", "cloud": "🤖CLOUD"}.get(ai_mode, "🤖AI")
        fragments += [
            ("class:prompt.sep", " "),
            ("class:prompt.ai",  f"[{mode_label}]"),
        ]

    # ── Vi mode ───────────────────────────────────────────────────────────
    if vi_mode == "command":
        fragments += [(" class:prompt.sep", " "), ("class:prompt.ai", "[N]")]

    # ── Exit code ─────────────────────────────────────────────────────────
    if last_exit != 0:
        fragments += [
            ("class:prompt.sep",   " "),
            ("class:prompt.arrow", f"[{last_exit}]"),
        ]

    # ── Arrow ─────────────────────────────────────────────────────────────
    fragments += [
        ("class:prompt.sep",    "\n"),
        ("class:prompt.arrow",  "❯"),
        ("class:prompt.dollar", " "),
    ]

    return FormattedText(fragments)


def get_style() -> Style:
    return get_prompt_style()
