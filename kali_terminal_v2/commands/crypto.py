"""
commands/crypto.py — Cryptography & encoding toolkit for KaliTerminal v2.

Commands:
  hash         Hash files (md5/sha1/sha256/sha512/sha3_256/all)
  hash-text    Hash strings directly
  encode       Encode text (base64/url/hex/binary/rot13/morse)
  decode       Decode text (base64/url/hex/binary/rot13/morse)
  jwt-decode   Decode & analyze JWT tokens
"""

import os
import hashlib
import base64
import binascii
import urllib.parse
import json
import datetime

from ui.theme import Colors

C = Colors

# ══════════════════════════════════════════════════════════════════════════════
#  HASH (files)
# ══════════════════════════════════════════════════════════════════════════════

ALGOS = {
    "md5":      hashlib.md5,
    "sha1":     hashlib.sha1,
    "sha224":   hashlib.sha224,
    "sha256":   hashlib.sha256,
    "sha384":   hashlib.sha384,
    "sha512":   hashlib.sha512,
    "sha3_256": lambda: hashlib.new("sha3_256"),
    "sha3_512": lambda: hashlib.new("sha3_512"),
    "blake2b":  lambda: hashlib.blake2b(),
    "blake2s":  lambda: hashlib.blake2s(),
}


def cmd_hash(args: list, state: dict) -> int:
    """hash <file> [algorithm] — Hash a file. Algorithms: md5/sha1/sha256/sha512/sha3_256/all"""
    if not args:
        print(C.info("Usage: hash <file> [algorithm]"))
        print(C.info(f"Algorithms: {' | '.join(ALGOS.keys())} | all (default)"))
        return 0

    filepath = args[0]
    algo     = args[1].lower() if len(args) > 1 else "all"

    if not os.path.isabs(filepath):
        filepath = os.path.join(state.get("cwd", os.getcwd()), filepath)

    if not os.path.isfile(filepath):
        print(C.error(f"File not found: {filepath}"))
        return 1

    try:
        with open(filepath, "rb") as f:
            data = f.read()
    except PermissionError:
        print(C.error("Permission denied reading file."))
        return 1

    size = os.path.getsize(filepath)
    print(f"\n{C.BLUE}{'═'*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}FILE HASH: {os.path.basename(filepath)}{C.RESET}")
    print(f"  {C.GRAY}Size: {_fmt_size(size)}{C.RESET}")
    print(f"{C.BLUE}{'═'*65}{C.RESET}\n")

    run = {algo: ALGOS[algo]} if algo != "all" and algo in ALGOS else ALGOS
    if algo not in ALGOS and algo != "all":
        print(C.error(f"Unknown algorithm: {algo}"))
        return 1

    for name, fn in run.items():
        h = fn()
        h.update(data)
        print(f"  {C.YELLOW}{C.BOLD}{name.upper():<12}{C.RESET}  {C.CYAN}{h.hexdigest()}{C.RESET}")

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}\n")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  HASH-TEXT
# ══════════════════════════════════════════════════════════════════════════════

def cmd_hash_text(args: list, state: dict) -> int:
    """hash-text <text> [algorithm] — Hash a string directly."""
    if not args:
        print(C.info("Usage: hash-text <text> [algorithm]"))
        return 0

    algo = "all"
    # Last arg might be algorithm
    if len(args) > 1 and args[-1].lower() in ALGOS:
        algo    = args[-1].lower()
        text    = " ".join(args[:-1])
    else:
        text = " ".join(args)

    data = text.encode("utf-8")

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}STRING HASH{C.RESET}")
    print(f"  {C.GRAY}Input: {text[:60]}{C.RESET}")
    print(f"{C.BLUE}{'═'*65}{C.RESET}\n")

    run = {algo: ALGOS[algo]} if algo != "all" and algo in ALGOS else \
          {"md5": ALGOS["md5"], "sha1": ALGOS["sha1"],
           "sha256": ALGOS["sha256"], "sha512": ALGOS["sha512"]}

    for name, fn in run.items():
        h = fn()
        h.update(data)
        print(f"  {C.YELLOW}{C.BOLD}{name.upper():<12}{C.RESET}  {C.CYAN}{h.hexdigest()}{C.RESET}")

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}\n")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  ENCODE
# ══════════════════════════════════════════════════════════════════════════════

MORSE = {
    'A':'.-','B':'-...','C':'-.-.','D':'-..','E':'.','F':'..-.','G':'--.','H':'....',
    'I':'..','J':'.---','K':'-.-','L':'.-..','M':'--','N':'-.','O':'---','P':'.--.','Q':'--.-',
    'R':'.-.','S':'...','T':'-','U':'..-','V':'...-','W':'.--','X':'-..-','Y':'-.--','Z':'--..',
    '0':'-----','1':'.----','2':'..---','3':'...--','4':'....-','5':'.....','6':'-....','7':'--...',
    '8':'---..','9':'----.',' ':' / ',
}
MORSE_REV = {v: k for k, v in MORSE.items()}


