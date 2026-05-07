"""
core/terminal.py — Central REPL engine for KaliTerminal v2.

Responsibilities:
  - Boot sequence: banner, load config, build session
  - REPL: read → parse → alias expand → dispatch → loop
  - Routing: builtins → AI commands → system commands
  - State: cwd, history, env_vars, exit codes, AI state
  - Features: pipe support, variable expansion, source, vi-mode
"""

import os
import sys
import signal
import shlex

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory, InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition
from prompt_toolkit.enums import EditingMode

from ui.banner   import print_banner
from ui.prompt   import build_prompt, get_style
from ui.theme    import Colors, set_theme, get_theme
from ui.themes   import THEMES

from core.completer import KaliCompleter, register_commands
from core.executor  import execute

from utils.config import (
    load_prefs, save_prefs, get_pref, set_pref,
    load_aliases, save_aliases,
    load_bookmarks, save_bookmarks,
)

C = Colors
HISTORY_FILE = os.path.expanduser("~/.kali_v2_history")


class KaliTerminal:
    """
    The masterpiece KaliTerminal v2.

    State dict keys:
      cwd         — current working directory
      prev_dir    — previous directory (for cd -)
      history     — list of raw command strings
      last_exit   — last command exit code
      env_vars    — user-defined variables
      running     — REPL loop flag
      ai_enabled  — whether AI features are active
      ai_mode     — "off" | "local" | "cloud"
      vi_mode     — current vi editing mode
    """

    def __init__(self):
        prefs = load_prefs()

        self.state: dict = {
            "cwd":        os.getcwd(),
            "prev_dir":   os.getcwd(),
            "history":    [],
            "last_exit":  0,
            "env_vars":   {},
            "running":    True,
            "ai_enabled": prefs.get("ai_enabled", False),
            "ai_mode":    prefs.get("ai_mode", "off"),
            "vi_mode":    "insert",
            "prefs":      prefs,
            "aliases":    load_aliases(),
            "bookmarks":  load_bookmarks(),
        }

        # ── Apply saved theme ─────────────────────────────────────────────
        try:
            set_theme(prefs.get("theme", "kali"))
        except Exception:
            set_theme("kali")

        # ── Load all commands, register for tab-completion ────────────────
        self._load_commands()

        # ── History (file-backed) ──────────────────────────────────────────
        try:
            pt_history = FileHistory(HISTORY_FILE)
        except Exception:
            pt_history = InMemoryHistory()

        # ── Tab completer ─────────────────────────────────────────────────
        self._completer = KaliCompleter(cwd_getter=lambda: self.state["cwd"])

        # ── Key bindings ───────────────────────────────────────────────────
        kb = self._build_keybindings()

        # ── Editing mode ───────────────────────────────────────────────────
        editing_mode = (EditingMode.VI
                        if prefs.get("vi_mode", False)
                        else EditingMode.EMACS)

        # ── Prompt session ─────────────────────────────────────────────────
        self.session = PromptSession(
            history              = pt_history,
            completer            = self._completer,
            auto_suggest         = AutoSuggestFromHistory(),
            style                = get_style(),
            key_bindings         = kb,
            mouse_support        = prefs.get("mouse_support", False),
            complete_while_typing= prefs.get("complete_while_type", True),
            editing_mode         = editing_mode,
            enable_history_search= True,
        )

    # ── Command registry ───────────────────────────────────────────────────────

    def _load_commands(self):
        """Import all command modules and build the BUILTINS registry."""
        from commands.builtins     import BUILTINS     as _B
        from commands.network      import NET_COMMANDS  as _N
        from commands.crypto       import CRYPTO_CMDS   as _C
        from commands.security     import SEC_CMDS      as _S
        from commands.system       import SYS_CMDS      as _SY
        from commands.productivity import PROD_CMDS     as _P
        from commands.ai_engine    import AI_CMDS       as _A

        self.COMMANDS: dict = {
            **_B, **_N, **_C, **_S, **_SY, **_P, **_A,
        }

        # Extra meta-commands handled in _dispatch but listed for completion
        meta = ["exit", "quit", "export", "unset", "source", "."]
        register_commands(list(self.COMMANDS.keys()) + meta)

    # ── Key bindings ───────────────────────────────────────────────────────────

    def _build_keybindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("c-l")
        def _clear(event):
            os.system("clear")

        @kb.add("c-d")
        def _exit(event):
            self.state["running"] = False
            event.app.exit()

        @kb.add("c-r")
        def _history_search(event):
            """Ctrl+R already handled by prompt_toolkit natively."""
            pass

        return kb

    # ── Boot ───────────────────────────────────────────────────────────────────

    def run(self):
        signal.signal(signal.SIGINT, lambda s, f: None)
        fast = self.state["prefs"].get("fast_banner", False)
        print_banner(fast=fast)
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        if self.state["prefs"].get("welcome_tips", True):
            self._print_tip()

        self._repl()

    def _print_tip(self):
        import random
        tips = [
            f"Type {C.CYAN}help{C.RESET} for all commands, {C.CYAN}cheatsheet{C.RESET} for security quick-ref",
            f"AI is OFF — type {C.CYAN}ai on{C.RESET} and set up your provider to enable it",
            f"Type {C.CYAN}theme-list{C.RESET} to see 7 available themes",
            f"Tab completion works on commands, paths, and sub-arguments",
            f"Use {C.CYAN}Ctrl+R{C.RESET} to search command history interactively",
            f"Type {C.CYAN}ai mode local{C.RESET} to use Ollama (runs 100%% offline)",
            f"Type {C.CYAN}port-scan 192.168.1.1{C.RESET} to scan a host",
        ]
        print(f"  {C.GRAY}💡 {random.choice(tips)}{C.RESET}\n")

    # ── REPL ───────────────────────────────────────────────────────────────────

    def _repl(self):
        while self.state["running"]:
            try:
                raw = self.session.prompt(
                    lambda: build_prompt(
                        self.state["cwd"],
                        self.state["last_exit"],
                        ai_enabled = self.state["ai_enabled"],
                        ai_mode    = self.state["ai_mode"],
                        show_time  = self.state["prefs"].get("show_time_prompt", False),
                    ),
                    style = get_style(),
                )
            except KeyboardInterrupt:
                print()
                self.state["last_exit"] = 130
                continue
            except EOFError:
                print(f"\n{C.paint('[ Goodbye! Stay elite. ]', C.RED, bold=True)}\n")
                break

            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue

            # Record history (no duplicates at head)
            hist = self.state["history"]
            if not hist or hist[-1] != raw:
                hist.append(raw)

            # Dispatch
            exit_code = self._dispatch(raw)
            self.state["last_exit"] = exit_code

    # ── Dispatch ───────────────────────────────────────────────────────────────

    def _dispatch(self, raw: str) -> int:
        """Route command to handler. Returns exit code."""

        # ── Semicolon chains: cmd1; cmd2; cmd3 ───────────────────────────
        if ";" in raw and not _is_quoted(raw, ";"):
            parts = _split_on(raw, ";")
            last  = 0
            for part in parts:
                part = part.strip()
                if part:
                    last = self._dispatch(part)
            return last

        # ── && chains: cmd1 && cmd2 ───────────────────────────────────────
        if "&&" in raw and not _is_quoted(raw, "&&"):
            parts = _split_on(raw, "&&")
            for part in parts:
                part = part.strip()
                if part:
                    rc = self._dispatch(part)
                    if rc != 0:
                        return rc
            return 0

        # ── || chains: cmd1 || cmd2 ───────────────────────────────────────
        if " || " in raw and not _is_quoted(raw, " || "):
            parts = _split_on(raw, " || ")
            for part in parts:
                part = part.strip()
                if part:
                    rc = self._dispatch(part)
                    if rc == 0:
                        return 0
            return 1

        # ── Parse tokens ──────────────────────────────────────────────────
        try:
            parts = shlex.split(raw)
        except ValueError:
            parts = raw.split()

        if not parts:
            return 0

        cmd  = parts[0]
        args = parts[1:]

        # ── Alias expansion ───────────────────────────────────────────────
        aliases = self.state["aliases"]
        if cmd in aliases:
            expanded = aliases[cmd]
            # Prevent recursive alias
            exp_parts = expanded.split()
            if exp_parts and exp_parts[0] != cmd:
                return self._dispatch(expanded + " " + " ".join(args))

        # ── Built-ins (hardcoded) ─────────────────────────────────────────
        if cmd in ("exit", "quit"):
            msg = " ".join(args) if args else "Goodbye! Stay elite."
            print(f"\n{C.paint(f'[ {msg} ]', C.RED, bold=True)}\n")
            self.state["running"] = False
            return 0

        if cmd == "export":
            return self._handle_export(args)

        if cmd == "unset":
            for var in args:
                os.environ.pop(var, None)
                self.state["env_vars"].pop(var, None)
            return 0

        if cmd in ("source", "."):
            return self._handle_source(args)

        if cmd == "set":
            return self._handle_set(args)

        # ── Registered commands ───────────────────────────────────────────
        if cmd in self.COMMANDS:
            try:
                return self.COMMANDS[cmd](args, self.state)
            except KeyboardInterrupt:
                print(f"\n{C.warn('Interrupted.')}")
                return 130
            except Exception as e:
                print(C.error(f"Command '{cmd}' crashed: {e}"))
                return 1

        # ── System command ────────────────────────────────────────────────
        result = execute(raw, cwd=self.state["cwd"])
        return result.exit_code

    # ── Built-in handlers ──────────────────────────────────────────────────────

    def _handle_export(self, args: list) -> int:
        if not args:
            for k, v in sorted(os.environ.items()):
                print(f"{C.CYAN}export {k}{C.RESET}={C.GREEN}{v!r}{C.RESET}")
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

    def _handle_source(self, args: list) -> int:
        if not args:
            print(C.error("source: filename required"))
            return 1
        path = os.path.expanduser(args[0])
        if not os.path.isabs(path):
            path = os.path.join(self.state["cwd"], path)
        try:
            with open(path) as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(C.error(f"source: {args[0]}: No such file"))
            return 1
        except PermissionError:
            print(C.error(f"source: {args[0]}: Permission denied"))
            return 1
        last = 0
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                last = self._dispatch(line)
        return last

    def _handle_set(self, args: list) -> int:
        """set <key> <value> — update terminal preferences."""
        if not args:
            prefs = self.state["prefs"]
            print(C.header("Terminal Settings"))
            for k, v in sorted(prefs.items()):
                if not k.endswith("_key") and k != "prefs":
                    print(f"  {C.CYAN}{k:<28}{C.RESET} = {C.GREEN}{v}{C.RESET}")
            return 0

        if len(args) < 2:
            print(C.error("Usage: set <key> <value>"))
            return 1

        key, val_str = args[0], " ".join(args[1:])
        # Type coerce
        if val_str.lower() in ("true", "yes", "on", "1"):
            val: object = True
        elif val_str.lower() in ("false", "no", "off", "0"):
            val = False
        else:
            try:
                val = int(val_str)
            except ValueError:
                val = val_str

        set_pref(key, val)
        self.state["prefs"][key] = val
        print(C.success(f"set {key} = {val}"))
        return 0


# ── Utilities ──────────────────────────────────────────────────────────────────

def _is_quoted(s: str, char: str) -> bool:
    in_s = in_d = False
    i = 0
    while i < len(s):
        c = s[i]
        if c == "'" and not in_d:
            in_s = not in_s
        elif c == '"' and not in_s:
            in_d = not in_d
        elif s[i:i+len(char)] == char and not in_s and not in_d:
            return False
        i += 1
    return True


def _split_on(s: str, sep: str) -> list:
    """Split string on unquoted separator."""
    parts  = []
    cur    = []
    in_s   = in_d = False
    i      = 0
    while i < len(s):
        c = s[i]
        if c == "'" and not in_d:
            in_s = not in_s
        elif c == '"' and not in_s:
            in_d = not in_d
        elif s[i:i+len(sep)] == sep and not in_s and not in_d:
            parts.append("".join(cur))
            cur = []
            i  += len(sep)
            continue
        cur.append(c)
        i += 1
    parts.append("".join(cur))
    return parts
