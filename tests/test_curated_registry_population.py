import json
from pathlib import Path

from knowledge.analyze_knowledge_readiness import analyze_knowledge_readiness
from knowledge.registry_contracts import REGISTRY_SPECS, load_registry, validate_registry
from knowledge.validate_registries import (
    build_validation_summary,
    render_quality_report,
    write_outputs,
)


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = ROOT / "data/knowledge"
CURATED_COUNTS = {
    "synonyms": 3,
    "deities": 3,
    "authors": 3,
    "motifs": 3,
    "literary_devices": 3,
}


def records(name: str) -> list[dict]:
    return load_registry(KNOWLEDGE / f"{name}.json")["records"]


def test_curated_registries_validate_and_have_unique_ids() -> None:
    for name, expected_count in CURATED_COUNTS.items():
        registry = load_registry(KNOWLEDGE / f"{name}.json")
        id_field = REGISTRY_SPECS[name]["id_field"]
        identifiers = [record[id_field] for record in registry["records"]]

        assert registry["status"] == "curated_seed_v1"
        assert len(registry["records"]) == expected_count
        assert identifiers == sorted(identifiers)
        assert len(identifiers) == len(set(identifiers))
        assert all(record["status"] == "curated_seed" for record in registry["records"])
        assert validate_registry(name, registry) == []


def test_required_synonym_concepts_and_forms_are_present() -> None:
    by_id = {record["concept_id"]: record for record in records("synonyms")}

    assert by_id["concept_moon"]["canonical_term"] == "சந்திரன்"
    assert set(by_id["concept_moon"]["synonyms"]) == {"நிலா", "மதி", "திங்கள்"}
    assert by_id["concept_moon"]["variant_forms"] == ["நிலவு"]
    assert by_id["concept_sun"]["synonyms"] == ["கதிரவன்"]
    assert by_id["concept_ocean"]["synonyms"] == ["சமுத்திரம்"]


def test_required_deities_and_aliases_are_present() -> None:
    by_name = {record["canonical_name"]: record for record in records("deities")}

    assert set(by_name) == {"சிவன்", "முருகன்", "விஷ்ணு"}
    assert "சிவபெருமான்" in by_name["சிவன்"]["aliases"]
    assert "கந்தன்" in by_name["முருகன்"]["aliases"]
    assert "திருமால்" in by_name["விஷ்ணு"]["aliases"]


def test_required_authors_and_known_works_are_present() -> None:
    by_name = {record["canonical_name"]: record for record in records("authors")}

    assert set(by_name) == {"திருஞானசம்பந்தர்", "திருநாவுக்கரசர்", "சுந்தரர்"}
    assert "சம்பந்தர்" in by_name["திருஞானசம்பந்தர்"]["aliases"]
    assert "அப்பர்" in by_name["திருநாவுக்கரசர்"]["aliases"]
    assert "நம்பியாரூரர்" in by_name["சுந்தரர்"]["aliases"]
    assert all(record["works"] for record in by_name.values())


def test_required_motifs_and_literary_devices_are_present() -> None:
    motif_ids = {record["motif_id"] for record in records("motifs")}
    device_names = {record["device_name"] for record in records("literary_devices")}

    assert motif_ids == {
        "motif_fire_imagery",
        "motif_lunar_imagery",
        "motif_river_imagery",
    }
    assert device_names == {"உவமை", "உருவகம்", "அடைமொழி"}


def test_validation_summary_and_quality_report_are_deterministic(tmp_path: Path) -> None:
    first = build_validation_summary(KNOWLEDGE)
    second = build_validation_summary(KNOWLEDGE)
    summary_path = tmp_path / "summary.json"
    report_path = tmp_path / "report.md"

    assert first == second
    assert first["status"] == "VALID"
    assert first["curated_entries"]["synonyms"] == 3
    assert first["lexical_form_counts"]["synonyms"] == 9
    write_outputs(first, summary_path=summary_path, report_path=report_path)
    assert json.loads(summary_path.read_text(encoding="utf-8")) == first
    assert report_path.read_text(encoding="utf-8") == render_quality_report(first)


def test_readiness_improves_over_phase_21_without_claiming_extraction() -> None:
    analysis = analyze_knowledge_readiness(KNOWLEDGE)

    assert analysis["foundation_readiness_score"] == 79.4
    assert analysis["analytical_readiness_score"] == 47.5
    assert analysis["foundation_readiness_score"] > analysis["baseline"]["foundation_readiness_score"]
    assert analysis["analytical_readiness_score"] > analysis["baseline"]["analytical_readiness_score"]
    assert analysis["decision"] == "CURATED_SEED_READY_EXTRACTION_NOT_STARTED"
    assert analysis["extraction_performed"] is False
    assert analysis["scraping_performed"] is False
    assert analysis["llm_calls"] == 0
    assert all(item["evidence_link_count"] == 0 for item in analysis["capabilities"])
    assert all(item["corpus_annotation_count"] == 0 for item in analysis["capabilities"])


def test_validation_code_has_no_network_extraction_or_llm_path() -> None:
    text = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in (
            "src/knowledge/registry_contracts.py",
            "src/knowledge/validate_registries.py",
            "src/knowledge/analyze_knowledge_readiness.py",
        )
    )
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
        assert forbidden not in text
