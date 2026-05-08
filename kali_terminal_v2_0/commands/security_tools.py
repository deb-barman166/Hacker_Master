"""
commands/security_tools.py — Security and password utilities (v2.0 Masterpiece).

Commands:
  - password-gen: Generate secure random passwords
  - random-uuid: Generate UUIDs
  - random-mac: Generate random MAC addresses
  - sanitize: Sanitize output for safe display
  - cypher: Encrypt text with various algorithms
  - decypher: Decrypt text
  - base64-img: Convert image to base64
"""

import os
import secrets
import string
import uuid
import re
import hashlib
import base64
import json
import time
from datetime import datetime

from ui.theme import Colors

C = Colors


def cmd_password_gen(args: list, state: dict, terminal=None) -> int:
    """Generate secure random passwords. Usage: password-gen [length] [count] [options]"""
    length = 16
    count = 1
    use_upper = True
    use_lower = True
    use_digits = True
    use_special = True
    exclude_ambiguous = False
    no_repeat = False
    pronounceable = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in ("-n", "--no-special"):
            use_special = False
        elif arg in ("-a", "--no-ambiguous"):
            exclude_ambiguous = True
        elif arg in ("-u", "--uppercase-only"):
            use_lower = False
        elif arg in ("-l", "--lowercase-only"):
            use_upper = False
        elif arg in ("-d", "--digits-only"):
            use_upper = False
            use_special = False
        elif arg in ("-r", "--no-repeat"):
            no_repeat = True
        elif arg in ("-p", "--pronounceable"):
            pronounceable = True
        elif arg == "--help":
            print(C.info("Usage: password-gen [length] [count] [options]"))
            print(C.info("Options:"))
            print(C.info("  -n, --no-special    Exclude special characters"))
            print(C.info("  -a, --no-ambiguous   Exclude ambiguous chars (0O1lI)"))
            print(C.info("  -u, --uppercase-only Only use uppercase letters"))
            print(C.info("  -l, --lowercase-only Only use lowercase letters"))
            print(C.info("  -d, --digits-only   Only use digits"))
            print(C.info("  -r, --no-repeat     No repeated characters"))
            print(C.info("  -p, --pronounceable Generate pronounceable passwords"))
            print(C.info("Examples:"))
            print(C.info("  password-gen          # 16-char password"))
            print(C.info("  password-gen 32       # 32-char password"))
            print(C.info("  password-gen 20 5     # 5 passwords, 20 chars each"))
            print(C.info("  password-gen 16 3 -n  # No special chars"))
            print(C.info("  password-gen -p 12    # Pronounceable password"))
            return 0
        else:
            try:
                if i == 0:
                    length = int(arg)
                elif i == 1:
                    count = int(arg)
            except ValueError:
                pass
        i += 1

    length = max(4, min(128, length))
    count = max(1, min(100, count))

    print(f"\n{C.RED}{C.BOLD}")
    print(f"  ╔══════════════════════════════════════════════════════════════════╗")
    print(f"  ║                    PASSWORD GENERATOR                            ║")
    print(f"  ╚══════════════════════════════════════════════════════════════════╝")
    print(f"{C.RESET}")

    if pronounceable:
        passwords = [_generate_pronounceable(length) for _ in range(count)]
        charset = "pronounceable"
    else:
        charset = ""
        if use_upper:
            charset += string.ascii_uppercase
        if use_lower:
            charset += string.ascii_lowercase
        if use_digits:
            charset += string.digits
        if use_special:
            charset += "!@#$%^&*()_+-=[]{}|;:,.<>?"

        if exclude_ambiguous:
            ambiguous = "0O1lI|"
            charset = "".join(c for c in charset if c not in ambiguous)

        if not charset:
            charset = string.ascii_letters + string.digits

        if no_repeat:
            passwords = [_generate_no_repeat(charset, length) for _ in range(count)]
        else:
            passwords = ["".join(secrets.choice(charset) for _ in range(length)) for _ in range(count)]

    print(f"  {C.CYAN}Length{C.RESET}:   {C.WHITE}{length}{C.RESET}")
    print(f"  {C.CYAN}Count{C.RESET}:    {C.WHITE}{count}{C.RESET}")
    print(f"  {C.CYAN}Charset{C.RESET}: {C.WHITE}{len(charset)} chars{C.RESET}")
    print()

    # Entropy info
    import math
    entropy = math.log2(len(charset)) * length
    strength = "WEAK" if entropy < 40 else "FAIR" if entropy < 60 else "GOOD" if entropy < 80 else "STRONG" if entropy < 100 else "VERY STRONG"
    strength_color = C.RED if strength == "WEAK" else C.YELLOW if strength in ("FAIR", "GOOD") else C.GREEN

    print(f"  {C.YELLOW}{C.BOLD}Security Analysis:{C.RESET}")
    print(f"  {C.CYAN}Entropy{C.RESET}:   {C.WHITE}{entropy:.1f} bits{C.RESET}")
    print(f"  {C.CYAN}Strength{C.RESET}: {strength_color}{C.BOLD}{strength}{C.RESET}")
    print(f"  {C.CYAN}Crack Time{C.RESET}: {C.WHITE}{_estimate_crack_time(entropy)}{C.RESET}")
    print()

    print(f"  {C.GREEN}{C.BOLD}Generated Passwords:{C.RESET}")
    for i, pwd in enumerate(passwords):
        # Password strength indicator
        pwd_strength = "WEAK" if len(set(pwd)) < 8 else "MEDIUM" if len(set(pwd)) < 12 else "STRONG"
        pwd_color = C.RED if pwd_strength == "WEAK" else C.YELLOW if pwd_strength == "MEDIUM" else C.GREEN
        print(f"  {C.CYAN}[{i+1}]{C.RESET}  {C.WHITE}{pwd}{C.RESET}  {pwd_color}({pwd_strength}){C.RESET}")

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def _generate_pronounceable(length: int) -> str:
    """Generate a pronounceable password."""
    vowels = "aeiou"
    consonants = "bcdfghjklmnpqrstvwxyz"
    password = []
    for i in range(length):
        if i % 2 == 0:
            password.append(secrets.choice(consonants))
        else:
            password.append(secrets.choice(vowels))
    return "".join(password)


