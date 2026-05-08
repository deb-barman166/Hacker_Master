"""
commands/crypto_tools.py — Encoding, decoding, and hashing utilities (v2.0 Masterpiece).

Commands:
  - hash: Calculate file hashes (MD5, SHA1, SHA256, SHA512, etc.)
  - encode: Encode text (base64, url, hex, html, unicode)
  - decode: Decode text (base64, url, hex, html, unicode)
  - rot13: ROT13 cipher
  - caesar: Caesar cipher with customizable shift
  - hash-identify: Identify hash type
  - hash-crack: Basic hash cracking
  - ssl-check: SSL/TLS certificate checker
"""

import os
import hashlib
import base64
import urllib.parse
import re
import string
import json
from datetime import datetime
import html
import unicodedata
import subprocess

from ui.theme import Colors

C = Colors


def cmd_hash(args: list, state: dict, terminal=None) -> int:
    """Calculate file hashes. Usage: hash <file> [algorithm]"""
    if not args:
        print(C.info("Usage: hash <file> [algorithm]"))
        print(C.info("Algorithms: md5, sha1, sha256, sha512, sha3_256, sha3_512, blake2b, all (default: all)"))
        print(C.info("Examples:"))
        print(C.info("  hash myfile.txt"))
        print(C.info("  hash myfile.txt sha256"))
        return 0

    filepath = args[0]
    algo = args[1].lower() if len(args) > 1 else "all"

    if not os.path.isfile(filepath):
        print(C.error(f"File not found: {filepath}"))
        return 1

    algorithms = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
        "sha3_256": hashlib.sha3_256,
        "sha3_512": hashlib.sha3_512,
        "blake2b": hashlib.blake2b,
        "blake2s": hashlib.blake2s,
    }

    if algo == "all":
        algos_to_run = algorithms
    elif algo in algorithms:
        algos_to_run = {algo: algorithms[algo]}
    else:
        print(C.error(f"Unknown algorithm: {algo}. Choose: {', '.join(algorithms.keys())}, all"))
        return 1

    size = os.path.getsize(filepath)
    print(f"\n{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}FILE HASH: {os.path.basename(filepath)}{C.RESET}")
    print(f"  {C.GRAY}Size: {_fmt_size(size)}{C.RESET}")
    print(f"{C.BLUE}{'='*70}{C.RESET}")

    try:
        with open(filepath, "rb") as f:
            data = f.read()
    except IOError as e:
        print(C.error(f"Cannot read file: {e}"))
        return 1

    for name, func in algos_to_run.items():
        if name in ["blake2b"]:
            h = func(data, digest_size=64)
        elif name in ["blake2s"]:
            h = func(data, digest_size=32)
        else:
            h = func(data)
        hex_digest = h.hexdigest()
        print(f"\n  {C.YELLOW}{C.BOLD}{name.upper()}{C.RESET}")
        print(f"  {C.CYAN}{hex_digest}{C.RESET}")

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def cmd_encode(args: list, state: dict, terminal=None) -> int:
    """Encode text. Usage: encode <text> [format]"""
    if not args:
        print(C.info("Usage: encode <text> [format]"))
        print(C.info("Formats: base64 (default), url, hex, html, unicode, binary, octal"))
        print(C.info("Examples:"))
        print(C.info("  encode Hello World"))
        print(C.info("  encode 'hello world' url"))
        print(C.info("  encode '68656c6c6f' hex"))
        return 0

    fmt = "base64"
    text_parts = []
    for arg in args:
        if arg.lower() in ("base64", "url", "hex", "html", "unicode", "binary", "octal") and not text_parts:
            fmt = arg.lower()
        else:
            text_parts.append(arg)

    text = " ".join(text_parts)

    print(f"\n{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}ENCODE ({fmt.upper()}){C.RESET}")
    print(f"{C.BLUE}{'='*70}{C.RESET}")

    print(f"\n  {C.CYAN}Input{C.RESET}:  {C.WHITE}{text}{C.RESET}")
    print(f"  {C.YELLOW}Output{C.RESET}: ", end="")

    try:
        if fmt == "base64":
            encoded = base64.b64encode(text.encode()).decode()
        elif fmt == "url":
            encoded = urllib.parse.quote(text, safe='')
        elif fmt == "hex":
            encoded = text.encode().hex()
        elif fmt == "html":
            encoded = html.escape(text)
        elif fmt == "unicode":
            encoded = text.encode('unicode_escape').decode('ascii')
        elif fmt == "binary":
            encoded = ' '.join(format(ord(c), '08b') for c in text)
        elif fmt == "octal":
            encoded = ' '.join(format(ord(c), '03o') for c in text)
        else:
            encoded = text

        print(f"{C.GREEN}{encoded}{C.RESET}")
        print(f"\n  {C.GRAY}Length: {len(encoded)} characters{C.RESET}")
        print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    except Exception as e:
        print(f"{C.RED}{e}{C.RESET}")
        return 1
    return 0


