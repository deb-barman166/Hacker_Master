"""
commands/ai_engine.py — MASTERPIECE AI engine for KaliTerminal v2.

╔══════════════════════════════════════════════════════════════════════╗
║  AI is OFF by default. User must explicitly enable it.              ║
║                                                                      ║
║  LOCAL mode  → Ollama (100% offline, open-source models)            ║
║    Supports: llama3.2, mistral, gemma2, phi3, codellama, qwen2…    ║
║                                                                      ║
║  CLOUD mode  → Any API key you provide:                             ║
║    Anthropic (Claude), OpenAI (GPT-4o), Google (Gemini),           ║
║    Groq (llama3/mixtral), Mistral AI, Cohere                       ║
╚══════════════════════════════════════════════════════════════════════╝

Commands:
  ai on / off            enable / disable AI features
  ai mode local          use Ollama (local, offline)
  ai mode cloud          use cloud API
  ai setup               interactive setup wizard
  ai key <provider> <k>  set API key
  ai models              list available models
  ai status              show configuration
  ai <question>          ask anything (cybersecurity expert mode)
  ai explain <cmd>       explain a command or concept
  ai code <task>         generate code
  ai ctf <desc>          CTF challenge analysis & hints
  ai scan <output>       analyze scan results
  ai chat                enter multi-turn chat mode
"""

import os
import sys
import json
import urllib.request
import urllib.error
import urllib.parse
import time

from ui.theme   import Colors
from utils.config import get_pref, set_pref, load_prefs, save_prefs

C = Colors

# ══════════════════════════════════════════════════════════════════════════════
#  Provider registry
# ══════════════════════════════════════════════════════════════════════════════

PROVIDERS = {
    "anthropic": {
        "name":    "Anthropic (Claude)",
        "url":     "https://api.anthropic.com/v1/messages",
        "key_env": "ANTHROPIC_API_KEY",
        "models":  ["claude-opus-4-5", "claude-sonnet-4-5", "claude-haiku-4-5"],
        "default": "claude-haiku-4-5",
    },
    "openai": {
        "name":    "OpenAI (GPT)",
        "url":     "https://api.openai.com/v1/chat/completions",
        "key_env": "OPENAI_API_KEY",
        "models":  ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
        "default": "gpt-4o-mini",
    },
    "gemini": {
        "name":    "Google Gemini",
        "url":     "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        "key_env": "GEMINI_API_KEY",
        "models":  ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"],
        "default": "gemini-1.5-flash",
    },
    "groq": {
        "name":    "Groq (ultra-fast inference)",
        "url":     "https://api.groq.com/openai/v1/chat/completions",
        "key_env": "GROQ_API_KEY",
        "models":  ["llama-3.3-70b-versatile", "llama-3.1-8b-instant",
                    "mixtral-8x7b-32768", "gemma2-9b-it"],
        "default": "llama-3.3-70b-versatile",
    },
    "mistral": {
        "name":    "Mistral AI",
        "url":     "https://api.mistral.ai/v1/chat/completions",
        "key_env": "MISTRAL_API_KEY",
        "models":  ["mistral-large-latest", "mistral-small-latest", "mistral-nemo"],
        "default": "mistral-small-latest",
    },
    "cohere": {
        "name":    "Cohere",
        "url":     "https://api.cohere.com/v1/chat",
        "key_env": "COHERE_API_KEY",
        "models":  ["command-r-plus", "command-r", "command-light"],
        "default": "command-r",
    },
}

# Expert cybersecurity system prompt
CYBER_EXPERT_SYSTEM = """You are an elite cybersecurity expert and ethical hacker with 34 years of experience. You specialize in:

• Penetration testing, red teaming, CTF challenges
• Network security, web application security, binary exploitation
• Malware analysis, forensics, threat intelligence
• Security tool usage: nmap, metasploit, burpsuite, wireshark, sqlmap, hashcat, john, gobuster, and hundreds more
• Programming: Python, Bash, C, Assembly for security tooling
• OWASP Top 10, CVEs, exploit development

Personality: Direct, technical, no-nonsense. You give real answers. No excessive disclaimers.
Format: Use clear sections. For commands, use code blocks with ``` markers. Be concise but complete.
Context: You are running inside KaliTerminal v2 — a professional security terminal."""


