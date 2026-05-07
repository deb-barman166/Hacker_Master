# 🐉 KaliTerminal v2 — MASTERPIECE Edition

```
██╗  ██╗ █████╗ ██╗     ██╗    ████████╗███████╗██████╗ ███╗   ███╗
██║ ██╔╝██╔══██╗██║     ██║    ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║
█████╔╝ ███████║██║     ██║       ██║   █████╗  ██████╔╝██╔████╔██║
██╔═██╗ ██╔══██║██║     ██║       ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║
██║  ██╗██║  ██║███████╗██║       ██║   ███████╗██║  ██║██║ ╚═╝ ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝       ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝
                PYTHON v2  ·  MASTERPIECE EDITION
```

> A professional, full-featured **Python-based Cybersecurity CLI terminal** that feels like real Kali Linux — with an optional **dual-mode AI assistant** (local Ollama or any cloud API).

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install prompt-toolkit psutil

# 2. Run
python main.py

# 3. Optional: start with a theme
python main.py --theme cyberpunk
python main.py --fast        # skip animation
```

---

## ✨ Features

### 🖥️ Terminal Experience
| Feature | Details |
|---|---|
| **Real Kali Linux feel** | `user@host:path ❯` prompt with git branch, venv, AI mode |
| **Tab completion** | Commands, subcommands, file paths, ~/ expansion |
| **History** | Persistent file-backed history, Ctrl+R search |
| **Vi mode** | Enable with `set vi_mode true` |
| **Auto-suggest** | Ghost text from history |
| **Pipe support** | `cmd1 \| cmd2 \| cmd3` |
| **Redirects** | `cmd > file`, `cmd >> file`, `cmd < file` |
| **Chains** | `cmd1; cmd2`, `cmd1 && cmd2`, `cmd1 \|\| cmd2` |
| **Background** | `cmd &` |
| **Variables** | `export VAR=value` |
| **Source** | `source script.sh` |
| **Aliases** | Persistent across sessions |
| **Bookmarks** | Save dirs, `cd @name` |

### 🎨 Themes (7)
```
kali       — Classic red & blue (default)
matrix     — Pure green hacker
cyberpunk  — Neon yellow & purple
dracula    — Dark purple & pink
midnight   — Deep ocean blue
blood      — Dark deep red
ocean      — Teal & seafoam
```
Switch: `theme <name>`

### 🔐 Security Toolkit

#### Network
| Command | Description |
|---|---|
| `port-scan <host> [spec]` | TCP scanner with service ID, banner grab, threading |
| `dns-lookup <host> [type]` | A / AAAA / MX / NS / TXT / CNAME / SOA |
| `whois <domain\|ip>` | Full WHOIS lookup |
| `ip-info` | Network interfaces, MACs, TX/RX stats |
| `ip-geo <ip>` | Geolocation — country, city, ISP, lat/lon |
| `ssl-check <host>` | Certificate info, expiry, SANs, cipher suite |
| `http-headers <url>` | Response headers + security header analysis |
| `netstat-enhanced` | Active connections, listening ports, process names |

#### Crypto & Encoding
| Command | Description |
|---|---|
| `hash <file> [algo]` | md5 / sha1 / sha256 / sha512 / sha3 / blake2 / all |
| `hash-text <text>` | Hash strings directly |
| `encode <text> [fmt]` | base64 / base32 / url / hex / binary / rot13 / morse / html |
| `decode <text> [fmt]` | Same formats |
| `jwt-decode <token>` | Header + payload inspection, expiry check, security warnings |

#### Security
| Command | Description |
|---|---|
| `password-gen` | Cryptographically secure. PIN, passphrase, or custom charset |
| `password-audit <pw>` | Entropy, crack time estimates, pattern detection |
| `vuln-search <term>` | CVE search via CIRCL API |
| `cheatsheet <tool>` | nmap / sqlmap / hydra / john / hashcat / metasploit / gobuster / curl / netcat / burp / wireshark |

#### System
| Command | Description |
|---|---|
| `disk-usage [path]` | Visual tree with size bars |
| `proc-monitor` | top / search / kill / tree |
| `sysinfo` | Full system info with resource bars |

### 🤖 AI Assistant — DUAL MODE

> **AI is OFF by default.** You must explicitly enable it.

#### Local Mode (Ollama — 100% Offline)
```bash
# 1. Install Ollama: https://ollama.com
# 2. Start it:
ollama serve

