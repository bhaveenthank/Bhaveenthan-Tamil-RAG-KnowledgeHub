import json
from pathlib import Path

from corpus.validate_pilot_categories import (
    build_summary,
    render_report,
    verified_pilots,
    write_outputs,
)


ROOT = Path(__file__).resolve().parents[1]


def test_verified_categories_are_detected() -> None:
    plan = json.loads(
        (ROOT / "data/processed/corpus_registry/pilot_category_plan.json").read_text(
            encoding="utf-8"
        )
    )

    assert [pilot["category_id"] for pilot in verified_pilots(plan)] == [
        "grammar",
        "sangam_literature",
        "saivam",
        "dictionaries",
    ]


def test_comparison_and_schema_stress_test_exist() -> None:
    summary = build_summary(ROOT)

    assert {item["parser_family"] for item in summary["category_comparisons"]} == {
        "verse_parser",
        "dictionary_parser",
        "grammar_parser",
    }
    assert summary["verified_category_count"] == 4
    assert {item["schema_area"] for item in summary["schema_coverage"]} == {
        "verse_records",
        "commentary_records",
        "dictionary_entries",
        "grammar_rules",
    }
    commentary = next(
        item
        for item in summary["schema_coverage"]
        if item["schema_area"] == "commentary_records"
    )
    assert commentary["status"] == "partial"


def test_next_category_recommendation_exists() -> None:
    recommendation = build_summary(ROOT)["next_recommended_pilot"]

    assert recommendation["category_id"] == "twentieth_century_prose"
    assert recommendation["parser_family"] == "prose_parser"
    assert recommendation["next_action"].startswith("complete rights review")


def test_outputs_are_generated(tmp_path) -> None:
    summary = build_summary(ROOT)
    output = tmp_path / "summary.json"
    report = tmp_path / "report.md"
    write_outputs(summary, output_path=output, report_path=report)

    loaded = json.loads(output.read_text(encoding="utf-8"))
    assert loaded["verified_category_count"] == 4
    assert report.exists()
    assert "Cross-Parser Comparison" in report.read_text(encoding="utf-8")


def test_output_is_deterministic() -> None:
    first = build_summary(ROOT)
    second = build_summary(ROOT)

    assert first == second
    assert render_report(first) == render_report(second)


def test_validation_is_read_only_and_offline() -> None:
    script = (
        ROOT / "src/corpus/validate_pilot_categories.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "urlopen",
        "fetch_html",
        "ingest_category(",
        "openai",
        "anthropic",
        "google.cloud",
    ):
        assert forbidden not in script
