"""
commands/crypto.py — Cryptography & Encoding Suite for Kali Terminal v1.0

Commands:
  hash <algo> <text|file>    — Hash with MD5/SHA1/SHA256/SHA512/BLAKE2
  encode <method> <text>     — Base64 / URL / Hex / Binary encoding
  decode <method> <text>     — Decode the above
  rot13 <text>               — ROT13 cipher
  caesar <n> <text>          — Caesar cipher (shift n)
  xor <key> <hex_data>       — XOR with a key
  passgen [length] [flags]   — Generate secure random password
  pwdcheck <password>        — Password strength checker
  b64file <encode|decode> <file> — Base64 encode/decode a file
"""

import os
import hashlib
import base64
import urllib.parse
import secrets
import string
import binascii
import re

from ui.theme import Colors
from utils.formatters import table, panel

C = Colors


# ══════════════════════════════════════════════════════════════════════
#  Hash Command
# ══════════════════════════════════════════════════════════════════════

HASH_ALGOS = {
    "md5":     hashlib.md5,
    "sha1":    hashlib.sha1,
    "sha256":  hashlib.sha256,
    "sha512":  hashlib.sha512,
    "sha224":  hashlib.sha224,
    "sha384":  hashlib.sha384,
    "blake2b": lambda: hashlib.blake2b(),
    "blake2s": lambda: hashlib.blake2s(),
}


def cmd_hash(args: list, state: dict) -> int:
    """
    hash <algo> <text>          — Hash text
    hash <algo> --file <path>   — Hash file
    hash all <text>             — Show all hash algorithms
    """
    if len(args) < 2:
        print(C.error("Usage: hash <algo|all> <text|--file path>"))
        algos = " | ".join(HASH_ALGOS.keys())
        print(f"  Algorithms: {C.CYAN}{algos}{C.RESET}")
        return 1

    algo = args[0].lower()
    is_file = "--file" in args or "-f" in args

    # Gather input
    if is_file:
        try:
            fi = args.index("--file") if "--file" in args else args.index("-f")
            file_path = args[fi + 1]
        except (ValueError, IndexError):
            print(C.error("Usage: hash <algo> --file <path>"))
            return 1
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            source = f"file:{file_path}"
        except FileNotFoundError:
            print(C.error(f"File not found: {file_path}"))
            return 1
        except PermissionError:
            print(C.error(f"Permission denied: {file_path}"))
            return 1
    else:
        text = " ".join(args[1:])
        data = text.encode("utf-8")
        source = f"text: \"{text[:40]}\""

    print(f"\n{C.BOLD}{C.BLUE}[ HASH ENGINE ]{C.RESET}  Input: {C.CYAN}{source}{C.RESET}\n")

    if algo == "all":
        rows = []
        for name, fn in HASH_ALGOS.items():
            h = fn()
            h.update(data)
            rows.append((name.upper(), h.hexdigest()))
        print(table(rows, headers=["ALGORITHM", "HASH"], title="ALL HASHES"))
    elif algo in HASH_ALGOS:
        h = HASH_ALGOS[algo]()
        h.update(data)
        digest = h.hexdigest()
        print(f"  {C.BOLD}{C.WHITE}{algo.upper()}{C.RESET}: {C.GREEN}{digest}{C.RESET}")
        if is_file:
            size = len(data)
            print(f"  {C.GRAY}File size: {size:,} bytes{C.RESET}")
    else:
        print(C.error(f"Unknown algorithm: {algo}"))
        print(f"  Available: {C.CYAN}{' | '.join(HASH_ALGOS.keys())}{C.RESET}")
        return 1

    print()
    return 0


# ══════════════════════════════════════════════════════════════════════
#  Encode / Decode
# ══════════════════════════════════════════════════════════════════════

def cmd_encode(args: list, state: dict) -> int:
    """
    encode <method> <text>
    Methods: base64 | b64 | url | hex | binary | rot13 | html
    """
    if len(args) < 2:
        print(C.error("Usage: encode <method> <text>"))
        print(f"  Methods: {C.CYAN}base64 | url | hex | binary | html | morse{C.RESET}")
        return 1

    method = args[0].lower()
    text   = " ".join(args[1:])

    result = _do_encode(method, text)
    if result is None:
        print(C.error(f"Unknown encoding method: {method}"))
        return 1

    print(f"\n  {C.BOLD}{C.WHITE}{method.upper()} Encoded:{C.RESET}")
    print(f"  {C.GREEN}{result}{C.RESET}\n")
    return 0


def cmd_decode(args: list, state: dict) -> int:
    """
    decode <method> <text>
    Methods: base64 | b64 | url | hex | binary | html
    """
    if len(args) < 2:
        print(C.error("Usage: decode <method> <text>"))
        print(f"  Methods: {C.CYAN}base64 | url | hex | binary | html{C.RESET}")
        return 1

    method = args[0].lower()
    text   = " ".join(args[1:])

    result = _do_decode(method, text)
    if result is None:
        print(C.error(f"Unknown decoding method: {method}"))
        return 1

    print(f"\n  {C.BOLD}{C.WHITE}{method.upper()} Decoded:{C.RESET}")
    print(f"  {C.CYAN}{result}{C.RESET}\n")
    return 0