# 3. Pull a model:
ollama pull llama3.2       # 3B fast
ollama pull mistral        # 7B strong
ollama pull codellama      # code specialist

# 4. Configure in KaliTerminal:
ai mode local
ai on
```

#### Cloud Mode (Any API Key)
Supported providers:
- **Anthropic** — Claude Opus, Sonnet, Haiku
- **OpenAI** — GPT-4o, GPT-4o-mini
- **Google** — Gemini 1.5 Flash/Pro
- **Groq** — Llama 3.3 70B (ultra-fast, free tier)
- **Mistral AI** — Mistral Large, Small
- **Cohere** — Command R+

```bash
# Interactive wizard:
ai setup

# Or manual:
ai mode cloud
ai key groq YOUR_KEY_HERE    # Groq has a free tier!
ai on
```

#### AI Commands (when AI is ON)
```bash
ai <question>          # Ask the cybersecurity expert anything
ai explain nmap        # Explain a command or concept
ai code python scanner # Generate code
ai ctf <description>   # CTF challenge analysis
ai scan <nmap output>  # Analyze scan results
ai chat                # Multi-turn chat mode
ai models              # List available models
ai status              # Show current config
```

### 📝 Productivity
| Command | Description |
|---|---|
| `note add <text> [#tags]` | Quick notes with tags |
| `note list [tag]` | Browse notes |
| `todo add <task> [--priority]` | Task manager with priorities |
| `todo list` / `todo done <id>` | Manage tasks |
| `calc <expr>` | Scientific calculator (sin, sqrt, pi, KB, GB…) |
| `timer start\|stop\|lap\|countdown` | Stopwatch & countdown |

---

## 🗂 Project Structure

```
kali_terminal_v2/
├── main.py                  Entry point
├── requirements.txt
├── README.md
│
├── core/
│   ├── terminal.py          Main REPL engine
│   ├── completer.py         Tab completion
│   └── executor.py          System commands (pipe, redirect, bg)
│
├── ui/
│   ├── banner.py            Boot banner with live sysinfo
│   ├── prompt.py            Dynamic prompt builder
│   ├── theme.py             Theme engine + Colors class
│   └── themes/
│       └── __init__.py      7 color themes
│
├── commands/
│   ├── builtins.py          cd, pwd, clear, history, help, theme,
│   │                        alias, bookmark, cheatsheet, sysinfo
│   ├── network.py           port-scan, dns-lookup, whois, ip-geo,
│   │                        ssl-check, http-headers, netstat
│   ├── crypto.py            hash, encode, decode, jwt-decode
│   ├── security.py          password-gen, password-audit, vuln-search
│   ├── system.py            disk-usage, proc-monitor
│   ├── productivity.py      note, todo, calc, timer
│   └── ai_engine.py         AI dual-mode (Ollama + cloud APIs)
│
└── utils/
    └── config.py            Persistent config (~/.kali_terminal_v2/)
```

---

## ⚙️ Configuration

Settings stored in `~/.kali_terminal_v2/prefs.json`

```bash
# In terminal:
set theme cyberpunk
set vi_mode true
set show_time_prompt true
set fast_banner true
set complete_while_type true

# Show all settings:
set
```

---

## 🔑 API Key Storage

Keys stored locally in `~/.kali_terminal_v2/prefs.json` — **never sent anywhere except your chosen provider**.

```bash
ai key anthropic sk-ant-...
ai key openai sk-...
ai key groq gsk_...
ai key gemini AIza...
```

---

## 📋 Requirements

| Package | Required | Purpose |
|---|---|---|
| `prompt-toolkit` | ✅ Yes | REPL, tab completion, history |
| `psutil` | ⚡ Recommended | System stats, process monitor |

All other features use Python standard library only.

---

## 💡 Tips

```bash
# Pipe commands
port-scan 192.168.1.1 1-1024 | grep OPEN

# Hash + check
hash-text "admin:password" sha256

# Encode for CTF
encode "flag{secret}" base64
decode "ZmxhZ3tzZWNyZXR9" base64

# Password wordlist generation style
password-gen -l 12 -c 20 --no-ambiguous

# Bookmark important dirs
bookmark add tools /opt/tools
cd @tools

# Chain commands
dns-lookup target.com && ssl-check target.com

# AI-assisted CTF
ai ctf "Binary exploitation challenge, 64-bit ELF, stack canary enabled, PIE disabled"
```

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ by a cybersecurity enthusiast for the community.*
*Stay ethical. Hack responsibly. Keep learning.*
