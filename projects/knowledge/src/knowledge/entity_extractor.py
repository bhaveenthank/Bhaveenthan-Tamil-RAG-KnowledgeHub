from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

DEFAULT_KNOWLEDGE_DIR = Path("data/knowledge")
DEFAULT_NORMALIZED_DIR = Path("data/processed/normalized_categories")
DEFAULT_CORPUS_PATH = Path("data/processed/corpus/irandaam_thirumurai.jsonl")

SUPPORTED_LABELS = {"deity", "author", "place", "work"}


@dataclass(frozen=True)
class EntityTerm:
    term: str
    label: str
    canonical_id: str
    canonical_name: str
    source: str


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def normalize_term(term: str) -> str:
    return re.sub(r"\s+", " ", term.strip(" \n\t\r.,;:!?()[]{}\"'"))


def add_term(
    terms: dict[tuple[str, str], EntityTerm],
    *,
    term: str,
    label: str,
    canonical_id: str,
    canonical_name: str,
    source: str,
) -> None:
    cleaned = normalize_term(term)
    if not cleaned or label not in SUPPORTED_LABELS:
        return
    key = (cleaned, label)
    current = terms.get(key)
    candidate = EntityTerm(
        term=cleaned,
        label=label,
        canonical_id=canonical_id,
        canonical_name=canonical_name,
        source=source,
    )
    if current is None or (candidate.source, candidate.canonical_id) < (
        current.source,
        current.canonical_id,
    ):
        terms[key] = candidate


def terms_from_registry(
    knowledge_dir: Path = DEFAULT_KNOWLEDGE_DIR,
) -> dict[tuple[str, str], EntityTerm]:
    terms: dict[tuple[str, str], EntityTerm] = {}
    registry_map = {
        "deities.json": ("deity", "deity_id", "canonical_name", "aliases"),
        "authors.json": ("author", "author_id", "canonical_name", "aliases"),
        "places.json": ("place", "place_id", "canonical_name", "aliases"),
        "works.json": ("work", "work_id", "canonical_title", "aliases"),
    }
    for file_name, (label, id_field, title_field, alias_field) in registry_map.items():
        payload = load_json(knowledge_dir / file_name)
        for record in payload.get("records", []):
            canonical_id = record.get(id_field, "")
            canonical_name = record.get(title_field, "")
            add_term(
                terms,
                term=canonical_name,
                label=label,
                canonical_id=canonical_id,
                canonical_name=canonical_name,
                source=f"registry:{file_name}",
            )
            for alias in record.get(alias_field, []):
                add_term(
                    terms,
                    term=alias,
                    label=label,
                    canonical_id=canonical_id,
                    canonical_name=canonical_name,
                    source=f"registry:{file_name}",
                )
    return terms


def terms_from_local_metadata(
    normalized_dir: Path = DEFAULT_NORMALIZED_DIR,
    corpus_path: Path = DEFAULT_CORPUS_PATH,
) -> dict[tuple[str, str], EntityTerm]:
    terms: dict[tuple[str, str], EntityTerm] = {}
    for path in sorted(normalized_dir.glob("*.jsonl")) if normalized_dir.exists() else []:
        for record in iter_jsonl(path):
            record_id = record.get("record_id", "")
            author = record.get("author", "")
            title = record.get("title", "")
            if author:
                add_term(
                    terms,
                    term=author,
                    label="author",
                    canonical_id=f"local_author:{author}",
                    canonical_name=author,
                    source=f"metadata:{path.name}:{record_id}",
                )
            if title:
                add_term(
                    terms,
                    term=title,
                    label="work",
                    canonical_id=f"local_work:{title}",
                    canonical_name=title,
                    source=f"metadata:{path.name}:{record_id}",
                )
                add_term(
                    terms,
                    term=title.rstrip("?"),
                    label="work",
                    canonical_id=f"local_work:{title}",
                    canonical_name=title,
                    source=f"metadata:{path.name}:{record_id}",
                )
    for record in iter_jsonl(corpus_path):
        hymn_title = record.get("hymn_title", "")
        match = re.search(r"^\S+\s+(.+?)\s+-", hymn_title)
        if match:
            place = match.group(1)
            add_term(
                terms,
                term=place,
                label="place",
                canonical_id=f"local_place:{place}",
                canonical_name=place,
                source=f"metadata:{corpus_path.name}:{record.get('song_no', '')}",
            )
    return terms


def build_entity_terms(
    knowledge_dir: Path = DEFAULT_KNOWLEDGE_DIR,
    normalized_dir: Path = DEFAULT_NORMALIZED_DIR,
    corpus_path: Path = DEFAULT_CORPUS_PATH,
) -> list[EntityTerm]:
    terms = terms_from_registry(knowledge_dir)
    for key, term in terms_from_local_metadata(normalized_dir, corpus_path).items():
        terms.setdefault(key, term)
    return sorted(
        terms.values(),
        key=lambda item: (item.term, item.label, item.canonical_id, item.source),
    )


def extract_entities(text: str, terms: list[EntityTerm] | None = None) -> list[dict[str, Any]]:
    entity_terms = terms if terms is not None else build_entity_terms()
    matches: dict[tuple[int, int, str, str], dict[str, Any]] = {}
    for term in entity_terms:
        start = 0
        while True:
            index = text.find(term.term, start)
            if index == -1:
                break
            end = index + len(term.term)
            key = (index, end, term.label, term.term)
            matches[key] = {
                "type": "entity",
                "label": term.label,
                "text": term.term,
                "start": index,
                "end": end,
                "canonical_id": term.canonical_id,
                "canonical_name": term.canonical_name,
                "match_source": term.source,
            }
            start = index + 1
    candidates = [
        matches[key]
        for key in sorted(
            matches,
            key=lambda item: (item[0], -(item[1] - item[0]), item[2], item[3]),
        )
    ]
    selected: list[dict[str, Any]] = []
    for candidate in candidates:
        overlaps_same_entity = any(
            candidate["label"] == existing["label"]
            and candidate["canonical_id"] == existing["canonical_id"]
            and candidate["start"] >= existing["start"]
            and candidate["end"] <= existing["end"]
            for existing in selected
        )
        if not overlaps_same_entity:
            selected.append(candidate)
    return sorted(
        selected,
        key=lambda item: (item["start"], item["end"], item["label"], item["text"]),
    )