MORSE = {
    'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....','I':'..','J':'.---',
    'K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-','R':'.-.','S':'...','T':'-',
    'U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..',
    '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....',
    '6':'-....','7':'--...','8':'---..','9':'----.',
    ' ':'/', '.':'.-.-.-',',':'--..--','?':'..--..','/':'-..-.',
}

MORSE_REV = {v: k for k, v in MORSE.items()}


def _do_encode(method: str, text: str):
    try:
        if method in ("base64", "b64"):
            return base64.b64encode(text.encode()).decode()
        elif method == "url":
            return urllib.parse.quote(text)
        elif method == "hex":
            return text.encode().hex()
        elif method == "binary":
            return " ".join(format(ord(c), "08b") for c in text)
        elif method == "html":
            return text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")
        elif method == "rot13":
            return text.translate(str.maketrans(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm"
            ))
        elif method == "morse":
            return " ".join(MORSE.get(c.upper(), "?") for c in text)
        elif method in ("urlencode", "url_encode"):
            return urllib.parse.urlencode({"q": text})[2:]
    except Exception as e:
        return f"[ERROR: {e}]"
    return None


def _do_decode(method: str, text: str):
    try:
        if method in ("base64", "b64"):
            # Add padding if needed
            pad = len(text) % 4
            if pad:
                text += "=" * (4 - pad)
            return base64.b64decode(text).decode("utf-8", errors="replace")
        elif method == "url":
            return urllib.parse.unquote(text)
        elif method == "hex":
            return bytes.fromhex(text.replace(" ", "")).decode("utf-8", errors="replace")
        elif method == "binary":
            chunks = text.split()
            return "".join(chr(int(b, 2)) for b in chunks)
        elif method == "html":
            return (text.replace("&amp;","&").replace("&lt;","<")
                    .replace("&gt;",">").replace("&quot;",'"').replace("&#39;","'"))
        elif method == "rot13":
            return _do_encode("rot13", text)  # ROT13 is self-inverse
        elif method == "morse":
            words = text.split(" / ")
            result = []
            for word in words:
                chars = word.split()
                result.append("".join(MORSE_REV.get(c, "?") for c in chars))
            return " ".join(result)
    except Exception as e:
        return f"[ERROR: {e}]"
    return None


# ══════════════════════════════════════════════════════════════════════
#  Caesar Cipher
# ══════════════════════════════════════════════════════════════════════

def cmd_caesar(args: list, state: dict) -> int:
    """caesar <shift> <text>  — Caesar cipher encrypt/decrypt."""
    if len(args) < 2:
        print(C.error("Usage: caesar <shift> <text>   e.g. caesar 13 hello"))
        return 1
    try:
        shift = int(args[0]) % 26
    except ValueError:
        print(C.error("Shift must be an integer"))
        return 1

    text   = " ".join(args[1:])
    result = []
    for ch in text:
        if ch.isalpha():
            base = ord('A') if ch.isupper() else ord('a')
            result.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            result.append(ch)

    cipher_text = "".join(result)
    print(f"\n  {C.BOLD}{C.WHITE}Caesar (shift={shift}):{C.RESET}")
    print(f"  {C.CYAN}Plain : {C.WHITE}{text}{C.RESET}")
    print(f"  {C.CYAN}Cipher: {C.GREEN}{cipher_text}{C.RESET}")

    # Brute force section
    if "--brute" in args or "-b" in args:
        print(f"\n  {C.YELLOW}Brute force all 26 shifts:{C.RESET}")
        for s in range(26):
            dec = "".join(
                chr((ord(c) - (ord('A') if c.isupper() else ord('a')) + s) % 26
                    + (ord('A') if c.isupper() else ord('a'))) if c.isalpha() else c
                for c in text
            )
            print(f"  {C.GRAY}[{s:2d}]{C.RESET} {dec}")
    print()
    return 0


# ══════════════════════════════════════════════════════════════════════
#  XOR
# ══════════════════════════════════════════════════════════════════════

def cmd_xor(args: list, state: dict) -> int:
    """
    xor <key> <hex_data>   — XOR hex data with key
    xor <key> --text <t>   — XOR text with key
    """
    if len(args) < 2:
        print(C.error("Usage: xor <key> <hex_data>   or   xor <key> --text <text>"))
        return 1

    key = args[0].encode()
    is_text = "--text" in args or "-t" in args

    try:
        if is_text:
            idx = args.index("--text") if "--text" in args else args.index("-t")
            data = " ".join(args[idx+1:]).encode()
        else:
            data = bytes.fromhex(args[1].replace("0x","").replace(" ",""))
    except (ValueError, IndexError) as e:
        print(C.error(f"Invalid input: {e}"))
        return 1

    result = bytes(b ^ key[i % len(key)] for i, b in enumerate(data))

    print(f"\n  {C.BOLD}{C.WHITE}XOR Result:{C.RESET}")
    print(f"  {C.CYAN}Key     : {C.WHITE}{args[0]!r}{C.RESET}")
    print(f"  {C.CYAN}Hex     : {C.GREEN}{result.hex()}{C.RESET}")
    try:
        txt = result.decode("utf-8")
        print(f"  {C.CYAN}ASCII   : {C.YELLOW}{txt!r}{C.RESET}")
    except UnicodeDecodeError:
        pass
    print()
    return 0


