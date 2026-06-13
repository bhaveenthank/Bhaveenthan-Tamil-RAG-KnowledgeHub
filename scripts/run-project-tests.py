from __future__ import annotations

import argparse
import subprocess
import sys


TEST_TARGETS = {
    "crawler": "projects/crawler/tests",
    "parser": "projects/parser/tests",
    "normalizer": "projects/normalizer/tests",
    "knowledge": "projects/knowledge/tests",
    "retrieval": "projects/retrieval/tests",
    "evaluation": "projects/evaluation/tests",
    "shared": "shared/tvu-common/tests",
    "workspace": "tests",
    "all": "",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run tests for one reorg project boundary.")
    parser.add_argument("target", choices=sorted(TEST_TARGETS), nargs="?", default="all")
    args = parser.parse_args(argv)

    command = [sys.executable, "-m", "pytest"]
    if TEST_TARGETS[args.target]:
        command.append(TEST_TARGETS[args.target])
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