# ══════════════════════════════════════════════════════════════════════════════
#  AI main dispatcher
# ══════════════════════════════════════════════════════════════════════════════

def cmd_ai(args: list, state: dict) -> int:
    """Main AI command dispatcher."""
    if not args:
        return _ai_status(state)

    sub = args[0].lower()

    # ── Control commands (always available, even when AI is off) ──────────
    if sub == "on":
        return _ai_on(state)
    if sub == "off":
        return _ai_off(state)
    if sub == "status":
        return _ai_status(state)
    if sub == "setup":
        return _ai_setup(state)
    if sub == "mode" and len(args) > 1:
        return _ai_set_mode(args[1], state)
    if sub in ("key", "setkey") and len(args) > 2:
        return _ai_set_key(args[1], args[2], state)
    if sub == "models":
        return _ai_list_models(state)

    # ── Feature commands — require AI to be ON ────────────────────────────
    if not state.get("ai_enabled", False):
        print(f"\n  {C.YELLOW}⚠  AI is currently {C.BOLD}OFF{C.RESET}{C.YELLOW}.{C.RESET}")
        print(f"  Type {C.CYAN}ai on{C.RESET} to enable it.")
        print(f"  Type {C.CYAN}ai setup{C.RESET} to configure your AI provider.\n")
        return 1

    if sub == "explain":
        topic = " ".join(args[1:]) if len(args) > 1 else ""
        if not topic:
            print(C.error("Usage: ai explain <command|concept>"))
            return 1
        prompt = f"Explain this concisely for a cybersecurity professional: {topic}"
        return _ai_query(prompt, state)

    if sub == "code":
        task = " ".join(args[1:]) if len(args) > 1 else ""
        if not task:
            print(C.error("Usage: ai code <task description>"))
            return 1
        prompt = f"Write clean, working code for: {task}\nProvide only code with brief inline comments. Use Python unless specified."
        return _ai_query(prompt, state)

    if sub == "ctf":
        desc = " ".join(args[1:]) if len(args) > 1 else ""
        if not desc:
            print(C.error("Usage: ai ctf <challenge description>"))
            return 1
        prompt = (f"CTF Challenge Analysis:\n{desc}\n\n"
                  f"Analyze this CTF challenge. Identify: category, attack vectors, "
                  f"recommended tools, step-by-step approach, and common pitfalls.")
        return _ai_query(prompt, state)

    if sub == "scan":
        output = " ".join(args[1:]) if len(args) > 1 else ""
        if not output:
            print(C.error("Usage: ai scan <scan output or target>"))
            return 1
        prompt = (f"Analyze this network/security scan output:\n```\n{output}\n```\n"
                  f"Identify: open services, potential vulnerabilities, recommended next steps for pentesting.")
        return _ai_query(prompt, state)

    if sub == "chat":
        return _ai_chat_mode(state)

    # ── Free-form question ────────────────────────────────────────────────
    question = " ".join(args)
    return _ai_query(question, state)


# ══════════════════════════════════════════════════════════════════════════════
#  Control commands
# ══════════════════════════════════════════════════════════════════════════════

def _ai_on(state: dict) -> int:
    prefs = state.get("prefs", {})
    mode  = prefs.get("ai_mode", "off")

    if mode == "off":
        print(f"\n  {C.YELLOW}AI mode is set to 'off'. Choose a mode first:{C.RESET}")
        print(f"  {C.CYAN}ai mode local{C.RESET}  — Ollama (100%% offline, free)")
        print(f"  {C.CYAN}ai mode cloud{C.RESET}  — Cloud API (needs API key)")
        print(f"  {C.CYAN}ai setup{C.RESET}        — Interactive wizard\n")
        return 0

    state["ai_enabled"] = True
    prefs["ai_enabled"] = True
    set_pref("ai_enabled", True)

    if mode == "local":
        # Quick check if Ollama is running
        ok = _check_ollama(state)
        if ok:
            model = prefs.get("ai_local_model", "llama3.2")
            print(C.success(f"AI ENABLED — Local Ollama ({model})"))
        else:
            print(C.warn("Ollama doesn't seem to be running."))
            print(C.info("Start it with: ollama serve"))
            print(C.info("Pull a model : ollama pull llama3.2"))
    else:
        provider = prefs.get("ai_cloud_provider", "anthropic")
        model    = _get_cloud_model(prefs)
        print(C.success(f"AI ENABLED — Cloud: {PROVIDERS.get(provider,{}).get('name', provider)} ({model})"))

    state["ai_mode"] = mode
    return 0


