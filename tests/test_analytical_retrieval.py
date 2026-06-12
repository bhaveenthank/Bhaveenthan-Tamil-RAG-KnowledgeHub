from pathlib import Path

from analytics.analytical_query_classifier import classify_query, extract_target_term
from analytics.analytical_retriever import retrieve_analytical
from analytics.ask_analytics import build_examples, render_report


def test_intent_classification_and_term_extraction() -> None:
    classified = classify_query("எந்த ஆசிரியர் சந்திரன் தொடர்பான சொற்களை அதிகம் பயன்படுத்துகிறார்?")

    assert classified["intent"] == "group_by_author"
    assert classified["term"] == "சந்திரன்"
    assert classified["expanded"] is True
    assert classified["group_by"] == "author"


def test_group_by_work_and_category_selection() -> None:
    work = classify_query("உவமை எந்த works-இல் அதிகம் வருகிறது?")
    category = classify_query("எந்த corpus-இல் சிவன் அதிகமாக குறிப்பிடப்படுகிறார்?")

    assert work["intent"] == "group_by_work"
    assert work["group_by"] == "work"
    assert work["term"] == "உவமை"
    assert category["intent"] == "group_by_category"
    assert category["group_by"] == "category"


def test_record_type_query() -> None:
    classified = classify_query("அப்பர் தொடர்பான குறிப்புகள் எந்த record types-இல் வருகின்றன?")

    assert classified["intent"] == "group_by_record_type"
    assert classified["term"] == "அப்பர்"
    assert classified["expanded"] is True


def test_extract_target_term_fallback() -> None:
    assert extract_target_term("எந்த இடத்தில் அருள் வருகிறது?", terms=[]) == "இடத்தில்"


def test_analytical_retrieval_returns_structured_result() -> None:
    result = retrieve_analytical("எந்த corpus-இல் சிவன் அதிகமாக குறிப்பிடப்படுகிறார்?", top_n=3)

    assert result["intent"] == "group_by_category"
    assert result["term"] == "சிவன்"
    assert result["group_by"] == "category"
    assert result["total_occurrences"] > 0
    assert result["top_results"]
    assert result["evidence_samples"]


def test_unsupported_query_handling() -> None:
    result = retrieve_analytical("hello please summarize everything", top_n=3)

    assert result["intent"] == "unsupported"
    assert result["total_occurrences"] == 0
    assert result["top_results"] == []
    assert any("could not be mapped" in item for item in result["limitations"])


def test_examples_and_report_are_deterministic() -> None:
    first = build_examples()
    second = build_examples()
    report = render_report(first)

    assert first == second
    assert len(first["examples"]) == 4
    assert "Analytical Retrieval Report" in report
    assert "group_by_author" in report


def test_no_scraping_or_llm_dependencies() -> None:
    text = "\n".join(
        Path(path).read_text(encoding="utf-8").lower()
        for path in (
            "src/analytics/analytical_query_classifier.py",
            "src/analytics/analytical_retriever.py",
            "src/analytics/ask_analytics.py",
        )
    )

    for forbidden in ("requests", "httpx", "urlopen", "openai", "anthropic", "google.cloud"):
        assert forbidden not in text
