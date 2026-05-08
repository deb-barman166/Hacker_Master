"""
commands/text_tools.py — Text formatting and manipulation tools (v2.0 Masterpiece).

Commands:
  - json-format: Format JSON file
  - json-minify: Minify JSON
  - yaml-convert: YAML to JSON/JSON to YAML
  - markdown: View markdown rendered
  - ascii-table: Generate ASCII table
  - regex-test: Test regular expressions
"""

import os
import json
import re
from ui.theme import Colors

C = Colors


def cmd_json_format(args: list, state: dict, terminal=None) -> int:
    """Format JSON file or string. Usage: json-format <file|text>"""
    if not args:
        print(C.info("Usage: json-format <file|json_string>"))
        return 0

    input_text = args[0]

    # Try to read from file
    if os.path.isfile(input_text):
        try:
            with open(input_text, 'r') as f:
                data = json.load(f)
            output = json.dumps(data, indent=2, sort_keys=True)
            print(f"\n{C.GREEN}Formatted JSON from file:{C.RESET}")
            print(output)
        except json.JSONDecodeError as e:
            print(C.error(f"Invalid JSON: {e}"))
            return 1
        except Exception as e:
            print(C.error(f"Error: {e}"))
            return 1
    else:
        # Try to parse as JSON string
        try:
            data = json.loads(input_text)
            output = json.dumps(data, indent=2, sort_keys=True)
            print(f"\n{C.GREEN}Formatted JSON:{C.RESET}")
            print(output)
        except json.JSONDecodeError as e:
            print(C.error(f"Invalid JSON: {e}"))
            return 1

    return 0


def cmd_json_minify(args: list, state: dict, terminal=None) -> int:
    """Minify JSON. Usage: json-minify <file|text>"""
    if not args:
        print(C.info("Usage: json-minify <file|json_string>"))
        return 0

    input_text = args[0]

    if os.path.isfile(input_text):
        try:
            with open(input_text, 'r') as f:
                data = json.load(f)
            output = json.dumps(data, separators=(',', ':'))
            print(f"\n{C.GREEN}Minified JSON:{C.RESET}")
            print(output)
            print(f"\n  {C.GRAY}Original: {os.path.getsize(input_text)} bytes")
            print(f"  {C.GRAY}Minified: {len(output)} bytes")
        except Exception as e:
            print(C.error(f"Error: {e}"))
            return 1
    else:
        try:
            data = json.loads(input_text)
            output = json.dumps(data, separators=(',', ':'))
            print(f"\n{C.GREEN}Minified JSON:{C.RESET}")
            print(output)
        except json.JSONDecodeError as e:
            print(C.error(f"Invalid JSON: {e}"))
            return 1

    return 0


def cmd_yaml_convert(args: list, state: dict, terminal=None) -> int:
    """Convert YAML to JSON or vice versa. Usage: yaml-convert <file> [to]"""
    if not args:
        print(C.info("Usage: yaml-convert <file> [json|yaml]"))
        return 0

    filepath = args[0]
    target = args[1].lower() if len(args) > 1 else "json"

    try:
        import yaml
    except ImportError:
        print(C.error("PyYAML required. Install with: pip install pyyaml"))
        return 1

    if not os.path.isfile(filepath):
        print(C.error(f"File not found: {filepath}"))
        return 1

    try:
        with open(filepath, 'r') as f:
            content = f.read()

        if filepath.endswith('.yaml') or filepath.endswith('.yml'):
            # Convert YAML to JSON
            data = yaml.safe_load(content)
            output = json.dumps(data, indent=2, sort_keys=True)
            print(f"\n{C.GREEN}Converted to JSON:{C.RESET}")
            print(output)
        elif filepath.endswith('.json'):
            # Convert JSON to YAML
            data = json.loads(content)
            output = yaml.dump(data, default_flow_style=False)
            print(f"\n{C.GREEN}Converted to YAML:{C.RESET}")
            print(output)
        else:
            print(C.error("File must have .json, .yaml, or .yml extension"))
            return 1

    except Exception as e:
        print(C.error(f"Conversion error: {e}"))
        return 1

    return 0