def _ai_off(state: dict) -> int:
    state["ai_enabled"] = False
    state.setdefault("prefs", {})["ai_enabled"] = False
    set_pref("ai_enabled", False)
    print(C.success("AI features DISABLED. All AI commands are now unavailable."))
    return 0


def _ai_set_mode(mode: str, state: dict) -> int:
    mode = mode.lower()
    if mode not in ("local", "cloud", "off"):
        print(C.error("Mode must be: local | cloud | off"))
        return 1

    state.setdefault("prefs", {})["ai_mode"] = mode
    state["ai_mode"] = mode
    set_pref("ai_mode", mode)

    if mode == "local":
        print(C.success("AI mode set to LOCAL (Ollama)."))
        print(C.info("Make sure Ollama is running: ollama serve"))
        print(C.info("Pull models: ollama pull llama3.2"))
        print(C.info("Then run: ai on"))
    elif mode == "cloud":
        prefs    = state.get("prefs", {})
        provider = prefs.get("ai_cloud_provider", "anthropic")
        key_pref = f"{provider}_key"
        has_key  = bool(prefs.get(key_pref) or os.environ.get(PROVIDERS.get(provider,{}).get("key_env","")))
        if has_key:
            print(C.success(f"AI mode set to CLOUD ({PROVIDERS.get(provider,{}).get('name','?')})."))
            print(C.info("Run: ai on"))
        else:
            print(C.success("AI mode set to CLOUD."))
            print(C.warn(f"No API key found for '{provider}'."))
            print(C.info(f"Set it with: ai key {provider} <YOUR_API_KEY>"))
            print(C.info("Or run: ai setup"))
    else:
        state["ai_enabled"] = False
        set_pref("ai_enabled", False)
        print(C.success("AI mode set to OFF."))
    return 0


def _ai_set_key(provider: str, key: str, state: dict) -> int:
    provider = provider.lower()
    if provider not in PROVIDERS:
        print(C.error(f"Unknown provider: '{provider}'"))
        print(C.info(f"Available: {', '.join(PROVIDERS.keys())}"))
        return 1

    pref_key = f"{provider}_key"
    set_pref(pref_key, key)
    state.setdefault("prefs", {})[pref_key] = key

    # Also set env var for the session
    env_var = PROVIDERS[provider]["key_env"]
    os.environ[env_var] = key

    masked = key[:6] + "…" + key[-4:] if len(key) > 10 else "****"
    print(C.success(f"API key set for {PROVIDERS[provider]['name']}: {masked}"))
    print(C.info(f"Run: ai mode cloud  →  ai on"))
    return 0


