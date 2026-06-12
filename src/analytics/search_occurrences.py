from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from analytics.build_occurrence_index import DEFAULT_OUTPUT
from retrieval.query_expander import QueryExpander, ordered_unique

DEFAULT_EXAMPLES = Path("data/processed/analytics/occurrence_search_examples.json")
SNIPPET_RADIUS = 42


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value or "").split())


def load_index(path: Path = DEFAULT_OUTPUT) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def snippet(text: str, start: int, end: int, radius: int = SNIPPET_RADIUS) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    prefix = "..." if left else ""
    suffix = "..." if right < len(text) else ""
    return prefix + text[left:right].strip() + suffix


def matched_terms(term: str, expand_query: bool = False, expander: QueryExpander | None = None) -> tuple[list[str], dict[str, Any] | None]:
    normalized = normalize_text(term)
    if not expand_query:
        return [normalized], None
    expansion = (expander or QueryExpander()).expand(normalized)
    terms = expansion["expanded_terms"] or [normalized]
    return ordered_unique(terms), expansion


def search_occurrences(
    term: str,
    *,
    expand_query: bool = False,
    index_rows: list[dict[str, Any]] | None = None,
    index_path: Path = DEFAULT_OUTPUT,
    expander: QueryExpander | None = None,
    limit: int | None = None,
) -> dict[str, Any]:
    terms, expansion = matched_terms(term, expand_query, expander)
    rows = index_rows if index_rows is not None else load_index(index_path)
    results: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, int, int]] = set()

    for row in rows:
        text = row["text"]
        for matched_term in terms:
            if not matched_term:
                continue
            start = text.find(matched_term)
            while start != -1:
                end = start + len(matched_term)
                key = (row["record_id"], row["field_name"], matched_term, start, end)
                if key not in seen:
                    seen.add(key)
                    results.append(
                        {
                            "matched_term": matched_term,
                            "matched_field": row["field_name"],
                            "match_start": start,
                            "match_end": end,
                            "snippet": snippet(text, start, end),
                            "corpus_id": row["corpus_id"],
                            "category_id": row["category_id"],
                            "record_id": row["record_id"],
                            "record_type": row["record_type"],
                            "author": row["author"],
                            "title": row["title"],
                            "source_url": row["source_url"],
                            "commentary_url": row["commentary_url"],
                            "source_metadata": row.get("source_metadata", {}),
                            "deterministic_key": (
                                f"{row['record_id']}:{row['field_name']}:{matched_term}:{start}"
                            ),
                        }
                    )
                start = text.find(matched_term, start + 1)

    results.sort(key=lambda item: item["deterministic_key"])
    total_occurrences = len(results)
    if limit is not None:
        results = results[:limit]
    return {
        "query_term": normalize_text(term),
        "expand_query": expand_query,
        "matched_terms": terms,
        "query_expansion": expansion,
        "occurrence_count": total_occurrences,
        "returned_count": len(results),
        "results": results,
    }


def build_example_results(index_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    examples = []
    for term, expand in (
        ("சந்திரன்", True),
        ("சிவன்", True),
        ("அப்பர்", True),
        ("உவமை", True),
    ):
        result = search_occurrences(term, expand_query=expand, index_rows=index_rows, limit=5)
        examples.append(
            {
                "term": term,
                "expand_query": expand,
                "matched_terms": result["matched_terms"],
                "occurrence_count": result["occurrence_count"],
                "example_records": result["results"],
            }
        )
    return {
        "examples_version": "occurrence-search-examples-v1",
        "examples": examples,
    }


def write_example_results(output: Path = DEFAULT_EXAMPLES, index_path: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    payload = build_example_results(load_index(index_path))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search the local occurrence evidence index")
    parser.add_argument("--term", required=True)
    parser.add_argument("--expand-query", action="store_true")
    parser.add_argument("--index", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--write-examples", action="store_true")
    parser.add_argument("--examples-output", type=Path, default=DEFAULT_EXAMPLES)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = search_occurrences(
        args.term,
        expand_query=args.expand_query,
        index_path=args.index,
        limit=args.limit,
    )
    if args.write_examples:
        write_example_results(args.examples_output, args.index)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
