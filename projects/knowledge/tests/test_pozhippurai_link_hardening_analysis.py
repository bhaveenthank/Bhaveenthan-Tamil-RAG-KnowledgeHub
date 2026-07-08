import csv
from pathlib import Path

from knowledge.analyze_pozhippurai_link_hardening import (
    analyze_links,
    write_outputs,
)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_hardening_analysis_categories_and_outputs(tmp_path: Path) -> None:
    primary = tmp_path / "primary.csv"
    secondary = tmp_path / "secondary.csv"
    write_csv(
        primary,
        [
            {
                "link_id": "high1",
                "confidence": "high",
                "score": "0.91",
                "relationship_type": "describes_entity",
                "manual_review_required": "False",
                "diagnostic_note": "High-confidence link with strong lexical/entity/containment evidence.",
                "features": "{'sequence_alignment_method': 'forward_dynamic_programming', 'shared_entity_types': ['TEMPLE'], 'synonym_score': 0.2}",
                "source_text": "கோயில்",
                "target_text": "திருக்கோயில்",
            },
            {
                "link_id": "low1",
                "confidence": "low",
                "score": "0.22",
                "relationship_type": "explains_phrase",
                "manual_review_required": "True",
                "diagnostic_note": "The best target is close to the second-best target, so several pozhppurai spans may be plausible.",
                "features": "{'sequence_alignment_method': 'unordered_assignment', 'shared_entity_types': [], 'synonym_score': 0.0}",
                "source_text": "அடி",
                "target_text": "விளக்கம்",
            },
            {
                "link_id": "med1",
                "confidence": "medium",
                "score": "0.48",
                "relationship_type": "interprets_image",
                "manual_review_required": "False",
                "diagnostic_note": "Medium-confidence link; likely useful but should be sampled before scholarly use.",
                "features": "{}",
                "source_text": "பிறை",
                "target_text": "சந்திரன்",
            },
        ],
    )
    write_csv(
        secondary,
        [
            {
                "link_id": "none1",
                "secondary_table_reason": "empty_pozhippurai",
            }
        ],
    )

    analysis = analyze_links(primary, secondary)
    assert analysis["primary_rows"] == 3
    assert analysis["secondary_rows"] == 1
    assert analysis["category_counts"]["accepted_high_ready"] == 1
    assert analysis["category_counts"]["low_ambiguous_multiple_targets"] == 1
    assert analysis["category_counts"]["medium_review_sample"] == 1
    assert analysis["secondary_reason_counts"]["empty_pozhippurai"] == 1
    assert any(item["capability"] == "metaphors" and item["ontology_status"] == "partial" for item in analysis["knowledge_annotation_capabilities"])

    output_json = tmp_path / "analysis.json"
    report = tmp_path / "report.md"
    sample = tmp_path / "sample.csv"
    write_outputs(analysis, output_json, report, sample)
    assert output_json.exists()
    assert "Knowledge Annotation Coverage" in report.read_text(encoding="utf-8")
    sample_text = sample.read_text(encoding="utf-8")
    assert "low_ambiguous_multiple_targets" in sample_text
    assert "accepted_high_ready" not in sample_text
