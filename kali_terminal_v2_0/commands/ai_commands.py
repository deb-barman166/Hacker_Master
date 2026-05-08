"""
commands/ai_commands.py — AI integration commands (v2.0 Masterpiece).

Commands:
  - ai-enable: Enable AI features
  - ai-disable: Disable AI features
  - ai-config: Configure AI settings
  - ai: Chat with AI
  - ai-explain: Get AI explanation
  - ai-analyze: Analyze with AI
  - ai-help: Show AI help
"""

import os
import sys
from typing import Optional

from ui.theme import Colors

C = Colors


def _get_ai_engine(terminal):
    """Get the AI engine from terminal."""
    if hasattr(terminal, 'ai_engine') and terminal.ai_engine:
        return terminal.ai_engine
    else:
        print(C.error("AI not enabled. Use 'ai-enable' to enable AI features."))
        return None


def cmd_ai_enable(args: list, state: dict, terminal=None) -> int:
    """Enable AI features. Usage: ai-enable [backend] [model]"""
    if not terminal:
        print(C.error("Terminal context not available"))
        return 1

    backend = args[0] if args else "ollama"
    model = args[1] if len(args) > 1 else None

    print(f"\n{C.BLUE}{'='*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}AI ENABLER{C.RESET}")
    print(f"{C.BLUE}{'='*65}{C.RESET}\n")

    try:
        from ai_modules.ai_engine import AIEngine

        # Determine backend
        if backend == "ollama":
            print(f"  {C.YELLOW}Initializing Ollama (local AI)...{C.RESET}")
            model = model or os.environ.get("OLLAMA_MODEL", "llama3.2")
        elif backend == "openai":
            print(f"  {C.YELLOW}Initializing OpenAI...{C.RESET}")
            model = model or "gpt-4"
        elif backend == "anthropic":
            print(f"  {C.YELLOW}Initializing Anthropic Claude...{C.RESET}")
            model = model or "claude-3-opus-20240229"
        elif backend == "gemini":
            print(f"  {C.YELLOW}Initializing Google Gemini...{C.RESET}")
            model = model or "gemini-pro"
        else:
            print(C.error(f"Unknown backend: {backend}"))
            print(C.info("Available: ollama, openai, anthropic, gemini"))
            return 1

        terminal.ai_engine = AIEngine(backend=backend, model=model)
        terminal.state["ai_backend"] = backend
        terminal.state["ai_model"] = model
        terminal.state["ai_enabled"] = True

        if terminal.ai_engine.is_connected:
            print(f"\n  {C.GREEN}{C.BOLD}[+] AI Enabled Successfully!{C.RESET}")
            print(f"  {C.CYAN}Backend{C.RESET}: {C.WHITE}{backend}{C.RESET}")
            print(f"  {C.CYAN}Model{C.RESET}:  {C.WHITE}{model}{C.RESET}")
        else:
            print(f"\n  {C.YELLOW}AI initialized but not connected.")
            print(f"  Make sure {backend} is running and accessible.{C.RESET}")

    except ImportError as e:
        print(C.error(f"Missing dependency: {e}"))
        print(C.info("Install required packages: pip install openai anthropic google-generativeai"))
        return 1
    except Exception as e:
        print(C.error(f"Failed to enable AI: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*65}{C.RESET}\n")
    return 0


def cmd_ai_disable(args: list, state: dict, terminal=None) -> int:
    """Disable AI features. Usage: ai-disable"""
    if not terminal:
        print(C.error("Terminal context not available"))
        return 1

    terminal.state["ai_enabled"] = False
    terminal.ai_engine = None

    print(C.success("AI disabled successfully."))
    return 0


def cmd_ai_config(args: list, state: dict, terminal=None) -> int:
    """Configure AI settings. Usage: ai-config [key] [value]"""
    if not terminal:
        print(C.error("Terminal context not available"))
        return 1

    if not args:
        # Show current config
        print(f"\n{C.BLUE}{'='*65}{C.RESET}")
        print(f"  {C.BOLD}{C.WHITE}AI CONFIGURATION{C.RESET}")
        print(f"{C.BLUE}{'='*65}{C.RESET}\n")

        print(f"  {C.CYAN}Status{C.RESET}:    {C.GREEN if terminal.state.get('ai_enabled') else C.RED}{'Enabled' if terminal.state.get('ai_enabled') else 'Disabled'}{C.RESET}")
        print(f"  {C.CYAN}Backend{C.RESET}:   {C.WHITE}{terminal.state.get('ai_backend', 'none')}{C.RESET}")
        print(f"  {C.CYAN}Model{C.RESET}:     {C.WHITE}{terminal.state.get('ai_model', 'N/A')}{C.RESET}")

        if terminal.ai_engine:
            stats = terminal.ai_engine.get_stats()
            print(f"\n  {C.YELLOW}{C.BOLD}Usage Stats:{C.RESET}")
            print(f"  {C.CYAN}Connected{C.RESET}:  {C.GREEN if stats.get('is_connected') else C.RED}{stats.get('is_connected')}{C.RESET}")
            print(f"  {C.CYAN}Messages{C.RESET}:  {C.WHITE}{stats.get('total_messages', 0)}{C.RESET}")
            print(f"  {C.CYAN}History{C.RESET}:   {C.WHITE}{stats.get('conversation_length', 0)} messages{C.RESET}")

        print(f"\n  {C.GRAY}Configuration Options:{C.RESET}")
        print(f"    {C.CYAN}ai-config backend <name>{C.RESET}  - Set backend (ollama/openai/anthropic/gemini)")
        print(f"    {C.CYAN}ai-config model <name>{C.RESET}    - Set model name")
        print(f"    {C.CYAN}ai-config api-key <key>{C.RESET}    - Set API key")
        print(f"    {C.CYAN}ai-config temp <0-2>{C.RESET}       - Set temperature")
        print(f"    {C.CYAN}ai-config clear{C.RESET}             - Clear conversation history")

        print(f"\n{C.BLUE}{'='*65}{C.RESET}\n")
        return 0

    key = args[0].lower()
    value = args[1] if len(args) > 1 else None

    if key == "backend":
        if value:
            terminal.state["ai_backend"] = value
            print(C.success(f"Backend set to: {value}"))
        else:
            print(C.error("Please specify a backend: ollama, openai, anthropic, gemini"))

    elif key == "model":
        if value:
            terminal.state["ai_model"] = value
            print(C.success(f"Model set to: {value}"))
        else:
            print(C.error("Please specify a model name"))

    elif key == "api-key":
        if value:
            os.environ["AI_API_KEY"] = value
            print(C.success("API key set"))

    elif key == "temp" or key == "temperature":
        if value:
            try:
                temp = float(value)
                if terminal.ai_engine:
                    terminal.ai_engine.config.temperature = temp
                print(C.success(f"Temperature set to: {temp}"))
            except ValueError:
                print(C.error("Temperature must be a number between 0 and 2"))
        else:
            print(C.error("Please specify a temperature value"))

    elif key == "clear":
        if terminal.ai_engine:
            terminal.ai_engine.clear_history()
        else:
            print(C.warn("No AI engine to clear"))

    else:
        print(C.error(f"Unknown configuration option: {key}"))

    return 0


def cmd_ai_chat(args: list, state: dict, terminal=None) -> int:
    """Chat with AI. Usage: ai <prompt>"""
    if not args:
        print(C.info("Usage: ai <prompt>"))
        print(C.info("Example: ai explain SQL injection vulnerabilities"))
        return 0

    prompt = " ".join(args)

    # Check if this is a special command
    if prompt.lower().startswith("explain "):
        return cmd_ai_explain([prompt[8:]], state, terminal)
    elif prompt.lower().startswith("analyze "):
        return cmd_ai_analyze([prompt[8:]], state, terminal)

    engine = _get_ai_engine(terminal)
    if not engine:
        return 1

    print(f"\n{C.CYAN}{C.BOLD}You:{C.RESET} {prompt}\n")

    print(f"{C.GREEN}{C.BOLD}AI:{C.RESET} ", end="", flush=True)

    response = engine.chat(prompt, stream=True)

    print(f"\n")
    return 0


def cmd_ai_explain(args: list, state: dict, terminal=None) -> int:
    """Get AI explanation of a security concept. Usage: ai-explain <concept>"""
    if not args:
        print(C.info("Usage: ai-explain <concept>"))
        print(C.info("Examples:"))
        print(C.info("  ai-explain SQL injection"))
        print(C.info("  ai-explain buffer overflow"))
        print(C.info("  ai-explain XSS attack"))
        return 0

    concept = " ".join(args)
    engine = _get_ai_engine(terminal)

    if not engine:
        return 1

    prompt = f"""Explain the following cybersecurity concept in detail:
Concept: {concept}

Please provide:
1. What it is
2. How it works
3. Real-world examples
4. How to detect it
5. How to prevent it
6. Security testing considerations

Be educational and thorough."""

    print(f"\n{C.CYAN}{C.BOLD}Concept:{C.RESET} {concept}\n")
    print(f"{C.GREEN}{C.BOLD}Explanation:{C.RESET}\n")

    response = engine.chat(prompt, stream=True)

    print()
    return 0


def cmd_ai_analyze(args: list, state: dict, terminal=None) -> int:
    """Analyze code or data with AI. Usage: ai-analyze <type> [content]"""
    if len(args) < 1:
        print(C.info("Usage: ai-analyze <type> [content]"))
        print(C.info("Types: code, hash, network, malware"))
        print(C.info("Example: ai-analyze code function vulnerable_code()"))
        return 0

    analyze_type = args[0].lower()
    content = " ".join(args[1:]) if len(args) > 1 else ""

    engine = _get_ai_engine(terminal)
    if not engine:
        return 1

    prompts = {
        "code": f"""Analyze the following code for security vulnerabilities:

```{content}
```

Provide:
1. Identified vulnerabilities (with severity)
2. Risk assessment
3. Exploitation scenarios
4. Remediation recommendations""",

        "hash": f"""Analyze this hash:

Hash: {content}

Provide:
1. Likely hash type
2. Possible plaintext
3. Cracking recommendations
4. Prevention strategies""",

        "network": f"""Analyze this network data:

{content}

Provide:
1. Protocol identification
2. Notable patterns
3. Security concerns
4. Investigation recommendations""",

        "malware": f"""Analyze this for potential malware indicators:

{content[:1000]}

Provide:
1. Suspicious patterns
2. IOCs (Indicators of Compromise)
3. Behavioral analysis
4. Recommended actions"""
    }

    if analyze_type not in prompts:
        print(C.error(f"Unknown analysis type: {analyze_type}"))
        print(C.info("Available types: code, hash, network, malware"))
        return 1

    prompt = prompts[analyze_type]

    print(f"\n{C.CYAN}{C.BOLD}Analysis Type:{C.RESET} {analyze_type}\n")
    print(f"{C.GREEN}{C.BOLD}Results:{C.RESET}\n")

    response = engine.chat(prompt, stream=True)

    print()
    return 0


def cmd_ai_help(args: list, state: dict, terminal=None) -> int:
    """Show AI help and usage. Usage: ai-help"""
    print(f"""
{C.BLUE}{'='*65}{C.RESET}
  {C.BOLD}{C.WHITE}AI INTEGRATION HELP{C.RESET}
{C.BLUE}{'='*65}{C.RESET}

  {C.GREEN}Available Commands:{C.RESET}

    {C.CYAN}ai-enable [backend] [model]{C.RESET}
        Enable AI features with specified backend.
        Backends: ollama (local), openai, anthropic, gemini

    {C.CYAN}ai-disable{C.RESET}
        Disable AI features.

    {C.CYAN}ai-config [key] [value]{C.RESET}
        Configure AI settings.
        Options: backend, model, api-key, temperature, clear

    {C.CYAN}ai <prompt>{C.RESET}
        Chat directly with AI.
        Example: ai explain the OWASP Top 10

    {C.CYAN}ai-explain <concept>{C.RESET}
        Get detailed explanation of security concept.
        Example: ai-explain XSS attack

    {C.CYAN}ai-analyze <type> [content]{C.RESET}
        Analyze code, hashes, network data.
        Types: code, hash, network, malware

  {C.YELLOW}Setup Instructions:{C.RESET}

    {C.GRAY}Local (Ollama):{C.RESET}
      1. Install Ollama: curl -fsSL https://ollama.com/install.sh
      2. Pull model: ollama pull llama3.2
      3. Start server: ollama serve
      4. Enable: ai-enable ollama

    {C.GRAY}OpenAI:{C.RESET}
      1. Get API key from https://platform.openai.com
      2. Set key: export OPENAI_API_KEY=sk-...
      3. Enable: ai-enable openai gpt-4

    {C.GRAY}Anthropic Claude:{C.RESET}
      1. Get API key from https://console.anthropic.com
      2. Set key: export ANTHROPIC_API_KEY=sk-ant-...
      3. Enable: ai-enable anthropic claude-3-opus

    {C.GRAY}Google Gemini:{C.RESET}
      1. Get API key from https://aistudio.google.com
      2. Set key: export GEMINI_API_KEY=...
      3. Enable: ai-enable gemini gemini-pro

  {C.MAGENTA}Use Cases:{C.RESET}

    {C.CYAN}ai explain SQL injection{C.RESET}        - Learn about vulnerabilities
    {C.CYAN}ai-analyze code <code>{C.RESET}          - Analyze code security
    {C.CYAN}ai pentest 192.168.1.1 recon{C.RESET}   - Get pentest guidance
    {C.CYAN}ai Hash: 5f4dcc3b5aa765d61d8327deb882cf99{C.RESET} - Analyze hash

{C.BLUE}{'='*65}{C.RESET}
""")
    return 0