def _generate_no_repeat(charset: str, length: int) -> str:
    """Generate password without repeating characters."""
    if length > len(charset):
        length = len(charset)
    chars = list(charset)
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars[:length])


def _estimate_crack_time(entropy: float) -> str:
    """Estimate password crack time based on entropy."""
    # Assuming 10 billion guesses per second
    guesses_per_second = 10_000_000_000
    total_combinations = 2 ** entropy
    seconds = total_combinations / guesses_per_second / 2  # Average case

    if seconds < 1:
        return "Instant"
    elif seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    elif seconds < 86400:
        return f"{seconds/3600:.1f} hours"
    elif seconds < 31536000:
        return f"{seconds/86400:.1f} days"
    elif seconds < 31536000 * 100:
        return f"{seconds/31536000:.1f} years"
    elif seconds < 31536000 * 1000000:
        return f"{seconds/31536000/1000:.1f} thousand years"
    else:
        return f"{seconds/31536000/1000000:.1f} million years"


def cmd_random_uuid(args: list, state: dict, terminal=None) -> int:
    """Generate random UUIDs. Usage: random-uuid [count] [version]"""
    count = 1
    version = 4

    if args:
        try:
            count = int(args[0])
        except ValueError:
            pass
    if len(args) > 1:
        version = int(args[1])

    count = max(1, min(100, count))
    version = max(1, min(5, version))

    print(f"\n{C.BLUE}{'='*60}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}UUID GENERATOR (v{version}){C.RESET}")
    print(f"{C.BLUE}{'='*60}{C.RESET}\n")

    for i in range(count):
        if version == 1:
            u = str(uuid.uuid1())
        elif version == 4:
            u = str(uuid.uuid4())
        else:
            u = str(uuid.uuid4())  # Default to v4

        print(f"  {C.CYAN}[{i+1}]{C.RESET}  {C.GREEN}{u}{C.RESET}")

    print(f"\n  {C.GRAY}Generated {count} UUID(s){C.RESET}")
    print(f"\n{C.BLUE}{'='*60}{C.RESET}\n")
    return 0


