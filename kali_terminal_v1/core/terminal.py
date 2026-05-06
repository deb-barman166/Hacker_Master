"""
core/terminal.py — Kali Terminal v1.0 — Central Engine

This is the heart of the terminal. Responsibilities:
  • Boot: load config, apply theme, print banner
  • REPL: read → expand aliases → resolve → dispatch → loop
  • Alias expansion
  • Export / unset / source handlers
  • Key bindings (Ctrl+C, Ctrl+D, Ctrl+L, Ctrl+Z)
  • Session state management (cwd, history, aliases, bookmarks, prefs)
  • Plugin loading
"""

import os
import sys
import signal

from prompt_toolkit           import PromptSession
from prompt_toolkit.history   import FileHistory, InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from ui.banner     import print_banner
from ui.prompt     import build_prompt, get_style
from ui.theme      import Colors, apply_theme

from core.completer import KaliCompleter
from core.executor  import execute

from commands.builtins import BUILTINS
from commands.network  import NETWORK_COMMANDS
from commands.crypto   import CRYPTO_COMMANDS
from commands.ai       import AI_COMMANDS

from utils.config import (
    load_theme, load_aliases, load_bookmarks, load_prefs, HIST_FILE
)

from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters     import Condition

C = Colors

# ── Merge all command tables ───────────────────────────────────────────────────
ALL_COMMANDS: dict = {}
ALL_COMMANDS.update(BUILTINS)
ALL_COMMANDS.update(NETWORK_COMMANDS)
ALL_COMMANDS.update(CRYPTO_COMMANDS)
ALL_COMMANDS.update(AI_COMMANDS)


