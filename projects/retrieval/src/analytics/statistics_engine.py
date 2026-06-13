from __future__ import annotations

from collections import Counter
from typing import Any

from analytics.aggregation_engine import group_occurrences


def unique_count(results: list[dict[str, Any]], field: str) -> int:
    return len({result.get(field, "") for result in results if result.get(field)})


def percentage_distribution(counter: Counter[str], total: int) -> list[dict[str, Any]]:
    rows = [
        {
            "key": key,
            "count": count,
            "percentage": round((count / total * 100) if total else 0.0, 4),
        }
        for key, count in counter.items()
    ]
    return sorted(rows, key=lambda row: (-row["count"], row["key"]))


def compute_statistics(
    occurrence_result: dict[str, Any],
    *,
    group_by: str = "author",
    top_n: int = 10,
) -> dict[str, Any]:
    results = occurrence_result.get("results", [])
    total = int(occurrence_result.get("occurrence_count", len(results)))
    term_counts = Counter(result.get("matched_term", "") for result in results)
    field_counts = Counter(result.get("matched_field", "") for result in results)
    aggregation = group_occurrences(occurrence_result, group_by=group_by, top_n=top_n)
    return {
        "statistics_version": "statistics-engine-v1",
        "query_term": occurrence_result.get("query_term", ""),
        "expand_query": bool(occurrence_result.get("expand_query", False)),
        "matched_terms": occurrence_result.get("matched_terms", []),
        "total_occurrences": total,
        "unique_records": unique_count(results, "record_id"),
        "unique_works": unique_count(results, "work"),
        "unique_authors": unique_count(results, "author"),
        "top_n": top_n,
        "group_by": group_by,
        "top_groups": aggregation["groups"],
        "term_distribution": percentage_distribution(term_counts, total),
        "field_distribution": percentage_distribution(field_counts, total),
    }
