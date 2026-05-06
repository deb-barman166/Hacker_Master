"""
commands/ai.py — AI Assistant for Kali Terminal v1.0

Connects to the Anthropic API (Claude) to provide:
  • Cybersecurity Q&A
  • Command explanations
  • Code help
  • CTF hints
  • Hacking technique walkthroughs

Usage:
  ai <question>              — Ask Claude anything
  ai --setup <api_key>       — Store your Anthropic API key
  ai explain <command>       — Explain a Linux command
  ai code <language> <task>  — Generate code
  ai ctf <challenge_desc>    — CTF challenge hints
"""

import os
import json
import urllib.request
import urllib.error

from ui.theme import Colors
from utils.config import get_pref, set_pref

C = Colors

AI_SYSTEM_PROMPT = """You are KaliAI — the built-in AI assistant for Kali Linux Terminal.
You are an elite cybersecurity expert, penetration tester, and Python developer.
You help users with:
- Linux commands and shell scripting
- Cybersecurity concepts and techniques (ethical hacking, pentesting, CTF)
- Python programming and automation
- Network security and analysis
- Malware analysis (educational only)
- Bug bounty hunting tips
- Cryptography and encoding
- AI/ML concepts when asked

Be concise but thorough. Use technical language. Format responses with:
- Clear sections using ── SECTION ── headers
- Code blocks using backticks for commands/code
- Bullet points for lists
- Warnings for dangerous operations (mark with ⚠)

You are inside a terminal, so keep responses terminal-friendly (no markdown headers).
Always remind users to use techniques ethically and only on systems they own or have permission to test."""


def _get_api_key() -> str | None:
    """Get API key from config or environment."""
    # Check environment first
    env_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if env_key:
        return env_key
    # Then check stored config
    return get_pref("anthropic_api_key")


def _call_claude(prompt: str, api_key: str) -> str:
    """Make a request to the Anthropic API."""
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1024,
        "system": AI_SYSTEM_PROMPT,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    data    = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type":      "application/json",
        "x-api-key":         api_key,
        "anthropic-version": "2023-06-01",
    }

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data, headers=headers, method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            content = body.get("content", [])
            for block in content:
                if block.get("type") == "text":
                    return block["text"]
            return "(No response from AI)"
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(error_body)
            msg = err_json.get("error", {}).get("message", error_body)
        except Exception:
            msg = error_body[:200]
        raise RuntimeError(f"API error {e.code}: {msg}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")


def _render_response(text: str):
    """Pretty-print the AI response."""
    print(f"\n{C.BLUE}{'─'*66}{C.RESET}")
    print(f"  {C.RED}{C.BOLD}🤖 KaliAI{C.RESET}")
    print(f"{C.BLUE}{'─'*66}{C.RESET}\n")

    in_code = False
    for line in text.splitlines():
        # Code blocks
        if line.strip().startswith("```"):
            in_code = not in_code
            lang = line.strip()[3:].strip()
            if in_code:
                print(f"  {C.BLUE}{'─'*50}{C.RESET}  {C.GRAY}{lang}{C.RESET}")
            else:
                print(f"  {C.BLUE}{'─'*50}{C.RESET}")
            continue

        if in_code:
            print(f"  {C.YELLOW}{line}{C.RESET}")
            continue

        # Section headers
        if line.strip().startswith("──") or line.strip().startswith("**"):
            clean = line.strip().strip("─*").strip()
            print(f"\n  {C.CYAN}{C.BOLD}{clean}{C.RESET}")
            continue

        # Bullet points
        if line.strip().startswith(("- ", "• ", "▸ ")):
            rest = line.strip()[2:]
            print(f"  {C.GREEN}▸{C.RESET} {C.WHITE}{rest}{C.RESET}")
            continue

        # Warnings
        if "⚠" in line:
            print(f"  {C.YELLOW}{C.BOLD}{line}{C.RESET}")
            continue

        # Normal text
        if line.strip():
            print(f"  {C.WHITE}{line}{C.RESET}")
        else:
            print()

    print(f"\n{C.BLUE}{'─'*66}{C.RESET}\n")


