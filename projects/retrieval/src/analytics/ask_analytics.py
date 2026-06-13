from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analytics.analytical_retriever import retrieve_analytical

DEFAULT_OUTPUT = Path("data/processed/analytics/analytical_retrieval_examples.json")
DEFAULT_REPORT = Path("reports/analytical-retrieval-report.md")
EXAMPLE_QUERIES = (
    "எந்த ஆசிரியர் சந்திரன் தொடர்பான சொற்களை அதிகம் பயன்படுத்துகிறார்?",
    "எந்த corpus-இல் சிவன் அதிகமாக குறிப்பிடப்படுகிறார்?",
    "உவமை எந்த works-இல் அதிகம் வருகிறது?",
    "அப்பர் தொடர்பான குறிப்புகள் எந்த record types-இல் வருகின்றன?",
)


def build_examples() -> dict:
    return {
        "examples_version": "analytical-retrieval-examples-v1",
        "examples": [retrieve_analytical(query) for query in EXAMPLE_QUERIES],
    }


def render_report(payload: dict) -> str:
    lines = [
        "# Analytical Retrieval Report",
        "",
        "## Supported Intents",
        "",
        "- `term_occurrence`",
        "- `group_by_author`",
        "- `group_by_work`",
        "- `group_by_category`",
        "- `group_by_record_type`",
        "- `compare_sources`",
        "- `unsupported`",
        "",
        "## Example Structured Outputs",
        "",
    ]
    for example in payload["examples"]:
        top = example["top_results"][0] if example["top_results"] else {}
        lines.extend(
            [
                f"### {example['query']}",
                "",
                f"- Intent: `{example['intent']}`",
                f"- Term: `{example['term']}`",
                f"- Expanded: `{str(example['expanded']).lower()}`",
                f"- Group by: `{example['group_by']}`",
                f"- Total occurrences: `{example['total_occurrences']}`",
                f"- Top result: `{top.get('group_key', '-')}` with `{top.get('occurrence_count', 0)}` occurrences",
                "",
            ]
        )
    lines.extend(
        [
            "## Limitations",
            "",
            "- Classification is deterministic and rule-based.",
            "- Outputs are structured analytics, not fluent final answers.",
            "- Counts depend on literal occurrence evidence and curated expansion seeds.",
            "- No LLM call, scraping, cloud job, embedding regeneration, or vector rebuild is performed.",
            "",
            "## Next Steps",
            "",
            "Phase 27 can add answer composition after every statistic is traceable to evidence samples and citations.",
            "",
        ]
    )
    return "\n".join(lines)


def write_examples(output: Path = DEFAULT_OUTPUT, report: Path = DEFAULT_REPORT) -> dict:
    payload = build_examples()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(payload), encoding="utf-8")
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run rule-based analytical retrieval")
    parser.add_argument("--query", required=True)
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument("--write-examples", action="store_true")
    parser.add_argument("--examples-output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = retrieve_analytical(args.query, top_n=args.top_n)
    if args.write_examples:
        write_examples(args.examples_output, args.report)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
