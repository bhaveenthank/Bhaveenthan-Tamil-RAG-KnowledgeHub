import hashlib
import json
from pathlib import Path

from knowledge.analyze_knowledge_readiness import (
    REGISTRY_SPECS,
    analyze_knowledge_readiness,
    render_report,
    validate_registry,
    write_outputs,
)


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "data/knowledge"


def test_all_registry_files_exist_and_have_seed_records() -> None:
    for name in REGISTRY_SPECS:
        path = KNOWLEDGE / f"{name}.json"
        assert path.exists()
        registry = json.loads(path.read_text(encoding="utf-8"))
        assert registry["registry_name"] == name
        assert registry["schema_version"] == "knowledge-registry-v1"
        assert registry["status"] == "foundation_seed_only"
        assert len(registry["records"]) == 1


def test_registry_seed_schemas_validate() -> None:
    for name in REGISTRY_SPECS:
        registry = json.loads(
            (KNOWLEDGE / f"{name}.json").read_text(encoding="utf-8")
        )
        assert validate_registry(name, registry) == []


def test_documented_schema_definitions_exist() -> None:
    schemas = (ROOT / "docs/registry-schemas.md").read_text(encoding="utf-8")

    for identifier in (
        "entity_id",
        "concept_id",
        "motif_id",
        "author_id",
        "deity_id",
        "place_id",
        "work_id",
        "theme_id",
        "device_id",
    ):
        assert identifier in schemas
    assert "annotation_id" in schemas
    assert "source_url" in schemas


def test_readiness_analysis_is_deterministic_and_foundation_only() -> None:
    first = analyze_knowledge_readiness(KNOWLEDGE)
    second = analyze_knowledge_readiness(KNOWLEDGE)

    assert first == second
    assert first["registry_count"] == 9
    assert first["primary_capability_count"] == 8
    assert first["foundation_readiness_score"] == 70.0
    assert first["analytical_readiness_score"] == 35.0
    assert first["decision"] == "FOUNDATION_READY_EXTRACTION_NOT_STARTED"
    assert first["extraction_performed"] is False
    assert first["scraping_performed"] is False
    assert first["llm_calls"] == 0
    assert all(not item["schema_errors"] for item in first["capabilities"])


def test_readiness_outputs_are_generated(tmp_path: Path) -> None:
    analysis = analyze_knowledge_readiness(KNOWLEDGE)
    output = tmp_path / "readiness.json"
    report = tmp_path / "readiness.md"

    write_outputs(analysis, output_path=output, report_path=report)

    assert json.loads(output.read_text(encoding="utf-8")) == analysis
    text = report.read_text(encoding="utf-8")
    assert "Knowledge Readiness Report" in text
    assert "35.0/100" in text
    assert render_report(analysis) == text


def test_question_mapping_targets_and_roadmap_exist() -> None:
    mapping = (ROOT / "reports/literary-question-mapping.md").read_text(
        encoding="utf-8"
    )
    targets = (ROOT / "reports/future-extraction-targets.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "reports/knowledge-layer-roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "எந்த நாயன்மார் சந்திரனை அதிகமாக பயன்படுத்துகிறார்?" in mapping
    assert "சிவனுக்கான அடைமொழிகள் என்ன?" in mapping
    for target in ("deity names", "epithets", "metaphors", "similes", "motifs"):
        assert target in targets
    for phase in range(22, 28):
        assert f"Phase {phase}" in roadmap


def test_analyzer_has_no_scraping_extraction_or_llm_dependencies() -> None:
    script = (
        ROOT / "src/knowledge/analyze_knowledge_readiness.py"
    ).read_text(encoding="utf-8")

    for forbidden in (
        "import requests",
        "from requests",
        "import httpx",
        "from httpx",
        "urlopen",
        "openai",
        "anthropic",
        "google.cloud",
        "data/processed/corpus",
        "data/releases",
    ):
        assert forbidden not in script


def test_frozen_corpus_is_unchanged() -> None:
    release = ROOT / "data/releases/irandaam-thirumurai-v1"
    expected = {}
    for line in (release / "corpus_checksum.sha256").read_text(
        encoding="utf-8"
    ).splitlines():
        digest, filename = line.split(maxsplit=1)
        expected[filename] = digest
    corpus = release / "irandaam_thirumurai.jsonl"

    assert hashlib.sha256(corpus.read_bytes()).hexdigest() == expected[corpus.name]
