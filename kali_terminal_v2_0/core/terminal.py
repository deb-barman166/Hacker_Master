"""
core/terminal.py — The central terminal engine (v2.0 Masterpiece).

Responsibilities:
  - Boot sequence (banner, config load, plugin init)
  - REPL loop (read -> parse -> dispatch -> display)
  - Builtin vs system command routing
  - History management with search
  - Session state (cwd, exit codes, vars, git branch)
  - Alias expansion
  - Multi-line command support
  - Plugin lifecycle management
  - AI integration (Ollama + API keys)
"""

import os
import sys
import signal
import time
import threading
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory, FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.key_binding import KeyBindings

from core.config import get_config, HISTORY_FILE
from core.completer import KaliCompleter
from core.executor import execute
from core.plugin_system import PluginManager
from core.session_manager import SessionManager
from commands.builtins import BUILTINS
from commands.aliases import AliasManager, cmd_alias, cmd_unalias, cmd_aliases
from commands.network_tools import (
    cmd_ip_info, cmd_netstat_enhanced, cmd_port_scan, cmd_subnet_calc,
    cmd_dns_lookup, cmd_whois_lookup, cmd_traceroute, cmd_ping_sweep
)
from commands.crypto_tools import (
    cmd_hash, cmd_encode, cmd_decode, cmd_rot13, cmd_caesar,
    cmd_hash_identify, cmd_hash_cracker, cmd_ssl_check
)
from commands.security_tools import (
    cmd_password_gen, cmd_random_uuid, cmd_random_mac, cmd_sanitize,
    cmd_cypher, cmd_decypher, cmd_base64_img
)
from commands.forensics_tools import (
    cmd_hexdump, cmd_strings_extract, cmd_file_analysis, cmd_entropy,
    cmd_xor_data, cmd_binwalk_extract
)
from commands.web_tools import (
    cmd_http_headers, cmd_http_post, cmd_sql_test, cmd_xss_test,
    cmd_dir_scan, cmd_subdomain_enum, cmd_cert_check
)
from commands.ai_commands import (
    cmd_ai_enable, cmd_ai_disable, cmd_ai_config, cmd_ai_chat,
    cmd_ai_explain, cmd_ai_analyze, cmd_ai_help
)
from commands.system_tools import (
    cmd_disk_usage, cmd_proc_monitor, cmd_sysinfo_enhanced
)
from commands.text_tools import (
    cmd_json_format, cmd_json_minify, cmd_yaml_convert, cmd_markdown,
    cmd_ascii_table, cmd_regex_test
)
from commands.productivity import (
    cmd_notes, cmd_todo, cmd_plugins, cmd_save_session, cmd_load_session,
    cmd_lsessions, cmd_calendar, cmd_reminders
)
from ui.banner import print_banner
from ui.prompt import build_prompt, get_prompt_style
from ui.theme import Colors

# ── Register ALL built-in commands into the BUILTINS dispatch table ────────
BUILTINS.update({
    # Aliases
    "alias":           cmd_alias,
    "unalias":         cmd_unalias,
    "aliases":         cmd_aliases,

    # Network
    "ip-info":         cmd_ip_info,
    "netstat-enhanced": cmd_netstat_enhanced,
    "port-scan":       cmd_port_scan,
    "subnet-calc":     cmd_subnet_calc,
    "dns-lookup":      cmd_dns_lookup,
    "whois":           cmd_whois_lookup,
    "traceroute":      cmd_traceroute,
    "ping-sweep":      cmd_ping_sweep,

    # Crypto
    "hash":            cmd_hash,
    "encode":          cmd_encode,
    "decode":          cmd_decode,
    "rot13":           cmd_rot13,
    "caesar":          cmd_caesar,
    "hash-identify":   cmd_hash_identify,
    "hash-crack":      cmd_hash_cracker,
    "ssl-check":       cmd_ssl_check,

    # Security
    "password-gen":    cmd_password_gen,
    "random-uuid":     cmd_random_uuid,
    "random-mac":      cmd_random_mac,
    "sanitize":        cmd_sanitize,
    "cypher":          cmd_cypher,
    "decypher":        cmd_decypher,
    "base64-img":      cmd_base64_img,

    # Forensics
    "hexdump":         cmd_hexdump,
    "strings":         cmd_strings_extract,
    "file-analysis":   cmd_file_analysis,
    "entropy":         cmd_entropy,
    "xor-data":        cmd_xor_data,
    "binwalk":         cmd_binwalk_extract,

    # Web Security
    "http-headers":    cmd_http_headers,
    "http-post":       cmd_http_post,
    "sql-test":        cmd_sql_test,
    "xss-test":        cmd_xss_test,
    "dir-scan":        cmd_dir_scan,
    "subdomain-enum":  cmd_subdomain_enum,
    "cert-check":      cmd_cert_check,

    # AI Commands
    "ai-enable":       cmd_ai_enable,
    "ai-disable":      cmd_ai_disable,
    "ai-config":       cmd_ai_config,
    "ai":              cmd_ai_chat,
    "ai-explain":      cmd_ai_explain,
    "ai-analyze":      cmd_ai_analyze,
    "ai-help":         cmd_ai_help,

    # System
    "disk-usage":      cmd_disk_usage,
    "proc-monitor":    cmd_proc_monitor,
    "sysinfo":         cmd_sysinfo_enhanced,

    # Text
    "json-format":     cmd_json_format,
    "json-minify":     cmd_json_minify,
    "yaml-convert":    cmd_yaml_convert,
    "markdown":        cmd_markdown,
    "ascii-table":     cmd_ascii_table,
    "regex-test":      cmd_regex_test,

    # Productivity
    "notes":           cmd_notes,
    "todo":            cmd_todo,
    "plugins":         cmd_plugins,
    "save-session":   cmd_save_session,
    "load-session":    cmd_load_session,
    "lsessions":       cmd_lsessions,
    "calendar":        cmd_calendar,
    "reminders":       cmd_reminders,
})