def cmd_decode(args: list, state: dict, terminal=None) -> int:
    """Decode text. Usage: decode <encoded_text> [format]"""
    if not args:
        print(C.info("Usage: decode <encoded_text> [format]"))
        print(C.info("Formats: base64 (default), url, hex, html, unicode, binary, octal"))
        print(C.info("Examples:"))
        print(C.info("  decode SGVsbG8gV29ybGQ="))
        print(C.info("  decode 'Hello%20World' url"))
        print(C.info("  decode '68656c6c6f' hex"))
        return 0

    fmt = "base64"
    text_parts = []
    for arg in args:
        if arg.lower() in ("base64", "url", "hex", "html", "unicode", "binary", "octal") and not text_parts:
            fmt = arg.lower()
        else:
            text_parts.append(arg)

    text = " ".join(text_parts)

    print(f"\n{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}DECODE ({fmt.upper()}){C.RESET}")
    print(f"{C.BLUE}{'='*70}{C.RESET}")

    print(f"\n  {C.CYAN}Input{C.RESET}:  {C.WHITE}{text[:50]}{'...' if len(text) > 50 else ''}{C.RESET}")
    print(f"  {C.YELLOW}Output{C.RESET}: ", end="")

    try:
        if fmt == "base64":
            decoded = base64.b64decode(text).decode()
        elif fmt == "url":
            decoded = urllib.parse.unquote(text)
        elif fmt == "hex":
            decoded = bytes.fromhex(text).decode()
        elif fmt == "html":
            decoded = html.unescape(text)
        elif fmt == "unicode":
            decoded = text.encode('ascii').decode('unicode_escape')
        elif fmt == "binary":
            bytes_list = text.split()
            decoded = ''.join(chr(int(b, 2)) for b in bytes_list)
        elif fmt == "octal":
            bytes_list = text.split()
            decoded = ''.join(chr(int(b, 8)) for b in bytes_list)
        else:
            decoded = text

        print(f"{C.GREEN}{decoded}{C.RESET}")
        print(f"\n  {C.GRAY}Length: {len(decoded)} characters{C.RESET}")
        print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    except Exception as e:
        print(f"{C.RED}Decode error: {e}{C.RESET}")
        return 1
    return 0


def cmd_rot13(args: list, state: dict, terminal=None) -> int:
    """ROT13 cipher. Usage: rot13 <text>"""
    if not args:
        print(C.info("Usage: rot13 <text>"))
        return 0

    text = " ".join(args)
    result = text.translate(str.maketrans(
        string.ascii_lowercase + string.ascii_uppercase,
        string.ascii_lowercase[13:] + string.ascii_lowercase[:13] +
        string.ascii_uppercase[13:] + string.ascii_uppercase[:13]
    ))

    print(f"\n{C.BLUE}{'='*60}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}ROT13 CIPHER{C.RESET}")
    print(f"{C.BLUE}{'='*60}{C.RESET}")
    print(f"\n  {C.CYAN}Input{C.RESET}:  {C.WHITE}{text}{C.RESET}")
    print(f"  {C.GREEN}Output{C.RESET}: {C.GREEN}{result}{C.RESET}")
    print(f"\n{C.BLUE}{'='*60}{C.RESET}\n")
    return 0


