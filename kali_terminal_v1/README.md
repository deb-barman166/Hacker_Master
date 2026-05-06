# 🐉 Kali Linux Terminal — Version 1.0.0

```
  ██╗  ██╗ █████╗ ██╗      ██╗    ████████╗███████╗██████╗
  ██║ ██╔╝██╔══██╗██║      ██║    ╚══██╔══╝██╔════╝██╔══██╗
  █████╔╝ ███████║██║      ██║       ██║    █████╗  ██████╔╝
  ██╔═██╗ ██╔══██║██║      ██║       ██║    ██╔══╝  ██╔══██╗
  ██║  ██╗██║  ██║███████╗ ██║       ██║   ███████╗██║  ██║
  ╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═╝       ╚═╝   ╚══════╝╚═╝  ╚═╝
              TERMINAL v1.0.0 — Python-Powered Hacker Terminal
```

> **Full Python-based Kali Linux terminal simulator** — upgrades v2 with AI, multi-theme engine, crypto suite, network tools, persistent state, live monitor, matrix animation, and much more.

---

## ⚡ What's New in v1.0

| Feature                    | v1.0 |
|----------------------------|------|
| Themes                     | ✅ 5 themes (Kali/Dracula/Matrix/Ocean/Blood) |
| AI Assistant (Claude)      | ✅ Full cybersec Q&A + code gen |
| TCP Port Scanner           | ✅ Multi-threaded, with service detection |
| Ping Sweep                 | ✅ CIDR subnet sweep |
| DNS Lookup                 | ✅ All record types |
| Banner Grab                | ✅ TCP service banner |
| HTTP Header Inspector      | ✅ Full response headers |
| Hash Engine                | ✅ MD5/SHA1/SHA256/SHA512/BLAKE2/all |
| Encode/Decode              | ✅ Base64/URL/Hex/Binary/HTML/Morse |
| Caesar Cipher              | ✅ + brute force mode |
| XOR Encryption             | ✅ |
| Password Generator         | ✅ Cryptographically secure |
| Password Strength Checker  | ✅ 9-point analysis |
| Persistent Aliases         | ✅ Saved to disk |
| Bookmarks                  | ✅ Named directory shortcuts |
| Notes                      | ✅ Timestamped sticky notes |
| TODO Manager               | ✅ With priorities |
| Live System Monitor        | ✅ Real-time CPU/RAM/disk |
| Matrix Animation           | ✅ Full terminal matrix rain |
| Tree View                  | ✅ Colored directory tree |
| Calculator                 | ✅ Safe Python math eval |
| Weather                    | ✅ ASCII weather (wttr.in) |
| Git-Aware Prompt           | ✅ Branch + dirty + ahead/behind |
| Time in Prompt             | ✅ Optional |
| Preferences System         | ✅ Persistent JSON prefs |
| Session Persistence        | ✅ ~/.kali_terminal/ |
| Boot Animation             | ✅ Fake boot sequence |

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run
python3 main.py
```

---

## 📦 Dependencies

```
prompt_toolkit  — interactive REPL, tab completion, key bindings
psutil          — CPU, RAM, disk, network metrics
```

Optional (auto-detected):
```
dnspython       — full DNS record type support (pip install dnspython)
```

---

## 🎨 Themes

```bash
theme               # list all themes
theme dracula       # switch to Dracula
theme matrix        # go full hacker
theme ocean         # cool blues
theme blood         # aggressive red
theme kali          # classic (default)
```

---

## 🤖 AI Assistant

Powered by Claude (Anthropic). Requires a free API key.

```bash
# Setup (one time)
ai --setup sk-ant-api-key-here
# or
export ANTHROPIC_API_KEY=sk-ant-your-key