def cmd_markdown(args: list, state: dict, terminal=None) -> int:
    """View markdown rendered in terminal. Usage: markdown <file>"""
    if not args:
        print(C.info("Usage: markdown <file>"))
        return 0

    filepath = args[0]

    if not os.path.isfile(filepath):
        print(C.error(f"File not found: {filepath}"))
        return 1

    try:
        with open(filepath, 'r') as f:
            content = f.read()

        # Simple markdown rendering
        print(f"\n{C.CYAN}{'='*70}{C.RESET}")
        print(f"{C.BOLD}{C.WHITE}Markdown Preview: {filepath}{C.RESET}")
        print(f"{C.CYAN}{'='*70}{C.RESET}\n")

        for line in content.split('\n'):
            line = line.rstrip()

            # Headers
            if line.startswith('### '):
                print(f"{C.YELLOW}{C.BOLD}{line[4:]}{C.RESET}")
            elif line.startswith('## '):
                print(f"{C.YELLOW}{C.BOLD}{line[3:]}{C.RESET}")
            elif line.startswith('# '):
                print(f"{C.YELLOW}{C.BOLD}{line[2:]}{C.RESET}")

            # Bold
            elif '**' in line:
                line = re.sub(r'\*\*(.+?)\*\*', f"{C.BOLD}\\1{C.RESET}", line)
                print(line)

            # Code blocks
            elif line.startswith('```'):
                pass

            # Lists
            elif line.startswith('- '):
                print(f"  {C.CYAN}*{C.RESET} {line[2:]}")

            # Regular text
            elif line.strip():
                print(line)

    except Exception as e:
        print(C.error(f"Error: {e}"))
        return 1

    print(f"\n{C.CYAN}{'='*70}{C.RESET}\n")
    return 0


def cmd_ascii_table(args: list, state: dict, terminal=None) -> int:
    """Generate ASCII table. Usage: ascii-table <headers> [data...]"""
    if len(args) < 2:
        print(C.info("Usage: ascii-table <col1,col2,...> <row1> <row2> ..."))
        print(C.info("Example: ascii-table 'Name,Age,City' 'John,25,NYC' 'Jane,30,LA'"))
        return 0

    headers = [h.strip() for h in args[0].split(',')]
    rows = []

    for arg in args[1:]:
        rows.append([cell.strip() for cell in arg.split(',')])

    if not rows:
        print(C.error("No data rows provided"))
        return 1

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(cell))

    total_width = sum(col_widths) + len(headers) * 3 + 1

    print(f"\n{C.BLUE}{'='*total_width}{C.RESET}")

    # Header
    header_line = "│"
    for i, h in enumerate(headers):
        header_line += f" {h:<{col_widths[i]}} │"
    print(header_line)

    # Separator
    sep_line = "├" + "┼".join(["─" * (w + 2) for w in col_widths]) + "┤"
    print(sep_line.replace("┼", "┼").replace("┤", "┤"))

    # Rows
    for row in rows:
        row_line = "│"
        for i, cell in enumerate(row):
            if i < len(col_widths):
                row_line += f" {cell:<{col_widths[i]}} │"
        print(f"{C.CYAN}{row_line}{C.RESET}")

    print(f"{C.BLUE}{'='*total_width}{C.RESET}\n")
    return 0


def cmd_regex_test(args: list, state: dict, terminal=None) -> int:
    """Test regular expressions. Usage: regex-test <pattern> [text]"""
    if not args:
        print(C.info("Usage: regex-test <pattern> [text]"))
        print(C.info("Example: regex-test '^\\w+@\\w+\\.\\w+$' 'test@example.com'"))
        return 0

    pattern = args[0]
    text = args[1] if len(args) > 1 else ""

    try:
        regex = re.compile(pattern)
        print(f"\n{C.BLUE}{'='*65}{C.RESET}")
        print(f"  {C.BOLD}{C.WHITE}REGEX TEST{C.RESET}")
        print(f"{C.BLUE}{'='*65}{C.RESET}")
        print(f"  {C.CYAN}Pattern{C.RESET}: {C.GREEN}{pattern}{C.RESET}")

        if text:
            print(f"  {C.CYAN}Text{C.RESET}: {C.WHITE}{text}{C.RESET}\n")

            # Find all matches
            matches = regex.findall(text)
            print(f"  {C.YELLOW}Matches found: {len(matches)}{C.RESET}")

            if matches:
                print(f"\n  {C.GREEN}{C.BOLD}Matches:{C.RESET}")
                for i, match in enumerate(matches, 1):
                    print(f"    {C.CYAN}{i}.{C.RESET} {C.WHITE}{match}{C.RESET}")

                # Show match positions
                print(f"\n  {C.YELLOW}{C.BOLD}Match Positions:{C.RESET}")
                for match in regex.finditer(text):
                    print(f"    {C.CYAN}Match: '{match.group()}' at {match.span()}{C.RESET}")

            # Test if full match
            full_match = regex.fullmatch(text)
            if full_match:
                print(f"\n  {C.GREEN}{C.BOLD}[+] Full match!{C.RESET}")
            else:
                print(f"\n  {C.RED}[-] No full match{C.RESET}")

        print(f"\n{C.BLUE}{'='*65}{C.RESET}\n")

    except re.error as e:
        print(C.error(f"Invalid regex: {e}"))
        return 1

    return 0