"""
commands/security.py — Security tools for KaliTerminal v2.

Commands:
  password-gen    Cryptographically secure password generator
  password-audit  Password strength analyzer with crack-time estimates
  vuln-search     CVE / vulnerability search via NVD/CIRCL API
"""

import os
import math
import secrets
import string
import json
import urllib.request
import urllib.error
from datetime import datetime

from ui.theme import Colors

C = Colors

# ══════════════════════════════════════════════════════════════════════════════
#  PASSWORD GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

AMBIGUOUS  = "0O1lI"
SPECIAL    = "!@#$%^&*()_+-=[]{}|;:,.<>?"
WORDLIST   = [
    "correct","horse","battery","staple","apple","cloud","tiger","river",
    "ocean","mountain","thunder","falcon","rocket","cipher","matrix","pixel",
    "nexus","vertex","aurora","zenith","quasar","nebula","cosmos","vector",
    "shadow","phantom","echo","nova","storm","frost","vortex","pulse",
]


def cmd_password_gen(args: list, state: dict) -> int:
    """
    password-gen [options]
    -l <n>         length (default: 20)
    -c <n>         count (default: 1)
    --no-special   exclude special chars
    --no-ambiguous exclude ambiguous chars (0O1lI)
    --upper-only   uppercase only
    --lower-only   lowercase only
    --pin [n]      numeric PIN (default 6 digits)
    --phrase [n]   memorable passphrase (default 4 words)
    --passphrase   same as --phrase
    """
    length   = 20
    count    = 1
    upper    = True
    lower    = True
    digits   = True
    special  = True
    no_ambig = False
    pin_mode = False
    pin_len  = 6
    phrase   = False
    phrase_n = 4

    i = 0
    while i < len(args):
        a = args[i]
        if a in ("-l", "--length") and i+1 < len(args):
            length = int(args[i+1]); i += 2
        elif a in ("-c", "--count") and i+1 < len(args):
            count = int(args[i+1]); i += 2
        elif a == "--no-special":
            special = False; i += 1
        elif a == "--no-ambiguous":
            no_ambig = True; i += 1
        elif a == "--upper-only":
            lower = False; i += 1
        elif a == "--lower-only":
            upper = False; i += 1
        elif a in ("--pin",):
            pin_mode = True
            if i+1 < len(args) and args[i+1].isdigit():
                pin_len = int(args[i+1]); i += 2
            else:
                i += 1
        elif a in ("--phrase", "--passphrase"):
            phrase = True
            if i+1 < len(args) and args[i+1].isdigit():
                phrase_n = int(args[i+1]); i += 2
            else:
                i += 1
        else:
            try:
                if not a.startswith("-"):
                    length = int(a)
            except ValueError:
                pass
            i += 1

    length  = max(4, min(256, length))
    count   = max(1, min(50, count))

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}PASSWORD GENERATOR{C.RESET}")
    print(f"{C.BLUE}{'═'*65}{C.RESET}\n")

    if pin_mode:
        charset = string.digits
        print(f"  {C.GRAY}Mode: PIN ({pin_len} digits){C.RESET}\n")
        for n in range(count):
            pw = "".join(secrets.choice(charset) for _ in range(pin_len))
            print(f"  {C.GREEN}{C.BOLD}[{n+1}]{C.RESET}  {C.WHITE}{pw}{C.RESET}")
        print()
        return 0

    if phrase:
        print(f"  {C.GRAY}Mode: Passphrase ({phrase_n} words){C.RESET}\n")
        for n in range(count):
            words = [secrets.choice(WORDLIST) for _ in range(phrase_n)]
            sep   = secrets.choice(["-", ".", "_", "+", "#"])
            num   = secrets.randbelow(10000)
            pw    = sep.join(words) + str(num)
            entropy = math.log2(len(WORDLIST) ** phrase_n * 10000)
            print(f"  {C.GREEN}{C.BOLD}[{n+1}]{C.RESET}  {C.WHITE}{pw}{C.RESET}  "
                  f"{C.GRAY}({entropy:.0f} bits){C.RESET}")
        print()
        return 0

    # Build charset
    charset = ""
    if upper:
        charset += string.ascii_uppercase
    if lower:
        charset += string.ascii_lowercase
    if digits:
        charset += string.digits
    if special:
        charset += SPECIAL
    if no_ambig:
        charset = "".join(c for c in charset if c not in AMBIGUOUS)
    if not charset:
        charset = string.ascii_letters + string.digits

    # Entropy & strength
    entropy  = math.log2(len(charset)) * length
    strength = ("WEAK" if entropy < 40 else
                "FAIR" if entropy < 60 else
                "GOOD" if entropy < 80 else
                "STRONG" if entropy < 100 else "VERY STRONG")
    s_color  = (C.RED if strength == "WEAK" else
                C.ORANGE if strength == "FAIR" else
                C.YELLOW if strength == "GOOD" else
                C.GREEN)

    print(f"  {C.CYAN}Charset{C.RESET} : {len(charset)} chars  "
          f"  {C.CYAN}Length{C.RESET}: {length}  "
          f"  {C.CYAN}Entropy{C.RESET}: {C.BOLD}{entropy:.1f} bits{C.RESET}  "
          f"  {s_color}{C.BOLD}{strength}{C.RESET}\n")

    for n in range(count):
        # Ensure at least one char from each required set
        pw_chars = []
        if upper:
            pw_chars.append(secrets.choice(string.ascii_uppercase))
        if lower:
            pw_chars.append(secrets.choice(string.ascii_lowercase))
        if digits:
            pw_chars.append(secrets.choice(string.digits))
        if special:
            pw_chars.append(secrets.choice(SPECIAL))

        remaining = length - len(pw_chars)
        pw_chars += [secrets.choice(charset) for _ in range(remaining)]
        secrets.SystemRandom().shuffle(pw_chars)
        pw = "".join(pw_chars)

        print(f"  {C.GREEN}{C.BOLD}[{n+1}]{C.RESET}  {C.WHITE}{pw}{C.RESET}")

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}\n")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  PASSWORD AUDIT
# ══════════════════════════════════════════════════════════════════════════════