# ══════════════════════════════════════════════════════════════════════
#  Password Generator
# ══════════════════════════════════════════════════════════════════════

def cmd_passgen(args: list, state: dict) -> int:
    """
    passgen [length] [--no-symbols] [--no-digits] [--no-upper] [--count N]
    Generate cryptographically secure passwords.
    """
    length   = 16
    n_count  = 1
    use_sym  = True
    use_dig  = True
    use_up   = True

    i = 0
    while i < len(args):
        if args[i] == "--no-symbols":    use_sym = False
        elif args[i] == "--no-digits":   use_dig = False
        elif args[i] == "--no-upper":    use_up  = False
        elif args[i] == "--count" and i+1 < len(args):
            try: n_count = int(args[i+1]); i += 1
            except ValueError: pass
        elif args[i].isdigit():
            length = int(args[i])
        i += 1

    alphabet  = string.ascii_lowercase
    if use_up:  alphabet += string.ascii_uppercase
    if use_dig: alphabet += string.digits
    if use_sym: alphabet += "!@#$%^&*()_+-=[]{}|;:,.<>?"

    print(f"\n{C.BOLD}{C.BLUE}[ PASSWORD GENERATOR ]{C.RESET}  Length: {C.CYAN}{length}{C.RESET}\n")

    for i in range(n_count):
        pwd = "".join(secrets.choice(alphabet) for _ in range(length))
        strength = _pwd_strength(pwd)
        print(f"  {C.GREEN}{pwd}{C.RESET}  {strength}")

    print()
    return 0


# ══════════════════════════════════════════════════════════════════════
#  Password Strength Checker
# ══════════════════════════════════════════════════════════════════════

def cmd_pwdcheck(args: list, state: dict) -> int:
    """pwdcheck <password> — Analyze password strength."""
    if not args:
        print(C.error("Usage: pwdcheck <password>"))
        return 1

    pwd = " ".join(args)
    print(f"\n{C.BOLD}{C.BLUE}[ PASSWORD ANALYZER ]{C.RESET}\n")
    print(f"  Password : {C.WHITE}{pwd}{C.RESET}")
    print(f"  Length   : {C.CYAN}{len(pwd)}{C.RESET} chars\n")

    checks = [
        ("Length ≥ 8",     len(pwd) >= 8),
        ("Length ≥ 12",    len(pwd) >= 12),
        ("Length ≥ 16",    len(pwd) >= 16),
        ("Lowercase",      any(c.islower() for c in pwd)),
        ("Uppercase",      any(c.isupper() for c in pwd)),
        ("Digits",         any(c.isdigit() for c in pwd)),
        ("Special chars",  any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in pwd)),
        ("No common word", not any(w in pwd.lower() for w in
                                   ["password","pass","123","qwerty","admin","root","letmein"])),
        ("No sequences",   not re.search(r"(012|123|234|345|456|567|678|789|890|abc|bcd|cde)", pwd.lower())),
    ]

    score = sum(1 for _, ok in checks if ok)
    for desc, ok in checks:
        icon  = C.paint("[✔]", C.GREEN, bold=True) if ok else C.paint("[✘]", C.RED)
        print(f"  {icon}  {C.WHITE}{desc}{C.RESET}")

    strength = _strength_label(score, len(checks))
    print(f"\n  Score: {C.CYAN}{score}/{len(checks)}{C.RESET}  Strength: {strength}\n")
    return 0


def _pwd_strength(pwd: str) -> str:
    score = sum([
        len(pwd) >= 8,
        len(pwd) >= 12,
        any(c.islower() for c in pwd),
        any(c.isupper() for c in pwd),
        any(c.isdigit() for c in pwd),
        any(c in "!@#$%^&*()" for c in pwd),
    ])
    return _strength_label(score, 6)


def _strength_label(score: int, total: int) -> str:
    ratio = score / total
    if ratio >= 0.9: return C.paint("★★★★★ VERY STRONG", C.GREEN, bold=True)
    if ratio >= 0.7: return C.paint("★★★★☆ STRONG",      C.GREEN)
    if ratio >= 0.5: return C.paint("★★★☆☆ MODERATE",    C.YELLOW)
    if ratio >= 0.3: return C.paint("★★☆☆☆ WEAK",        C.ORANGE)
    return C.paint("★☆☆☆☆ VERY WEAK",    C.RED, bold=True)


# ══════════════════════════════════════════════════════════════════════
#  Dispatch
# ══════════════════════════════════════════════════════════════════════

CRYPTO_COMMANDS = {
    "hash":      cmd_hash,
    "encode":    cmd_encode,
    "decode":    cmd_decode,
    "caesar":    cmd_caesar,
    "xor":       cmd_xor,
    "passgen":   cmd_passgen,
    "pwdcheck":  cmd_pwdcheck,
}
