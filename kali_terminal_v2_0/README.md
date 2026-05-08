# 🕶️ Kali Terminal v2 - Masterpiece Edition

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

**The most powerful Kali Linux Terminal Simulator with AI Integration**

---

## 🎯 Overview

Kali Terminal v2 is a professional-grade CLI tool that mimics the Kali Linux terminal experience with advanced AI integration. It provides 100+ cybersecurity commands, multiple AI backends support, and a highly customizable interface.

## ✨ Features

### 🤖 AI Integration
- **Local AI**: Ollama with all open-source models (Llama2, Mistral, CodeLlama, etc.)
- **Cloud AI**: OpenAI (GPT-4, GPT-3.5), Anthropic (Claude), Google (Gemini)
- **Toggle Control**: AI features can be enabled/disabled on demand
- **Multiple Commands**: AI chat, code explanation, security analysis, help generation

### 🛡️ Cybersecurity Tools

#### Network Reconnaissance
- `ip-info` - IP lookup and geolocation
- `netstat-enhanced` - Network connections analysis
- `port-scan` - Port scanning with 100+ service detection
- `subnet-calc` - CIDR subnet calculator
- `dns-lookup` - DNS resolution
- `whois-lookup` - Domain information
- `traceroute` - Network path tracing
- `ping-sweep` - Live host discovery

#### Cryptography
- `hash` - Generate MD5, SHA1, SHA256, SHA512, SHA3, BLAKE2
- `encode` / `decode` - Base64, URL, Hex, HTML, Unicode, Binary, Octal
- `rot13` - ROT13 cipher
- `caesar` - Caesar cipher encryption
- `hash-identify` - Hash format detection
- `hash-cracker` - Hash cracking with dictionaries
- `ssl-check` - SSL/TLS certificate analysis

#### Security Utilities
- `gen-pass` - Secure password generator with entropy
- `random-uuid` - UUID generation
- `random-mac` - MAC address generator
- `sanitize` - Data sanitization
- `cypher` / `decypher` - Caesar, Vigenere, XOR, ROT47

#### Forensics
- `hexdump` - Hexadecimal dump
- `strings` - String extraction
- `file-analysis` - Comprehensive file analysis
- `entropy` - Entropy calculation with visual map
- `xor-data` - XOR data transformation
- `binwalk-extract` - Binary analysis

#### Web Security
- `http-headers` - HTTP header analysis with security rating
- `http-post` - HTTP POST requests
- `sql-test` - SQL injection testing
- `xss-test` - XSS vulnerability testing
- `dir-scan` - Directory brute forcing
- `subdomain-enum` - Subdomain enumeration
- `cert-check` - SSL certificate inspection

### 🎨 User Interface

#### Themes (8 Built-in)
- `kali` - Classic Kali Linux green
- `hacker` - Matrix green on black
- `matrix` - Digital rain effect
- `cyberpunk` - Neon cyberpunk colors
- `nord` - Nord dark theme
- `dracula` - Dracula purple theme
- `monokai` - Monokai syntax colors
- `gruvbox` - Gruvbox retro theme

#### Prompt Styles
- `minimal` - Clean and simple
- `detailed` - Full path and info
- `powerline` - Powerline-style prompt
- `kali` - Kali Linux style

### 🔧 Additional Features

- **Tab Completion**: Intelligent command completion
- **Command History**: Full command history with search
- **Aliases**: Custom command aliases
- **Session Management**: Save and load terminal sessions
- **Plugin System**: Extend functionality with plugins
- **Environment Variables**: Variable support in commands
- **Multi-line Commands**: Command chaining with `;`
- **Pipe Support**: Unix-style piping

## 🚀 Installation

### Prerequisites
```bash
Python 3.8 or higher
pip
```

### Install from Source
```bash
# Clone the repository
git clone https://github.com/kaliterminal/v2.git
cd kali-terminal-v2

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Quick Start
```bash
# Run with default settings
python main.py

# Run without banner
python main.py --no-banner

# Start with specific theme
python main.py --theme cyberpunk

# Enable AI with Ollama
python main.py --ai-backend ollama --ai-model llama2