COMMON_PASSWORDS = {
    "password", "123456", "password1", "12345678", "qwerty", "abc123",
    "monkey", "1234567", "letmein", "trustno1", "dragon", "master",
    "sunshine", "princess", "welcome", "shadow", "superman", "michael",
    "football", "baseball", "iloveyou", "admin", "login", "root",
    "pass", "test", "guest", "123", "1234", "12345", "123456789",
}


def cmd_password_audit(args: list, state: dict) -> int:
    """password-audit <password> — Analyze password strength and estimate crack time."""
    if not args:
        print(C.info("Usage: password-audit <password>"))
        print(C.info("Example: password-audit MyP@ssw0rd!"))
        return 0

    pw = " ".join(args)

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}PASSWORD AUDIT{C.RESET}")
    print(f"{C.BLUE}{'═'*65}{C.RESET}\n")

    # Checks
    checks = {
        "Length ≥ 12":     len(pw) >= 12,
        "Length ≥ 20":     len(pw) >= 20,
        "Uppercase":        any(c.isupper() for c in pw),
        "Lowercase":        any(c.islower() for c in pw),
        "Digits":           any(c.isdigit() for c in pw),
        "Special chars":    any(c in SPECIAL for c in pw),
        "Not dictionary":   pw.lower() not in COMMON_PASSWORDS,
        "No repeats ≥3":    not _has_repeats(pw, 3),
        "No sequences":     not _has_sequence(pw),
        "No keyboard walk": not _has_keyboard_walk(pw),
    }

    pass_count = sum(1 for v in checks.values() if v)
    fail_count = len(checks) - pass_count

    for label, ok in checks.items():
        icon  = f"{C.GREEN}✔{C.RESET}" if ok else f"{C.RED}✗{C.RESET}"
        color = C.WHITE if ok else C.GRAY
        print(f"  {icon}  {color}{label}{C.RESET}")

    # Entropy calculation
    pool = 0
    if any(c.islower() for c in pw):
        pool += 26
    if any(c.isupper() for c in pw):
        pool += 26
    if any(c.isdigit() for c in pw):
        pool += 10
    if any(c in SPECIAL for c in pw):
        pool += len(SPECIAL)

    entropy = math.log2(pool) * len(pw) if pool > 0 else 0
    strength, s_color = _strength_label(entropy)

    print(f"\n  {C.CYAN}Length  {C.RESET}: {len(pw)}")
    print(f"  {C.CYAN}Pool    {C.RESET}: {pool} characters")
    print(f"  {C.CYAN}Entropy {C.RESET}: {C.BOLD}{entropy:.1f} bits{C.RESET}")
    print(f"  {C.CYAN}Strength{C.RESET}: {s_color}{C.BOLD}{strength}{C.RESET}")

    # Crack time estimates
    print(f"\n  {C.YELLOW}Estimated Crack Time (offline, GPU attack):{C.RESET}")
    combos = pool ** len(pw) if pool > 0 else 1

    GPU_SPEEDS = {
        "100M hashes/s  (MD5, single GPU)":   1e8,
        "10B hashes/s   (MD5, high-end rig)":  1e10,
        "1T hashes/s    (MD5, cluster)":        1e12,
        "1B hashes/s    (bcrypt ~cost12)":      1e3,  # bcrypt is slow
    }

    for desc, speed in GPU_SPEEDS.items():
        secs = combos / speed
        print(f"  {C.GRAY}{desc:<44}{C.RESET}  {_format_time(secs)}")

    if pw.lower() in COMMON_PASSWORDS:
        print(f"\n  {C.RED}⚠ CRITICAL: This is a KNOWN COMMON PASSWORD!{C.RESET}")
        print(f"  {C.RED}⚠ Any attacker will crack it in under 1 second using a dictionary.{C.RESET}")

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}\n")
    return 0


