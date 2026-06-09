from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rag.citation_builder import (
    build_citation_package,
    load_context_package,
    render_citation_report,
)

DEFAULT_RAG_DIR = Path("data/processed/rag")
DEFAULT_OUTPUT = DEFAULT_RAG_DIR / "sample_citations.json"
DEFAULT_REPORT = Path("reports/citation-grounding-report.md")


def resolve_input_path(value: Path) -> Path:
    if value.exists():
        return value
    candidate = DEFAULT_RAG_DIR / value
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"context package not found: {value}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export deterministic source-grounded citations from a context package")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_path = resolve_input_path(args.input)
    context_package = load_context_package(input_path)
    citation_package = build_citation_package(context_package)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(citation_package, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.report.write_text(
        render_citation_report(citation_package, input_path=str(input_path)),
        encoding="utf-8",
    )
    print(
        f"Citations exported: citations={citation_package['citation_count']} "
        f"groups={len(citation_package['citation_groups'])} output={args.output} report={args.report}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

