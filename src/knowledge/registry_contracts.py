from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REGISTRY_SPECS: dict[str, dict[str, Any]] = {
    "synonyms": {
        "capability": "synonym_readiness",
        "id_field": "concept_id",
        "canonical_field": "canonical_term",
        "alias_fields": ("synonyms", "variant_forms"),
        "required": {"concept_id", "canonical_term", "synonyms", "variant_forms"},
    },
    "entities": {
        "capability": "entity_readiness",
        "id_field": "entity_id",
        "canonical_field": "canonical_name",
        "alias_fields": ("aliases",),
        "required": {
            "entity_id",
            "entity_type",
            "canonical_name",
            "aliases",
            "description",
        },
    },
    "motifs": {
        "capability": "motif_readiness",
        "id_field": "motif_id",
        "canonical_field": "motif_name",
        "alias_fields": (),
        "required": {"motif_id", "motif_name", "description", "example_patterns"},
    },
    "authors": {
        "capability": "author_readiness",
        "id_field": "author_id",
        "canonical_field": "canonical_name",
        "alias_fields": ("aliases",),
        "required": {"author_id", "canonical_name", "aliases", "period", "works"},
    },
    "deities": {
        "capability": "deity_readiness",
        "id_field": "deity_id",
        "canonical_field": "canonical_name",
        "alias_fields": ("aliases",),
        "required": {
            "deity_id",
            "canonical_name",
            "aliases",
            "tradition",
            "description",
        },
    },
    "places": {
        "capability": "place_readiness",
        "id_field": "place_id",
        "canonical_field": "canonical_name",
        "alias_fields": ("aliases",),
        "required": {
            "place_id",
            "canonical_name",
            "aliases",
            "place_type",
            "description",
        },
    },
    "themes": {
        "capability": "theme_readiness",
        "id_field": "theme_id",
        "canonical_field": "theme_name",
        "alias_fields": (),
        "required": {"theme_id", "theme_name", "description", "related_concepts"},
    },
    "literary_devices": {
        "capability": "literary_device_readiness",
        "id_field": "device_id",
        "canonical_field": "device_name",
        "alias_fields": (),
        "required": {
            "device_id",
            "device_name",
            "description",
            "recognition_cues",
        },
    },
    "works": {
        "capability": "work_registry_support",
        "id_field": "work_id",
        "canonical_field": "canonical_title",
        "alias_fields": ("aliases",),
        "required": {
            "work_id",
            "canonical_title",
            "aliases",
            "authors",
            "period",
            "genre",
        },
    },
}

LIST_FIELDS = {
    "aliases",
    "synonyms",
    "variant_forms",
    "example_patterns",
    "works",
    "authors",
    "related_concepts",
    "recognition_cues",
}
ALLOWED_REGISTRY_STATUSES = {"foundation_seed_only", "curated_seed_v1"}


def load_registry(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalized(value: Any) -> str:
    return str(value or "").strip()


def validate_registry(name: str, registry: dict[str, Any]) -> list[str]:
    spec = REGISTRY_SPECS[name]
    errors: list[str] = []
    status = registry.get("status")
    if registry.get("registry_name") != name:
        errors.append("registry_name mismatch")
    if registry.get("schema_version") != "knowledge-registry-v1":
        errors.append("invalid schema_version")
    if status not in ALLOWED_REGISTRY_STATUSES:
        errors.append("invalid registry status")
    records = registry.get("records")
    if not isinstance(records, list):
        return errors + ["records must be a list"]

    identifiers: list[str] = []
    canonical_values: list[str] = []
    alias_owners: dict[str, str] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"record {index} must be an object")
            continue
        missing = spec["required"] - record.keys()
        if missing:
            errors.append(f"record {index} missing {sorted(missing)}")
        if status == "curated_seed_v1" and record.get("status") != "curated_seed":
            errors.append(f"record {index} missing curated_seed status")

        identifier = _normalized(record.get(spec["id_field"]))
        canonical = _normalized(record.get(spec["canonical_field"]))
        if not identifier:
            errors.append(f"record {index} has invalid {spec['id_field']}")
        else:
            identifiers.append(identifier)
        if not canonical:
            errors.append(f"record {index} has invalid {spec['canonical_field']}")
        else:
            canonical_values.append(canonical)

        for field in spec["required"] & LIST_FIELDS:
            if field in record and not isinstance(record[field], list):
                errors.append(f"record {index} field {field} must be a list")

        aliases: list[str] = []
        for field in spec["alias_fields"]:
            values = record.get(field, [])
            if isinstance(values, list):
                aliases.extend(_normalized(value) for value in values if _normalized(value))
        if len(aliases) != len(set(aliases)):
            errors.append(f"record {index} contains duplicate aliases")
        if canonical and canonical in aliases:
            errors.append(f"record {index} repeats canonical value as alias")
        for alias in aliases:
            owner = alias_owners.setdefault(alias, identifier)
            if owner != identifier:
                errors.append(f"alias {alias!r} maps to multiple IDs")

    if len(identifiers) != len(set(identifiers)):
        errors.append("duplicate registry IDs")
    if len(canonical_values) != len(set(canonical_values)):
        errors.append("duplicate canonical values")
    if identifiers != sorted(identifiers):
        errors.append("records must be sorted by deterministic ID")
    return errors
