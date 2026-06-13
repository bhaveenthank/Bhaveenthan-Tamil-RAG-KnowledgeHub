from __future__ import annotations

from typing import Any

from analytics.analytical_query_classifier import classify_query
from analytics.analyze_term import analyze_term


def evidence_samples(groups: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for group in groups:
        for sample in group.get("example_records", []):
            samples.append(
                {
                    "group_key": group.get("group_key", ""),
                    "record_id": sample.get("record_id", ""),
                    "matched_term": sample.get("matched_term", ""),
                    "matched_field": sample.get("matched_field", ""),
                    "snippet": sample.get("snippet", ""),
                    "source_url": sample.get("source_url", ""),
                }
            )
            if len(samples) >= limit:
                return samples
    return samples


def retrieve_analytical(query: str, *, top_n: int = 10) -> dict[str, Any]:
    classification = classify_query(query)
    intent = classification["intent"]
    limitations = [
        "Rule-based analytical retrieval only; no LLM answer generation is performed.",
        "Counts are literal occurrence counts from the local evidence index.",
    ]
    if intent == "unsupported":
        return {
            "query": classification["query"],
            "intent": intent,
            "term": classification["term"],
            "expanded": False,
            "group_by": None,
            "total_occurrences": 0,
            "top_results": [],
            "evidence_samples": [],
            "limitations": [
                *limitations,
                "The query could not be mapped to a supported analytical intent or term.",
            ],
            "classification": classification,
        }

    group_by = classification["group_by"] or "category"
    analytics = analyze_term(
        classification["term"],
        expand_query=classification["expanded"],
        group_by=group_by,
        top_n=top_n,
    )
    top_groups = analytics["statistics"]["top_groups"]
    return {
        "query": classification["query"],
        "intent": intent,
        "term": classification["term"],
        "expanded": classification["expanded"],
        "group_by": group_by,
        "total_occurrences": analytics["occurrence_summary"]["total_occurrences"],
        "matched_terms": analytics["occurrence_summary"]["matched_terms"],
        "top_results": [
            {
                "rank": rank,
                "group_key": group["group_key"],
                "occurrence_count": group["occurrence_count"],
                "percentage": group["percentage"],
                "unique_records": group["unique_records"],
                "unique_works": group["unique_works"],
                "unique_authors": group["unique_authors"],
            }
            for rank, group in enumerate(top_groups, start=1)
        ],
        "evidence_samples": evidence_samples(top_groups),
        "limitations": limitations,
        "classification": classification,
        "statistics": {
            "term_distribution": analytics["statistics"]["term_distribution"],
            "field_distribution": analytics["statistics"]["field_distribution"],
        },
    }