def _rot13(text: str) -> str:
    result = []
    for c in text:
        if 'a' <= c <= 'z':
            result.append(chr((ord(c) - ord('a') + 13) % 26 + ord('a')))
        elif 'A' <= c <= 'Z':
            result.append(chr((ord(c) - ord('A') + 13) % 26 + ord('A')))
        else:
            result.append(c)
    return "".join(result)


def _to_morse(text: str) -> str:
    return " ".join(MORSE.get(c.upper(), c) for c in text)


def _from_morse(text: str) -> str:
    words = text.split(" / ")
    result = []
    for word in words:
        chars = word.split(" ")
        result.append("".join(MORSE_REV.get(c, c) for c in chars))
    return " ".join(result)


ENCODERS = {
    "base64":  lambda t: base64.b64encode(t.encode()).decode(),
    "base32":  lambda t: base64.b32encode(t.encode()).decode(),
    "base16":  lambda t: base64.b16encode(t.encode()).decode(),
    "url":     lambda t: urllib.parse.quote(t, safe=""),
    "hex":     lambda t: t.encode().hex(),
    "binary":  lambda t: " ".join(format(b, "08b") for b in t.encode()),
    "rot13":   _rot13,
    "morse":   _to_morse,
    "html":    lambda t: t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
                          .replace('"',"&quot;").replace("'","&#x27;"),
}

DECODERS = {
    "base64":  lambda t: base64.b64decode(t).decode(errors="replace"),
    "base32":  lambda t: base64.b32decode(t).decode(errors="replace"),
    "base16":  lambda t: base64.b16decode(t).decode(errors="replace"),
    "url":     lambda t: urllib.parse.unquote(t),
    "hex":     lambda t: bytes.fromhex(t).decode(errors="replace"),
    "binary":  lambda t: "".join(chr(int(b, 2)) for b in t.split()),
    "rot13":   _rot13,
    "morse":   _from_morse,
    "html":    lambda t: t.replace("&amp;","&").replace("&lt;","<").replace("&gt;",">")
                          .replace("&quot;",'"').replace("&#x27;","'"),
}


def cmd_encode(args: list, state: dict) -> int:
    """encode <text> [format] — Encode. Formats: base64|base32|url|hex|binary|rot13|morse|html"""
    if not args:
        print(C.info("Usage: encode <text> [format]"))
        print(C.info(f"Formats: {' | '.join(ENCODERS.keys())} (default: base64)"))
        return 0

    fmt  = "base64"
    text_parts = []
    for a in args:
        if a.lower() in ENCODERS and not text_parts:
            fmt = a.lower()
        else:
            text_parts.append(a)

    text = " ".join(text_parts)
    if not text:
        print(C.error("No text to encode."))
        return 1

    print(f"\n{C.BLUE}{'═'*60}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}ENCODE → {fmt.upper()}{C.RESET}")
    print(f"{C.BLUE}{'═'*60}{C.RESET}\n")
    print(f"  {C.CYAN}Input {C.RESET}: {C.WHITE}{text}{C.RESET}")

    try:
        result = ENCODERS[fmt](text)
        print(f"  {C.YELLOW}Output{C.RESET}: {C.GREEN}{result}{C.RESET}")
    except Exception as e:
        print(C.error(f"Encode failed: {e}"))
        return 1

    # Also show common formats when encoding base64
    if fmt == "base64":
        print(f"\n  {C.GRAY}Also:")
        print(f"    URL-encoded  : {urllib.parse.quote(text, safe='')}{C.RESET}")
        print(f"    {C.GRAY}Hex          : {text.encode().hex()}{C.RESET}")

    print(f"\n{C.BLUE}{'═'*60}{C.RESET}\n")
    return 0


def cmd_decode(args: list, state: dict) -> int:
    """decode <text> [format] — Decode. Formats: base64|url|hex|binary|rot13|morse|html"""
    if not args:
        print(C.info("Usage: decode <encoded_text> [format]"))
        print(C.info(f"Formats: {' | '.join(DECODERS.keys())} (default: base64)"))
        return 0

    fmt  = "base64"
    text_parts = []
    for a in args:
        if a.lower() in DECODERS and not text_parts:
            fmt = a.lower()
        else:
            text_parts.append(a)

    text = " ".join(text_parts)
    if not text:
        print(C.error("No text to decode."))
        return 1

    print(f"\n{C.BLUE}{'═'*60}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}DECODE ← {fmt.upper()}{C.RESET}")
    print(f"{C.BLUE}{'═'*60}{C.RESET}\n")
    print(f"  {C.CYAN}Input {C.RESET}: {C.WHITE}{text}{C.RESET}")

    try:
        result = DECODERS[fmt](text)
        print(f"  {C.YELLOW}Output{C.RESET}: {C.GREEN}{result}{C.RESET}")
    except Exception as e:
        print(C.error(f"Decode failed ({fmt}): {e}"))
        # Auto-try
        for name, fn in DECODERS.items():
            if name != fmt:
                try:
                    r = fn(text)
                    if r and all(32 <= ord(c) < 127 for c in r[:20]):
                        print(f"  {C.GRAY}Tried {name}: {r}{C.RESET}")
                        break
                except Exception:
                    pass
        return 1

    print(f"\n{C.BLUE}{'═'*60}{C.RESET}\n")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
