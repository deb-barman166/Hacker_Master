"""
commands/aliases.py — Alias management for Kali Terminal v2.0 Masterpiece.
"""

import os
import re
from ui.theme import Colors

C = Colors


class AliasManager:
    """Manages command aliases."""

    def __init__(self):
        # Default aliases
        self.aliases = {
            "ll": "ls -la",
            "la": "ls -la",
            "l": "ls -l",
            "grep": "grep --color=auto",
            "cls": "clear",
            "..": "cd ..",
            "...": "cd ../..",
            "home": "cd ~",
            "doc": "cd ~/Documents",
            "dl": "cd ~/Downloads",
        }

    def expand(self, cmd: str) -> str:
        """Expand aliases in command."""
        parts = cmd.split()
        if not parts:
            return cmd

        first_word = parts[0].strip()

        # Check if it's an alias
        if first_word in self.aliases:
            expanded = self.aliases[first_word]
            if len(parts) > 1:
                return f"{expanded} {' '.join(parts[1:])}"
            return expanded

        # Check if first word contains =
        if "=" in cmd and not os.path.exists(first_word):
            return cmd

        return cmd

    def set_alias(self, name: str, value: str):
        """Set an alias."""
        self.aliases[name] = value

    def remove_alias(self, name: str) -> bool:
        """Remove an alias."""
        if name in self.aliases:
            del self.aliases[name]
            return True
        return False

    def list_aliases(self) -> dict:
        """List all aliases."""
        return self.aliases.copy()


def cmd_alias(args: list, state: dict, terminal=None) -> int:
    """Create an alias. Usage: alias name=command"""
    if not args:
        return cmd_aliases(args, state, terminal)

    for arg in args:
        if "=" in arg:
            name, _, value = arg.partition("=")
            name = name.strip()
            value = value.strip().strip('"').strip("'")

            if not name:
                print(C.error("alias: name required"))
                return 1

            if terminal:
                terminal.aliases.set_alias(name, value)
                print(C.success(f"Alias '{name}' set to '{value}'"))
            else:
                print(C.error("Terminal context not available"))
                return 1
        else:
            print(C.warn(f"alias: invalid format: {arg} (use name=value)"))

    return 0


def cmd_unalias(args: list, state: dict, terminal=None) -> int:
    """Remove an alias. Usage: unalias name"""
    if not args:
        print(C.error("unalias: name required"))
        return 1

    for name in args:
        if terminal:
            if terminal.aliases.remove_alias(name):
                print(C.success(f"Alias '{name}' removed"))
            else:
                print(C.warn(f"unalias: '{name}': not found"))
        else:
            print(C.error("Terminal context not available"))
            return 1

    return 0


def cmd_aliases(args: list, state: dict, terminal=None) -> int:
    """List all aliases."""
    if not terminal:
        print(C.error("Terminal context not available"))
        return 1

    aliases = terminal.aliases.list_aliases()

    if not aliases:
        print(C.info("No aliases defined"))
        return 0

    print(f"\n{C.BLUE}{'='*60}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}ALIASES ({len(aliases)}){C.RESET}")
    print(f"{C.BLUE}{'='*60}{C.RESET}")

    for name, value in sorted(aliases.items()):
        print(f"  {C.CYAN}{name:<15}{C.RESET} {C.GRAY}->{C.RESET} {C.WHITE}{value}{C.RESET}")

    print(f"\n{C.BLUE}{'='*60}{C.RESET}\n")
    return 0