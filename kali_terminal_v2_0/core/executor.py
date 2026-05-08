"""
core/executor.py — Executes real Linux shell commands (v2.0 Masterpiece).

Features:
  - Timed execution with elapsed display
  - Command logging to file
  - Output capture mode for plugins
  - Better signal handling
  - Timeout support
  - Background job tracking
"""

import os
import sys
import subprocess
import signal
import time
from datetime import datetime

from ui.theme import Colors
from core.config import get_config

C = Colors


class CommandResult:
    """Lightweight struct holding execution outcome."""
    __slots__ = ("exit_code", "captured_output", "error_msg", "elapsed", "command")

    def __init__(self, exit_code=0, captured_output="", error_msg="",
                 elapsed=0.0, command=""):
        self.exit_code = exit_code
        self.captured_output = captured_output
        self.error_msg = error_msg
        self.elapsed = elapsed
        self.command = command

    @property
    def success(self) -> bool:
        return self.exit_code == 0


def execute(command: str, cwd: str, capture: bool = False,
            timeout: int = None) -> CommandResult:
    """
    Execute a shell command string.

    Args:
        command:  The shell command to run
        cwd:      Current working directory
        capture:  If True, capture output instead of streaming
        timeout:  Max seconds to wait (None = infinite)

    Returns:
        CommandResult with exit code and optional captured output.
    """
    if not command.strip():
        return CommandResult(exit_code=0)

    command = os.path.expandvars(command)
    env = os.environ.copy()
    config = get_config()

    # Log command
    if config.get("log_commands"):
        _log_command(command, cwd)

    start_time = time.time()

    try:
        if capture:
            # Capture mode: for plugin use
            proc = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
                executable="/bin/bash",
            )
            elapsed = time.time() - start_time
            return CommandResult(
                exit_code=proc.returncode,
                captured_output=proc.stdout,
                error_msg=proc.stderr,
                elapsed=elapsed,
                command=command,
            )
        else:
            # Streaming mode: real-time output
            proc = subprocess.Popen(
                command,
                shell=True,
                cwd=cwd,
                env=env,
                stdin=sys.stdin,
                stdout=sys.stdout,
                stderr=sys.stderr,
                executable="/bin/bash",
            )
            proc.wait(timeout=timeout)
            elapsed = time.time() - start_time

            # Show elapsed time for long-running commands
            if elapsed > 2.0:
                print(f"\n{C.DIM}[Completed in {elapsed:.2f}s]{C.RESET}")

            return CommandResult(
                exit_code=proc.returncode,
                elapsed=elapsed,
                command=command,
            )

    except subprocess.TimeoutExpired:
        proc.kill()
        print(C.error(f"Command timed out after {timeout}s"))
        return CommandResult(exit_code=124, error_msg="Timeout")

    except KeyboardInterrupt:
        try:
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=2)
        except Exception:
            pass
        print()
        return CommandResult(exit_code=130, error_msg="Interrupted")

    except FileNotFoundError as e:
        msg = f"command not found: {command.split()[0]}"
        print(C.error(msg))
        return CommandResult(exit_code=127, error_msg=msg)

    except PermissionError as e:
        msg = f"Permission denied: {e}"
        print(C.error(msg))
        return CommandResult(exit_code=126, error_msg=msg)

    except Exception as e:
        msg = f"Execution error: {e}"
        print(C.error(msg))
        return CommandResult(exit_code=1, error_msg=msg)


def execute_capture(command: str, cwd: str, timeout: int = 30) -> CommandResult:
    """Execute and capture output (for plugin/internal use)."""
    return execute(command, cwd, capture=True, timeout=timeout)


def which(cmd: str) -> str:
    """Return full path of a command if it exists on PATH, else ''."""
    result = subprocess.run(
        ["which", cmd], capture_output=True, text=True
    )
    return result.stdout.strip()


def is_command_available(cmd: str) -> bool:
    """True if `cmd` is findable on PATH."""
    return bool(which(cmd))


def _log_command(command: str, cwd: str):
    """Append command to log file."""
    try:
        from core.config import LOG_FILE
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user = os.environ.get("USER", "root")
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a") as f:
            f.write(f"[{timestamp}] [{user}@{cwd}] {command}\n")
    except Exception:
        pass