#  JWT DECODE
# ══════════════════════════════════════════════════════════════════════════════

def cmd_jwt_decode(args: list, state: dict) -> int:
    """jwt-decode <token> — Decode and inspect a JWT token (no signature verification)."""
    if not args:
        print(C.info("Usage: jwt-decode <jwt-token>"))
        print(C.info("Decodes header and payload without verifying signature."))
        return 0

    token = args[0].strip()
    parts = token.split(".")
    if len(parts) != 3:
        print(C.error("Invalid JWT: expected 3 parts (header.payload.signature)"))
        return 1

    def b64_decode_part(s: str) -> dict:
        # Add padding
        s = s + "=" * (4 - len(s) % 4)
        try:
            decoded = base64.urlsafe_b64decode(s)
            return json.loads(decoded)
        except Exception as e:
            return {"_error": str(e)}

    header  = b64_decode_part(parts[0])
    payload = b64_decode_part(parts[1])
    sig_raw = parts[2]

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}JWT TOKEN DECODER{C.RESET}")
    print(f"{C.BLUE}{'═'*65}{C.RESET}\n")

    print(f"  {C.YELLOW}━━━ HEADER ━━━{C.RESET}")
    for k, v in header.items():
        print(f"  {C.CYAN}{k:<20}{C.RESET}  {C.WHITE}{v}{C.RESET}")

    print(f"\n  {C.YELLOW}━━━ PAYLOAD ━━━{C.RESET}")
    now = datetime.datetime.utcnow().timestamp()
    for k, v in payload.items():
        val_str = str(v)
        color   = C.WHITE
        extra   = ""

        # Time fields
        if k in ("exp", "iat", "nbf") and isinstance(v, (int, float)):
            try:
                dt      = datetime.datetime.utcfromtimestamp(v)
                extra   = f"  {C.GRAY}({dt.strftime('%Y-%m-%d %H:%M:%S UTC')}){C.RESET}"
                if k == "exp":
                    if v < now:
                        extra += f"  {C.RED}⚠ EXPIRED{C.RESET}"
                        color = C.RED
                    else:
                        secs = int(v - now)
                        hrs  = secs // 3600
                        extra += f"  {C.GREEN}(expires in {hrs}h){C.RESET}"
                        color = C.GREEN
            except Exception:
                pass

        print(f"  {C.CYAN}{k:<20}{C.RESET}  {color}{val_str}{C.RESET}{extra}")

    print(f"\n  {C.YELLOW}━━━ SIGNATURE ━━━{C.RESET}")
    print(f"  {C.GRAY}(raw, not verified){C.RESET}")
    print(f"  {C.WHITE}{sig_raw[:60]}{'...' if len(sig_raw) > 60 else ''}{C.RESET}")

    # Security warnings
    alg = header.get("alg", "").upper()
    print(f"\n  {C.YELLOW}━━━ SECURITY NOTES ━━━{C.RESET}")
    if alg == "NONE":
        print(f"  {C.RED}⚠ CRITICAL: Algorithm is 'none' — NO signature! Token trivially forgeable.{C.RESET}")
    elif alg.startswith("HS"):
        print(f"  {C.YELLOW}⚠ Symmetric HMAC ({alg}) — secret must be kept private.{C.RESET}")
        print(f"  {C.GRAY}  Try: hashcat -a 0 -m 16500 <token> wordlist.txt{C.RESET}")
    elif alg.startswith("RS") or alg.startswith("ES"):
        print(f"  {C.GREEN}✔ Asymmetric algorithm ({alg}) — verify with public key.{C.RESET}")

    if "kid" in header:
        print(f"  {C.YELLOW}⚠ Key ID (kid) present — check for SQL/path injection: {header['kid']}{C.RESET}")

    print(f"\n{C.BLUE}{'═'*65}{C.RESET}\n")
    return 0


# ── Helpers ────────────────────────────────────────────────────────────────────

def _fmt_size(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ══════════════════════════════════════════════════════════════════════════════
#  Registry
# ══════════════════════════════════════════════════════════════════════════════

CRYPTO_CMDS: dict = {
    "hash":       cmd_hash,
    "hash-text":  cmd_hash_text,
    "hashtext":   cmd_hash_text,
    "encode":     cmd_encode,
    "decode":     cmd_decode,
    "jwt-decode": cmd_jwt_decode,
    "jwt":        cmd_jwt_decode,
}
