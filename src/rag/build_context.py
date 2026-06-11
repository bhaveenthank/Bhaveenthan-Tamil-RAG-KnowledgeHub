from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.context_builder import DEFAULT_MAX_CONTEXT_CHARS, DEFAULT_TOP_K, ContextBuilder


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a citation-ready context package without answer generation")
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument("--max-context-chars", type=int, default=DEFAULT_MAX_CONTEXT_CHARS)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--expand-query",
        action="store_true",
        help="Expand curated aliases and literary concepts before hybrid retrieval",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, builder: ContextBuilder | None = None) -> int:
    args = parse_args(argv)
    package = (builder or ContextBuilder()).build(
        query=args.query,
        top_k=args.top_k,
        max_context_chars=args.max_context_chars,
        expand_query=args.expand_query,
    )
    rendered = json.dumps(package, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(
            f"Context package written: contexts={package['context_count']} "
            f"chars={package['context_limits']['used_context_chars']} output={args.output}"
        )
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
