"""
ui/theme.py — Multi-Theme Engine for Kali Terminal v1.0

Themes:
  kali    — Classic Kali: black + electric blue + blood red  (default)
  dracula — Dracula: purple + pink + dark bg
  matrix  — Matrix: deep green on black, like the movie
  ocean   — Ocean: teal + aqua + dark blue
  blood   — Blood: deep red/crimson, aggressive dark hacker
  nord    — Nord: cool blues and nordic frost

Each theme provides: ANSI color codes + prompt_toolkit Style object
"""

from prompt_toolkit.styles import Style


# ══════════════════════════════════════════════════════════════════════
#  Base Colors class — ANSI codes
# ══════════════════════════════════════════════════════════════════════

class Colors:
    """ANSI escape codes, themeable via set_theme()."""

    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    ITALIC  = "\033[3m"
    UNDER   = "\033[4m"
    BLINK   = "\033[5m"
    REVERSE = "\033[7m"

    # ── Fixed colors (never change with theme) ─────────────────────
    TRUE_RED    = "\033[38;5;196m"
    TRUE_GREEN  = "\033[38;5;46m"
    TRUE_BLUE   = "\033[38;5;27m"
    TRUE_YELLOW = "\033[38;5;226m"
    TRUE_WHITE  = "\033[97m"
    TRUE_GRAY   = "\033[38;5;244m"
    TRUE_BLACK  = "\033[30m"

    # ── Theme-variable colors (set by set_theme()) ─────────────────
    RED     = "\033[38;5;196m"
    BLUE    = "\033[38;5;39m"
    GREEN   = "\033[38;5;84m"
    CYAN    = "\033[38;5;51m"
    YELLOW  = "\033[38;5;220m"
    WHITE   = "\033[97m"
    GRAY    = "\033[38;5;244m"
    MAGENTA = "\033[38;5;207m"
    ORANGE  = "\033[38;5;208m"
    PURPLE  = "\033[38;5;135m"

    # ── Backgrounds ───────────────────────────────────────────────
    BG_BLACK  = "\033[40m"
    BG_RED    = "\033[41m"
    BG_BLUE   = "\033[44m"
    BG_DARK   = "\033[48;5;235m"

    # ── Semantic aliases ──────────────────────────────────────────
    ERROR   = "\033[38;5;196m"
    SUCCESS = "\033[38;5;84m"
    INFO    = "\033[38;5;39m"
    WARNING = "\033[38;5;220m"
    CMD     = "\033[38;5;51m"
    PATH    = "\033[38;5;84m"
    HOST    = "\033[38;5;39m"
    USER    = "\033[38;5;196m"
    ACCENT  = "\033[38;5;207m"

    @staticmethod
    def paint(text: str, color: str, bold: bool = False,
              underline: bool = False) -> str:
        mods = ""
        if bold:      mods += Colors.BOLD
        if underline: mods += Colors.UNDER
        return f"{mods}{color}{text}{Colors.RESET}"

    @staticmethod
    def gradient(text: str, colors: list) -> str:
        """Apply a gradient of colors across characters."""
        if not colors:
            return text
        result = ""
        for i, ch in enumerate(text):
            color = colors[i % len(colors)]
            result += f"{color}{ch}"
        return result + Colors.RESET

    @staticmethod
    def error(text: str) -> str:
        return Colors.paint(f"[✘] {text}", Colors.ERROR, bold=True)

    @staticmethod
    def success(text: str) -> str:
        return Colors.paint(f"[✔] {text}", Colors.SUCCESS, bold=True)

    @staticmethod
    def info(text: str) -> str:
        return Colors.paint(f"[ℹ] {text}", Colors.INFO)

    @staticmethod
    def warn(text: str) -> str:
        return Colors.paint(f"[⚠] {text}", Colors.WARNING, bold=True)

    @staticmethod
    def header(text: str, width: int = 60) -> str:
        line = "═" * width
        return (
            f"\n{Colors.BLUE}{line}{Colors.RESET}\n"
            f"  {Colors.BOLD}{Colors.WHITE}{text}{Colors.RESET}\n"
            f"{Colors.BLUE}{line}{Colors.RESET}"
        )

    @staticmethod
    def box(lines: list, title: str = "", width: int = 56) -> str:
        """Render a box with optional title."""
        C = Colors
        out = []
        if title:
            title_str = f" {title} "
            left = (width - len(title_str)) // 2
            right = width - len(title_str) - left
            out.append(f"{C.BLUE}╔{'═'*left}{C.BOLD}{C.WHITE}{title_str}{C.RESET}{C.BLUE}{'═'*right}╗{C.RESET}")
        else:
            out.append(f"{C.BLUE}╔{'═'*width}╗{C.RESET}")
        for line in lines:
            # Strip ANSI for length calculation
            import re
            ansi_escape = re.compile(r'\033\[[0-9;]*m')
            clean = ansi_escape.sub('', line)
            pad = width - len(clean) - 2
            out.append(f"{C.BLUE}║{C.RESET} {line}{' '*max(0,pad)} {C.BLUE}║{C.RESET}")
        out.append(f"{C.BLUE}╚{'═'*width}╝{C.RESET}")
        return "\n".join(out)


