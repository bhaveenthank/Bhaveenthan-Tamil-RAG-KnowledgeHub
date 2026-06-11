import json
from pathlib import Path

from corpus.audit_multi_category_readiness import (
    build_audit,
    render_report,
    write_outputs,
)


ROOT = Path(__file__).resolve().parents[1]


def test_audit_generation_and_scores() -> None:
    audit = build_audit(ROOT)

    assert audit["verified_category_count"] == 4
    assert audit["verified_record_count"] == 16
    assert audit["expansion_readiness"]["category_count"] == 32
    assert set(audit["readiness_scores"]) == {
        "schema_readiness",
        "parser_readiness",
        "metadata_readiness",
        "citation_readiness",
        "analytics_readiness",
        "expansion_readiness",
        "overall_readiness",
    }
    assert all(0 <= score <= 100 for score in audit["readiness_scores"].values())


def test_category_matrix_covers_registry() -> None:
    audit = build_audit(ROOT)
    matrix = audit["category_readiness_matrix"]

    assert len(matrix) == 32
    assert len({item["category_id"] for item in matrix}) == 32
    assert {item["architecture_status"] for item in matrix} <= {
        "ready",
        "partial",
        "not_ready",
    }
    status = {item["category_id"]: item["architecture_status"] for item in matrix}
    assert status["saivam"] == "ready"
    assert status["sangam_literature"] == "ready"
    assert status["dictionaries"] == "ready"
    assert status["grammar"] == "ready"
    assert status["encyclopedias"] == "not_ready"


def test_parser_and_strategic_recommendation() -> None:
    audit = build_audit(ROOT)
    parsers = {
        item["parser_family"]: item for item in audit["parser_readiness"]["matrix"]
    }

    assert parsers["verse_parser"]["status"] == "pilot_verified"
    assert parsers["dictionary_parser"]["status"] == "pilot_verified"
    assert parsers["grammar_parser"]["status"] == "pilot_verified"
    assert audit["strategic_recommendation"]["category_id"] == "twentieth_century_prose"
    future = {
        item["category"]: item["status"]
        for item in audit["future_category_readiness"]
    }
    assert future == {
        "grammar": "ready",
        "prose": "partial",
        "encyclopedias": "not_ready",
        "mixed_content": "not_ready",
    }


def test_json_and_report_generation(tmp_path: Path) -> None:
    audit = build_audit(ROOT)
    output = tmp_path / "audit.json"
    report = tmp_path / "audit.md"
    write_outputs(audit, output_path=output, report_path=report)

    loaded = json.loads(output.read_text(encoding="utf-8"))
    text = report.read_text(encoding="utf-8")
    assert loaded == audit
    assert "Can The Current Architecture Support All 32 TamilVU Categories?" in text
    assert "Choose **twentieth-century prose**" in text


def test_outputs_are_deterministic() -> None:
    first = build_audit(ROOT)
    second = build_audit(ROOT)

    assert first == second
    assert render_report(first) == render_report(second)


def test_auditor_is_offline_and_read_only() -> None:
    script = (
        ROOT / "src/corpus/audit_multi_category_readiness.py"
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
