from __future__ import annotations

import argparse
import ast
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

DEFAULT_LINK_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4")
DEFAULT_PRIMARY = DEFAULT_LINK_ROOT / "paadal_pozhippurai_links_v4_primary_clean_links.csv"
DEFAULT_SECONDARY = DEFAULT_LINK_ROOT / "paadal_pozhippurai_links_v4_secondary_no_link.csv"
DEFAULT_OUTPUT_JSON = DEFAULT_LINK_ROOT / "paadal_pozhippurai_links_v4_hardening_analysis.json"
DEFAULT_OUTPUT_REPORT = DEFAULT_LINK_ROOT / "paadal_pozhippurai_links_v4_hardening_report.md"
DEFAULT_SAMPLE_CSV = DEFAULT_LINK_ROOT / "paadal_pozhippurai_links_v4_hardening_review_samples.csv"

CATEGORY_GUIDANCE = {
    "low_surface_vocab_gap": {
        "meaning": "The paadal span and selected pozhppurai span share little direct surface vocabulary.",
        "fix": "Add synonym/semantic lexicons, morphology-aware matching, and ontology relation cues before manual review.",
    },
    "low_order_only_support": {
        "meaning": "The selected span is mainly chosen by poem/commentary order.",
        "fix": "Use neighbouring span constraints, reverse-order alignment, and relation cue scoring to confirm or move the target.",
    },
    "low_missing_entity_anchor": {
        "meaning": "No accepted entity anchor is shared across the paadal and pozhppurai spans.",
        "fix": "Improve entity annotation for deity epithets, thalam names, sacred objects, body parts, and myth event terms.",
    },
    "low_ambiguous_multiple_targets": {
        "meaning": "The best and second-best target spans are too close.",
        "fix": "Resolve with global sequence assignment, next/previous span evidence, and manual gold examples for repeated patterns.",
    },
    "low_weak_similarity": {
        "meaning": "The combined score is weak even after current lexical/entity/order evidence.",
        "fix": "Keep for review; promote only when synonym, ontology, or curated examples support the target.",
    },
    "medium_review_sample": {
        "meaning": "Likely useful link, but not yet strong enough for scholarly use without sampling.",
        "fix": "Sample by thirumurai and relationship type; promote repeatable patterns into gold rules.",
    },
    "accepted_high_ready": {
        "meaning": "Strong link; ready for baseline chat/retrieval use.",
        "fix": "Use as positive training/evaluation data.",
    },
    "empty_pozhippurai_secondary": {
        "meaning": "No usable pozhppurai text exists for the row.",
        "fix": "Keep outside the main linked corpus; do not count as linker failure.",
    },
}

