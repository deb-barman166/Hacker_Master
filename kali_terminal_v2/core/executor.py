"""
core/executor.py — System command executor for KaliTerminal v2.

Handles:
  - Pipe chains:        cmd1 | cmd2 | cmd3
  - Output redirect:    cmd > file, cmd >> file
  - Input redirect:     cmd < file
  - Background jobs:    cmd &
  - Subshell:           $(cmd) and `cmd`
  - Environment expand: $VAR
"""

import os
import sys
import shlex
import subprocess
from dataclasses import dataclass


@dataclass
class ExecResult:
    exit_code: int
    stdout: str = ""
    stderr: str = ""


def execute(raw: str, cwd: str, env: dict = None) -> ExecResult:
    """
    Execute a raw command string in the given cwd.

    Handles pipes, redirects, background, env expansion.
    Returns ExecResult with exit_code.
    """
    raw = raw.strip()
    if not raw:
        return ExecResult(0)

    # ── Background job: cmd & ─────────────────────────────────────────────
    background = False
    if raw.endswith("&") and not raw.endswith("\\&"):
        background = True
        raw = raw[:-1].strip()

    # ── Pipe chain: cmd1 | cmd2 | cmd3 ───────────────────────────────────
    if "|" in raw and not _is_quoted(raw, "|"):
        return _execute_pipe(raw, cwd, env, background)

    # ── Redirect: cmd > file, cmd >> file, cmd < file ─────────────────────
    if any(tok in raw for tok in [" > ", " >> ", " < ", ">/", ">>/", "</"]):
        return _execute_redirect(raw, cwd, env, background)

    # ── Simple command ─────────────────────────────────────────────────────
    return _run_simple(raw, cwd, env, background)


# ── Pipe execution ─────────────────────────────────────────────────────────────

def _execute_pipe(raw: str, cwd: str, env: dict, background: bool) -> ExecResult:
    """Execute a pipeline of commands."""
    segments = _split_on_pipe(raw)
    if len(segments) < 2:
        return _run_simple(raw, cwd, env, background)

    merged_env = {**os.environ, **(env or {})}
    procs = []

    try:
        prev_stdout = None
        for i, seg in enumerate(segments):
            seg = seg.strip()
            is_last = (i == len(segments) - 1)
            args = _parse_args(seg)
            if not args:
                continue

            proc = subprocess.Popen(
                args,
                cwd=cwd,
                env=merged_env,
                stdin=prev_stdout,
                stdout=None if is_last else subprocess.PIPE,
                stderr=None,
            )
            if prev_stdout:
                prev_stdout.close()
            prev_stdout = proc.stdout
            procs.append(proc)

        # Wait for last process
        last = procs[-1]
        last.wait()
        # Terminate others
        for p in procs[:-1]:
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill()

        return ExecResult(last.returncode)

    except FileNotFoundError as e:
        cmd_name = str(e).split("'")[1] if "'" in str(e) else str(e)
        print(f"\033[38;5;196m[✗] Command not found: {cmd_name}\033[0m")
        return ExecResult(127)
    except PermissionError as e:
        print(f"\033[38;5;196m[✗] Permission denied: {e}\033[0m")
        return ExecResult(126)


# ── Redirect execution ─────────────────────────────────────────────────────────