def cmd_random_mac(args: list, state: dict, terminal=None) -> int:
    """Generate random MAC addresses. Usage: random-mac [count] [type]"""
    count = 1
    mac_type = "random"

    if args:
        try:
            count = int(args[0])
        except ValueError:
            pass
    if len(args) > 1:
        mac_type = args[1].lower()

    count = max(1, min(50, count))

    OUI_PREFIXES = {
        "cisco": "00:00:0C",
        "vmware": "00:0C:29",
        "virtualbox": "08:00:27",
        "oracle": "00:03:93",
        "microsoft": "00:0D:3A",
        "apple": "00:03:93",
        "intel": "00:1B:21",
        "local": "02:00:00"
    }

    print(f"\n{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}MAC ADDRESS GENERATOR{C.RESET}")
    print(f"{C.BLUE}{'='*70}{C.RESET}\n")

    for i in range(count):
        if mac_type in OUI_PREFIXES:
            prefix = OUI_PREFIXES[mac_type]
            suffix = ":".join(f"{secrets.randbelow(256):02X}" for _ in range(3))
            mac = f"{prefix}:{suffix}"
        else:
            mac = ":".join(f"{secrets.randbelow(256):02X}" for _ in range(6))

        print(f"  {C.CYAN}[{i+1}]{C.RESET}  {C.GREEN}{mac}{C.RESET}")

    print(f"\n  {C.GRAY}Generated {count} MAC address(es){C.RESET}")
    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def cmd_sanitize(args: list, state: dict, terminal=None) -> int:
    """Sanitize output for safe display. Usage: sanitize <text> [mode]"""
    if not args:
        print(C.info("Usage: sanitize <text> [mode]"))
        print(C.info("Modes:"))
        print(C.info("  html     - Escape HTML characters"))
        print(C.info("  sql      - Escape SQL special characters"))
        print(C.info("  shell    - Escape shell special characters"))
        print(C.info("  url      - URL encode"))
        print(C.info("  json     - Escape JSON special characters"))
        print(C.info("  full     - Full sanitization"))
        return 0

    text = " ".join(args[:-1]) if len(args) > 1 else args[0]
    mode = args[-1].lower() if len(args) > 1 else "html"

    print(f"\n{C.BLUE}{'='*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}TEXT SANITIZATION ({mode.upper()}){C.RESET}")
    print(f"{C.BLUE}{'='*65}{C.RESET}")

    print(f"\n  {C.CYAN}Input{C.RESET}:  {C.WHITE}{text}{C.RESET}")
    print(f"  {C.YELLOW}Output{C.RESET}: ", end="")

    if mode == "html":
        import html
        result = html.escape(text)
    elif mode == "sql":
        result = text.replace("'", "''").replace('"', '""').replace(";", "")
    elif mode == "shell":
        result = re.sub(r'[^a-zA-Z0-9._-]', lambda m: f'\\{m.group()}' if m.group() not in ' _-' else m.group(), text)
    elif mode == "url":
        import urllib.parse
        result = urllib.parse.quote(text, safe='')
    elif mode == "json":
        result = json.dumps(text)[1:-1]
    elif mode == "full":
        import html
        import urllib.parse
        result = html.escape(text)
        result = urllib.parse.quote(result)
    else:
        result = text

    print(f"{C.GREEN}{result}{C.RESET}")
    print(f"\n  {C.GRAY}Length: {len(result)} chars{C.RESET}")
    print(f"\n{C.BLUE}{'='*65}{C.RESET}\n")
    return 0


def cmd_cypher(args: list, state: dict, terminal=None) -> int:
    """Encrypt text with various algorithms. Usage: cypher <text> <key> [algorithm]"""
    if len(args) < 2:
        print(C.info("Usage: cypher <text> <key> [algorithm]"))
        print(C.info("Algorithms: caesar, vigenere, xor, rot47 (default: caesar)"))
        return 0

    text = args[0]
    key = args[1]
    algo = args[2].lower() if len(args) > 2 else "vigenere"

    print(f"\n{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}ENCRYPTION ({algo.upper()}){C.RESET}")
    print(f"{C.BLUE}{'='*70}{C.RESET}")

    print(f"\n  {C.CYAN}Input{C.RESET}:  {C.WHITE}{text}{C.RESET}")
    print(f"  {C.CYAN}Key{C.RESET}:    {C.WHITE}{key}{C.RESET}")
    print(f"  {C.YELLOW}Output{C.RESET}: ", end="")

    try:
        if algo == "caesar":
            shift = sum(ord(c) for c in key) % 26
            result = _caesar_cipher(text, shift)
        elif algo == "vigenere":
            result = _vigenere_cipher(text, key, encrypt=True)
        elif algo == "xor":
            result = _xor_cipher(text, key)
        elif algo == "rot47":
            result = _rot47(text)
        else:
            result = text

        print(f"{C.GREEN}{result}{C.RESET}")
    except Exception as e:
        print(f"{C.RED}{e}{C.RESET}")
        return 1

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def cmd_decypher(args: list, state: dict, terminal=None) -> int:
    """Decrypt text. Usage: decypher <text> <key> [algorithm]"""
    if len(args) < 2:
        print(C.info("Usage: decypher <text> <key> [algorithm]"))
        print(C.info("Algorithms: caesar, vigenere, xor, rot47 (default: caesar)"))
        return 0

    text = args[0]
    key = args[1]
    algo = args[2].lower() if len(args) > 2 else "vigenere"

    print(f"\n{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}DECRYPTION ({algo.upper()}){C.RESET}")
    print(f"{C.BLUE}{'='*70}{C.RESET}")

    print(f"\n  {C.CYAN}Input{C.RESET}:  {C.WHITE}{text}{C.RESET}")
    print(f"  {C.CYAN}Key{C.RESET}:    {C.WHITE}{key}{C.RESET}")
    print(f"  {C.YELLOW}Output{C.RESET}: ", end="")

    try:
        if algo == "caesar":
            shift = sum(ord(c) for c in key) % 26
            result = _caesar_cipher(text, -shift)
        elif algo == "vigenere":
            result = _vigenere_cipher(text, key, encrypt=False)
        elif algo == "xor":
            result = _xor_cipher(text, key)
        elif algo == "rot47":
            result = _rot47(text)
        else:
            result = text

        print(f"{C.GREEN}{result}{C.RESET}")
    except Exception as e:
        print(f"{C.RED}{e}{C.RESET}")
        return 1

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def _caesar_cipher(text: str, shift: int) -> str:
    """Caesar cipher implementation."""
    result = ""
    for char in text:
        if char.isalpha():
            base = ord('A') if char.isupper() else ord('a')
            result += chr((ord(char) - base + shift) % 26 + base)
        else:
            result += char
    return result