def _has_repeats(pw: str, n: int) -> bool:
    for i in range(len(pw) - n + 1):
        if len(set(pw[i:i+n])) == 1:
            return True
    return False


def _has_sequence(pw: str) -> bool:
    for i in range(len(pw) - 2):
        if ord(pw[i+1]) == ord(pw[i]) + 1 and ord(pw[i+2]) == ord(pw[i]) + 2:
            return True
    return False


def _has_keyboard_walk(pw: str) -> bool:
    rows = ["qwertyuiop", "asdfghjkl", "zxcvbnm", "1234567890"]
    pw_l = pw.lower()
    for row in rows:
        for i in range(len(row) - 2):
            if row[i:i+3] in pw_l or row[i:i+3][::-1] in pw_l:
                return True
    return False


def _strength_label(entropy: float) -> tuple:
    if entropy < 28:
        return "VERY WEAK",   C.RED
    if entropy < 36:
        return "WEAK",        C.RED
    if entropy < 60:
        return "FAIR",        C.YELLOW
    if entropy < 80:
        return "GOOD",        C.YELLOW
    if entropy < 100:
        return "STRONG",      C.GREEN
    return "VERY STRONG",     C.GREEN


def _format_time(secs: float) -> str:
    if secs < 1:
        return f"{C.RED}{C.BOLD}Instant{C.RESET}"
    if secs < 60:
        return f"{C.RED}{secs:.1f} seconds{C.RESET}"
    if secs < 3600:
        return f"{C.RED}{secs/60:.1f} minutes{C.RESET}"
    if secs < 86400:
        return f"{C.YELLOW}{secs/3600:.1f} hours{C.RESET}"
    if secs < 86400*365:
        return f"{C.YELLOW}{secs/86400:.1f} days{C.RESET}"
    if secs < 86400*365*1000:
        return f"{C.GREEN}{secs/(86400*365):.1f} years{C.RESET}"
    return f"{C.GREEN}{C.BOLD}Centuries+{C.RESET}"


# ══════════════════════════════════════════════════════════════════════════════
#  VULNERABILITY SEARCH
# ══════════════════════════════════════════════════════════════════════════════

def cmd_vuln_search(args: list, state: dict) -> int:
    """
    vuln-search <term>   — Search CVEs by keyword (uses CIRCL CVE API)
    vuln-search CVE-YYYY-XXXXX — Look up specific CVE
    """
    if not args:
        print(C.info("Usage: vuln-search <keyword|CVE-ID>"))
        print(C.info("Examples:"))
        print(C.info("  vuln-search apache log4j"))
        print(C.info("  vuln-search CVE-2021-44228"))
        print(C.info("  vuln-search openssh rce 2024"))
        return 0

    query = " ".join(args)

    print(f"\n{C.BLUE}{'═'*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}VULNERABILITY SEARCH: {query}{C.RESET}")
    print(f"{C.BLUE}{'═'*70}{C.RESET}\n")

    # Specific CVE lookup
    if query.upper().startswith("CVE-"):
        return _cve_lookup(query.upper())

    # Keyword search via CIRCL API
    encoded = urllib.parse.quote(query)
    url     = f"https://cve.circl.lu/api/search/{encoded}"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "KaliTerminal/2.0", "Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        results = data if isinstance(data, list) else data.get("results", [])

        if not results:
            print(C.warn(f"No CVEs found for '{query}'."))
            print(C.info("Try: https://nvd.nist.gov/vuln/search"))
            print(f"{C.BLUE}{'═'*70}{C.RESET}\n")
            return 0

        print(f"  {C.GRAY}Found {len(results)} results (showing top 10){C.RESET}\n")

        for cve in results[:10]:
            _print_cve_summary(cve)

    except urllib.error.URLError as e:
        print(C.error(f"Network error: {e.reason}"))
        print(C.info(f"Try: https://nvd.nist.gov/vuln/search?query={encoded}"))
        return 1
    except Exception as e:
        print(C.error(f"Search failed: {e}"))
        return 1

    print(f"{C.BLUE}{'═'*70}{C.RESET}\n")
    return 0