# Enable AI with OpenAI
python main.py --ai-api-key YOUR_API_KEY --ai-backend openai
```

## 📋 Usage

### AI Commands
```bash
# Enable AI
ai-enable

# Disable AI
ai-disable

# Configure AI backend
ai-config --backend ollama --model llama2

# Chat with AI
ai-chat Explain SQL injection vulnerabilities

# Analyze code
ai-analyze /path/to/file.py

# Explain security concept
ai-explain What is XSS and how to prevent it
```

### Network Commands
```bash
# IP lookup
ip-info 8.8.8.8

# Port scan
port-scan 192.168.1.1 -r 1-1000

# Subnet calculation
subnet-calc 192.168.1.0/24

# DNS lookup
dns-lookup example.com

# WHOIS lookup
whois example.com
```

### Cryptography
```bash
# Generate hash
hash sha256 "Hello World"

# Encode base64
encode base64 "Hello"

# Hash identification
hash-identify 5d41402abc4b2a76b9719d911017c592

# SSL check
ssl-check google.com
```

### File Analysis
```bash
# Hex dump
hexdump /bin/ls

# String extraction
strings /bin/ls

# File analysis
file-analysis /path/to/file

# Entropy calculation
entropy /path/to/file
```

## ⚙️ Configuration

### AI Configuration
```bash
# Ollama (Local)
ai-config --backend ollama --base-url http://localhost:11434 --model llama2

# OpenAI
ai-config --backend openai --api-key YOUR_KEY --model gpt-4

# Anthropic
ai-config --backend anthropic --api-key YOUR_KEY --model claude-3

# Gemini
ai-config --backend gemini --api-key YOUR_KEY --model gemini-pro
```

### Theme Configuration
```bash
# List available themes
theme --list

# Switch theme
theme cyberpunk

# Set default theme
theme --set hacker
```

### Alias Management
```bash
# List aliases
alias --list

# Create alias
alias ll="ls -la"

# Remove alias
unalias ll
```

## 🛠️ Development

### Project Structure
```
kali_terminal_v2/
├── main.py              # Entry point
├── core/
│   ├── terminal.py      # Main terminal engine
│   ├── config.py        # Configuration management
│   ├── executor.py      # Command execution
│   ├── completer.py     # Tab completion
│   ├── plugin_system.py # Plugin management
│   └── session_manager.py # Session handling
├── commands/
│   ├── network_tools.py
│   ├── crypto_tools.py
│   ├── security_tools.py
│   ├── forensics_tools.py
│   ├── web_tools.py
│   ├── ai_commands.py
│   ├── builtins.py
│   ├── aliases.py
│   ├── system_tools.py
│   ├── text_tools.py
│   └── productivity.py
├── ai_modules/
│   └── ai_engine.py     # AI integration
├── ui/
│   ├── banner.py        # Boot banner
│   ├── theme.py         # Theme system
│   ├── themes/          # Theme definitions
│   └── prompt.py        # Prompt builder
└── utils/
    └── __init__.py
```

## 📜 Commands Reference

### Built-in Commands
| Command | Description |
|---------|-------------|
| `help` | Show help information |
| `clear` / `cls` | Clear screen |
| `cd` | Change directory |
| `pwd` | Print working directory |
| `history` | Show command history |
| `alias` | Manage aliases |
| `theme` | Switch themes |
| `calc` | Calculator |
| `date` | Show current date/time |

### AI Commands
| Command | Description |
|---------|-------------|
| `ai-enable` | Enable AI features |
| `ai-disable` | Disable AI features |
| `ai-config` | Configure AI backend |
| `ai-chat` | Chat with AI |
| `ai-explain` | Get explanations |
| `ai-analyze` | Analyze code/files |
| `ai-help` | Get AI help |

## 🔒 Security Notice

This tool is designed for:
- **Educational purposes**
- **Authorized security testing**
- **Legal penetration testing**
- **Security research**

⚠️ **Disclaimer**: Unauthorized access to computer systems is illegal. Always obtain proper authorization before testing any system.

## 📄 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit Pull Requests.

## 📧 Contact

- GitHub: [kaliterminal/v2](https://github.com/kaliterminal/v2)
- Email: security@kaliterminal.local

---

**Version 2.0.0 - Masterpiece Edition**