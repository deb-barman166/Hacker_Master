"""
core/executor.py — Shell Command Executor for Kali Terminal v1.0

Executes real Linux commands via subprocess with:
  • Real-time output streaming
  • Graceful Ctrl+C handling
  • Full shell support (pipes, redirects, &&, ||, ;)
  • Environment passthrough
  • Exit code capture for prompt indicator
"""

import os
import sys
import signal
import subprocess

from ui.theme import Colors

C = Colors


class CommandResult:
    """Execution outcome."""
    __slots__ = ("exit_code", "captured_output", "error_msg")

    def __init__(self, exit_code: int = 0, captured_output: str = "",
                 error_msg: str = ""):
        self.exit_code       = exit_code
        self.captured_output = captured_output
        self.error_msg       = error_msg

    @property
    def success(self) -> bool:
        return self.exit_code == 0


def execute(command: str, cwd: str, env: dict = None) -> CommandResult:
    """
    Execute a shell command with real-time I/O streaming.
    Supports full shell syntax: pipes, redirects, &&, ||, ;, &
    """
    if not command.strip():
        return CommandResult(exit_code=0)

    command = os.path.expandvars(command)
    run_env = env or os.environ.copy()

    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            cwd=cwd,
            env=run_env,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            executable="/bin/bash",
        )
        proc.wait()
        return CommandResult(exit_code=proc.returncode)

    except KeyboardInterrupt:
        try:
            proc.send_signal(signal.SIGINT)
            proc.wait(timeout=2)
        except Exception:
            pass
        print()
        return CommandResult(exit_code=130, error_msg="Interrupted")

    except FileNotFoundError:
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


def which(cmd: str) -> str | None:
    result = subprocess.run(["which", cmd], capture_output=True, text=True)
    out = result.stdout.strip()
    return out if out else None


def is_available(cmd: str) -> bool:
    return which(cmd) is not None