def cmd_caesar(args: list, state: dict, terminal=None) -> int:
    """Caesar cipher with customizable shift. Usage: caesar <text> [shift] [decode]"""
    if not args:
        print(C.info("Usage: caesar <text> [shift] [decode]"))
        print(C.info("Examples:"))
        print(C.info("  caesar Hello 3"))
        print(C.info("  caesar Khoor 3 decode"))
        return 0

    text = ""
    shift = 3
    decode = False

    for i, arg in enumerate(args):
        if arg.lower() == "decode":
            decode = True
        elif arg.isdigit():
            shift = int(arg)
        else:
            text = arg if not text else text + " " + arg

    shift = -shift if decode else shift

    result = ""
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            result += chr((ord(char) - base + shift) % 26 + base)
        else:
            result += char

    print(f"\n{C.BLUE}{'='*60}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}CAESAR CIPHER (shift={abs(shift)}){C.RESET}")
    print(f"{C.BLUE}{'='*60}{C.RESET}")
    print(f"\n  {C.CYAN}Input{C.RESET}:  {C.WHITE}{text}{C.RESET}")
    print(f"  {C.GREEN}Output{C.RESET}: {C.GREEN}{result}{C.RESET}")
    print(f"  {C.GRAY}Mode: {'Decode' if decode else 'Encode'}{C.RESET}")
    print(f"\n{C.BLUE}{'='*60}{C.RESET}\n")
    return 0


def cmd_hash_identify(args: list, state: dict, terminal=None) -> int:
    """Identify hash type. Usage: hash-identify <hash>"""
    if not args:
        print(C.info("Usage: hash-identify <hash>"))
        return 0

    hash_value = args[0]
    hash_length = len(hash_value)
    is_hex = all(c in '0123456789abcdefABCDEF' for c in hash_value)

    print(f"\n{C.BLUE}{'='*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}HASH IDENTIFICATION{C.RESET}")
    print(f"{C.BLUE}{'='*65}{C.RESET}")
    print(f"\n  {C.CYAN}Hash{C.RESET}:      {C.WHITE}{hash_value}{C.RESET}")
    print(f"  {C.CYAN}Length{C.RESET}:     {C.WHITE}{hash_length} characters{C.RESET}")
    print(f"  {C.CYAN}Type{C.RESET}:       {C.WHITE}{'Hexadecimal' if is_hex else 'Unknown'}{C.RESET}\n")

    possible_types = []

    if is_hex:
        if hash_length == 32:
            possible_types.append(("MD5", "Most common, used for checksums"))
        if hash_length == 40:
            possible_types.append(("SHA1", "Older hash, deprecated for security"))
        if hash_length == 56:
            possible_types.append(("SHA224", "Part of SHA-2 family"))
        if hash_length == 64:
            possible_types.append(("SHA256", "Widely used, secure"))
        if hash_length == 96:
            possible_types.append(("SHA384", "Part of SHA-2 family"))
        if hash_length == 128:
            possible_types.append(("SHA512", "Very secure, large output"))
        if hash_length == 56 and hash_value.startswith("$4$"):
            possible_types.append(("bcrypt", "Used for password hashing"))
        if hash_value.startswith("$1$"):
            possible_types.append(("MD5crypt", "Linux password hash"))
        if hash_value.startswith("$5$"):
            possible_types.append(("SHA256crypt", "Linux password hash"))
        if hash_value.startswith("$6$"):
            possible_types.append(("SHA512crypt", "Linux password hash"))
        if hash_value.startswith("$2a$") or hash_value.startswith("$2b$"):
            possible_types.append(("bcrypt", "Password hashing"))

    if not possible_types:
        possible_types.append(("Unknown", "Could not identify hash type"))

    print(f"  {C.YELLOW}{C.BOLD}Possible Types:{C.RESET}")
    for hash_type, description in possible_types:
        print(f"    {C.CYAN}{hash_type:<15}{C.RESET} {C.GRAY}{description}{C.RESET}")

    # Additional analysis
    print(f"\n  {C.YELLOW}{C.BOLD}Characteristics:{C.RESET}")
    entropy = _calculate_entropy(hash_value)
    print(f"    {C.CYAN}Entropy{C.RESET}: {entropy:.2f} bits/char")
    print(f"    {C.CYAN}Pattern{C.RESET}:  {'Random' if entropy > 4 else 'Patterned'}")

    print(f"\n{C.BLUE}{'='*65}{C.RESET}\n")
    return 0