def _execute_redirect(raw: str, cwd: str, env: dict, background: bool) -> ExecResult:
    """Handle >, >>, < redirects."""
    stdin_file  = None
    stdout_file = None
    append      = False
    cmd_part    = raw

    # Output append
    if ">>" in raw and not _is_quoted(raw, ">>"):
        parts      = raw.split(">>", 1)
        cmd_part   = parts[0].strip()
        stdout_file = parts[1].strip()
        append     = True
    # Output overwrite
    elif ">" in raw and not _is_quoted(raw, ">"):
        parts = raw.split(">", 1)
        cmd_part   = parts[0].strip()
        stdout_file = parts[1].strip()

    # Input redirect
    if "<" in cmd_part and not _is_quoted(cmd_part, "<"):
        parts      = cmd_part.split("<", 1)
        cmd_part   = parts[0].strip()
        stdin_file = parts[1].strip()

    merged_env = {**os.environ, **(env or {})}
    args = _parse_args(cmd_part)
    if not args:
        return ExecResult(0)

    try:
        stdin_fh  = open(os.path.join(cwd, stdin_file), "r") if stdin_file else None
        stdout_fh = open(
            os.path.join(cwd, stdout_file),
            "a" if append else "w"
        ) if stdout_file else None

        proc = subprocess.Popen(
            args, cwd=cwd, env=merged_env,
            stdin=stdin_fh, stdout=stdout_fh
        )
        if not background:
            proc.wait()
        else:
            print(f"\033[38;5;244m[bg] PID {proc.pid}\033[0m")

        for fh in [stdin_fh, stdout_fh]:
            if fh:
                fh.close()

        return ExecResult(proc.returncode or 0)

    except FileNotFoundError as e:
        cmd_name = str(e).split("'")[1] if "'" in str(e) else str(e)
        print(f"\033[38;5;196m[✗] Command not found: {cmd_name}\033[0m")
        return ExecResult(127)


# ── Simple command ─────────────────────────────────────────────────────────────

def _run_simple(raw: str, cwd: str, env: dict, background: bool) -> ExecResult:
    """Run a single command with no special operators."""
    merged_env = {**os.environ, **(env or {})}
    args = _parse_args(raw)
    if not args:
        return ExecResult(0)

    try:
        proc = subprocess.Popen(args, cwd=cwd, env=merged_env)
        if background:
            print(f"\033[38;5;244m[bg] PID {proc.pid}\033[0m")
            return ExecResult(0)
        proc.wait()
        return ExecResult(proc.returncode)

    except FileNotFoundError:
        # Try with shell=True as fallback for complex constructs
        try:
            proc = subprocess.Popen(raw, shell=True, cwd=cwd, env=merged_env)
            if background:
                print(f"\033[38;5;244m[bg] PID {proc.pid}\033[0m")
                return ExecResult(0)
            proc.wait()
            return ExecResult(proc.returncode)
        except Exception as e:
            cmd_name = args[0] if args else raw.split()[0]
            print(f"\033[38;5;196m[✗] '{cmd_name}': command not found\033[0m")
            return ExecResult(127)
    except PermissionError:
        print(f"\033[38;5;196m[✗] Permission denied: {args[0]}\033[0m")
        return ExecResult(126)
    except KeyboardInterrupt:
        return ExecResult(130)


# ── Utilities ─────────────────────────────────────────────────────────────────

def _parse_args(cmd: str) -> list[str]:
    """Parse command string into args, expanding $VARS."""
    cmd = os.path.expandvars(cmd)
    try:
        return shlex.split(cmd)
    except ValueError:
        return cmd.split()


def _is_quoted(s: str, char: str) -> bool:
    """Very rough check: is the char inside quotes?"""
    in_single = False
    in_double = False
    i = 0
    while i < len(s):
        c = s[i]
        if c == "'" and not in_double:
            in_single = not in_single
        elif c == '"' and not in_single:
            in_double = not in_double
        elif s[i:i+len(char)] == char and not in_single and not in_double:
            return False  # Found unquoted
        i += 1
    return True  # All occurrences were quoted


def _split_on_pipe(raw: str) -> list[str]:
    """Split on unquoted | (not ||)."""
    segments = []
    current  = []
    in_single = in_double = False
    i = 0
    while i < len(raw):
        c = raw[i]
        if c == "'" and not in_double:
            in_single = not in_single
        elif c == '"' and not in_single:
            in_double = not in_double
        elif c == "|" and not in_single and not in_double:
            # peek ahead: || is OR not pipe
            if i + 1 < len(raw) and raw[i+1] == "|":
                current.append(c)
                i += 1
            else:
                segments.append("".join(current))
                current = []
                i += 1
                continue
        else:
            current.append(c)
        i += 1
    if current:
        segments.append("".join(current))
    return segments
