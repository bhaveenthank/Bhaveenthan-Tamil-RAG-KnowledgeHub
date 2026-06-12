import json
from pathlib import Path

from knowledge.analyze_annotation_readiness import (
    analyze_annotation_readiness,
    write_outputs as write_readiness_outputs,
)
from knowledge.validate_annotations import (
    ANNOTATION_FILES,
    validate_annotations,
    write_outputs as write_validation_outputs,
)


def test_annotation_docs_exist() -> None:
    for path in [
        Path("docs/annotated-fixture-framework.md"),
        Path("docs/annotation-guidelines.md"),
        Path("docs/annotation-schema.md"),
    ]:
        text = path.read_text(encoding="utf-8")
        assert path.exists()
        assert "annotation" in text.lower()


def test_gold_annotation_files_exist_and_are_manual_only() -> None:
    annotation_dir = Path("data/knowledge/annotations")
    for file_name in ANNOTATION_FILES:
        payload = json.loads((annotation_dir / file_name).read_text(encoding="utf-8"))
        assert payload["schema_version"] == "annotation-gold-v1"
        assert payload["status"] == "manual_gold_seed"
        assert payload["automatic_extraction_performed"] is False
        assert 3 <= len(payload["records"]) <= 10


def test_annotation_validator_runs_and_checks_spans() -> None:
    validation = validate_annotations()

    assert validation["valid"] is True
    assert validation["annotation_file_count"] == 8
    assert validation["record_count"] >= 24
    assert validation["annotation_count"] >= 24
    assert validation["automatic_extraction_performed"] is False
    assert validation["scraping_performed"] is False
    assert validation["llm_calls"] == 0


def test_annotation_readiness_is_deterministic() -> None:
    first = analyze_annotation_readiness()
    second = analyze_annotation_readiness()

    assert first == second
    assert first["phase"] == "phase_30"
    assert first["decision"] == "ANNOTATION_SEED_READY_EXTRACTION_NOT_STARTED"
    assert first["overall_readiness_score"] > 0
    assert first["automatic_extraction_performed"] is False
    assert first["registry_population_performed"] is False
    assert first["llm_calls"] == 0


def test_annotation_reports_can_be_generated(tmp_path: Path) -> None:
    validation = validate_annotations()
    readiness = analyze_annotation_readiness()
    validation_output = tmp_path / "annotation_validation.json"
    validation_report = tmp_path / "annotation-fixture-report.md"
    readiness_output = tmp_path / "annotation_readiness.json"
    readiness_report = tmp_path / "annotation-readiness-report.md"

    write_validation_outputs(
        validation,
        output_path=validation_output,
        report_path=validation_report,
    )
    write_readiness_outputs(
        readiness,
        output_path=readiness_output,
        report_path=readiness_report,
    )

    assert validation_output.exists()
    assert validation_report.exists()
    assert readiness_output.exists()
    assert readiness_report.exists()
    assert "Annotation Fixture Report" in validation_report.read_text(encoding="utf-8")
    assert "Annotation Readiness Report" in readiness_report.read_text(encoding="utf-8")


def test_required_phase_reports_exist() -> None:
    for path in [
        Path("reports/annotation-fixture-report.md"),
        Path("reports/extraction-evaluation-plan.md"),
        Path("reports/annotation-impact-analysis.md"),
    ]:
        assert path.exists()

    plan = Path("reports/extraction-evaluation-plan.md").read_text(encoding="utf-8")
    for phase in ("Phase 31", "Phase 32", "Phase 33", "Phase 34", "Phase 35", "Phase 36", "Phase 37"):
        assert phase in plan


def test_annotation_scripts_have_no_network_or_llm_dependencies() -> None:
    for path in [
        Path("src/knowledge/validate_annotations.py"),
        Path("src/knowledge/analyze_annotation_readiness.py"),
    ]:
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in ("requests", "httpx", "urlopen", "openai", "anthropic", "google.cloud"):
            assert forbidden not in text
