#!/usr/bin/env python3
"""Abort commits when risky files are present."""

from __future__ import annotations

import subprocess
import sys
from pathlib import PurePosixPath


LOG_EXTENSIONS = {".log", ".out", ".err"}
DEBUG_LOG_PREFIXES = (
    "npm-debug.log",
    "yarn-debug.log",
    "yarn-error.log",
    "pnpm-debug.log",
)
HIGH_RISK_BINARY_EXTENSIONS = {
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".class",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
    ".jar",
    ".iso",
    ".dmg",
    ".db",
    ".sqlite",
    ".sqlite3",
}


def _run_status() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        print("precommit-guard: git not found.", file=sys.stderr)
        sys.exit(2)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        if stderr:
            print(stderr, file=sys.stderr)
        else:
            print("precommit-guard: failed to read git status.", file=sys.stderr)
        sys.exit(2)
    return [line for line in result.stdout.splitlines() if line]


def _extract_path(status_line: str) -> str:
    # Porcelain v1 format is "XY <path>".
    payload = status_line[3:] if len(status_line) >= 4 else ""
    # Renames may show as "old -> new"; inspect destination path.
    if " -> " in payload:
        payload = payload.split(" -> ", 1)[1]
    return payload.strip()


def _is_log_path(path: str) -> bool:
    p = PurePosixPath(path)
    name = p.name.lower()

    if p.suffix.lower() in LOG_EXTENSIONS:
        return True
    if any(name.startswith(prefix) for prefix in DEBUG_LOG_PREFIXES):
        return True
    if "logs" in {part.lower() for part in p.parts}:
        return True
    return False


def _has_high_risk_binary_extension(path: str) -> bool:
    return PurePosixPath(path).suffix.lower() in HIGH_RISK_BINARY_EXTENSIONS


def main() -> int:
    lines = _run_status()
    log_violations: list[str] = []
    untracked_binary_violations: list[str] = []

    for line in lines:
        status = line[:2]
        path = _extract_path(line)
        if not path:
            continue

        if _is_log_path(path):
            log_violations.append(path)
        if status == "??" and _has_high_risk_binary_extension(path):
            untracked_binary_violations.append(path)

    if not log_violations and not untracked_binary_violations:
        print("precommit-guard: OK")
        return 0

    print("precommit-guard: BLOCKED")
    if log_violations:
        print("\nReason: log-like files are present")
        for path in sorted(set(log_violations)):
            print(f"  - {path}")
    if untracked_binary_violations:
        print("\nReason: untracked high-risk binary files are present")
        for path in sorted(set(untracked_binary_violations)):
            print(f"  - {path}")

    print("\nResolve the blocked files, then retry the commit flow.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
