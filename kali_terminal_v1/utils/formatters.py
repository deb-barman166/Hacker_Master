"""
utils/formatters.py — Rich table and panel formatters for Kali Terminal v1.

Provides consistent, beautiful output rendering for all built-in commands.
"""

import re
import shutil
from ui.theme import Colors

C = Colors


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return re.compile(r'\033\[[0-9;]*m').sub('', text)


def visible_len(text: str) -> int:
    """Length of text ignoring ANSI codes."""
    return len(strip_ansi(text))


def terminal_width() -> int:
    return shutil.get_terminal_size(fallback=(100, 24)).columns


def bar(pct: float, width: int = 20, label: bool = True) -> str:
    """Colored progress bar."""
    pct = max(0.0, min(100.0, pct))
    filled = int(width * pct / 100)
    empty  = width - filled
    if pct < 50:
        color = C.TRUE_GREEN
    elif pct < 75:
        color = C.YELLOW
    elif pct < 90:
        color = C.ORANGE
    else:
        color = C.TRUE_RED
    b = f"{color}{'█' * filled}{'░' * empty}{C.RESET}"
    if label:
        b += f" {color}{pct:5.1f}%{C.RESET}"
    return b


def table(rows: list, headers: list = None, title: str = "",
          col_colors: list = None) -> str:
    """
    Render a styled table.

    rows    — list of row tuples/lists
    headers — optional header row
    title   — optional box title
    """
    if not rows:
        return C.warn("(empty table)")

    all_rows = ([headers] + list(rows)) if headers else list(rows)

    # Calculate column widths
    n_cols = max(len(r) for r in all_rows)
    widths = [0] * n_cols
    for row in all_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], visible_len(str(cell)))

    w = sum(widths) + n_cols * 3 + 1  # borders + padding
    lines = []

    # Title bar
    if title:
        t = f" {title} "
        pad_l = (w - len(t)) // 2
        pad_r = w - len(t) - pad_l
        lines.append(
            f"{C.BLUE}╔{'═'*pad_l}{C.BOLD}{C.WHITE}{t}"
            f"{C.RESET}{C.BLUE}{'═'*pad_r}╗{C.RESET}"
        )
    else:
        lines.append(f"{C.BLUE}╔{'═'*w}╗{C.RESET}")

    def render_row(row, is_header=False):
        parts = []
        for i, cell in enumerate(row):
            cell_str = str(cell)
            clean    = visible_len(cell_str)
            pad      = widths[i] - clean
            if is_header:
                parts.append(f" {C.BOLD}{C.CYAN}{cell_str}{' '*pad}{C.RESET} ")
            elif col_colors and i < len(col_colors):
                parts.append(f" {col_colors[i]}{cell_str}{' '*pad}{C.RESET} ")
            else:
                parts.append(f" {C.WHITE}{cell_str}{' '*pad}{C.RESET} ")
        inner = f"{C.BLUE}│{C.RESET}".join(parts)
        return f"{C.BLUE}║{C.RESET}{inner}{C.BLUE}║{C.RESET}"

    def divider(char="═"):
        segs = [f"{'═'*(widths[i]+2)}" for i in range(n_cols)]
        return f"{C.BLUE}╠{'╪'.join(segs)}╣{C.RESET}"

    if headers:
        lines.append(render_row(headers, is_header=True))
        lines.append(divider())
        for row in rows:
            lines.append(render_row(row))
    else:
        for row in rows:
            lines.append(render_row(row))

    lines.append(f"{C.BLUE}╚{'═'*w}╝{C.RESET}")
    return "\n".join(lines)


def panel(content: str, title: str = "", width: int = None,
          border_color: str = None) -> str:
    """Wrap content in a bordered panel."""
    bc = border_color or C.BLUE
    w  = width or min(terminal_width() - 2, 78)

    lines_out = [f"{bc}╔{'═'*(w-2)}╗{C.RESET}"]
    if title:
        t = f"  {C.BOLD}{C.WHITE}{title}{C.RESET}"
        lines_out.append(f"{bc}║{C.RESET}{t}")
        lines_out.append(f"{bc}╠{'═'*(w-2)}╣{C.RESET}")

    for line in content.splitlines():
        vl  = visible_len(line)
        pad = max(0, w - vl - 4)
        lines_out.append(f"{bc}║{C.RESET}  {line}{' '*pad}  {bc}║{C.RESET}")

    lines_out.append(f"{bc}╚{'═'*(w-2)}╝{C.RESET}")
    return "\n".join(lines_out)


def tree_view(path: str, prefix: str = "", max_depth: int = 3,
              current_depth: int = 0) -> list:
    """
    Return list of colored tree lines for a directory.
    Used by the `tree` builtin command.
    """
    import os
    lines = []
    if current_depth >= max_depth:
        return lines

    try:
        entries = sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError:
        lines.append(f"{prefix}  {C.paint('[Permission Denied]', C.TRUE_RED)}")
        return lines

    total = len(entries)
    for idx, entry in enumerate(entries):
        is_last   = (idx == total - 1)
        connector = "└── " if is_last else "├── "
        ext_prefix = "    " if is_last else "│   "

        if entry.is_dir(follow_symlinks=False):
            name_str = C.paint(entry.name + "/", C.BLUE, bold=True)
        elif entry.is_symlink():
            target = os.readlink(entry.path)
            name_str = f"{C.paint(entry.name, C.CYAN)} → {C.paint(target, C.GRAY)}"
        elif os.access(entry.path, os.X_OK):
            name_str = C.paint(entry.name, C.GREEN, bold=True)
        else:
            ext = os.path.splitext(entry.name)[1].lower()
            if ext in (".py", ".js", ".ts", ".go", ".rs", ".c", ".cpp"):
                name_str = C.paint(entry.name, C.YELLOW)
            elif ext in (".jpg", ".png", ".gif", ".svg", ".webp"):
                name_str = C.paint(entry.name, C.MAGENTA)
            elif ext in (".zip", ".tar", ".gz", ".bz2", ".xz", ".7z"):
                name_str = C.paint(entry.name, C.TRUE_RED)
            elif ext in (".md", ".txt", ".rst", ".log"):
                name_str = C.paint(entry.name, C.WHITE)
            else:
                name_str = C.paint(entry.name, C.GRAY)

        lines.append(f"{C.GRAY}{prefix}{connector}{C.RESET}{name_str}")

        if entry.is_dir(follow_symlinks=False):
            lines.extend(
                tree_view(entry.path, prefix + ext_prefix,
                          max_depth, current_depth + 1)
            )

    return lines
