from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

DEFAULT_KNOWLEDGE_DIR = Path("data/knowledge")
REGISTRY_ORDER = ("synonyms", "authors", "deities", "motifs", "literary_devices")
REGISTRY_FIELDS = {
    "synonyms": ("canonical_term", ("synonyms", "variant_forms"), "concept_id"),
    "authors": ("canonical_name", ("aliases",), "author_id"),
    "deities": ("canonical_name", ("aliases",), "deity_id"),
    "motifs": ("motif_name", ("example_patterns",), "motif_id"),
    "literary_devices": ("device_name", ("recognition_cues",), "device_id"),
}
WORD_CHARACTER = r"\w\u0B80-\u0BFF"


def normalize_text(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value or "").split())


def ordered_unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def term_pattern(term: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?<![{WORD_CHARACTER}]){re.escape(term)}(?![{WORD_CHARACTER}])",
        flags=re.UNICODE,
    )


def find_term(query: str, candidates: list[str]) -> tuple[str, tuple[int, int]] | None:
    matches: list[tuple[int, int, str]] = []
    for candidate in candidates:
        match = term_pattern(candidate).search(query)
        if match:
            matches.append((match.start(), -len(candidate), candidate))
    if not matches:
        return None
    start, _negative_length, candidate = min(matches)
    return candidate, (start, start + len(candidate))


def load_registries(knowledge_dir: Path = DEFAULT_KNOWLEDGE_DIR) -> dict[str, list[dict[str, Any]]]:
    registries: dict[str, list[dict[str, Any]]] = {}
    for registry_name in REGISTRY_ORDER:
        path = knowledge_dir / f"{registry_name}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        registries[registry_name] = payload.get("records", [])
    return registries


class QueryExpander:
    def __init__(
        self,
        knowledge_dir: Path = DEFAULT_KNOWLEDGE_DIR,
        registries: dict[str, list[dict[str, Any]]] | None = None,
    ) -> None:
        self.registries = registries if registries is not None else load_registries(knowledge_dir)

    def expand(self, query: str) -> dict[str, Any]:
        original_query = normalize_text(query)
        expanded_terms: list[str] = []
        matched_registries: list[str] = []
        rules: list[dict[str, Any]] = []
        insertions: list[tuple[int, list[str]]] = []

        for registry_name in REGISTRY_ORDER:
            canonical_field, related_fields, id_field = REGISTRY_FIELDS[registry_name]
            for record in self.registries.get(registry_name, []):
                canonical = normalize_text(str(record.get(canonical_field, "")))
                related = ordered_unique(
                    [
                        normalize_text(str(term))
                        for field in related_fields
                        for term in record.get(field, [])
                    ]
                )
                candidates = ordered_unique([canonical, *related])
                found = find_term(original_query, candidates)
                if not found:
                    continue

                matched_term, (_start, end) = found
                approved_terms = ordered_unique([matched_term, canonical, *related])
                added_terms = [term for term in approved_terms if term != matched_term]
                expanded_terms.extend(approved_terms)
                if registry_name not in matched_registries:
                    matched_registries.append(registry_name)
                rules.append(
                    {
                        "registry": registry_name,
                        "record_id": str(record.get(id_field, "")),
                        "matched_term": matched_term,
                        "canonical_term": canonical,
                        "added_terms": added_terms,
                    }
                )
                if added_terms:
                    insertions.append((end, added_terms))

        expanded_terms = ordered_unique(expanded_terms)
        expanded_query_text = original_query
        for position, additions in sorted(insertions, key=lambda item: item[0], reverse=True):
            new_terms = [
                term
                for term in additions
                if not term_pattern(term).search(expanded_query_text)
            ]
            if new_terms:
                expanded_query_text = (
                    expanded_query_text[:position]
                    + " "
                    + " ".join(new_terms)
                    + expanded_query_text[position:]
                )
        expanded_query_text = normalize_text(expanded_query_text)

        return {
            "original_query": original_query,
            "expanded_terms": expanded_terms,
            "matched_registries": matched_registries,
            "expansion_rules": rules,
            "expanded_query_text": expanded_query_text,
            "expansion_applied": expanded_query_text != original_query,
        }
