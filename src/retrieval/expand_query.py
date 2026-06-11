from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from retrieval.query_expander import QueryExpander


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Expand a query using curated Tamil literary registries")
    parser.add_argument("--query", required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, expander: QueryExpander | None = None) -> int:
    args = parse_args(argv)
    result = (expander or QueryExpander()).expand(args.query)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