class KaliTerminal:
    """
    Top-level terminal object. One instance per session.

    State:
      cwd          — current working directory
      prev_dir     — for `cd -`
      history      — list of executed commands
      last_exit    — last command's exit code (for prompt dot)
      env_vars     — user-exported variables
      aliases      — loaded+user-defined aliases
      bookmarks    — named directory shortcuts
      prefs        — terminal preferences
      running      — REPL loop flag
      theme        — active theme name
    """

    def __init__(self):
        # ── Load persistent config ─────────────────────────────────────────────
        theme_name = load_theme()
        apply_theme(theme_name)

        aliases   = load_aliases()
        bookmarks = load_bookmarks()
        prefs     = load_prefs()

        # ── Session state ──────────────────────────────────────────────────────
        self.state: dict = {
            "cwd":       os.getcwd(),
            "prev_dir":  os.getcwd(),
            "history":   [],
            "last_exit": 0,
            "env_vars":  {},
            "aliases":   aliases,
            "bookmarks": bookmarks,
            "prefs":     prefs,
            "running":   True,
            "theme":     theme_name,
        }

        # ── History file ───────────────────────────────────────────────────────
        try:
            pt_history = FileHistory(str(HIST_FILE))
        except Exception:
            pt_history = InMemoryHistory()

        # ── Completer ──────────────────────────────────────────────────────────
        completer = KaliCompleter(
            cwd_getter=lambda: self.state["cwd"],
            state_getter=lambda: self.state,
        )

        # ── Key bindings ───────────────────────────────────────────────────────
        kb = self._build_keybindings()

        # ── Prompt session ─────────────────────────────────────────────────────
        self.session = PromptSession(
            history             = pt_history,
            completer           = completer,
            auto_suggest        = AutoSuggestFromHistory(),
            style               = get_style(),
            key_bindings        = kb,
            mouse_support       = prefs.get("mouse_support", False),
            complete_while_typing = prefs.get("autocomplete", True),
            vi_mode             = prefs.get("vi_mode", False),
        )

    # ── Key Bindings ────────────────────────────────────────────────────────────

    def _build_keybindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("c-l")
        def _clear(event):
            os.system("clear")

        @kb.add("c-d")
        def _exit(event):
            self.state["running"] = False
            event.app.exit()

        @kb.add("f1")
        def _help(event):
            """F1 = quick help"""
            print()
            from commands.builtins import cmd_help
            cmd_help([], self.state)

        return kb

    # ── Boot ────────────────────────────────────────────────────────────────────

    def run(self):
        """Entry point: print banner then enter the REPL."""
        signal.signal(signal.SIGINT, lambda s, f: None)

        prefs = self.state["prefs"]
        animated = prefs.get("boot_animation", True)
        print_banner(animated=animated)

        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self._repl()

    # ── REPL ────────────────────────────────────────────────────────────────────

    def _repl(self):
        """Read → Expand → Dispatch → Loop."""
        while self.state["running"]:
            # Refresh style in case theme changed
            try:
                style = get_style()
            except Exception:
                style = None

            try:
                raw = self.session.prompt(
                    lambda: build_prompt(
                        self.state["cwd"],
                        self.state["last_exit"],
                        show_time = self.state["prefs"].get("show_time_in_prompt", False),
                        show_git  = self.state["prefs"].get("show_git_branch", True),
                    ),
                    style = style,
                )
            except KeyboardInterrupt:
                print()
                self.state["last_exit"] = 130
                continue
            except EOFError:
                print(f"\n{C.paint('Goodbye! Stay elite. 🔴', C.RED, bold=True)}\n")
                break

            raw = raw.strip()
            if not raw:
                continue

            # Record in history
            hist = self.state["history"]
            if not hist or hist[-1] != raw:
                hist.append(raw)

            # Expand aliases
            expanded = self._expand_aliases(raw)

            # Dispatch
            self.state["last_exit"] = self._dispatch(expanded)

    # ── Alias expansion ─────────────────────────────────────────────────────────

    def _expand_aliases(self, raw: str) -> str:
        """Expand an alias if the first word matches."""
        try:
            import shlex
            parts = shlex.split(raw)
        except ValueError:
            parts = raw.split()

        if not parts:
            return raw

        aliases = self.state.get("aliases", {})
        cmd = parts[0]
        if cmd in aliases:
            alias_cmd = aliases[cmd]
            if parts[1:]:
                return alias_cmd + " " + " ".join(parts[1:])
            return alias_cmd

        return raw

    # ── Dispatch ────────────────────────────────────────────────────────────────

    def _dispatch(self, raw: str) -> int:
        """Route command to the appropriate handler."""
        try:
            import shlex
            parts = shlex.split(raw)
        except ValueError:
            parts = raw.split()

        if not parts:
            return 0

        cmd  = parts[0]
        args = parts[1:]

        # ── exit / quit ────────────────────────────────────────────────────────
        if cmd in ("exit", "quit"):
            code = 0
            if args:
                try:
                    code = int(args[0])
                except ValueError:
                    pass
            print(f"\n{C.paint('Goodbye! Stay elite. 🔴', C.RED, bold=True)}\n")
            self.state["running"] = False
            return code

        # ── export ────────────────────────────────────────────────────────────
        if cmd == "export":
            return self._handle_export(args)

        # ── unset ─────────────────────────────────────────────────────────────
        if cmd == "unset":
            for var in args:
                os.environ.pop(var, None)
                self.state["env_vars"].pop(var, None)
            return 0

        # ── source / . ────────────────────────────────────────────────────────
        if cmd in ("source", "."):
            return self._handle_source(args)

        # ── Built-in commands (builtins + network + crypto + AI) ──────────────
        if cmd in ALL_COMMANDS:
            try:
                return ALL_COMMANDS[cmd](args, self.state)
            except KeyboardInterrupt:
                print()
                return 130
            except Exception as e:
                print(C.error(f"Command '{cmd}' error: {e}"))
                return 1

        # ── System commands ────────────────────────────────────────────────────
        result = execute(raw, cwd=self.state["cwd"])
        return result.exit_code

    # ── export handler ──────────────────────────────────────────────────────────

    def _handle_export(self, args: list) -> int:
        if not args:
            for key, val in sorted(os.environ.items()):
                print(f"{C.CYAN}export {key}{C.RESET}={C.GREEN}{val!r}{C.RESET}")
            return 0

        for arg in args:
            if "=" in arg:
                var, _, val = arg.partition("=")
                val = os.path.expandvars(val).strip('"').strip("'")
                os.environ[var] = val
                self.state["env_vars"][var] = val
            else:
                if arg in self.state["env_vars"]:
                    os.environ[arg] = self.state["env_vars"][arg]
                else:
                    print(C.warn(f"export: '{arg}' not defined"))
        return 0

    # ── source handler ──────────────────────────────────────────────────────────

    def _handle_source(self, args: list) -> int:
        if not args:
            print(C.error("source: filename required"))
            return 1

        script_path = os.path.expanduser(args[0])
        if not os.path.isabs(script_path):
            script_path = os.path.join(self.state["cwd"], script_path)

        try:
            with open(script_path) as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(C.error(f"source: {args[0]}: No such file"))
            return 1
        except PermissionError:
            print(C.error(f"source: {args[0]}: Permission denied"))
            return 1

        last_code = 0
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            expanded = self._expand_aliases(line)
            last_code = self._dispatch(expanded)

        return last_code