def _calculate_entropy(data: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not data:
        return 0
    import math
    freq = {}
    for c in data:
        freq[c] = freq.get(c, 0) + 1
    entropy = 0
    for count in freq.values():
        prob = count / len(data)
        entropy -= prob * math.log2(prob)
    return entropy


def cmd_hash_cracker(args: list, state: dict, terminal=None) -> int:
    """Basic hash cracking. Usage: hash-crack <hash> [wordlist]"""
    if len(args) < 2:
        print(C.info("Usage: hash-crack <hash> [wordlist_path]"))
        print(C.info("Examples:"))
        print(C.info("  hash-crack 5f4dcc3b5aa765d61d8327deb882cf99 wordlist.txt"))
        print(C.info("  hash-crack e10adc3949ba59abbe56e057f20f883e"))
        return 0

    hash_value = args[0].lower()
    wordlist_path = args[1] if len(args) > 1 else None

    print(f"\n{C.RED}{C.BOLD}")
    print(f"  ╔═══════════════════════════════════════════════════════════╗")
    print(f"  ║              HASH CRACKER — Educational Use Only        ║")
    print(f"  ╚═══════════════════════════════════════════════════════════╝")
    print(f"{C.RESET}")

    hash_length = len(hash_value)
    hash_type = _identify_hash_type(hash_value)

    print(f"  {C.CYAN}Target Hash{C.RESET}:    {C.WHITE}{hash_value}{C.RESET}")
    print(f"  {C.CYAN}Detected Type{C.RESET}:  {C.WHITE}{hash_type}{C.RESET}")

    # Built-in wordlists for demo
    common_passwords = [
        "123456", "password", "123456789", "12345678", "12345",
        "qwerty", "abc123", "password123", "admin", "letmein",
        "welcome", "monkey", "dragon", "master", "hello",
        "shadow", "sunshine", "princess", "football", "baseball"
    ]

    print(f"\n  {C.YELLOW}Cracking with built-in wordlist...{C.RESET}\n")

    found = False
    for password in common_passwords:
        if hash_type == "MD5":
            computed = hashlib.md5(password.encode()).hexdigest()
        elif hash_type == "SHA1":
            computed = hashlib.sha1(password.encode()).hexdigest()
        elif hash_type == "SHA256":
            computed = hashlib.sha256(password.encode()).hexdigest()
        else:
            computed = hashlib.md5(password.encode()).hexdigest()

        if computed == hash_value:
            print(f"  {C.GREEN}{C.BOLD}[+] FOUND!{C.RESET}")
            print(f"  {C.CYAN}Password{C.RESET}: {C.WHITE}{password}{C.RESET}")
            found = True
            break
        else:
            print(f"\r  {C.GRAY}Testing: {password:<20}{C.RESET}", end="")

    if not found and wordlist_path and os.path.isfile(wordlist_path):
        print(f"\n\n  {C.YELLOW}Using custom wordlist: {wordlist_path}{C.RESET}\n")
        try:
            with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f):
                    password = line.strip()
                    if not password:
                        continue

                    if hash_type == "MD5":
                        computed = hashlib.md5(password.encode()).hexdigest()
                    elif hash_type == "SHA1":
                        computed = hashlib.sha1(password.encode()).hexdigest()
                    elif hash_type == "SHA256":
                        computed = hashlib.sha256(password.encode()).hexdigest()
                    else:
                        computed = hashlib.md5(password.encode()).hexdigest()

                    if computed == hash_value:
                        print(f"\n  {C.GREEN}{C.BOLD}[+] FOUND!{C.RESET}")
                        print(f"  {C.CYAN}Password{C.RESET}: {C.WHITE}{password}{C.RESET}")
                        found = True
                        break

                    if line_num % 100 == 0:
                        print(f"\r  {C.GRAY}Checked {line_num} passwords...{C.RESET}", end="")
        except Exception as e:
            print(C.error(f"Error reading wordlist: {e}"))

    if not found:
        print(f"\n\n  {C.YELLOW}Password not found in wordlist.{C.RESET}")
        print(f"  {C.GRAY}Try using a larger wordlist with: hash-crack {hash_value} <wordlist>{C.RESET}")

    print(f"\n{C.BLUE}{'='*65}{C.RESET}\n")
    return 0


