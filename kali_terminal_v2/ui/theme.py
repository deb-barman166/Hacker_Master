"""
ui/theme.py — Dynamic theme engine for KaliTerminal v2.

Provides:
  - Colors class with dynamic ANSI attributes
  - set_theme() / get_theme()
  - prompt_toolkit Style generation
"""

from prompt_toolkit.styles import Style
from ui.themes import THEMES

_current_theme = "kali"


def set_theme(name: str):
    """Switch active theme, updating Colors class attributes."""
    global _current_theme
    if name not in THEMES:
        raise ValueError(f"Unknown theme: '{name}'. Available: {', '.join(THEMES.keys())}")
    _current_theme = name
    colors = THEMES[name]["colors"]
    for attr, value in colors.items():
        setattr(Colors, attr, value)
    # Semantic aliases always in sync
    Colors.ERROR   = Colors.RED
    Colors.SUCCESS = Colors.GREEN
    Colors.INFO    = Colors.BLUE
    Colors.WARNING = Colors.YELLOW
    Colors.CMD     = Colors.CYAN
    Colors.PATH    = Colors.GREEN
    Colors.HOST    = Colors.BLUE
    Colors.USER    = Colors.RED


def get_theme() -> str:
    return _current_theme


def get_prompt_style(theme_name: str = None) -> Style:
    name = theme_name or _current_theme
    if name not in THEMES:
        name = "kali"
    return Style.from_dict(THEMES[name]["prompt_style"])


def get_logo_color() -> str:
    return THEMES.get(_current_theme, THEMES["kali"]).get("logo_color", "\033[38;5;196m")


class Colors:
    """ANSI escape codes — dynamically updated per theme."""
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"
    UNDER   = "\033[4m"
    BLINK   = "\033[5m"
    REVERSE = "\033[7m"

    # Default: Kali theme — overridden by set_theme()
    RED     = "\033[38;5;196m"
    BLUE    = "\033[38;5;39m"
    GREEN   = "\033[38;5;84m"
    CYAN    = "\033[38;5;51m"
    YELLOW  = "\033[38;5;220m"
    WHITE   = "\033[97m"
    GRAY    = "\033[38;5;244m"
    MAGENTA = "\033[38;5;207m"
    ORANGE  = "\033[38;5;208m"
    PURPLE  = "\033[38;5;141m"

    # Background
    BG_BLACK = "\033[40m"
    BG_RED   = "\033[41m"
    BG_BLUE  = "\033[44m"
    BG_GREEN = "\033[42m"

    # Semantic (always mirror theme)
    ERROR   = RED
    SUCCESS = GREEN
    INFO    = BLUE
    WARNING = YELLOW
    CMD     = CYAN
    PATH    = GREEN
    HOST    = BLUE
    USER    = RED

    # ── Helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def paint(text: str, color: str, bold: bool = False) -> str:
        b = Colors.BOLD if bold else ""
        return f"{b}{color}{text}{Colors.RESET}"

    @staticmethod
    def error(text: str) -> str:
        return Colors.paint(f"[✗] {text}", Colors.RED, bold=True)

    @staticmethod
    def success(text: str) -> str:
        return Colors.paint(f"[✔] {text}", Colors.GREEN, bold=True)

    @staticmethod
    def info(text: str) -> str:
        return Colors.paint(f"[*] {text}", Colors.BLUE)

    @staticmethod
    def warn(text: str) -> str:
        return Colors.paint(f"[!] {text}", Colors.YELLOW, bold=True)

    @staticmethod
    def header(text: str, width: int = 60) -> str:
        pad = max(0, width - len(text) - 6)
        return (
            f"\n{Colors.BOLD}{Colors.BLUE}{'━'*3} {text} {'━'*pad}{Colors.RESET}\n"
        )

    @staticmethod
    def box(lines: list, title: str = "", color: str = None) -> str:
        c = color or Colors.BLUE
        inner = max((len(l) for l in lines), default=20)
        if title:
            inner = max(inner, len(title) + 2)
        w = inner + 4
        out = []
        out.append(f"{c}╔{'═'*w}╗{Colors.RESET}")
        if title:
            pad = w - len(title) - 2
            out.append(f"{c}║{Colors.RESET} {Colors.BOLD}{Colors.WHITE}{title}{Colors.RESET}{' '*pad} {c}║{Colors.RESET}")
            out.append(f"{c}╠{'═'*w}╣{Colors.RESET}")
        for line in lines:
            pad = inner - len(line)
            out.append(f"{c}║{Colors.RESET}  {Colors.WHITE}{line}{Colors.RESET}{' '*pad}  {c}║{Colors.RESET}")
        out.append(f"{c}╚{'═'*w}╝{Colors.RESET}")
        return "\n".join(out)

    @staticmethod
    def progress_bar(pct: float, width: int = 30, label: str = "") -> str:
        filled = int(width * pct / 100)
        bar = "█" * filled + "░" * (width - filled)
        color = Colors.GREEN if pct < 60 else Colors.YELLOW if pct < 85 else Colors.RED
        lbl = f" {label}" if label else ""
        return f"{color}{bar}{Colors.RESET} {Colors.BOLD}{pct:.1f}%{Colors.RESET}{lbl}"

    @staticmethod
    def table(headers: list, rows: list, col_color: str = None) -> str:
        c = col_color or Colors.CYAN
        widths = [max(len(str(h)), *(len(str(r[i])) for r in rows), 4)
                  for i, h in enumerate(headers)]
        sep = "─" * (sum(widths) + 3 * len(widths) + 1)
        lines = [f"{Colors.BLUE}{sep}{Colors.RESET}"]
        hdr = "  ".join(f"{Colors.BOLD}{c}{str(h):<{widths[i]}}{Colors.RESET}"
                        for i, h in enumerate(headers))
        lines.append(f"  {hdr}")
        lines.append(f"{Colors.BLUE}{sep}{Colors.RESET}")
        for row in rows:
            cells = "  ".join(f"{Colors.WHITE}{str(row[i]) if i < len(row) else '':<{widths[i]}}{Colors.RESET}"
                               for i in range(len(headers)))
            lines.append(f"  {cells}")
        lines.append(f"{Colors.BLUE}{sep}{Colors.RESET}")
        return "\n".join(lines)


# Boot with default theme
set_theme("kali")
