from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analytics.aggregation_engine import SUPPORTED_GROUPS
from analytics.search_occurrences import search_occurrences
from analytics.statistics_engine import compute_statistics

DEFAULT_OUTPUT = Path("data/processed/analytics/aggregation_examples.json")
DEFAULT_REPORT = Path("reports/aggregation-engine-report.md")
EXAMPLE_TERMS = ("சந்திரன்", "சிவன்", "அப்பர்", "உவமை")


def analyze_term(
    term: str,
    *,
    expand_query: bool = False,
    group_by: str = "category",
    top_n: int = 10,
) -> dict[str, Any]:
    occurrence_result = search_occurrences(term, expand_query=expand_query)
    statistics = compute_statistics(occurrence_result, group_by=group_by, top_n=top_n)
    return {
        "analysis_version": "term-analytics-v1",
        "term": term,
        "expand_query": expand_query,
        "group_by": group_by,
        "occurrence_summary": {
            "matched_terms": occurrence_result["matched_terms"],
            "total_occurrences": occurrence_result["occurrence_count"],
            "unique_records": statistics["unique_records"],
            "unique_works": statistics["unique_works"],
            "unique_authors": statistics["unique_authors"],
        },
        "statistics": statistics,
    }


def build_aggregation_examples() -> dict[str, Any]:
    examples = []
    for term in EXAMPLE_TERMS:
        examples.append(analyze_term(term, expand_query=True, group_by="category", top_n=10))
    return {
        "examples_version": "aggregation-examples-v1",
        "examples": examples,
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Aggregation Engine Report",
        "",
        "## Summary",
        "",
        "The aggregation engine groups occurrence evidence into counts, rankings, and distributions. It performs no scraping, extraction, answer generation, or LLM calls.",
        "",
        "## Example Rankings",
        "",
    ]
    for example in payload["examples"]:
        summary = example["occurrence_summary"]
        lines.extend(
            [
                f"### {example['term']}",
                "",
                f"- Matched terms: `{', '.join(summary['matched_terms'])}`",
                f"- Total occurrences: `{summary['total_occurrences']}`",
                f"- Unique records: `{summary['unique_records']}`",
                f"- Unique works: `{summary['unique_works']}`",
                f"- Unique authors: `{summary['unique_authors']}`",
                "",
                "| Rank | Group | Occurrences | Percentage | Unique Records |",
                "| ---: | --- | ---: | ---: | ---: |",
            ]
        )
        for rank, group in enumerate(example["statistics"]["top_groups"][:5], start=1):
            lines.append(
                f"| {rank} | `{group['group_key']}` | {group['occurrence_count']} "
                f"| {group['percentage']:.2f}% | {group['unique_records']} |"
            )
        lines.append("")
    lines.extend(
        [
            "## Limitations",
            "",
            "- Counts are literal occurrence counts from the Phase 24 evidence index.",
            "- Expanded concept counts depend on the current curated registry seed terms.",
            "- This is aggregation infrastructure, not interpretive literary reasoning.",
            "- Future analytical retrieval should cite the underlying occurrence rows for every statistic.",
            "",
        ]
    )
    return "\n".join(lines)


def write_examples(
    output: Path = DEFAULT_OUTPUT,
    report: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    payload = build_aggregation_examples()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(payload), encoding="utf-8")
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate occurrence evidence for a Tamil literary term")
    parser.add_argument("--term", required=True)
    parser.add_argument("--expand-query", action="store_true")
    parser.add_argument("--group-by", choices=SUPPORTED_GROUPS, default="category")
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--write-examples", action="store_true")
    parser.add_argument("--examples-output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = analyze_term(
        args.term,
        expand_query=args.expand_query,
        group_by=args.group_by,
        top_n=args.top_n,
    )
    if args.write_examples:
        write_examples(args.examples_output, args.report)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