def _vigenere_cipher(text: str, key: str, encrypt: bool = True) -> str:
    """Vigenere cipher implementation."""
    result = []
    key_index = 0
    for char in text:
        if char.isalpha():
            key_char = key[key_index % len(key)]
            key_shift = ord(key_char.upper()) - ord('A')
            if not encrypt:
                key_shift = -key_shift
            base = ord('A') if char.isupper() else ord('a')
            result.append(chr((ord(char) - base + key_shift) % 26 + base))
            key_index += 1
        else:
            result.append(char)
    return "".join(result)


def _xor_cipher(text: str, key: str) -> str:
    """XOR cipher implementation."""
    key_bytes = key.encode()
    text_bytes = text.encode()
    result = bytearray()
    for i, byte in enumerate(text_bytes):
        result.append(byte ^ key_bytes[i % len(key_bytes)])
    return result.hex()


def _rot47(text: str) -> str:
    """ROT47 cipher - rotates ASCII characters 33-126 by 47 positions."""
    result = ""
    for char in text:
        code = ord(char)
        if 33 <= code <= 126:
            result += chr(33 + ((code - 33 + 47) % 94))
        else:
            result += char
    return result


def cmd_base64_img(args: list, state: dict, terminal=None) -> int:
    """Convert image to base64. Usage: base64-img <image_path> [output_mode]"""
    if not args:
        print(C.info("Usage: base64-img <image_path> [output_mode]"))
        print(C.info("Output modes: text (default), file, html"))
        return 0

    image_path = args[0]
    output_mode = args[1].lower() if len(args) > 1 else "text"

    if not os.path.isfile(image_path):
        print(C.error(f"File not found: {image_path}"))
        return 1

    try:
        import mimetypes
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        with open(image_path, "rb") as f:
            data = f.read()

        b64_data = base64.b64encode(data).decode()

        print(f"\n{C.BLUE}{'='*70}{C.RESET}")
        print(f"  {C.BOLD}{C.WHITE}BASE64 IMAGE CONVERSION{C.RESET}")
        print(f"{C.BLUE}{'='*70}{C.RESET}")
        print(f"  {C.CYAN}File{C.RESET}:     {C.WHITE}{image_path}{C.RESET}")
        print(f"  {C.CYAN}MIME{C.RESET}:     {C.WHITE}{mime_type}{C.RESET}")
        print(f"  {C.CYAN}Size{C.RESET}:     {C.WHITE}{_fmt_size(len(data))}{C.RESET}")
        print(f"  {C.CYAN}Base64{C.RESET}:   {C.WHITE}{len(b64_data)} chars{C.RESET}\n")

        if output_mode == "html":
            data_uri = f"data:{mime_type};base64,{b64_data}"
            print(f"  {C.YELLOW}HTML Data URI:{C.RESET}")
            print(f"  {C.GREEN}{data_uri[:80]}...{C.RESET}")
        elif output_mode == "file":
            output_path = image_path + ".b64"
            with open(output_path, "w") as f:
                f.write(b64_data)
            print(f"  {C.GREEN}Saved to: {output_path}{C.RESET}")
        else:
            print(f"  {C.YELLOW}Base64 Data:{C.RESET}")
            # Show first 200 chars
            chunk_size = 80
            for i in range(0, min(len(b64_data), 400), chunk_size):
                print(f"  {C.GREEN}{b64_data[i:i+chunk_size]}{C.RESET}")
            if len(b64_data) > 400:
                print(f"  {C.GRAY}... ({len(b64_data) - 400} more characters){C.RESET}")

    except Exception as e:
        print(C.error(f"Error: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def _fmt_size(n: int) -> str:
    """Human-readable byte count."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"