def _cve_lookup(cve_id: str) -> int:
    url = f"https://cve.circl.lu/api/cve/{cve_id}"
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "KaliTerminal/2.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())

        if not data:
            print(C.warn(f"{cve_id} not found in database."))
            return 1

        _print_cve_detail(data)

    except Exception as e:
        print(C.error(f"CVE lookup failed: {e}"))
        return 1
    return 0


def _print_cve_summary(cve: dict):
    cve_id   = cve.get("id", cve.get("CVE_ID", "N/A"))
    summary  = cve.get("summary", cve.get("Description", "No description"))[:100]
    cvss     = cve.get("cvss", cve.get("CVSS_score", 0)) or 0
    published= cve.get("Published", cve.get("published", ""))

    score_clr = _cvss_color(float(cvss))
    print(f"  {C.CYAN}{C.BOLD}{cve_id}{C.RESET}  "
          f"{score_clr}CVSS: {cvss}{C.RESET}  "
          f"{C.GRAY}{published[:10]}{C.RESET}")
    print(f"  {C.WHITE}{summary}...{C.RESET}\n")


def _print_cve_detail(cve: dict):
    cve_id   = cve.get("id", "N/A")
    summary  = cve.get("summary", "N/A")
    cvss     = float(cve.get("cvss", 0) or 0)
    published= cve.get("Published", "")
    modified = cve.get("Modified", "")
    refs     = cve.get("references", [])
    cwe      = cve.get("cwe", "N/A")

    score_clr = _cvss_color(cvss)
    sev = ("CRITICAL" if cvss >= 9.0 else
           "HIGH"     if cvss >= 7.0 else
           "MEDIUM"   if cvss >= 4.0 else
           "LOW"      if cvss > 0 else "N/A")

    def row(label, value, color=None):
        c = color or C.WHITE
        print(f"  {C.CYAN}{label:<20}{C.RESET}  {c}{value}{C.RESET}")

    row("CVE ID",       cve_id,         C.GREEN)
    row("CVSS Score",   f"{cvss:.1f} — {sev}", score_clr)
    row("CWE",          cwe)
    row("Published",    published[:19])
    row("Modified",     modified[:19])
    print()
    print(f"  {C.YELLOW}Description:{C.RESET}")
    # Word-wrap summary
    words = summary.split()
    line  = "  "
    for w in words:
        if len(line) + len(w) > 75:
            print(f"{C.WHITE}{line}{C.RESET}")
            line = "    "
        line += w + " "
    if line.strip():
        print(f"{C.WHITE}{line}{C.RESET}")

    if refs:
        print(f"\n  {C.YELLOW}References:{C.RESET}")
        for ref in refs[:5]:
            print(f"  {C.GRAY}• {ref}{C.RESET}")


def _cvss_color(score: float) -> str:
    if score >= 9.0:
        return C.RED + C.BOLD
    if score >= 7.0:
        return C.RED
    if score >= 4.0:
        return C.YELLOW
    return C.GREEN


# ══════════════════════════════════════════════════════════════════════════════
#  Registry
# ══════════════════════════════════════════════════════════════════════════════

SEC_CMDS: dict = {
    "password-gen":   cmd_password_gen,
    "passgen":        cmd_password_gen,
    "pwgen":          cmd_password_gen,
    "password-audit": cmd_password_audit,
    "pwaudit":        cmd_password_audit,
    "vuln-search":    cmd_vuln_search,
    "cve":            cmd_vuln_search,
}