def cmd_ai(args: list, state: dict) -> int:
    """
    ai <question>            — Ask the AI assistant
    ai --setup <key>         — Save your Anthropic API key
    ai explain <cmd>         — Explain a command
    ai code <lang> <task>    — Generate code snippet
    ai ctf <description>     — CTF challenge hints
    """
    if not args:
        print(f"\n{C.BOLD}{C.BLUE}[ KaliAI — AI ASSISTANT ]{C.RESET}\n")
        print(f"  Usage:  {C.CYAN}ai <question>{C.RESET}")
        print(f"  Setup:  {C.CYAN}ai --setup <your-anthropic-api-key>{C.RESET}")
        print(f"  Alt:    {C.CYAN}export ANTHROPIC_API_KEY=<key>{C.RESET}\n")
        print(f"  Examples:")
        print(f"    {C.GRAY}ai how does a buffer overflow work?")
        print(f"    ai explain nmap -sV -p- -A target")
        print(f"    ai code python port scanner")
        print(f"    ai ctf I found an SQLi in a login form, how do I exploit it?{C.RESET}\n")
        return 0

    # Setup API key
    if args[0] == "--setup":
        if len(args) < 2:
            print(C.error("Usage: ai --setup <your-anthropic-api-key>"))
            return 1
        key = args[1]
        if not key.startswith("sk-ant-"):
            print(C.warn("Warning: This doesn't look like a valid Anthropic API key (should start with sk-ant-)."))
        set_pref("anthropic_api_key", key)
        print(C.success("API key saved to ~/.kali_terminal/prefs.json"))
        print(C.info("Now try: ai how does XSS work?"))
        return 0

    # Check for API key
    api_key = _get_api_key()
    if not api_key:
        print(f"\n{C.YELLOW}[⚠] No Anthropic API key found.{C.RESET}")
        print(f"\n  To use the AI assistant:")
        print(f"  1. Get a free key at {C.CYAN}https://console.anthropic.com{C.RESET}")
        print(f"  2. Run: {C.CYAN}ai --setup sk-ant-your-key-here{C.RESET}")
        print(f"     or:  {C.CYAN}export ANTHROPIC_API_KEY=sk-ant-your-key{C.RESET}\n")
        return 1

    # Build prompt based on subcommand
    subcommand = args[0].lower()
    rest = " ".join(args[1:])

    if subcommand == "explain":
        prompt = f"Explain this Linux/shell command in detail. What does each flag/option do? When would you use it?\n\nCommand: {rest}"
    elif subcommand == "code":
        parts = args[1:]
        lang  = parts[0] if parts else "python"
        task  = " ".join(parts[1:]) if len(parts) > 1 else "hello world"
        prompt = f"Write a {lang} script/function to: {task}\nInclude comments and explain the key parts."
    elif subcommand == "ctf":
        prompt = f"CTF Challenge Help (educational only):\n\n{rest}\n\nProvide hints and methodology, not full exploits. Teach the concepts."
    elif subcommand == "scan":
        target = rest
        prompt = f"What nmap/scanning commands should I run to enumerate '{target}'? Give a full recon methodology."
    else:
        # Treat all args as the question
        prompt = " ".join(args)

    # Loading spinner
    import threading
    import sys

    stop_spinner = threading.Event()
    spinner_chars = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]

    def spin():
        i = 0
        while not stop_spinner.is_set():
            sys.stdout.write(f"\r  {C.CYAN}{spinner_chars[i % len(spinner_chars)]}{C.RESET}"
                             f"  {C.GRAY}KaliAI is thinking...{C.RESET}  ")
            sys.stdout.flush()
            stop_spinner.wait(0.1)
            i += 1
        sys.stdout.write("\r" + " " * 40 + "\r")
        sys.stdout.flush()

    spinner_thread = threading.Thread(target=spin, daemon=True)
    spinner_thread.start()

    try:
        response = _call_claude(prompt, api_key)
        stop_spinner.set()
        spinner_thread.join()
        _render_response(response)
        return 0
    except RuntimeError as e:
        stop_spinner.set()
        spinner_thread.join()
        print(C.error(f"AI request failed: {e}"))
        return 1
    except KeyboardInterrupt:
        stop_spinner.set()
        spinner_thread.join()
        print(f"\n{C.warn('AI request cancelled.')}\n")
        return 130


AI_COMMANDS = {
    "ai": cmd_ai,
}