def _ai_list_models(state: dict) -> int:
    prefs = state.get("prefs", {})
    mode  = prefs.get("ai_mode", "off")

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}AI MODELS{C.RESET}")
    print(f"{C.BLUE}{'═'*65}{C.RESET}\n")

    if mode == "local":
        print(f"  {C.YELLOW}Local Ollama Models:{C.RESET}")
        url = prefs.get("ai_local_url", "http://localhost:11434")
        try:
            req = urllib.request.Request(f"{url}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data  = json.loads(resp.read().decode())
                models = data.get("models", [])
            if models:
                for m in models:
                    name = m.get("name","")
                    size = m.get("size", 0)
                    sz   = f"{size/(1024**3):.1f}GB" if size else ""
                    curr = " ◄ active" if name == prefs.get("ai_local_model","") else ""
                    print(f"    {C.GREEN}{name:<35}{C.RESET}  {C.GRAY}{sz}{C.RESET}{C.CYAN}{curr}{C.RESET}")
            else:
                print(f"  {C.GRAY}No models installed. Run: ollama pull llama3.2{C.RESET}")
        except Exception:
            print(f"  {C.RED}Cannot connect to Ollama ({url}){C.RESET}")
            print(f"  {C.GRAY}Start with: ollama serve{C.RESET}")

        print(f"\n  {C.YELLOW}Popular models to pull:{C.RESET}")
        popular = [
            ("llama3.2",   "3B",  "Fast, general purpose"),
            ("llama3.1:8b","8B",  "Good balance of speed/quality"),
            ("mistral",    "7B",  "Strong reasoning"),
            ("gemma2:9b",  "9B",  "Google's model"),
            ("phi3:mini",  "3.8B","Microsoft's small model"),
            ("codellama",  "7B",  "Code specialist"),
            ("qwen2:7b",   "7B",  "Multilingual"),
            ("deepseek-coder","7B","Code & math"),
        ]
        for name, size, desc in popular:
            print(f"    {C.CYAN}ollama pull {name:<25}{C.RESET}  {C.GRAY}{size}  {desc}{C.RESET}")

    else:
        print(f"  {C.YELLOW}Cloud Providers & Models:{C.RESET}\n")
        cur_provider = prefs.get("ai_cloud_provider", "anthropic")
        for pid, pdata in PROVIDERS.items():
            key_pref = f"{pid}_key"
            has_key  = bool(prefs.get(key_pref) or os.environ.get(pdata["key_env"]))
            active   = " ◄ active" if pid == cur_provider else ""
            key_str  = f"{C.GREEN}[KEY SET]{C.RESET}" if has_key else f"{C.GRAY}[no key]{C.RESET}"
            print(f"  {C.CYAN}{pdata['name']}{C.RESET}{C.GREEN}{active}{C.RESET}  {key_str}")
            for m in pdata["models"]:
                dflt = " (default)" if m == pdata["default"] else ""
                print(f"    {C.WHITE}• {m}{C.RESET}{C.GRAY}{dflt}{C.RESET}")
            print()

    print(f"{C.BLUE}{'═'*65}{C.RESET}\n")
    return 0


def _ai_status(state: dict) -> int:
    prefs    = state.get("prefs", {})
    enabled  = state.get("ai_enabled", False)
    mode     = state.get("ai_mode", prefs.get("ai_mode", "off"))
    provider = prefs.get("ai_cloud_provider", "anthropic")

    print(f"\n{C.BLUE}{'═'*55}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}AI STATUS{C.RESET}")
    print(f"{C.BLUE}{'═'*55}{C.RESET}\n")

    status_str = f"{C.GREEN}{C.BOLD}ENABLED{C.RESET}" if enabled else f"{C.RED}DISABLED{C.RESET}"
    print(f"  {C.CYAN}AI Features {C.RESET}: {status_str}")
    print(f"  {C.CYAN}Mode        {C.RESET}: {C.YELLOW}{mode}{C.RESET}")

    if mode == "local":
        url   = prefs.get("ai_local_url", "http://localhost:11434")
        model = prefs.get("ai_local_model", "llama3.2")
        print(f"  {C.CYAN}Ollama URL  {C.RESET}: {url}")
        print(f"  {C.CYAN}Local Model {C.RESET}: {C.GREEN}{model}{C.RESET}")
        ok = _check_ollama(state, silent=True)
        ol_str = f"{C.GREEN}● RUNNING{C.RESET}" if ok else f"{C.RED}● NOT RUNNING{C.RESET}"
        print(f"  {C.CYAN}Ollama      {C.RESET}: {ol_str}")

    elif mode == "cloud":
        pdata   = PROVIDERS.get(provider, {})
        key_env = pdata.get("key_env", "")
        key_val = prefs.get(f"{provider}_key") or os.environ.get(key_env, "")
        model   = _get_cloud_model(prefs)
        k_str   = f"{C.GREEN}SET ({key_val[:6]}…){C.RESET}" if key_val else f"{C.RED}NOT SET{C.RESET}"
        print(f"  {C.CYAN}Provider    {C.RESET}: {pdata.get('name', provider)}")
        print(f"  {C.CYAN}Cloud Model {C.RESET}: {C.GREEN}{model}{C.RESET}")
        print(f"  {C.CYAN}API Key     {C.RESET}: {k_str}")

    print(f"\n  {C.GRAY}Commands:{C.RESET}")
    print(f"  {C.CYAN}ai on{C.RESET}               enable AI")
    print(f"  {C.CYAN}ai off{C.RESET}              disable AI")
    print(f"  {C.CYAN}ai mode local{C.RESET}       use Ollama (offline)")
    print(f"  {C.CYAN}ai mode cloud{C.RESET}       use cloud API")
    print(f"  {C.CYAN}ai setup{C.RESET}            interactive wizard")
    print(f"  {C.CYAN}ai key <provider> <k>{C.RESET} set API key")
    print()
    return 0


def _ai_setup(state: dict) -> int:
    """Interactive AI setup wizard."""
    print(f"\n{C.BLUE}{'═'*60}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}AI SETUP WIZARD{C.RESET}")
    print(f"{C.BLUE}{'═'*60}{C.RESET}\n")

    print(f"  {C.YELLOW}Choose AI mode:{C.RESET}")
    print(f"  {C.CYAN}1{C.RESET}  Local — Ollama (100%% offline, free, open-source)")
    print(f"  {C.CYAN}2{C.RESET}  Cloud — Use an API key (Anthropic, OpenAI, Gemini…)")
    print(f"  {C.CYAN}0{C.RESET}  Cancel\n")

    choice = input(f"  {C.CYAN}Select [1/2/0]{C.RESET}: ").strip()

    if choice == "0":
        print(C.info("Setup cancelled."))
        return 0

    if choice == "1":
        _setup_local(state)
    elif choice == "2":
        _setup_cloud(state)
    else:
        print(C.error("Invalid choice."))
        return 1

    return 0


def _setup_local(state: dict):
    prefs = state.get("prefs", {})
    print(f"\n  {C.YELLOW}── Local Ollama Setup ──{C.RESET}\n")

    url = input(f"  Ollama URL [{C.GRAY}http://localhost:11434{C.RESET}]: ").strip()
    if not url:
        url = "http://localhost:11434"

    set_pref("ai_local_url", url)
    prefs["ai_local_url"] = url

    # Check if running
    ok = _check_ollama(state, url=url)
    if ok:
        print(C.success(f"Connected to Ollama at {url}"))
        # Show available models
        try:
            req  = urllib.request.Request(f"{url}/api/tags")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data   = json.loads(resp.read().decode())
                models = [m["name"] for m in data.get("models", [])]
            if models:
                print(f"\n  {C.YELLOW}Available models:{C.RESET}")
                for i, m in enumerate(models, 1):
                    print(f"  {C.CYAN}{i}{C.RESET}  {m}")
                sel = input(f"\n  Select model [1-{len(models)}] or type name: ").strip()
                if sel.isdigit() and 1 <= int(sel) <= len(models):
                    model = models[int(sel)-1]
                else:
                    model = sel or models[0]
            else:
                print(C.warn("No models installed."))
                model = input(f"  Model name [{C.GRAY}llama3.2{C.RESET}]: ").strip() or "llama3.2"
                print(C.info(f"Pull it with: ollama pull {model}"))
        except Exception:
            model = input(f"  Model name [{C.GRAY}llama3.2{C.RESET}]: ").strip() or "llama3.2"
    else:
        print(C.warn(f"Cannot connect to Ollama at {url}"))
        print(C.info("Start it with: ollama serve"))
        model = input(f"  Model name to use [{C.GRAY}llama3.2{C.RESET}]: ").strip() or "llama3.2"

    set_pref("ai_local_model", model)
    set_pref("ai_mode", "local")
    set_pref("ai_enabled", True)
    prefs["ai_local_model"] = model
    prefs["ai_mode"]        = "local"
    prefs["ai_enabled"]     = True
    state["ai_mode"]        = "local"
    state["ai_enabled"]     = True

    print(C.success(f"AI configured: Ollama local → {model}"))
    print(C.info("AI is now ON. Type: ai What is SQL injection?"))


def _setup_cloud(state: dict):
    prefs = state.get("prefs", {})
    print(f"\n  {C.YELLOW}── Cloud API Setup ──{C.RESET}\n")

    for i, (pid, pdata) in enumerate(PROVIDERS.items(), 1):
        print(f"  {C.CYAN}{i}{C.RESET}  {pdata['name']}")

    sel = input(f"\n  Select provider [1-{len(PROVIDERS)}]: ").strip()
    try:
        idx      = int(sel) - 1
        provider = list(PROVIDERS.keys())[idx]
    except (ValueError, IndexError):
        print(C.error("Invalid selection."))
        return

    pdata   = PROVIDERS[provider]
    env_key = pdata["key_env"]

    # Check for existing key
    existing = prefs.get(f"{provider}_key") or os.environ.get(env_key, "")
    if existing:
        masked = existing[:6] + "…" + existing[-4:]
        keep   = input(f"  Key found: {masked}. Keep? [Y/n]: ").strip().lower()
        if keep != "n":
            api_key = existing
        else:
            api_key = input(f"  Enter new {pdata['name']} API key: ").strip()
    else:
        api_key = input(f"  Enter {pdata['name']} API key: ").strip()

    if not api_key:
        print(C.error("No key provided."))
        return

    # Model selection
    print(f"\n  {C.YELLOW}Available models:{C.RESET}")
    for i, m in enumerate(pdata["models"], 1):
        dflt = " (recommended)" if m == pdata["default"] else ""
        print(f"  {C.CYAN}{i}{C.RESET}  {m}{C.GRAY}{dflt}{C.RESET}")

    sel   = input(f"\n  Select model [1-{len(pdata['models'])}] or press Enter for default: ").strip()
    if sel.isdigit() and 1 <= int(sel) <= len(pdata["models"]):
        model = pdata["models"][int(sel)-1]
    else:
        model = pdata["default"]

    # Save everything
    set_pref(f"{provider}_key",    api_key)
    set_pref("ai_cloud_provider",  provider)
    set_pref("ai_cloud_model",     model)
    set_pref("ai_mode",            "cloud")
    set_pref("ai_enabled",         True)
    os.environ[env_key] = api_key
    prefs[f"{provider}_key"]    = api_key
    prefs["ai_cloud_provider"]  = provider
    prefs["ai_cloud_model"]     = model
    prefs["ai_mode"]            = "cloud"
    prefs["ai_enabled"]         = True
    state["ai_mode"]            = "cloud"
    state["ai_enabled"]         = True

    print(C.success(f"AI configured: {pdata['name']} ({model})"))
    print(C.info("AI is now ON. Type: ai Explain SQL injection"))


# ══════════════════════════════════════════════════════════════════════════════
#  Core query functions
# ══════════════════════════════════════════════════════════════════════════════

def _ai_query(prompt: str, state: dict, system: str = None) -> int:
    """Send a single query to the configured AI provider."""
    prefs    = state.get("prefs", {})
    mode     = state.get("ai_mode", prefs.get("ai_mode", "off"))
    sys_msg  = system or CYBER_EXPERT_SYSTEM

    print(f"\n  {C.GRAY}{'─'*55}{C.RESET}")
    print(f"  {C.CYAN}🤖 AI ({mode.upper()}){C.RESET}  {C.GRAY}thinking…{C.RESET}")
    print(f"  {C.GRAY}{'─'*55}{C.RESET}\n")

    try:
        if mode == "local":
            response = _query_ollama(prompt, sys_msg, prefs)
        elif mode == "cloud":
            response = _query_cloud(prompt, sys_msg, prefs)
        else:
            print(C.error("AI mode not configured. Run: ai setup"))
            return 1
    except Exception as e:
        print(C.error(f"AI request failed: {e}"))
        return 1

    if response:
        _print_ai_response(response)
    return 0


def _ai_chat_mode(state: dict) -> int:
    """Multi-turn chat with the AI."""
    prefs    = state.get("prefs", {})
    mode     = state.get("ai_mode", prefs.get("ai_mode", "off"))

    print(f"\n{C.BLUE}{'═'*60}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}AI CHAT MODE — Cybersecurity Expert{C.RESET}")
    print(f"  {C.GRAY}Mode: {mode}  |  Type 'exit' or Ctrl+D to quit{C.RESET}")
    print(f"{C.BLUE}{'═'*60}{C.RESET}\n")

    history  = []
    turn     = 0

    while True:
        try:
            user_input = input(f"  {C.GREEN}You{C.RESET}: ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {C.GRAY}Chat ended.{C.RESET}\n")
            break

        if not user_input or user_input.lower() in ("exit", "quit", "q"):
            break

        turn += 1
        history.append({"role": "user", "content": user_input})

        try:
            if mode == "local":
                response = _query_ollama_chat(history, CYBER_EXPERT_SYSTEM, prefs)
            else:
                response = _query_cloud_chat(history, CYBER_EXPERT_SYSTEM, prefs)
        except Exception as e:
            print(C.error(f"  AI error: {e}"))
            history.pop()
            continue

        if response:
            history.append({"role": "assistant", "content": response})
            print(f"\n  {C.CYAN}AI{C.RESET}: ", end="")
            _stream_print(response)
            print()

    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  Local Ollama
# ══════════════════════════════════════════════════════════════════════════════

def _check_ollama(state: dict, url: str = None, silent: bool = False) -> bool:
    prefs = state.get("prefs", {})
    url   = url or prefs.get("ai_local_url", "http://localhost:11434")
    try:
        req = urllib.request.Request(f"{url}/api/tags")
        with urllib.request.urlopen(req, timeout=3):
            return True
    except Exception:
        return False


def _query_ollama(prompt: str, system: str, prefs: dict) -> str:
    url   = prefs.get("ai_local_url", "http://localhost:11434")
    model = prefs.get("ai_local_model", "llama3.2")

    payload = {
        "model":  model,
        "prompt": f"[SYSTEM]\n{system}\n\n[USER]\n{prompt}",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 2048,
        }
    }

    req = urllib.request.Request(
        f"{url}/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
        return data.get("response", "")


def _query_ollama_chat(messages: list, system: str, prefs: dict) -> str:
    url   = prefs.get("ai_local_url", "http://localhost:11434")
    model = prefs.get("ai_local_model", "llama3.2")

    payload = {
        "model":    model,
        "messages": [{"role": "system", "content": system}] + messages,
        "stream":   False,
        "options":  {"temperature": 0.7, "num_predict": 2048},
    }

    req = urllib.request.Request(
        f"{url}/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode())
        return data.get("message", {}).get("content", "")


# ══════════════════════════════════════════════════════════════════════════════
#  Cloud providers
# ══════════════════════════════════════════════════════════════════════════════

def _get_cloud_model(prefs: dict) -> str:
    provider = prefs.get("ai_cloud_provider", "anthropic")
    saved    = prefs.get("ai_cloud_model", "")
    return saved or PROVIDERS.get(provider, {}).get("default", "")


def _get_api_key(provider: str, prefs: dict) -> str:
    pdata   = PROVIDERS.get(provider, {})
    key_env = pdata.get("key_env", "")
    return prefs.get(f"{provider}_key", "") or os.environ.get(key_env, "")


def _query_cloud(prompt: str, system: str, prefs: dict) -> str:
    messages = [{"role": "user", "content": prompt}]
    return _query_cloud_chat(messages, system, prefs)


def _query_cloud_chat(messages: list, system: str, prefs: dict) -> str:
    provider = prefs.get("ai_cloud_provider", "anthropic")
    api_key  = _get_api_key(provider, prefs)
    model    = _get_cloud_model(prefs)

    if not api_key:
        raise Exception(f"No API key for '{provider}'. Run: ai key {provider} <YOUR_KEY>")

    handler  = _CLOUD_HANDLERS.get(provider)
    if not handler:
        raise Exception(f"Unknown provider: {provider}")

    return handler(messages, system, model, api_key, prefs)


def _query_anthropic(messages: list, system: str, model: str, api_key: str, prefs: dict) -> str:
    payload = {
        "model":      model,
        "max_tokens": 2048,
        "system":     system,
        "messages":   messages,
    }
    req = urllib.request.Request(
        PROVIDERS["anthropic"]["url"],
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    return data.get("content", [{}])[0].get("text", "")


def _query_openai_compat(messages: list, system: str, model: str, api_key: str, url: str) -> str:
    """Shared handler for OpenAI-compatible APIs (OpenAI, Groq, Mistral)."""
    payload = {
        "model":    model,
        "messages": [{"role": "system", "content": system}] + messages,
        "max_tokens": 2048,
        "temperature": 0.7,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    return data["choices"][0]["message"]["content"]


def _query_openai(messages, system, model, api_key, prefs):
    return _query_openai_compat(messages, system, model, api_key, PROVIDERS["openai"]["url"])

def _query_groq(messages, system, model, api_key, prefs):
    return _query_openai_compat(messages, system, model, api_key, PROVIDERS["groq"]["url"])

def _query_mistral(messages, system, model, api_key, prefs):
    return _query_openai_compat(messages, system, model, api_key, PROVIDERS["mistral"]["url"])


def _query_gemini(messages: list, system: str, model: str, api_key: str, prefs: dict) -> str:
    url = PROVIDERS["gemini"]["url"].format(model=model)
    url = f"{url}?key={api_key}"

    # Build Gemini-format contents
    contents = []
    for m in messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": m["content"]}]})

    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": 2048,
            "temperature":     0.7,
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    candidates = data.get("candidates", [{}])
    return candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")


def _query_cohere(messages: list, system: str, model: str, api_key: str, prefs: dict) -> str:
    # Cohere chat API
    chat_history = []
    for m in messages[:-1]:
        role = "USER" if m["role"] == "user" else "CHATBOT"
        chat_history.append({"role": role, "message": m["content"]})

    user_msg = messages[-1]["content"] if messages else ""
    payload  = {
        "model":        model,
        "message":      user_msg,
        "chat_history": chat_history,
        "preamble":     system,
        "max_tokens":   2048,
        "temperature":  0.7,
    }
    req = urllib.request.Request(
        PROVIDERS["cohere"]["url"],
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
    return data.get("text", "")


_CLOUD_HANDLERS = {
    "anthropic": _query_anthropic,
    "openai":    _query_openai,
    "gemini":    _query_gemini,
    "groq":      _query_groq,
    "mistral":   _query_mistral,
    "cohere":    _query_cohere,
}


# ══════════════════════════════════════════════════════════════════════════════
#  Output rendering
# ══════════════════════════════════════════════════════════════════════════════

def _print_ai_response(text: str):
    """Print AI response with syntax highlighting for code blocks."""
    lines = text.split("\n")
    in_code = False
    lang    = ""

    for line in lines:
        if line.startswith("```"):
            in_code = not in_code
            if in_code:
                lang = line[3:].strip()
                print(f"  {C.BLUE}┌─ {lang or 'code'} {'─'*40}{C.RESET}")
            else:
                print(f"  {C.BLUE}└{'─'*44}{C.RESET}")
            continue

        if in_code:
            print(f"  {C.YELLOW}{line}{C.RESET}")
        elif line.startswith("# "):
            print(f"\n  {C.BOLD}{C.WHITE}{line[2:]}{C.RESET}")
        elif line.startswith("## "):
            print(f"\n  {C.CYAN}{line[3:]}{C.RESET}")
        elif line.startswith("### "):
            print(f"\n  {C.YELLOW}{line[4:]}{C.RESET}")
        elif line.startswith("- ") or line.startswith("• "):
            print(f"  {C.GREEN}•{C.RESET} {line[2:]}")
        elif line.startswith("**") and line.endswith("**"):
            print(f"  {C.BOLD}{line[2:-2]}{C.RESET}")
        else:
            print(f"  {line}")

    print()


def _stream_print(text: str):
    """Print text char by char for a streaming feel."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        if char in ".!?\n":
            time.sleep(0.015)


# ══════════════════════════════════════════════════════════════════════════════
#  Registry
# ══════════════════════════════════════════════════════════════════════════════

AI_CMDS: dict = {
    "ai": cmd_ai,
}
