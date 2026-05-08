"""
ui/theme.py — Dynamic theme loader and color utilities (v2.0 Masterpiece).

Applies the active theme's colors to the Colors class, and provides
prompt_toolkit Style objects based on the current theme.
"""

from prompt_toolkit.styles import Style
from ui.themes import THEMES

# ── Default fallback (Kali) ──────────────────────────────────────────────
_current_theme = "kali"


def set_theme(name: str):
    """Switch the active theme, updating Colors class attributes."""
    global _current_theme
    if name not in THEMES:
        raise ValueError(f"Unknown theme: {name}")
    _current_theme = name
    colors = THEMES[name]["colors"]
    for attr, value in colors.items():
        setattr(Colors, attr, value)
    # Semantic aliases
    Colors.ERROR = Colors.RED
    Colors.SUCCESS = Colors.GREEN
    Colors.INFO = Colors.BLUE
    Colors.WARNING = Colors.YELLOW
    Colors.CMD = Colors.CYAN
    Colors.PATH = Colors.GREEN
    Colors.HOST = Colors.BLUE
    Colors.USER = Colors.RED


def get_prompt_style(theme_name: str = None) -> Style:
    """Return prompt_toolkit Style for the given theme."""
    name = theme_name or _current_theme
    if name not in THEMES:
        name = "kali"
    return Style.from_dict(THEMES[name]["prompt_style"])


def get_current_theme() -> str:
    """Get the current theme name."""
    return _current_theme


class Colors:
    """ANSI escape codes — dynamically updated by theme."""
    # Defaults (Kali theme) — overridden by set_theme()
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"
    REVERSE = "\033[7m"

    # Basic colors
    BLACK = "\033[30m"
    RED = "\033[38;5;196m"
    GREEN = "\033[38;5;84m"
    YELLOW = "\033[38;5;220m"
    BLUE = "\033[38;5;39m"
    MAGENTA = "\033[38;5;207m"
    CYAN = "\033[38;5;51m"
    WHITE = "\033[97m"
    GRAY = "\033[38;5;244m"

    # Extended colors
    ORANGE = "\033[38;5;208m"
    PURPLE = "\033[38;5;141m"
    PINK = "\033[38;5;205m"
    LIME = "\033[38;5;118m"
    TEAL = "\033[38;5;43m"
    NAVY = "\033[38;5;19m"
    MAROON = "\033[38;5;124m"
    OLIVE = "\033[38;5;142m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Semantic
    ERROR = RED
    SUCCESS = GREEN
    INFO = BLUE
    WARNING = YELLOW
    CMD = CYAN
    PATH = GREEN
    HOST = BLUE
    USER = RED

    @staticmethod
    def paint(text: str, color: str, bold: bool = False) -> str:
        """Wrap text with color + optional bold, always reset after."""
        b = Colors.BOLD if bold else ""
        return f"{b}{color}{text}{Colors.RESET}"

    @staticmethod
    def error(text: str) -> str:
        return Colors.paint(f"[x] {text}", Colors.RED, bold=True)

    @staticmethod
    def success(text: str) -> str:
        return Colors.paint(f"[+] {text}", Colors.GREEN, bold=True)

    @staticmethod
    def info(text: str) -> str:
        return Colors.paint(f"[*] {text}", Colors.BLUE)

    @staticmethod
    def warn(text: str) -> str:
        return Colors.paint(f"[!] {text}", Colors.YELLOW, bold=True)

    @staticmethod
    def header(text: str) -> str:
        """Render a section header."""
        return f"\n{Colors.BOLD}{Colors.BLUE}  >> {text}{Colors.RESET}\n"

    @staticmethod
    def box(text_lines: list, title: str = None, color_attr="BLUE") -> str:
        """Render text inside a bordered box."""
        c = getattr(Colors, color_attr, Colors.BLUE)
        inner_width = max(len(line) for line in text_lines) if text_lines else 20
        if title:
            inner_width = max(inner_width, len(title) + 4)
        total_width = inner_width + 4

        lines = []
        lines.append(f"{c}{'═' * total_width}{Colors.RESET}")
        if title:
            pad = total_width - len(title) - 4
            lines.append(f"{c}║{Colors.RESET} {Colors.BOLD}{Colors.WHITE}{title}{Colors.RESET}{' ' * pad}{c}║{Colors.RESET}")
            lines.append(f"{c}║{Colors.RESET}{'─' * (total_width - 2)}{c}║{Colors.RESET}")
        for line in text_lines:
            pad = inner_width - len(line)
            lines.append(f"{c}║{Colors.RESET} {Colors.WHITE}{line}{Colors.RESET}{' ' * pad}{c}║{Colors.RESET}")
        lines.append(f"{c}{'═' * total_width}{Colors.RESET}")
        return "\n".join(lines)

    @staticmethod
    def rainbow(text: str) -> str:
        """Apply rainbow coloring to text."""
        colors = [Colors.RED, Colors.YELLOW, Colors.GREEN, Colors.CYAN, Colors.BLUE, Colors.MAGENTA]
        result = ""
        for i, char in enumerate(text):
            if char.isalnum():
                result += f"{colors[i % len(colors)]}{char}{Colors.RESET}"
            else:
                result += char
        return result

    @staticmethod
    def gradient(text: str, start_color: str, end_color: str) -> str:
        """Apply gradient coloring to text."""
        import re
        chars = [c for c in text if c.isalnum()]
        if not chars:
            return text

        result = []
        idx = 0
        for char in text:
            if char.isalnum():
                # Calculate color based on position
                pct = idx / max(1, len(chars) - 1)
                # This is a simplified gradient - in production you'd parse ANSI codes properly
                result.append(f"{start_color}{char}{Colors.RESET}")
                idx += 1
            else:
                result.append(char)
        return "".join(result)


# Initialize with default theme
set_theme("kali")