# Use
ai how does a SQL injection work?
ai explain nmap -sV -p- -A 192.168.1.1
ai code python bruteforce FTP login
ai ctf I found an LFI vulnerability in a PHP app
```

Get your free key at: https://console.anthropic.com

---

## 🌐 Network Tools

```bash
scan 192.168.1.1                    # scan common ports
scan 192.168.1.1 1 65535            # full port scan
scan 192.168.1.1 1 1000 --threads 500  # faster with more threads
ping_sweep 192.168.1.0/24          # who's alive?
dns google.com MX                   # MX records
dns github.com A                    # A records
myip                                # all my IPs
banner_grab 192.168.1.1 22          # SSH banner
http_headers https://example.com    # HTTP headers
```

---

## 🔒 Crypto Suite

```bash
hash sha256 password123             # hash text
hash all mysecret                   # all algorithms at once
hash md5 --file /etc/passwd         # hash a file
encode base64 Hello World           # encode
decode base64 SGVsbG8gV29ybGQ=      # decode
encode hex "flag{secret}"           # hex encode
encode morse SOS                    # Morse code
caesar 13 Hello World               # ROT13
caesar 3 Hello --brute              # try all 26 shifts
xor secret 48656c6c6f               # XOR
passgen 32                          # 32-char secure password
passgen 64 --count 5                # 5 passwords of length 64
pwdcheck MyP@ssw0rd123!             # strength analysis
```

---

## 📌 Bookmarks

```bash
bookmark add projects      # save current dir as 'projects'
bookmark                   # list all bookmarks
bookmark go projects       # jump to 'projects'
bookmark del projects      # remove it
bm go home                 # shorthand
```

---

## 📝 Notes & TODO

```bash
# Notes
note add Remember to update nmap scripts
note list
note del 1

# TODO
todo add --high Fix the buffer overflow
todo add Write pentest report
todo list
todo done 1
todo del 2
todo clear                 # remove completed tasks
```

---

## ⚙️ Preferences

```bash
set                                   # list all prefs
set show_git_branch true              # git branch in prompt
set show_time_in_prompt true          # HH:MM:SS in prompt
set vi_mode true                      # vim keybindings
set boot_animation false              # skip boot sequence
```

---

## 🌲 Other Commands

```bash
tree                    # directory tree (current dir)
tree /etc --depth 2     # tree with max depth 2
monitor                 # live CPU/RAM/disk monitor (Ctrl+C to stop)
matrix                  # matrix rain animation (Ctrl+C to exit)
calc 2**32              # calculator
calc sqrt(2) * pi       # math expressions
weather London          # ASCII weather
weather                 # weather for your location
sysinfo                 # full system panel
cheatsheet              # all sections
cheatsheet network      # network section only
tips                    # random pro-tip
tips all                # all tips
about                   # about this terminal
```

---

## 📁 Config Files

All config is stored in `~/.kali_terminal/`:

```
~/.kali_terminal/
├── theme.json        # active theme
├── aliases.json      # persistent aliases
├── bookmarks.json    # named dir bookmarks
├── notes.json        # sticky notes
├── todos.json        # task list
└── prefs.json        # terminal preferences
~/.kali_terminal_history  # command history
```

---

## 🗂️ Project Structure

```
kali_terminal_v1/
├── main.py                   # entry point
├── requirements.txt
├── README.md
├── core/
│   ├── terminal.py           # REPL engine + dispatch
│   ├── executor.py           # subprocess runner
│   └── completer.py          # smart tab completion
├── ui/
│   ├── banner.py             # boot banner + animation
│   ├── prompt.py             # git-aware prompt builder
│   └── theme.py              # 5-theme engine
├── commands/
│   ├── builtins.py           # cd, history, sysinfo, theme, alias, bookmark,
│   │                         # note, todo, tree, monitor, matrix, calc, weather, help
│   ├── network.py            # scan, ping_sweep, dns, myip, banner_grab, http_headers
│   ├── crypto.py             # hash, encode, decode, caesar, xor, passgen, pwdcheck
│   └── ai.py                 # AI assistant (Claude)
└── utils/
    ├── config.py             # persistent config / JSON storage
    └── formatters.py         # table, bar, panel, tree_view renderers
```

---

## 🎯 Built for

- Kali Linux users
- Cybersecurity students (CEH, OSCP, CTF)
- Python developers
- AI & hacking enthusiasts
- Anyone who wants a cool terminal

---

*Made with ❤️ and Python — v1.0.0*