# ══════════════════════════════════════════════════════════════════════
#  Theme Definitions
# ══════════════════════════════════════════════════════════════════════

THEMES = {
    "kali": {
        "name":    "Kali Dark",
        "desc":    "Classic Kali Linux — black, blue, and blood red",
        "emoji":   "🐉",
        "colors": {
            "RED":     "\033[38;5;196m",
            "BLUE":    "\033[38;5;39m",
            "GREEN":   "\033[38;5;84m",
            "CYAN":    "\033[38;5;51m",
            "YELLOW":  "\033[38;5;220m",
            "WHITE":   "\033[97m",
            "GRAY":    "\033[38;5;244m",
            "MAGENTA": "\033[38;5;207m",
            "ORANGE":  "\033[38;5;208m",
            "PURPLE":  "\033[38;5;135m",
            "ACCENT":  "\033[38;5;207m",
        },
        "prompt": {
            "bracket":    "#0088ff bold",
            "user":       "#ff2244 bold",
            "at":         "#ffffff",
            "host":       "#0088ff bold",
            "path":       "#00ff87 bold",
            "prompt-end": "#ff2244 bold",
            "dot-ok":     "#00ff87",
            "dot-err":    "#ff2244",
            "git-branch": "#ffaa00 bold",
            "git-dirty":  "#ff4444",
        },
    },
    "dracula": {
        "name":  "Dracula",
        "desc":  "Dracula theme — purple, pink, and dark elegance",
        "emoji": "🧛",
        "colors": {
            "RED":     "\033[38;5;210m",
            "BLUE":    "\033[38;5;61m",
            "GREEN":   "\033[38;5;84m",
            "CYAN":    "\033[38;5;117m",
            "YELLOW":  "\033[38;5;228m",
            "WHITE":   "\033[38;5;253m",
            "GRAY":    "\033[38;5;61m",
            "MAGENTA": "\033[38;5;212m",
            "ORANGE":  "\033[38;5;215m",
            "PURPLE":  "\033[38;5;141m",
            "ACCENT":  "\033[38;5;212m",
        },
        "prompt": {
            "bracket":    "#6272a4 bold",
            "user":       "#ff79c6 bold",
            "at":         "#f8f8f2",
            "host":       "#bd93f9 bold",
            "path":       "#50fa7b bold",
            "prompt-end": "#ff79c6 bold",
            "dot-ok":     "#50fa7b",
            "dot-err":    "#ff5555",
            "git-branch": "#f1fa8c bold",
            "git-dirty":  "#ff5555",
        },
    },
    "matrix": {
        "name":  "Matrix",
        "desc":  "You take the green pill. You see how deep the rabbit hole goes.",
        "emoji": "💊",
        "colors": {
            "RED":     "\033[38;5;46m",
            "BLUE":    "\033[38;5;34m",
            "GREEN":   "\033[38;5;46m",
            "CYAN":    "\033[38;5;40m",
            "YELLOW":  "\033[38;5;82m",
            "WHITE":   "\033[38;5;46m",
            "GRAY":    "\033[38;5;22m",
            "MAGENTA": "\033[38;5;40m",
            "ORANGE":  "\033[38;5;76m",
            "PURPLE":  "\033[38;5;34m",
            "ACCENT":  "\033[38;5;46m",
        },
        "prompt": {
            "bracket":    "#00aa00 bold",
            "user":       "#00ff00 bold",
            "at":         "#00cc00",
            "host":       "#00dd00 bold",
            "path":       "#00ff00 bold",
            "prompt-end": "#00ff00 bold",
            "dot-ok":     "#00ff00",
            "dot-err":    "#005500",
            "git-branch": "#00cc00 bold",
            "git-dirty":  "#007700",
        },
    },
    "ocean": {
        "name":  "Ocean Depth",
        "desc":  "Deep ocean — teal, aqua, and dark navy",
        "emoji": "🌊",
        "colors": {
            "RED":     "\033[38;5;203m",
            "BLUE":    "\033[38;5;45m",
            "GREEN":   "\033[38;5;86m",
            "CYAN":    "\033[38;5;87m",
            "YELLOW":  "\033[38;5;227m",
            "WHITE":   "\033[38;5;189m",
            "GRAY":    "\033[38;5;67m",
            "MAGENTA": "\033[38;5;123m",
            "ORANGE":  "\033[38;5;215m",
            "PURPLE":  "\033[38;5;75m",
            "ACCENT":  "\033[38;5;87m",
        },
        "prompt": {
            "bracket":    "#0087af bold",
            "user":       "#00d7af bold",
            "at":         "#afd7ff",
            "host":       "#00afff bold",
            "path":       "#87ffff bold",
            "prompt-end": "#00d7af bold",
            "dot-ok":     "#87ffaf",
            "dot-err":    "#ff5f5f",
            "git-branch": "#ffd700 bold",
            "git-dirty":  "#ff8700",
        },
    },
    "blood": {
        "name":  "Blood Moon",
        "desc":  "Aggressive crimson — for elite hackers only",
        "emoji": "🩸",
        "colors": {
            "RED":     "\033[38;5;160m",
            "BLUE":    "\033[38;5;124m",
            "GREEN":   "\033[38;5;130m",
            "CYAN":    "\033[38;5;166m",
            "YELLOW":  "\033[38;5;214m",
            "WHITE":   "\033[38;5;252m",
            "GRAY":    "\033[38;5;238m",
            "MAGENTA": "\033[38;5;196m",
            "ORANGE":  "\033[38;5;208m",
            "PURPLE":  "\033[38;5;88m",
            "ACCENT":  "\033[38;5;196m",
        },
        "prompt": {
            "bracket":    "#870000 bold",
            "user":       "#ff0000 bold",
            "at":         "#ffafaf",
            "host":       "#af0000 bold",
            "path":       "#ff5f00 bold",
            "prompt-end": "#ff0000 bold",
            "dot-ok":     "#af5f00",
            "dot-err":    "#ff0000",
            "git-branch": "#ff8700 bold",
            "git-dirty":  "#ff0000",
        },
    },
}


