import json
from pathlib import Path

from knowledge.analyze_extraction_readiness import (
    TARGETS,
    analyze_extraction_readiness,
    render_report,
    write_outputs,
)


def test_extraction_framework_docs_exist() -> None:
    docs = [
        Path("docs/literary-knowledge-extraction-framework.md"),
        Path("docs/knowledge-target-catalog.md"),
        Path("docs/extraction-schemas.md"),
    ]

    for path in docs:
        text = path.read_text(encoding="utf-8")
        assert path.exists()
        assert "extraction" in text.lower()


def test_placeholder_candidate_stores_are_framework_only() -> None:
    extraction_dir = Path("data/knowledge/extraction")
    expected_files = {
        "entities_candidates.json",
        "motif_candidates.json",
        "theme_candidates.json",
        "epithet_candidates.json",
        "simile_candidates.json",
        "metaphor_candidates.json",
        "relationship_candidates.json",
    }

    for file_name in expected_files:
        payload = json.loads((extraction_dir / file_name).read_text(encoding="utf-8"))
        assert payload["schema_version"] == "extraction-candidate-v1"
        assert payload["status"] == "framework_placeholder_only"
        assert payload["automatic_extraction_performed"] is False
        assert payload["records"]
        for record in payload["records"]:
            assert record["status"] == "placeholder_seed"
            assert record["confidence"] == 0.0
            assert record["source_record_id"] == "placeholder_only"


def test_extraction_readiness_analysis_is_deterministic() -> None:
    first = analyze_extraction_readiness()
    second = analyze_extraction_readiness()

    assert first == second
    assert first["phase"] == "phase_29"
    assert first["target_count"] == 8
    assert set(item["target"] for item in first["targets"]) == set(TARGETS)
    assert first["automatic_extraction_performed"] is False
    assert first["scraping_performed"] is False
    assert first["registry_population_performed"] is False
    assert first["llm_calls"] == 0


def test_report_generation_and_output_files(tmp_path: Path) -> None:
    analysis = analyze_extraction_readiness()
    output = tmp_path / "extraction_readiness.json"
    report = tmp_path / "extraction-readiness-report.md"

    write_outputs(analysis, output_path=output, report_path=report)

    assert output.exists()
    assert report.exists()
    assert json.loads(output.read_text(encoding="utf-8")) == analysis
    assert "Extraction Readiness Report" in report.read_text(encoding="utf-8")
    assert "relationship_extraction" in render_report(analysis)


def test_required_gap_and_roadmap_reports_exist() -> None:
    reports = [
        Path("reports/benchmark-to-knowledge-gap-mapping.md"),
        Path("reports/knowledge-population-roadmap.md"),
        Path("reports/knowledge-coverage-projection.md"),
    ]

    for path in reports:
        text = path.read_text(encoding="utf-8")
        assert path.exists()
        assert "extraction" in text.lower() or "knowledge" in text.lower()

    roadmap = Path("reports/knowledge-population-roadmap.md").read_text(encoding="utf-8")
    for phase in ("Phase 30", "Phase 31", "Phase 32", "Phase 33", "Phase 34", "Phase 35", "Phase 36"):
        assert phase in roadmap


def test_extraction_analyzer_has_no_network_or_llm_dependencies() -> None:
    text = Path("src/knowledge/analyze_extraction_readiness.py").read_text(
        encoding="utf-8"
    ).lower()

    for forbidden in ("requests", "httpx", "urlopen", "openai", "anthropic", "google.cloud"):
        assert forbidden not in text