C = Colors


class KaliTerminal:
    """
    The top-level terminal object (v2.0 Masterpiece).

    State held here:
      cwd          -- current working directory
      prev_dir     -- last visited dir (for cd -)
      history      -- list of command strings
      last_exit    -- exit code of last command
      env_vars     -- user-set variables (export VAR=val)
      running      -- REPL loop flag
      start_time   -- session start timestamp
      cmd_count    -- total commands executed
      aliases      -- alias manager instance
      plugins      -- plugin manager instance
      sessions     -- session manager instance
      multiline    -- multi-line buffer state
      ai_enabled   -- AI feature toggle
      ai_backend   -- AI backend type (ollama/openai/anthropic/gemini/none)
    """

    def __init__(self, show_banner=True, theme="kali", ai_backend="none",
                 ai_model=None, config_path=None):
        self.show_banner_flag = show_banner
        self.config = get_config(config_path)

        # Apply command line overrides
        if theme:
            self.config.set("theme", theme)
        if ai_backend:
            self.config.set("ai_backend", ai_backend)
        if ai_model:
            self.config.set("ai_model", ai_model)

        self.state: dict = {
            "cwd":        os.getcwd(),
            "prev_dir":   os.getcwd(),
            "history":    [],
            "last_exit":  0,
            "env_vars":   {},
            "running":    True,
            "start_time": time.time(),
            "cmd_count":  0,
            "ai_enabled": ai_backend != "none",
            "ai_backend": self.config.get("ai_backend", "none"),
            "ai_model":   self.config.get("ai_model", ""),
        }

        # ── Alias manager ──────────────────────────────────────────────────
        self.aliases = AliasManager()

        # ── Plugin manager ─────────────────────────────────────────────────
        self.plugins = PluginManager(self)

        # ── Session manager ────────────────────────────────────────────────
        self.sessions = SessionManager(self)

        # ── Multi-line command buffer ──────────────────────────────────────
        self.multiline_buffer: list[str] = []
        self.multiline_mode: bool = False

        # ── File-backed history ────────────────────────────────────────────
        try:
            pt_history = FileHistory(HISTORY_FILE)
        except Exception:
            pt_history = InMemoryHistory()

        # ── Tab completer ──────────────────────────────────────────────────
        completer = KaliCompleter(
            cwd_getter=lambda: self.state["cwd"],
            alias_getter=lambda: list(self.aliases.aliases.keys()),
        )

        # ── Key bindings ──────────────────────────────────────────────────
        kb = self._build_keybindings()

        # ── Prompt style ───────────────────────────────────────────────────
        prompt_style = get_prompt_style(self.config.theme)

        # ── Prompt session ─────────────────────────────────────────────────
        self.session = PromptSession(
            history=pt_history,
            completer=completer,
            auto_suggest=AutoSuggestFromHistory() if self.config.get("auto_suggest") else None,
            style=prompt_style,
            key_bindings=kb,
            mouse_support=self.config.get("mouse_support", False),
            complete_while_typing=self.config.get("complete_while_typing", True),
            multiline=False,
            prompt_continuation="... " if self.config.get("prompt_style") != "powerline" else "...> ",
        )

        # ── Initialize AI ──────────────────────────────────────────────────
        self._init_ai()

    def _init_ai(self):
        """Initialize AI backend based on configuration."""
        if self.state["ai_backend"] != "none":
            try:
                from ai_modules.ai_engine import AIEngine
                self.ai_engine = AIEngine(
                    backend=self.state["ai_backend"],
                    model=self.state.get("ai_model")
                )
                print(C.success(f"AI enabled with {self.state['ai_backend']} backend"))
            except Exception as e:
                print(C.warn(f"AI initialization failed: {e}"))
                self.state["ai_enabled"] = False
        else:
            self.ai_engine = None

    # ── Key Bindings ──────────────────────────────────────────────────────
    def _build_keybindings(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("c-l")          # Ctrl+L = clear screen
        def _clear(event):
            os.system("clear")

        @kb.add("c-d")          # Ctrl+D = exit
        def _exit(event):
            self.state["running"] = False
            event.app.exit()

        @kb.add("c-z")          # Ctrl+Z = undo
        def _undo(event):
            try:
                event.app.current_buffer.undo()
            except Exception:
                pass

        @kb.add("c-r")          # Ctrl+R = reverse search
        def _search(event):
            pass  # prompt_toolkit handles this

        return kb

    # ── Boot ──────────────────────────────────────────────────────────────
    def run(self):
        """Main entry — print banner, load plugins, enter REPL."""
        signal.signal(signal.SIGINT, lambda s, f: None)

        if self.show_banner_flag and self.config.get("show_banner", True):
            print_banner()

        # ── Load plugins ───────────────────────────────────────────────────
        self.plugins.load_all()

        # ── Run startup commands ──────────────────────────────────────────
        for cmd in self.config.get("startup_commands", []):
            self._dispatch(cmd)

        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self._repl()

    # ── REPL ──────────────────────────────────────────────────────────────
    def _repl(self):
        """Read -> Evaluate -> Print -> Loop."""
        while self.state["running"]:
            try:
                prompt_text = build_prompt(
                    self.state["cwd"],
                    self.state["last_exit"],
                    config=self.config,
                    ai_enabled=self.state["ai_enabled"]
                )
                raw = self.session.prompt(
                    prompt_text,
                    style=get_prompt_style(self.config.theme),
                )
            except KeyboardInterrupt:
                print()
                self.state["last_exit"] = 130
                continue
            except EOFError:
                print(f"\n{C.paint('Goodbye! Stay elite.', C.RED, bold=True)}\n")
                break

            raw = raw.strip()

            # ── Multi-line mode (backslash continuation) ───────────────────
            if raw.endswith("\\"):
                self.multiline_buffer.append(raw[:-1])
                self.multiline_mode = True
                continue
            elif self.multiline_mode:
                self.multiline_buffer.append(raw)
                raw = "\n".join(self.multiline_buffer)
                self.multiline_buffer = []
                self.multiline_mode = False

            if not raw:
                continue

            # Record in history
            hist = self.state["history"]
            dup_policy = self.config.get("history_duplicates", "ignore")
            if dup_policy == "ignore":
                if not hist or hist[-1] != raw:
                    hist.append(raw)
            elif dup_policy == "eraseprev":
                while raw in hist:
                    hist.remove(raw)
                hist.append(raw)
            else:
                hist.append(raw)

            # Dispatch
            self.state["cmd_count"] += 1
            exit_code = self._dispatch(raw)
            self.state["last_exit"] = exit_code

    # ── Dispatch ──────────────────────────────────────────────────────────
    def _dispatch(self, raw: str) -> int:
        """
        Route a raw command string to the right handler.

        Order of precedence:
          1. exit / quit     — must be caught here (ends REPL)
          2. Multi-command   — ;  &&  ||  chaining
          3. Alias expansion — user-defined aliases
          4. export VAR=     — environment variable setting
          5. Built-ins       — cd, history, sysinfo, theme, alias, ...
          6. Plugin commands — registered plugin commands
          7. Everything else -> subprocess (real Linux commands)
        """
        # ── Handle multi-command chains (; && ||) ────────────────────────
        if self._is_chained(raw):
            return self._dispatch_chain(raw)

        # ── Expand aliases ─────────────────────────────────────────────────
        raw = self.aliases.expand(raw)

        # Split off the leading command word
        try:
            parts = self._split_command(raw)
        except ValueError as e:
            print(C.error(f"Parse error: {e}"))
            return 1

        if not parts:
            return 0

        cmd = parts[0]
        args = parts[1:]

        # ── exit / quit ────────────────────────────────────────────────────
        if cmd in ("exit", "quit"):
            self._handle_exit()
            return 0

        # ── export VAR=value ──────────────────────────────────────────────
        if cmd == "export":
            return self._handle_export(args)

        # ── unset VAR ──────────────────────────────────────────────────────
        if cmd == "unset":
            for var in args:
                os.environ.pop(var, None)
                self.state["env_vars"].pop(var, None)
            return 0

        # ── source / . ────────────────────────────────────────────────────
        if cmd in ("source", "."):
            return self._handle_source(args)

        # ── Built-in commands ──────────────────────────────────────────────
        if cmd in BUILTINS:
            try:
                return BUILTINS[cmd](args, self.state, self)
            except Exception as e:
                print(C.error(f"Builtin '{cmd}' crashed: {e}"))
                return 1

        # ── Plugin commands ────────────────────────────────────────────────
        plugin_result = self.plugins.try_dispatch(cmd, args, self.state)
        if plugin_result is not None:
            return plugin_result

        # ── System commands (real Linux) ───────────────────────────────────
        result = execute(raw, cwd=self.state["cwd"])
        return result.exit_code

    def _handle_exit(self):
        """Clean exit with session summary."""
        elapsed = time.time() - self.state["start_time"]
        mins = int(elapsed // 60)
        secs = int(elapsed % 60)
        print(f"\n{C.BLUE}{'─' * 60}{C.RESET}")
        print(f"  {C.WHITE}Session Summary{C.RESET}")
        print(f"{C.BLUE}{'─' * 60}{C.RESET}")
        print(f"  {C.CYAN}Duration{C.RESET}:     {mins}m {secs}s")
        print(f"  {C.CYAN}Commands{C.RESET}:     {self.state['cmd_count']}")
        print(f"  {C.CYAN}Last Exit{C.RESET}:    {self.state['last_exit']}")
        print(f"  {C.CYAN}History Size{C.RESET}: {len(self.state['history'])}")
        print(f"  {C.CYAN}Plugins{C.RESET}:      {len(self.plugins.loaded)} active")
        print(f"  {C.CYAN}AI Enabled{C.RESET}:   {C.GREEN if self.state['ai_enabled'] else C.RED}{self.state['ai_enabled']}{C.RESET}")
        print(f"{C.BLUE}{'─' * 60}{C.RESET}")
        print(f"\n  {C.paint('Goodbye! Stay elite.', C.RED, bold=True)}\n")
        self.state["running"] = False

    # ── Chain dispatcher (; && ||) ────────────────────────────────────────
    def _is_chained(self, cmd: str) -> bool:
        """Check if command contains chaining operators outside of quotes."""
        in_single = in_double = False
        for ch in cmd:
            if ch == "'" and not in_double:
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double
            elif not in_single and not in_double:
                if ch == ';':
                    return True
        return False

    def _dispatch_chain(self, raw: str) -> int:
        """Execute semicolon-separated commands sequentially."""
        last_code = 0
        parts = raw.split(";")
        for part in parts:
            part = part.strip()
            if part:
                last_code = self._dispatch(part)
                if not self.state["running"]:
                    break
        return last_code

    # ── export handler ────────────────────────────────────────────────────
    def _handle_export(self, args: list) -> int:
        """Handle `export VAR=value` and `export VAR`."""
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

    # ── source handler ────────────────────────────────────────────────────
    def _handle_source(self, args: list) -> int:
        """Execute a shell script file line-by-line in the current context."""
        if not args:
            print(C.error("source: filename argument required"))
            return 1

        script_path = os.path.expanduser(args[0])
        if not os.path.isabs(script_path):
            script_path = os.path.join(self.state["cwd"], script_path)

        try:
            with open(script_path, "r") as f:
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
            last_code = self._dispatch(line)
            if not self.state["running"]:
                break
        return last_code

    # ── Command splitter ──────────────────────────────────────────────────
    @staticmethod
    def _split_command(raw: str) -> list:
        """Split command respecting quotes."""
        import shlex
        try:
            return shlex.split(raw)
        except ValueError:
            return raw.split()