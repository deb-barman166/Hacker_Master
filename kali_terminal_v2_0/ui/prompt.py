"""
ui/prompt.py  Prompt builder for Kali Terminal v2.0 Masterpiece.
"""

import os
import socket
import re
from pathlib import Path


def build_prompt(cwd: str, last_exit: int = 0, config=None, ai_enabled: bool = False) -> str:
    """
    Build the terminal prompt string.

    Supports multiple styles:
      - minimal: user@host:path$
      - detailed: [user@host path]$
      - powerline: Shows git branch, venv, exit code
      - kali: Full Kali-style prompt
    """

    if config:
        style = config.get("prompt_style", "minimal")
    else:
        style = "minimal"

    user = os.environ.get("USER", "root")
    hostname = socket.gethostname()
    home = os.path.expanduser("~")

    # Shorten path
    if cwd.startswith(home):
        path = "~" + cwd[len(home):]
    else:
        path = cwd
        # Limit path length
        max_len = config.get("prompt_max_path", 40) if config else 40
        if len(path) > max_len:
            parts = path.split(os.sep)
            if len(parts) > 3:
                path = ".../" + "/".join(parts[-2:])

    # Git branch
    git_branch = ""
    try:
        git_dir = Path(cwd)
        while git_dir != git_dir.parent:
            if (git_dir / ".git").exists():
                branch_file = git_dir / ".git" / "HEAD"
                if branch_file.exists():
                    content = branch_file.read_text().strip()
                    if content.startswith("ref: refs/heads/"):
                        git_branch = content.replace("ref: refs/heads/", "")
                break
            git_dir = git_dir.parent
    except:
        pass

    # Virtual environment
    venv = os.environ.get("VIRTUAL_ENV", "")
    if venv:
        venv_name = Path(venv).name
    else:
        venv_name = ""

    # Exit code indicator
    exit_indicator = ""
    if last_exit != 0:
        exit_indicator = " [{}]".format(last_exit)

    # AI indicator
    ai_indicator = ""
    if ai_enabled:
        ai_indicator = " [AI]"

    # Build prompt based on style
    if style == "minimal":
        prompt = "{user}@{hostname}:{path}$ ".format(
            user=user, hostname=hostname, path=path
        )

    elif style == "detailed":
        prompt = "[{user}@{hostname} {path}]# ".format(
            user=user, hostname=hostname, path=path
        )

    elif style == "powerline":
        prompt_parts = ["{user}@{hostname}".format(user=user, hostname=hostname)]
        if git_branch:
            prompt_parts.append("({})".format(git_branch))
        if venv_name:
            prompt_parts.append("[{}]".format(venv_name))
        prompt_parts.append(path)
        prompt = " ".join(prompt_parts) + "$ "

    elif style == "kali":
        # Full Kali-style prompt
        exit_str = " [{}]".format(last_exit) if last_exit != 0 else ""
        git_str = " ({})".format(git_branch) if git_branch else ""
        venv_str = " ({})".format(venv_name) if venv_name else ""
        ai_str = " [AI]" if ai_enabled else ""

        prompt = "\n{ai}{exit} {green}{user}{red}@{green}{hostname}{white}:{green}{path}{yellow}{git}{magenta}{venv}{exit_code}\n{white}${reset} ".format(
            user=user,
            hostname=hostname,
            path=path,
            git=git_str,
            venv=venv_str,
            exit_code=exit_str,
            ai=ai_str,
            green="\033[38;5;84m",
            red="\033[38;5;196m",
            yellow="\033[38;5;220m",
            cyan="\033[38;5;51m",
            white="\033[97m",
            magenta="\033[38;5;207m",
            reset="\033[0m"
        )

    else:
        prompt = "{user}@{hostname}:{path}$ ".format(
            user=user, hostname=hostname, path=path
        )

    return prompt


def get_prompt_style(theme_name: str) -> dict:
    """Return prompt_toolkit style dictionary for the given theme."""
    from ui.themes import THEMES

    if theme_name not in THEMES:
        theme_name = "kali"

    return THEMES[theme_name].get("prompt_style", {})