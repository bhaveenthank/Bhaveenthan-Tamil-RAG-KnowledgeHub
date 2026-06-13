from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

SUPPORTED_GROUPS = ("author", "category", "work", "record_type", "source")
GROUP_FIELD_MAP = {
    "author": "author",
    "category": "category_id",
    "work": "work",
    "record_type": "record_type",
    "source": "source",
}
UNKNOWN = "(unknown)"


def group_value(result: dict[str, Any], group_by: str) -> str:
    if group_by not in GROUP_FIELD_MAP:
        raise ValueError(f"unsupported group_by: {group_by}")
    value = result.get(GROUP_FIELD_MAP[group_by]) or UNKNOWN
    return str(value)


def group_occurrences(
    occurrence_result: dict[str, Any],
    *,
    group_by: str = "author",
    top_n: int = 10,
) -> dict[str, Any]:
    results = occurrence_result.get("results", [])
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        buckets[group_value(result, group_by)].append(result)

    total = int(occurrence_result.get("occurrence_count", len(results)))
    groups = []
    for key, items in buckets.items():
        matched_terms = Counter(item.get("matched_term", "") for item in items)
        fields = Counter(item.get("matched_field", "") for item in items)
        records = {item.get("record_id", "") for item in items if item.get("record_id")}
        works = {item.get("work", "") for item in items if item.get("work")}
        authors = {item.get("author", "") for item in items if item.get("author")}
        groups.append(
            {
                "group_by": group_by,
                "group_key": key,
                "occurrence_count": len(items),
                "percentage": round((len(items) / total * 100) if total else 0.0, 4),
                "unique_records": len(records),
                "unique_works": len(works),
                "unique_authors": len(authors),
                "matched_term_counts": dict(sorted(matched_terms.items())),
                "field_counts": dict(sorted(fields.items())),
                "example_records": [
                    {
                        "record_id": item.get("record_id", ""),
                        "matched_term": item.get("matched_term", ""),
                        "matched_field": item.get("matched_field", ""),
                        "snippet": item.get("snippet", ""),
                        "source_url": item.get("source_url", ""),
                    }
                    for item in sorted(items, key=lambda row: row.get("deterministic_key", ""))[:3]
                ],
            }
        )

    groups.sort(
        key=lambda item: (
            -item["occurrence_count"],
            item["group_key"],
        )
    )
    if top_n:
        groups = groups[:top_n]
    return {
        "aggregation_version": "aggregation-engine-v1",
        "query_term": occurrence_result.get("query_term", ""),
        "expand_query": bool(occurrence_result.get("expand_query", False)),
        "matched_terms": occurrence_result.get("matched_terms", []),
        "group_by": group_by,
        "total_occurrences": total,
        "group_count": len(groups),
        "groups": groups,
    }
