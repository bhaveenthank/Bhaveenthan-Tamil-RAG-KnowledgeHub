from __future__ import annotations

import subprocess
import sys


def run(command: list[str]) -> int:
    print("+", " ".join(command))
    return subprocess.call(command)


def main() -> int:
    checks = [
        [sys.executable, "scripts/check-boundaries.py"],
        [sys.executable, "-m", "pytest"],
    ]
    for command in checks:
        exit_code = run(command)
        if exit_code:
            return exit_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
