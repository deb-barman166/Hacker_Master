"""
ui/themes/__init__.py  Theme definitions for Kali Terminal v2.0 Masterpiece.

Each theme has:
  - name: Display name
  - colors: ANSI color definitions
  - prompt_style: prompt_toolkit style dictionary
"""

THEMES = {
    "kali": {
        "name": "Kali Linux",
        "colors": {
            "RESET": "\033[0m",
            "BOLD": "\033[1m",
            "DIM": "\033[2m",
            "RED": "\033[38;5;196m",
            "BLUE": "\033[38;5;39m",
            "GREEN": "\033[38;5;84m",
            "CYAN": "\033[38;5;51m",
            "YELLOW": "\033[38;5;220m",
            "WHITE": "\033[97m",
            "GRAY": "\033[38;5;244m",
            "MAGENTA": "\033[38;5;207m",
            "ORANGE": "\033[38;5;208m",
        },
        "prompt_style": {
            "": "#ansigreen",
            "username": "#ansicyan bold",
            "at": "#ansired",
            "hostname": "#ansigreen bold",
            "colon": "#ansigreen",
            "directory": "#ansicyan",
            "prompt": "#ansired",
        }
    },

    "hacker": {
        "name": "Hacker Green",
        "colors": {
            "RESET": "\033[0m",
            "BOLD": "\033[1m",
            "DIM": "\033[2m",
            "RED": "\033[38;5;82m",
            "BLUE": "\033[38;5;82m",
            "GREEN": "\033[38;5;82m",
            "CYAN": "\033[38;5;82m",
            "YELLOW": "\033[38;5;82m",
            "WHITE": "\033[38;5;82m",
            "GRAY": "\033[38;5;244m",
            "MAGENTA": "\033[38;5;82m",
            "ORANGE": "\033[38;5;82m",
        },
        "prompt_style": {
            "": "#ansigreen",
            "username": "#ansigreen bold",
            "at": "#ansigreen",
            "hostname": "#ansigreen bold",
            "colon": "#ansigreen",
            "directory": "#ansigreen",
            "prompt": "#ansigreen",
        }
    },

    "matrix": {
        "name": "Matrix",
        "colors": {
            "RESET": "\033[0m",
            "BOLD": "\033[1m",
            "DIM": "\033[2m",
            "RED": "\033[38;5;46m",
            "BLUE": "\033[38;5;46m",
            "GREEN": "\033[38;5;46m",
            "CYAN": "\033[38;5;46m",
            "YELLOW": "\033[38;5;46m",
            "WHITE": "\033[38;5;46m",
            "GRAY": "\033[38;5;238m",
            "MAGENTA": "\033[38;5;46m",
            "ORANGE": "\033[38;5;46m",
        },
        "prompt_style": {
            "": "#ansigreen",
            "username": "#ansigreen bold",
            "at": "#ansigreen",
            "hostname": "#ansigreen bold",
            "colon": "#ansigreen",
            "directory": "#ansigreen",
            "prompt": "#ansigreen",
        }
    },

    "cyberpunk": {
        "name": "Cyberpunk 2077",
        "colors": {
            "RESET": "\033[0m",
            "BOLD": "\033[1m",
            "DIM": "\033[2m",
            "RED": "\033[38;5;196m",
            "BLUE": "\033[38;5;21m",
            "GREEN": "\033[38;5;141m",
            "CYAN": "\033[38;5;51m",
            "YELLOW": "\033[38;5;226m",
            "WHITE": "\033[38;5;231m",
            "GRAY": "\033[38;5;59m",
            "MAGENTA": "\033[38;5;213m",
            "ORANGE": "\033[38;5;214m",
        },
        "prompt_style": {
            "": "#ansimagenta",
            "username": "#ansimagenta bold",
            "at": "#ansiyellow",
            "hostname": "#ansicyan bold",
            "colon": "#ansimagenta",
            "directory": "#ansicyan",
            "prompt": "#ansiyellow",
        }
    },

    "nord": {
        "name": "Nord",
        "colors": {
            "RESET": "\033[0m",
            "BOLD": "\033[1m",
            "DIM": "\033[2m",
            "RED": "\033[38;5;203m",
            "BLUE": "\033[38;5;75m",
            "GREEN": "\033[38;5;72m",
            "CYAN": "\033[38;5;109m",
            "YELLOW": "\033[38;5;180m",
            "WHITE": "\033[38;5;15m",
            "GRAY": "\033[38;5;145m",
            "MAGENTA": "\033[38;5;139m",
            "ORANGE": "\033[38;5;180m",
        },
        "prompt_style": {
            "": "#ansicyan",
            "username": "#ansicyan bold",
            "at": "#ansiyellow",
            "hostname": "#ansicyan bold",
            "colon": "#ansiwhite",
            "directory": "#ansiwhite",
            "prompt": "#ansicyan",
        }
    },

    "dracula": {
        "name": "Dracula",
        "colors": {
            "RESET": "\033[0m",
            "BOLD": "\033[1m",
            "DIM": "\033[2m",
            "RED": "\033[38;5;197m",
            "BLUE": "\033[38;5;117m",
            "GREEN": "\033[38;5;84m",
            "CYAN": "\033[38;5;117m",
            "YELLOW": "\033[38;5;228m",
            "WHITE": "\033[38;5;231m",
            "GRAY": "\033[38;5;145m",
            "MAGENTA": "\033[38;5;213m",
            "ORANGE": "\033[38;5;215m",
        },
        "prompt_style": {
            "": "#ansimagenta",
            "username": "#ansimagenta bold",
            "at": "#ansiwhite",
            "hostname": "#ansicyan bold",
            "colon": "#ansiwhite",
            "directory": "#ansiwhite",
            "prompt": "#ansimagenta",
        }
    },

    "monokai": {
        "name": "Monokai",
        "colors": {
            "RESET": "\033[0m",
            "BOLD": "\033[1m",
            "DIM": "\033[2m",
            "RED": "\033[38;5;197m",
            "BLUE": "\033[38;5;117m",
            "GREEN": "\033[38;5;114m",
            "CYAN": "\033[38;5;110m",
            "YELLOW": "\033[38;5;186m",
            "WHITE": "\033[38;5;231m",
            "GRAY": "\033[38;5;59m",
            "MAGENTA": "\033[38;5;213m",
            "ORANGE": "\033[38;5;208m",
        },
        "prompt_style": {
            "": "#ansiyellow",
            "username": "#ansigreen bold",
            "at": "#ansiwhite",
            "hostname": "#ansicyan bold",
            "colon": "#ansiwhite",
            "directory": "#ansicyan",
            "prompt": "#ansiyellow",
        }
    },
}


THEME_CATEGORIES = {
    "classic": ["kali"],
    "dark": ["nord", "dracula", "monokai"],
    "retro": ["matrix", "hacker"],
    "neon": ["cyberpunk"]
}