from pathlib import Path

from knowledge.entity_extractor import build_entity_terms, extract_entities
from knowledge.evaluate_entity_extraction import (
    evaluate_entity_extraction,
    render_report,
    write_outputs,
)


def test_deity_extraction() -> None:
    entities = extract_entities("சிவன் , திருமால்")
    labels = {(item["label"], item["text"]) for item in entities}

    assert ("deity", "சிவன்") in labels
    assert ("deity", "திருமால்") in labels


def test_author_work_and_place_extraction() -> None:
    text = "திருஞானசம்பந்தர் பாடிய திருப்பூந்தராய் பதிகம்"
    entities = extract_entities(text)
    labels = {(item["label"], item["text"]) for item in entities}

    assert ("author", "திருஞானசம்பந்தர்") in labels
    assert ("place", "திருப்பூந்தராய்") in labels

    work_entities = extract_entities("சுப்பிரமணிய பாரதி எழுதிய யாரைத் தொழுவது?")
    work_labels = {(item["label"], item["text"]) for item in work_entities}
    assert ("author", "சுப்பிரமணிய பாரதி") in work_labels
    assert ("work", "யாரைத் தொழுவது") in work_labels


def test_extraction_is_deterministic() -> None:
    terms = build_entity_terms()
    text = "சிவன் மற்றும் திருஞானசம்பந்தர்"

    assert extract_entities(text, terms) == extract_entities(text, terms)


def test_entity_evaluation_metrics() -> None:
    results = evaluate_entity_extraction()

    assert results["expected_count"] == 7
    assert results["precision"] == 1.0
    assert results["recall"] >= 0.85
    assert results["f1"] >= 0.9
    assert results["corpus_wide_extraction_performed"] is False
    assert results["scraping_performed"] is False
    assert results["llm_calls"] == 0


def test_report_and_output_generation(tmp_path: Path) -> None:
    results = evaluate_entity_extraction()
    output = tmp_path / "entity_extraction_results.json"
    report = tmp_path / "entity-extraction-report.md"

    write_outputs(results, output_path=output, report_path=report)

    assert output.exists()
    assert report.exists()
    assert "Entity Extraction Report" in report.read_text(encoding="utf-8")
    assert "Precision" in render_report(results)


def test_entity_extraction_scripts_have_no_network_or_llm_dependencies() -> None:
    for path in [
        Path("src/knowledge/entity_extractor.py"),
        Path("src/knowledge/evaluate_entity_extraction.py"),
    ]:
        text = path.read_text(encoding="utf-8").lower()
        for forbidden in ("requests", "httpx", "urlopen", "openai", "anthropic", "google.cloud"):
            assert forbidden not in text