ANNOTATION_CAPABILITIES = [
    {
        "capability": "deity_attributes",
        "ontology_status": "mostly_present",
        "covered_by": ["DEITY", "DIVINE_EPITHET", "BODY_PART", "SACRED_OBJECT", "FLORA", "FAUNA", "CELESTIAL"],
        "relations": ["wears", "wears_on", "holds", "rides", "smeared_with", "adorns"],
        "next_step": "Extract iconographic triples from high/medium paadal-pozhppurai links.",
    },
    {
        "capability": "places_thalam_links",
        "ontology_status": "present_but_needs_alias_alignment",
        "covered_by": ["SACRED_PLACE", "REGION", "RIVER", "MOUNTAIN"],
        "relations": ["sung_at", "enshrined_at", "located_on", "located_in", "flows_through"],
        "next_step": "Map V3 TEMPLE/thalam annotations into Ontology v1 SACRED_PLACE and add patikam-level thalam links.",
    },
    {
        "capability": "metaphors",
        "ontology_status": "partial",
        "covered_by": ["qualifier: in_simile", "pozhppurai relationship: interprets_image"],
        "relations": [],
        "next_step": "Develop a METAPHOR/POETIC_IMAGE layer with source image, target meaning, cue word, and certainty.",
    },
    {
        "capability": "devotional_results",
        "ontology_status": "partial",
        "covered_by": ["THEO_CONCEPT", "DEVOTIONAL_ACT"],
        "relations": ["grants", "praises", "worshipped_by"],
        "next_step": "Add a devotional-result extraction layer for results such as வினை நீங்கும், முத்தி, அருள், பிணி நீங்கும்.",
    },
    {
        "capability": "theological_concepts",
        "ontology_status": "present",
        "covered_by": ["THEO_CONCEPT", "COSMO_CONCEPT"],
        "relations": ["grants"],
        "next_step": "Create a curated concept registry and link concept mentions to paadal/pozhppurai evidence.",
    },
    {
        "capability": "mythological_actions",
        "ontology_status": "present",
        "covered_by": ["MYTH_EVENT", "MYTH_FIGURE", "MANIFESTATION"],
        "relations": ["agent_of", "patient_of", "instrument_of", "beneficiary_of", "event_mentioned_in"],
        "next_step": "Extract event mentions and normalize them to the mythological_event_canon.",
    },
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_features(value: str) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def categorize_row(row: dict[str, str]) -> str:
    confidence = row.get("confidence", "")
    note = row.get("diagnostic_note", "")
    if confidence == "high":
        return "accepted_high_ready"
    if confidence == "medium":
        return "medium_review_sample"
    if "share little surface vocabulary" in note:
        return "low_surface_vocab_gap"
    if "mainly supported by poem/commentary order" in note:
        return "low_order_only_support"
    if "No accepted Entity" in note:
        return "low_missing_entity_anchor"
    if "best target is close" in note:
        return "low_ambiguous_multiple_targets"
    if "weak combined similarity" in note:
        return "low_weak_similarity"
    return "low_weak_similarity" if confidence == "low" else "medium_review_sample"


def score_bucket(score: str) -> str:
    try:
        value = float(score or 0)
    except ValueError:
        value = 0.0
    if value >= 0.75:
        return "0.75-1.00"
    if value >= 0.50:
        return "0.50-0.74"
    if value >= 0.30:
        return "0.30-0.49"
    return "0.00-0.29"


def sample_rows(rows: list[dict[str, Any]], limit_per_category: int = 25) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        category = row["hardening_category"]
        if len(buckets[category]) < limit_per_category:
            buckets[category].append(row)
    ordered: list[dict[str, Any]] = []
    for category in sorted(buckets):
        ordered.extend(buckets[category])
    return ordered


def analyze_links(primary_path: Path = DEFAULT_PRIMARY, secondary_path: Path = DEFAULT_SECONDARY) -> dict[str, Any]:
    primary_rows = read_csv(primary_path)
    secondary_rows = read_csv(secondary_path)
    enriched_rows: list[dict[str, Any]] = []
    for row in primary_rows:
        features = parse_features(row.get("features", ""))
        enriched = dict(row)
        enriched["hardening_category"] = categorize_row(row)
        enriched["score_bucket"] = score_bucket(row.get("score", ""))
        enriched["sequence_alignment_method"] = features.get("sequence_alignment_method", "")
        enriched["shared_entity_types"] = ",".join(features.get("shared_entity_types", []) or [])
        enriched["synonym_score"] = features.get("synonym_score", 0.0)
        enriched_rows.append(enriched)

    secondary_reason_counts = Counter(row.get("secondary_table_reason", "") for row in secondary_rows)
    category_counts = Counter(row["hardening_category"] for row in enriched_rows)
    category_by_confidence = Counter((row.get("confidence", ""), row["hardening_category"]) for row in enriched_rows)
    category_by_relationship = Counter((row["hardening_category"], row.get("relationship_type", "")) for row in enriched_rows)
    method_counts = Counter(row.get("sequence_alignment_method") or row.get("method", "") for row in enriched_rows)
    alignment_by_confidence = Counter((row.get("confidence", ""), row.get("sequence_alignment_method") or row.get("method", "")) for row in enriched_rows)

    sample = sample_rows(
        [row for row in enriched_rows if row["hardening_category"] != "accepted_high_ready"],
        limit_per_category=25,
    )
    return {
        "analysis_version": "paadal-pozhppurai-hardening-v1",
        "primary_csv": str(primary_path),
        "secondary_csv": str(secondary_path),
        "primary_rows": len(primary_rows),
        "secondary_rows": len(secondary_rows),
        "confidence_counts": dict(sorted(Counter(row.get("confidence", "") for row in primary_rows).items())),
        "relationship_counts": dict(sorted(Counter(row.get("relationship_type", "") for row in primary_rows).items())),
        "category_counts": dict(sorted(category_counts.items())),
        "category_by_confidence": {
            f"{confidence}|{category}": count
            for (confidence, category), count in sorted(category_by_confidence.items())
        },
        "category_by_relationship": {
            f"{category}|{relationship}": count
            for (category, relationship), count in sorted(category_by_relationship.items())
        },
        "score_buckets": dict(sorted(Counter(row["score_bucket"] for row in enriched_rows).items())),
        "alignment_methods": dict(sorted(method_counts.items())),
        "alignment_by_confidence": {
            f"{confidence}|{method}": count
            for (confidence, method), count in sorted(alignment_by_confidence.items())
        },
        "secondary_reason_counts": dict(sorted(secondary_reason_counts.items())),
        "manual_review_required": dict(sorted(Counter(row.get("manual_review_required", "") for row in primary_rows).items())),
        "category_guidance": CATEGORY_GUIDANCE,
        "knowledge_annotation_capabilities": ANNOTATION_CAPABILITIES,
        "sample_rows": sample,
    }


def render_counts_table(title: str, counts: dict[str, int]) -> str:
    rows = "\n".join(f"| `{key}` | {value} |" for key, value in counts.items())
    return f"## {title}\n\n| Category | Rows |\n| --- | ---: |\n{rows}\n"


def render_report(analysis: dict[str, Any]) -> str:
    guidance_rows = "\n".join(
        f"| `{name}` | {details['meaning']} | {details['fix']} |"
        for name, details in analysis["category_guidance"].items()
    )
    capability_rows = "\n".join(
        f"| `{item['capability']}` | `{item['ontology_status']}` | {', '.join(item['covered_by'])} | {', '.join(item['relations']) or '-'} | {item['next_step']} |"
        for item in analysis["knowledge_annotation_capabilities"]
    )
    return f"""# Paadal-Pozhippurai Link Hardening Analysis

## Deliverable CSVs

- Primary linked corpus CSV: `{analysis['primary_csv']}`
- Secondary no-link CSV: `{analysis['secondary_csv']}`
- Review sample CSV: `{DEFAULT_SAMPLE_CSV}`

## Summary

- Primary clean linked rows: `{analysis['primary_rows']}`
- Secondary no-link rows: `{analysis['secondary_rows']}`
- Main-table no-link rows: `0`
- Secondary no-link reason: `{analysis['secondary_reason_counts']}`

{render_counts_table('Confidence Counts', analysis['confidence_counts'])}

{render_counts_table('Hardening Categories', analysis['category_counts'])}

{render_counts_table('Score Buckets', analysis['score_buckets'])}

{render_counts_table('Alignment Methods', analysis['alignment_methods'])}

## Low/Medium Confidence Categories And Fixes

| Category | Meaning | What To Do |
| --- | --- | --- |
{guidance_rows}

## Knowledge Annotation Coverage

| Capability | Ontology Status | Covered By | Relations | Next Step |
| --- | --- | --- | --- | --- |
{capability_rows}

## Recommended Hardening Order

1. Promote repeated medium links into high confidence through sampled review and gold rules.
2. Add ontology-backed entity anchors for deity epithets, thalam/place names, sacred objects, body parts, and myth events.
3. Add a metaphor/poetic-image annotation layer because this is only partial in the current ontology.
4. Add devotional-result extraction for அருள், வினை நீங்கும், முத்தி, பிணி நீங்கும், and similar result statements.
5. Re-run the linker and this hardening report after every new gold-rule batch.
"""


def write_outputs(
    analysis: dict[str, Any],
    output_json: Path = DEFAULT_OUTPUT_JSON,
    output_report: Path = DEFAULT_OUTPUT_REPORT,
    sample_csv: Path = DEFAULT_SAMPLE_CSV,
) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    output_report.write_text(render_report(analysis), encoding="utf-8")
    sample_fields = [
        "hardening_category",
        "confidence",
        "score",
        "score_bucket",
        "relationship_type",
        "thirumurai_no",
        "paadal_id",
        "source_text",
        "target_text",
        "diagnostic_note",
        "sequence_alignment_method",
        "shared_entity_types",
        "synonym_score",
        "link_id",
    ]
    write_csv(sample_csv, analysis["sample_rows"], sample_fields)


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze paadal-pozhppurai link hardening categories.")
    parser.add_argument("--primary", type=Path, default=DEFAULT_PRIMARY)
    parser.add_argument("--secondary", type=Path, default=DEFAULT_SECONDARY)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-report", type=Path, default=DEFAULT_OUTPUT_REPORT)
    parser.add_argument("--sample-csv", type=Path, default=DEFAULT_SAMPLE_CSV)
    args = parser.parse_args()
    analysis = analyze_links(args.primary, args.secondary)
    write_outputs(analysis, args.output_json, args.output_report, args.sample_csv)
    print(json.dumps({k: analysis[k] for k in ["primary_rows", "secondary_rows", "category_counts"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
