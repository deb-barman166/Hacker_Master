"""
core/plugin_system.py — Plugin system for Kali Terminal v2.0 Masterpiece.
"""

import os
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Callable, Any


class Plugin:
    """Represents a loaded plugin."""

    def __init__(self, name: str, module: Any, commands: Dict[str, Callable]):
        self.name = name
        self.module = module
        self.commands = commands
        self.enabled = True

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True


class PluginManager:
    """Manages plugin loading and lifecycle."""

    def __init__(self, terminal):
        self.terminal = terminal
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_dir = Path(__file__).parent.parent / "plugins"
        self._load_builtin_plugins()

    def _load_builtin_plugins(self):
        """Load any built-in plugins from plugins directory."""
        if not self.plugin_dir.exists():
            return

        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("_"):
                continue
            self._load_plugin_file(plugin_file)

    def _load_plugin_file(self, plugin_file: Path):
        """Load a plugin from a Python file."""
        try:
            spec = importlib.util.spec_from_file_location(
                plugin_file.stem, plugin_file
            )
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[plugin_file.stem] = module
                spec.loader.exec_module(module)

                # Look for plugin registration
                if hasattr(module, "register"):
                    plugin_info = module.register(self.terminal)
                    if plugin_info:
                        name = plugin_info.get("name", plugin_file.stem)
                        commands = plugin_info.get("commands", {})
                        self.plugins[name] = Plugin(name, module, commands)

        except Exception as e:
            print(f"Warning: Failed to load plugin {plugin_file}: {e}")

    def load_all(self):
        """Load all available plugins."""
        for name, plugin in self.plugins.items():
            plugin.enable()
        print(f"  {len(self.plugins)} plugins loaded")

    def try_dispatch(self, cmd: str, args: list, state: dict) -> int | None:
        """Try to dispatch a command to a plugin."""
        for plugin in self.plugins.values():
            if plugin.enabled and cmd in plugin.commands:
                return plugin.commands[cmd](args, state, self.terminal)
        return None

    def list_plugins(self) -> list:
        """List all loaded plugins."""
        return [(name, p.enabled) for name, p in self.plugins.items()]

    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin by name."""
        if name in self.plugins:
            self.plugins[name].enable()
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin by name."""
        if name in self.plugins:
            self.plugins[name].disable()
            return True
        return False