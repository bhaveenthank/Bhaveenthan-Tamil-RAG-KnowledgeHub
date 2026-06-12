from pathlib import Path

from analytics.aggregation_engine import group_occurrences
from analytics.analyze_term import analyze_term, build_aggregation_examples, render_report
from analytics.statistics_engine import compute_statistics


def occurrence_fixture() -> dict:
    return {
        "query_term": "சந்திரன்",
        "expand_query": True,
        "matched_terms": ["சந்திரன்", "மதி"],
        "occurrence_count": 4,
        "results": [
            {
                "matched_term": "சந்திரன்",
                "matched_field": "verse_text",
                "record_id": "r1",
                "record_type": "verse",
                "category_id": "thirumurai",
                "author": "சம்பந்தர்",
                "work": "தேவாரம்",
                "source": "TamilVU",
                "snippet": "சந்திரன்",
                "source_url": "https://example.test/r1",
                "deterministic_key": "r1:verse_text:சந்திரன்:0",
            },
            {
                "matched_term": "மதி",
                "matched_field": "kurippurai",
                "record_id": "r1",
                "record_type": "verse",
                "category_id": "thirumurai",
                "author": "சம்பந்தர்",
                "work": "தேவாரம்",
                "source": "TamilVU",
                "snippet": "மதி",
                "source_url": "https://example.test/r1",
                "deterministic_key": "r1:kurippurai:மதி:3",
            },
            {
                "matched_term": "மதி",
                "matched_field": "verse_text",
                "record_id": "r2",
                "record_type": "verse",
                "category_id": "sangam",
                "author": "கபிலர்",
                "work": "நற்றிணை",
                "source": "TamilVU",
                "snippet": "மதி",
                "source_url": "https://example.test/r2",
                "deterministic_key": "r2:verse_text:மதி:1",
            },
            {
                "matched_term": "மதி",
                "matched_field": "title",
                "record_id": "r3",
                "record_type": "dictionary_entry",
                "category_id": "dictionaries",
                "author": "",
                "work": "அகரமுதலி",
                "source": "TamilVU",
                "snippet": "மதி",
                "source_url": "https://example.test/r3",
                "deterministic_key": "r3:title:மதி:0",
            },
        ],
    }


def test_grouping_counting_and_ranking() -> None:
    grouped = group_occurrences(occurrence_fixture(), group_by="author")

    assert grouped["total_occurrences"] == 4
    assert grouped["groups"][0]["group_key"] == "சம்பந்தர்"
    assert grouped["groups"][0]["occurrence_count"] == 2
    assert grouped["groups"][0]["unique_records"] == 1
    assert "(unknown)" in {group["group_key"] for group in grouped["groups"]}


def test_statistics_distributions_are_deterministic() -> None:
    first = compute_statistics(occurrence_fixture(), group_by="category", top_n=5)
    second = compute_statistics(occurrence_fixture(), group_by="category", top_n=5)

    assert first == second
    assert first["total_occurrences"] == 4
    assert first["unique_records"] == 3
    assert first["unique_works"] == 3
    assert first["term_distribution"][0]["key"] == "மதி"
    assert first["term_distribution"][0]["percentage"] == 75.0


def test_expanded_search_compatibility_with_real_index() -> None:
    result = analyze_term("சந்திரன்", expand_query=True, group_by="category", top_n=3)

    assert result["occurrence_summary"]["total_occurrences"] >= 11
    assert "மதி" in result["occurrence_summary"]["matched_terms"]
    assert result["statistics"]["top_groups"]


def test_report_generation() -> None:
    payload = build_aggregation_examples()
    report = render_report(payload)

    assert len(payload["examples"]) == 4
    assert "Aggregation Engine Report" in report
    assert "சந்திரன்" in report


def test_unsupported_group_rejected() -> None:
    try:
        group_occurrences(occurrence_fixture(), group_by="unsupported")
    except ValueError as error:
        assert "unsupported group_by" in str(error)
    else:
        raise AssertionError("unsupported group was not rejected")


def test_no_scraping_or_llm_dependencies() -> None:
    text = "\n".join(
        Path(path).read_text(encoding="utf-8").lower()
        for path in (
            "src/analytics/aggregation_engine.py",
            "src/analytics/statistics_engine.py",
            "src/analytics/analyze_term.py",
        )
    )

    for forbidden in ("requests", "httpx", "urlopen", "openai", "anthropic", "google.cloud"):
        assert forbidden not in text
