"""
commands/forensics_tools.py — Digital forensics and analysis tools (v2.0 Masterpiece).

Commands:
  - hexdump: Display hex dump of file
  - strings: Extract strings from binary
  - file-analysis: Comprehensive file analysis
  - entropy: Calculate file entropy
  - xor-data: XOR data with key
  - binwalk: Analyze binary data for embedded files
"""

import os
import sys
import hashlib
import re
import struct
import math
import json
from datetime import datetime
import binascii

from ui.theme import Colors

C = Colors


def cmd_hexdump(args: list, state: dict, terminal=None) -> int:
    """Display hex dump of file. Usage: hexdump <file> [offset] [length]"""
    if not args:
        print(C.info("Usage: hexdump <file> [offset] [length]"))
        print(C.info("Examples:"))
        print(C.info("  hexdump file.bin"))
        print(C.info("  hexdump file.bin 0x100"))
        print(C.info("  hexdump file.bin 0 256"))
        return 0

    filepath = args[0]
    offset = 0
    length = 256

    if len(args) > 1:
        try:
            offset_str = args[1]
            if offset_str.startswith("0x"):
                offset = int(offset_str, 16)
            else:
                offset = int(offset_str)
        except ValueError:
            print(C.error(f"Invalid offset: {args[1]}"))
            return 1

    if len(args) > 2:
        try:
            length = int(args[2])
        except ValueError:
            print(C.error(f"Invalid length: {args[2]}"))
            return 1

    if not os.path.isfile(filepath):
        print(C.error(f"File not found: {filepath}"))
        return 1

    print(f"\n{C.BLUE}{'='*80}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}HEXDUMP: {filepath}{C.RESET}")
    print(f"{C.BLUE}{'='*80}{C.RESET}")
    print(f"  {C.CYAN}Offset{C.RESET}: 0x{offset:08X}  {C.CYAN}Length{C.RESET}: {length} bytes\n")

    try:
        with open(filepath, "rb") as f:
            f.seek(offset)
            data = f.read(length)

        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            hex_part = hex_part.ljust(48)

            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)

            print(f"  {C.GRAY}{offset+i:08X}  {C.WHITE}{hex_part}{C.RESET}  {C.CYAN}|{C.RESET}{C.GREEN}{ascii_part}{C.RESET}{C.CYAN}|{C.RESET}")

        print(f"\n  {C.GRAY}Total bytes shown: {len(data)}{C.RESET}")

    except Exception as e:
        print(C.error(f"Error reading file: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*80}{C.RESET}\n")
    return 0


def cmd_strings_extract(args: list, state: dict, terminal=None) -> int:
    """Extract strings from binary file. Usage: strings <file> [min_length]"""
    if not args:
        print(C.info("Usage: strings <file> [min_length]"))
        return 0

    filepath = args[0]
    min_length = 4

    if len(args) > 1:
        try:
            min_length = int(args[1])
        except ValueError:
            min_length = 4

    if not os.path.isfile(filepath):
        print(C.error(f"File not found: {filepath}"))
        return 1

    print(f"\n{C.BLUE}{'='*75}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}STRINGS EXTRACTION: {filepath}{C.RESET}")
    print(f"{C.BLUE}{'='*75}{C.RESET}")

    try:
        with open(filepath, "rb") as f:
            data = f.read()

        # Extract ASCII strings
        ascii_strings = re.findall(b'[\x20-\x7E]{%d,}' % min_length, data)

        # Extract Unicode strings
        unicode_strings = []
        try:
            decoded = data.decode('utf-16-le', errors='ignore')
            unicode_strings = re.findall(r'[\x20-\x7E]{%d,}' % min_length, decoded)
        except:
            pass

        print(f"\n  {C.CYAN}File Size{C.RESET}: {_fmt_size(len(data))}")
        print(f"  {C.CYAN}Min Length{C.RESET}: {min_length}")
        print(f"  {C.CYAN}ASCII Strings{C.RESET}: {len(ascii_strings)}")
        print(f"  {C.CYAN}Unicode Strings{C.RESET}: {len(unicode_strings)}\n")

        if ascii_strings:
            print(f"  {C.YELLOW}{C.BOLD}ASCII Strings:{C.RESET}")
            for i, s in enumerate(sorted(set(strings for s in ascii_strings))[:100]):
                try:
                    print(f"    {C.GRAY}{i+1:4d}{C.RESET}  {C.GREEN}{s.decode()[:80]}{C.RESET}")
                except:
                    pass

        if unicode_strings:
            print(f"\n  {C.YELLOW}{C.BOLD}Unicode Strings:{C.RESET}")
            for i, s in enumerate(sorted(set(unicode_strings))[:50]):
                print(f"    {C.GRAY}{i+1:4d}{C.RESET}  {C.CYAN}{s[:80]}{C.RESET}")

    except Exception as e:
        print(C.error(f"Error reading file: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*75}{C.RESET}\n")
    return 0


def cmd_file_analysis(args: list, state: dict, terminal=None) -> int:
    """Comprehensive file analysis. Usage: file-analysis <file>"""
    if not args:
        print(C.info("Usage: file-analysis <file>"))
        return 0

    filepath = args[0]

    if not os.path.isfile(filepath):
        print(C.error(f"File not found: {filepath}"))
        return 1

    print(f"\n{C.RED}{C.BOLD}")
    print(f"  ╔═══════════════════════════════════════════════════════════════════╗")
    print(f"  ║                    FILE ANALYSIS                                 ║")
    print(f"  ╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{C.RESET}")

    try:
        stat = os.stat(filepath)
        filename = os.path.basename(filepath)

        # File type detection
        with open(filepath, "rb") as f:
            header = f.read(32)
            magic = header[:8]

        file_type = _detect_file_type(header, filename)

        print(f"  {C.CYAN}Filename{C.RESET}:   {C.WHITE}{filename}{C.RESET}")
        print(f"  {C.CYAN}Type{C.RESET}:       {C.WHITE}{file_type}{C.RESET}")
        print(f"  {C.CYAN}Size{C.RESET}:       {C.WHITE}{_fmt_size(stat.st_size)}{C.RESET}")
        print(f"  {C.CYAN}Permissions{C.RESET}: {C.WHITE}{_fmt_perms(stat.st_mode)}{C.RESET}")
        print(f"  {C.CYAN}Created{C.RESET}:   {C.WHITE}{datetime.fromtimestamp(stat.st_ctime)}{C.RESET}")
        print(f"  {C.CYAN}Modified{C.RESET}:   {C.WHITE}{datetime.fromtimestamp(stat.st_mtime)}{C.RESET}")
        print(f"  {C.CYAN}Accessed{C.RESET}:   {C.WHITE}{datetime.fromtimestamp(stat.st_atime)}{C.RESET}")

        print(f"\n  {C.YELLOW}{C.BOLD}Hashes:{C.RESET}")
        with open(filepath, "rb") as f:
            data = f.read()

        print(f"  {C.CYAN}MD5{C.RESET}:    {C.GREEN}{hashlib.md5(data).hexdigest()}{C.RESET}")
        print(f"  {C.CYAN}SHA1{C.RESET}:   {C.GREEN}{hashlib.sha1(data).hexdigest()}{C.RESET}")
        print(f"  {C.CYAN}SHA256{C.RESET}: {C.GREEN}{hashlib.sha256(data).hexdigest()}{C.RESET}")

        print(f"\n  {C.YELLOW}{C.BOLD}Entropy Analysis:{C.RESET}")
        entropy = _calculate_file_entropy(data)
        print(f"  {C.CYAN}Entropy{C.RESET}: {C.WHITE}{entropy:.4f}{C.RESET}")
        print(f"  {C.CYAN}Type{C.RESET}:     {C.WHITE}{_entropy_type(entropy)}{C.RESET}")

        # Check for known signatures
        signatures = _check_signatures(header)
        if signatures:
            print(f"\n  {C.YELLOW}{C.BOLD}Detected Signatures:{C.RESET}")
            for sig in signatures:
                print(f"    {C.GREEN}{sig}{C.RESET}")

        # Magic bytes
        print(f"\n  {C.YELLOW}{C.BOLD}Magic Bytes:{C.RESET}")
        print(f"  {C.GRAY}{' '.join(f'{b:02X}' for b in header[:16])}{C.RESET}")

        # Suspicious indicators
        suspicious = _check_suspicious(data)
        if suspicious:
            print(f"\n  {C.YELLOW}{C.BOLD}Potential Indicators:{C.RESET}")
            for ind in suspicious:
                print(f"    {C.RED}{ind}{C.RESET}")

    except Exception as e:
        print(C.error(f"Error analyzing file: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*80}{C.RESET}\n")
    return 0


def _detect_file_type(header: bytes, filename: str) -> str:
    """Detect file type from header bytes and filename."""
    magic_signatures = {
        b"\x89PNG": "PNG Image",
        b"\xFF\xD8\xFF": "JPEG Image",
        b"GIF87a": "GIF Image",
        b"GIF89a": "GIF Image",
        b"RIFF": "RIFF (AVI/WAV)",
        b"%PDF": "PDF Document",
        b"\x1F\x8B": "GZIP Compressed",
        b"PK\x03\x04": "ZIP Archive",
        b"\x7FELF": "ELF Executable",
        b"MZ": "Windows Executable",
        b"\xCA\xFE\xBA\xBE": "Mach-O Executable",
        b"SQLite": "SQLite Database",
        b"\x00\x00\x01\x00": "ICO Image",
        b"BZh": "BZIP2 Compressed",
        b"\xFD7zXZ": "XZ Compressed",
    }

    for magic, ftype in magic_signatures.items():
        if header.startswith(magic):
            return ftype

    # Check by extension
    ext = os.path.splitext(filename)[1].lower()
    ext_types = {
        ".py": "Python Script",
        ".js": "JavaScript",
        ".html": "HTML Document",
        ".css": "CSS Stylesheet",
        ".json": "JSON Data",
        ".xml": "XML Document",
        ".txt": "Text File",
        ".md": "Markdown",
        ".sh": "Shell Script",
        ".c": "C Source Code",
        ".cpp": "C++ Source Code",
        ".java": "Java Source",
        ".class": "Java Class",
        ".so": "Shared Object",
        ".dll": "Dynamic Link Library",
        ".db": "Database",
        ".sqlite": "SQLite Database",
    }

    if ext in ext_types:
        return ext_types[ext]

    return "Unknown/Binary"


def _calculate_file_entropy(data: bytes) -> float:
    """Calculate Shannon entropy of file data."""
    if not data:
        return 0

    import math
    freq = {}
    for byte in data:
        freq[byte] = freq.get(byte, 0) + 1

    entropy = 0
    for count in freq.values():
        prob = count / len(data)
        entropy -= prob * math.log2(prob)

    return entropy


def _entropy_type(entropy: float) -> str:
    """Interpret entropy value."""
    if entropy < 3:
        return "Very Low (likely text/plain)"
    elif entropy < 4.5:
        return "Low (likely text/formatted)"
    elif entropy < 5.5:
        return "Medium (likely compressed/encrypted)"
    elif entropy < 7:
        return "High (likely compressed/encrypted)"
    else:
        return "Very High (likely encrypted/random)"


def _fmt_perms(mode: int) -> str:
    """Format file permissions."""
    import stat
    perms = []
    for who in ["USR", "GRP", "OTH"]:
        for what in ["R", "W", "X"]:
            attr = getattr(stat, f"S_I{what}{who}")
            perms.append("rwx"[["R", "W", "X"].index(what)] if mode & attr else "-")
    return "".join(perms)


def _check_signatures(header: bytes) -> list:
    """Check for known file signatures."""
    signatures = []

    sigs = [
        (b"PK", "ZIP/Office Document"),
        (b"%PDF", "PDF"),
        (b"\x89PNG", "PNG"),
        (b"\xFF\xD8\xFF", "JPEG"),
        (b"GIF", "GIF"),
        (b"RIFF", "RIFF Container"),
        (b"\x7FELF", "ELF Executable"),
        (b"MZ", "Windows Executable"),
        (b"SQLite", "SQLite"),
        (b"-----BEGIN", "PEM Certificate/Key"),
    ]

    for sig, name in sigs:
        if header.startswith(sig) or sig in header[:256]:
            signatures.append(name)

    return signatures


def _check_suspicious(data: bytes) -> list:
    """Check for suspicious indicators in data."""
    indicators = []

    suspicious_patterns = [
        (b"eval(", "JavaScript eval()"),
        (b"base64_decode", "Base64 decoding"),
        (b"system(", "System command execution"),
        (b"exec(", "Command execution"),
        (b"shell_exec", "Shell execution"),
        (b"passthru", "Command execution"),
        (b"curl_init", "HTTP request"),
        (b"http://", "HTTP URL"),
        (b"https://", "HTTPS URL"),
        (b"\\x", "Hex-encoded data"),
        (b"\\u00", "Unicode escape"),
    ]

    for pattern, name in suspicious_patterns:
        if pattern.lower() in data.lower():
            indicators.append(f"Contains: {name}")

    return indicators


def cmd_entropy(args: list, state: dict, terminal=None) -> int:
    """Calculate file entropy. Usage: entropy <file>"""
    if not args:
        print(C.info("Usage: entropy <file>"))
        return 0

    filepath = args[0]

    if not os.path.isfile(filepath):
        print(C.error(f"File not found: {filepath}"))
        return 1

    print(f"\n{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}ENTROPY ANALYSIS: {filepath}{C.RESET}")
    print(f"{C.BLUE}{'='*70}{C.RESET}\n")

    try:
        with open(filepath, "rb") as f:
            data = f.read()

        entropy = _calculate_file_entropy(data)

        print(f"  {C.CYAN}File Size{C.RESET}: {_fmt_size(len(data))}")
        print(f"  {C.CYAN}Entropy{C.RESET}:    {C.WHITE}{entropy:.6f}{C.RESET}")
        print(f"  {C.CYAN}Classification{C.RESET}: {C.WHITE}{_entropy_type(entropy)}{C.RESET}")

        # Visual entropy map
        print(f"\n  {C.YELLOW}{C.BOLD}Entropy Visualization:{C.RESET}")

        # Calculate entropy by chunks
        chunk_size = max(1, len(data) // 40)
        max_bar = 40

        print(f"  {C.GRAY}Min{C.RESET} ", end="")
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i+chunk_size]
            chunk_entropy = _calculate_file_entropy(chunk)

            # Map entropy to bar character
            if chunk_entropy < 2:
                bar_char = " "
            elif chunk_entropy < 3:
                bar_char = "."
            elif chunk_entropy < 4:
                bar_char = ":"
            elif chunk_entropy < 5:
                bar_char = "+"
            elif chunk_entropy < 6:
                bar_char = "="
            elif chunk_entropy < 7:
                bar_char = "*"
            else:
                bar_char = "#"

            color = C.GREEN if chunk_entropy < 4 else C.YELLOW if chunk_entropy < 6 else C.RED
            print(f"{color}{bar_char}{C.RESET}", end="")

        print(f" {C.GRAY}Max{C.RESET}")
        print(f"  {C.GRAY}(Low entropy = text/compressed, High entropy = encrypted/random){C.RESET}")

    except Exception as e:
        print(C.error(f"Error: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def cmd_xor_data(args: list, state: dict, terminal=None) -> int:
    """XOR data with key. Usage: xor-data <file> <key> [output]"""
    if len(args) < 2:
        print(C.info("Usage: xor-data <file> <key> [output]"))
        return 0

    filepath = args[0]
    key = args[1].encode()
    output_path = args[2] if len(args) > 2 else filepath + ".xor"

    if not os.path.isfile(filepath):
        print(C.error(f"File not found: {filepath}"))
        return 1

    print(f"\n{C.BLUE}{'='*70}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}XOR OPERATION{C.RESET}")
    print(f"{C.BLUE}{'='*70}{C.RESET}")

    try:
        with open(filepath, "rb") as f:
            data = f.read()

        print(f"  {C.CYAN}Input{C.RESET}:  {C.WHITE}{filepath}{C.RESET}")
        print(f"  {C.CYAN}Key{C.RESET}:    {C.WHITE}{args[1]}{C.RESET}")
        print(f"  {C.CYAN}Size{C.RESET}:   {C.WHITE}{_fmt_size(len(data))}{C.RESET}")

        # Perform XOR
        result = bytearray()
        for i, byte in enumerate(data):
            result.append(byte ^ key[i % len(key)])

        # Save output
        with open(output_path, "wb") as f:
            f.write(result)

        print(f"  {C.GREEN}Output{C.RESET}: {C.WHITE}{output_path}{C.RESET}")
        print(f"  {C.GREEN}Bytes written{C.RESET}: {len(result)}")

    except Exception as e:
        print(C.error(f"Error: {e}"))
        return 1

    print(f"\n{C.BLUE}{'='*70}{C.RESET}\n")
    return 0


def cmd_binwalk_extract(args: list, state: dict, terminal=None) -> int:
    """Analyze binary for embedded files. Usage: binwalk <file> [extract_dir]"""
    if not args:
        print(C.info("Usage: binwalk <file> [extract_dir]"))
        return 0

    filepath = args[0]
    extract_dir = args[1] if len(args) > 1 else os.path.splitext(filepath)[0] + "_extracted"

    if not os.path.isfile(filepath):
        print(C.error(f"File not found: {filepath}"))
        return 1

    print(f"\n{C.RED}{C.BOLD}")
    print(f"  ╔═══════════════════════════════════════════════════════════════════╗")
    print(f"  ║                    BINWALK ANALYSIS                              ║")
    print(f"  ╚═══════════════════════════════════════════════════════════════════╝")
    print(f"{C.RESET}")

    try:
        with open(filepath, "rb") as f:
            data = f.read()

        print(f"  {C.CYAN}File{C.RESET}: {_fmt_size(len(data))}\n")

        # Known signatures to search for
        signatures = [
            (b"\x89PNG", "PNG Image", "PNG"),
            (b"\xFF\xD8\xFF", "JPEG Image", "JPG"),
            (b"PK\x03\x04", "ZIP Archive", "ZIP"),
            (b"%PDF", "PDF Document", "PDF"),
            (b"\x1F\x8B", "GZIP Compressed", "GZ"),
            (b"\x7FELF", "ELF Executable", "ELF"),
            (b"MZ", "Windows Executable", "EXE"),
            (b"GIF87a", "GIF Image", "GIF"),
            (b"GIF89a", "GIF Image", "GIF"),
            (b"RIFF", "RIFF Container", "RIFF"),
        ]

        found_signatures = []

        for sig, name, ext in signatures:
            pos = 0
            while True:
                pos = data.find(sig, pos)
                if pos == -1:
                    break
                found_signatures.append((pos, name, ext, sig))
                pos += 1

        if found_signatures:
            print(f"  {C.YELLOW}{C.BOLD}Found Signatures:{C.RESET}\n")
            print(f"  {C.BOLD}{C.GRAY}{'Offset':<12}{'Type':<25}{'Entropy':<10}{C.RESET}")
            print(f"  {C.BLUE}{'-'*60}{C.RESET}")

            for offset, name, ext, sig in sorted(found_signatures):
                # Calculate entropy around signature
                start = max(0, offset - 16)
                end = min(len(data), offset + 64)
                chunk_entropy = _calculate_file_entropy(data[start:end])

                entropy_str = f"{chunk_entropy:.2f}"
                print(f"  {C.CYAN}0x{offset:08X}{C.RESET}  {C.WHITE}{name:<25}{C.RESET} {C.GREEN}{entropy_str:<10}{C.RESET}")

            print(f"\n  {C.GRAY}Total signatures found: {len(found_signatures)}{C.RESET}")
        else:
            print(f"  {C.YELLOW}No common signatures found.{C.RESET}")
            print(f"  {C.GRAY}File may be compressed, encrypted, or contain custom format.{C.RESET}")

        # Overall entropy
        overall_entropy = _calculate_file_entropy(data)
        print(f"\n  {C.CYAN}Overall Entropy{C.RESET}: {C.WHITE}{overall_entropy:.4f}{C.RESET}")
        print(f"  {C.CYAN}Analysis{C.RESET}: {_entropy_type(overall_entropy)}")

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