def _identify_hash_type(hash_value: str) -> str:
    """Identify hash type by length and format."""
    if hash_value.startswith(("$1$", "$2", "$5$", "$6$")):
        if hash_value.startswith("$1$"):
            return "MD5crypt"
        elif hash_value.startswith("$2"):
            return "bcrypt"
        elif hash_value.startswith("$5$"):
            return "SHA256crypt"
        elif hash_value.startswith("$6$"):
            return "SHA512crypt"

    length = len(hash_value)
    if length == 32:
        return "MD5"
    elif length == 40:
        return "SHA1"
    elif length == 56:
        return "SHA224"
    elif length == 64:
        return "SHA256"
    elif length == 96:
        return "SHA384"
    elif length == 128:
        return "SHA512"
    else:
        return "Unknown"


def cmd_ssl_check(args: list, state: dict, terminal=None) -> int:
    """SSL/TLS certificate checker. Usage: ssl-check <host> [port]"""
    if not args:
        print(C.info("Usage: ssl-check <host> [port]"))
        print(C.info("Examples:"))
        print(C.info("  ssl-check google.com"))
        print(C.info("  ssl-check mail.example.com 993"))
        return 0

    host = args[0]
    port = int(args[1]) if len(args) > 1 else 443

    print(f"\n{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}SSL/TLS CERTIFICATE CHECK: {host}:{port}{C.RESET}")
    print(f"{C.BLUE}{'='*70}{C.RESET}\n")

    try:
        import ssl
        import certifi

        context = ssl.create_default_context()
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED

        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()

                print(f"  {C.GREEN}{C.BOLD}[+] Connection Successful{C.RESET}")
                print(f"  {C.CYAN}Protocol{C.RESET}:     {C.WHITE}{ssock.version()}{C.RESET}")
                print(f"  {C.CYAN}Cipher{C.RESET}:       {C.WHITE}{ssock.cipher()[0]}{C.RESET}")
                print(f"  {C.CYAN}Bits{C.RESET}:         {C.WHITE}{ssock.cipher()[2]}{C.RESET}\n")

                # Parse certificate
                if cert:
                    subject = dict(x[0] for x in cert.get('subject', []))
                    issuer = dict(x[0] for x in cert.get('issuer', []))

                    def row(label, value):
                        print(f"  {C.CYAN}{label:<15}{C.RESET}: {C.WHITE}{value}{C.RESET}")

                    print(f"  {C.YELLOW}{C.BOLD}Certificate Details:{C.RESET}")
                    row("Subject", subject.get('commonName', 'N/A'))
                    row("Issuer", issuer.get('commonName', 'N/A'))

                    # Check expiry
                    not_after = cert.get('notAfter', '')
                    not_before = cert.get('notBefore', '')

                    print(f"\n  {C.YELLOW}{C.BOLD}Validity:{C.RESET}")
                    row("Not Before", not_before)
                    row("Not After", not_after)

                    # Check certificate chain
                    print(f"\n  {C.YELLOW}{C.BOLD}Certificate Info:{C.RESET}")
                    serial = cert.get('serialNumber', 'N/A')
                    row("Serial", serial[:20] + "..." if len(serial) > 20 else serial)

                    # Sanity check
                    import datetime
                    try:
                        expiry = datetime.datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                        days_left = (expiry - datetime.datetime.now()).days
                        if days_left < 0:
                            status = f"{C.RED}EXPIRED ({abs(days_left)} days ago){C.RESET}"
                        elif days_left < 30:
                            status = f"{C.RED}EXPIRING SOON ({days_left} days){C.RESET}"
                        else:
                            status = f"{C.GREEN}Valid ({days_left} days remaining){C.RESET}"
                        print(f"  {C.CYAN}Status{C.RESET}:         {status}")
                    except:
                        pass

    except ssl.SSLCertVerificationError as e:
        print(f"  {C.RED}{C.BOLD}[-] Certificate Error:{C.RESET}")
        print(f"  {C.WHITE}{str(e)}{C.RESET}")
    except socket.gaierror:
        print(C.error(f"Could not resolve: {host}"))
        return 1
    except Exception as e:
        print(C.error(f"Connection error: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


# Import socket for ssl-check
import socket


def _fmt_size(n: int) -> str:
    """Human-readable byte count."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"