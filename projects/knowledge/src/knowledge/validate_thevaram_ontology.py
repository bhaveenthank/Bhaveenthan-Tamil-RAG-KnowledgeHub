from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

DEFAULT_ONTOLOGY = Path("data/knowledge/ontology/thevaram_ontology_v1.json")
DEFAULT_RELATIONS = Path("data/knowledge/ontology/thevaram_relations_v1.json")
DEFAULT_MIGRATION = Path("data/knowledge/ontology/migration/v2_to_v1_type_map.csv")
DEFAULT_V2_ROOT = Path("data/processed/thevaram_entity_annotations_v2")
DEFAULT_V3_ROOT = Path("data/processed/thevaram_entity_annotations_v3")
DEFAULT_SUMMARY = Path("data/knowledge/ontology/thevaram_ontology_v1_validation.json")
DEFAULT_REPORT = Path("reports/thevaram-ontology-v1-validation-report.md")

EXPECTED_TYPE_COUNT = 25
REQUIRED_TYPES = {
    "DEITY",
    "DIVINE_EPITHET",
    "MYTH_FIGURE",
    "SAINT",
    "REL_GROUP",
    "SACRED_PLACE",
    "RIVER",
    "MOUNTAIN",
    "SACRED_OBJECT",
    "FLORA",
    "FAUNA",
    "CELESTIAL",
    "BODY_PART",
    "MYTH_EVENT",
    "THEO_CONCEPT",
    "DEVOTIONAL_ACT",
    "RITUAL",
    "PAN",
    "INSTRUMENT",
    "TEXT_WORK",
}
DEPRECATED_V2_TYPES = {"ACTION", "NATURE"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_ontology(ontology: dict[str, Any], relations: dict[str, Any], migration_rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    if ontology.get("schema_version") != "thevaram-ontology-v1":
        errors.append("ontology schema_version must be thevaram-ontology-v1")
    if relations.get("schema_version") != "thevaram-relations-v1":
        errors.append("relations schema_version must be thevaram-relations-v1")

    entity_types = ontology.get("entity_types", [])
    if len(entity_types) != EXPECTED_TYPE_COUNT:
        errors.append(f"expected {EXPECTED_TYPE_COUNT} entity types, found {len(entity_types)}")
    type_codes = [str(row.get("code", "")) for row in entity_types]
    if len(type_codes) != len(set(type_codes)):
        errors.append("duplicate entity type codes")
    missing_required = REQUIRED_TYPES - set(type_codes)
    if missing_required:
        errors.append(f"missing required types: {sorted(missing_required)}")
    for index, row in enumerate(entity_types):
        for field in ("code", "name", "branch", "tier", "definition", "examples"):
            if field not in row:
                errors.append(f"entity type {index} missing {field}")
        if row.get("tier") not in {1, 2, 3}:
            errors.append(f"entity type {row.get('code')} has invalid tier")
        if not isinstance(row.get("examples", []), list) or not row.get("examples"):
            errors.append(f"entity type {row.get('code')} must include examples")

    relation_names = [str(row.get("name", "")) for row in relations.get("relations", [])]
    if len(relation_names) != len(set(relation_names)):
        errors.append("duplicate relation names")
    known_type_or_text = set(type_codes) | {"Verse", "Patikam"}
    for relation in relations.get("relations", []):
        for field in ("name", "domain", "range", "category"):
            if field not in relation:
                errors.append(f"relation {relation.get('name')} missing {field}")
        for endpoint_field in ("domain", "range"):
            values = relation.get(endpoint_field, [])
            if not isinstance(values, list) or not values:
                errors.append(f"relation {relation.get('name')} {endpoint_field} must be a non-empty list")
                continue
            unknown = set(values) - known_type_or_text
            if unknown:
                errors.append(f"relation {relation.get('name')} has unknown {endpoint_field}: {sorted(unknown)}")

    migration_legacy_types = {row.get("legacy_type", "") for row in migration_rows}
    expected_legacy = {"DEITY", "BODY_PART", "NATURE", "SACRED_OBJECT", "THEOLOGICAL_CONCEPT", "ACTION"}
    if migration_legacy_types != expected_legacy:
        errors.append(f"migration map legacy types mismatch: {sorted(migration_legacy_types)}")
    return errors


def measured_counts(v2_root: Path, v3_root: Path) -> dict[str, Any]:
    v2_mentions = read_jsonl(v2_root / "entity_mentions.jsonl")
    v3_mentions = read_jsonl(v3_root / "entity_mentions.jsonl")
    v2_registry = read_jsonl(v2_root / "entity_registry.jsonl")
    v3_registry = read_jsonl(v3_root / "entity_registry.jsonl")
    v3_relationships = read_jsonl(v3_root / "entity_relationships.jsonl")
    exact_span_types: Counter[tuple[str, str, Any, Any, str]] = Counter()
    duplicate_cross_type_spans = 0
    seen_span_types: dict[tuple[str, str, Any, Any], set[str]] = {}
    for row in v2_mentions:
        key = (str(row.get("target_id")), str(row.get("field_name")), row.get("start_char"), row.get("end_char"))
        seen_span_types.setdefault(key, set()).add(str(row.get("entity_type")))
    duplicate_cross_type_spans = sum(1 for values in seen_span_types.values() if len(values) > 1)
    for row in v2_mentions:
        exact_span_types[
            (
                str(row.get("target_id")),
                str(row.get("field_name")),
                row.get("start_char"),
                row.get("end_char"),
                str(row.get("entity_type")),
            )
        ] += 1
    return {
        "v2": {
            "registry_entities": len(v2_registry),
            "mentions": len(v2_mentions),
            "mention_counts_by_type": dict(sorted(Counter(str(row.get("entity_type")) for row in v2_mentions).items())),
            "cross_type_overlap_spans": duplicate_cross_type_spans,
        },
        "v3": {
            "registry_entities": len(v3_registry),
            "mentions": len(v3_mentions),
            "mention_counts_by_type": dict(sorted(Counter(str(row.get("entity_type")) for row in v3_mentions).items())),
            "relationship_count": len(v3_relationships),
            "temple_mentions": sum(1 for row in v3_mentions if row.get("entity_type") == "TEMPLE"),
            "paadapatta_thalam_mentions": sum(
                1 for row in v3_mentions if row.get("entity_subtype") == "paadapatta_thalam"
            ),
        },
    }


def build_summary(
    *,
    ontology_path: Path = DEFAULT_ONTOLOGY,
    relations_path: Path = DEFAULT_RELATIONS,
    migration_path: Path = DEFAULT_MIGRATION,
    v2_root: Path = DEFAULT_V2_ROOT,
    v3_root: Path = DEFAULT_V3_ROOT,
) -> dict[str, Any]:
    ontology = read_json(ontology_path)
    relations = read_json(relations_path)
    migration_rows = read_csv(migration_path)
    errors = validate_ontology(ontology, relations, migration_rows)
    type_codes = [row["code"] for row in ontology.get("entity_types", [])]
    return {
        "summary_version": "thevaram-ontology-validation-v1",
        "ontology_path": str(ontology_path),
        "relations_path": str(relations_path),
        "migration_path": str(migration_path),
        "entity_type_count": len(type_codes),
        "tier_counts": dict(sorted(Counter(str(row.get("tier")) for row in ontology.get("entity_types", [])).items())),
        "relation_count": len(relations.get("relations", [])),
        "attribute_count": len(ontology.get("attribute_set", [])),
        "myth_event_count": len(ontology.get("mythological_event_canon", [])),
        "deprecated_v2_types": sorted(DEPRECATED_V2_TYPES),
        "required_types_present": sorted(REQUIRED_TYPES & set(type_codes)),
        "measured_counts": measured_counts(v2_root, v3_root),
        "validation_errors": errors,
        "status": "VALID" if not errors else "INVALID",
    }


def render_report(summary: dict[str, Any]) -> str:
    v2 = summary["measured_counts"]["v2"]
    v3 = summary["measured_counts"]["v3"]

    def table(mapping: dict[str, Any]) -> str:
        return "\n".join(f"| `{key}` | {value} |" for key, value in mapping.items()) or "| None | 0 |"

    return f"""# Thevaram Ontology v1 Validation Report

## Summary

- Status: `{summary['status']}`
- Entity types: `{summary['entity_type_count']}`
- Relations: `{summary['relation_count']}`
- Attributes: `{summary['attribute_count']}`
- Mythological event canon size: `{summary['myth_event_count']}`
- Deprecated v2 entity types: `{', '.join(summary['deprecated_v2_types'])}`

## Current Annotation Baseline

- v2 registry entities: `{v2['registry_entities']}`
- v2 mentions: `{v2['mentions']}`
- v2 cross-type overlap spans: `{v2['cross_type_overlap_spans']}`
- v3 registry entities: `{v3['registry_entities']}`
- v3 mentions: `{v3['mentions']}`
- v3 relationships: `{v3['relationship_count']}`
- v3 temple mentions: `{v3['temple_mentions']}`
- v3 paadapatta-thalam mentions: `{v3['paadapatta_thalam_mentions']}`

## v2 Mention Counts

| Type | Mentions |
| --- | ---: |
{table(v2['mention_counts_by_type'])}

## v3 Mention Counts

| Type | Mentions |
| --- | ---: |
{table(v3['mention_counts_by_type'])}

## Migration Stance

The v1 ontology supersedes the six-type v2 layer. The first operational migration should:

1. Convert `ACTION` to canonical `MYTH_EVENT` anchors.
2. Split `NATURE` into `FLORA`, `FAUNA`, `RIVER`, `MOUNTAIN`, and `CELESTIAL`.
3. Narrow `SACRED_OBJECT` to artefacts/substances and move role semantics into relations.
4. Add `DIVINE_EPITHET`, `SACRED_PLACE`, `SAINT`, `REL_GROUP`, `PAN`, and `TEXT_WORK`.
5. Queue WSD-heavy lexemes such as `பதி`, `பசு`, `மெய்`, and `மால்` for review.
"""


def write_outputs(summary: dict[str, Any], *, summary_path: Path, report_path: Path) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the Thevaram ontology v1 contract and measured baseline.")
    parser.add_argument("--ontology", type=Path, default=DEFAULT_ONTOLOGY)
    parser.add_argument("--relations", type=Path, default=DEFAULT_RELATIONS)
    parser.add_argument("--migration", type=Path, default=DEFAULT_MIGRATION)
    parser.add_argument("--v2-root", type=Path, default=DEFAULT_V2_ROOT)
    parser.add_argument("--v3-root", type=Path, default=DEFAULT_V3_ROOT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = build_summary(
        ontology_path=args.ontology,
        relations_path=args.relations,
        migration_path=args.migration,
        v2_root=args.v2_root,
        v3_root=args.v3_root,
    )
    write_outputs(summary, summary_path=args.summary, report_path=args.report)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