# ══════════════════════════════════════════════════════════════════════
#  Active Theme State
# ══════════════════════════════════════════════════════════════════════

_active_theme = "kali"


def get_active_theme() -> str:
    return _active_theme


def get_theme_names() -> list:
    return list(THEMES.keys())


def apply_theme(theme_name: str) -> bool:
    """Apply a theme by name. Returns True if successful."""
    global _active_theme
    if theme_name not in THEMES:
        return False

    theme = THEMES[theme_name]
    _active_theme = theme_name

    # Apply to Colors class
    for attr, value in theme["colors"].items():
        setattr(Colors, attr, value)

    # Update semantic aliases
    Colors.ERROR   = Colors.RED
    Colors.SUCCESS = Colors.GREEN
    Colors.INFO    = Colors.BLUE
    Colors.WARNING = Colors.YELLOW
    Colors.CMD     = Colors.CYAN
    Colors.PATH    = Colors.GREEN
    Colors.HOST    = Colors.BLUE
    Colors.USER    = Colors.RED
    Colors.ACCENT  = theme["colors"].get("ACCENT", Colors.MAGENTA)

    return True


def get_prompt_style(theme_name: str = None) -> Style:
    """Return prompt_toolkit Style for the current/given theme."""
    name = theme_name or _active_theme
    theme = THEMES.get(name, THEMES["kali"])
    return Style.from_dict(theme["prompt"])


# Apply default theme on import
apply_theme("kali")
