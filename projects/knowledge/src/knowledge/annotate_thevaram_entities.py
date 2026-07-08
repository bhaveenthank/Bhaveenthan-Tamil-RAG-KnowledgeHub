from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "thevaram-entity-annotation-v2"
DEFAULT_TABLE_ROOT = Path("data/processed/thevaram_normalized")
DEFAULT_SEED_DIR = Path("/Users/bhaveenthankajanikanth/Desktop/Tamil RAG/Pilot Entity datasets")
DEFAULT_REVIEW_DIR = Path("/Users/bhaveenthankajanikanth/Desktop/Tamil RAG/Entity Annotation")
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_entity_annotations_v2")
DEFAULT_REPORT = Path("reports/thevaram-entity-annotation-v2-report.md")

SEED_FILES = {
    "DEITY": "thevaram_deity_spans.tsv",
    "SACRED_OBJECT": "thevaram_sacred_object_audit.tsv",
    "BODY_PART": "thevaram_body_part_audit.tsv",
    "NATURE": "thevaram_nature_audit.tsv",
    "ACTION": "thevaram_action_audit.tsv",
    "THEOLOGICAL_CONCEPT": "thevaram_theology_audit.tsv",
}

TEXT_FIELDS = {
    "paadalgal": ("paadal_text",),
    "commentaries": ("kurippurai", "pozhppurai"),
}

DEITY_CANONICAL = {
    "SIVA": ("deity_siva", "சிவன்"),
    "PARVATI": ("deity_parvati", "பார்வதி/உமை"),
    "VISHNU": ("deity_vishnu", "விஷ்ணு/திருமால்"),
    "BRAHMA": ("deity_brahma", "பிரமன்/நான்முகன்"),
    "GANAPATI": ("deity_ganapati", "கணபதி"),
    "MURUGAN": ("deity_murugan", "முருகன்"),
}

PUNCTUATION = " \n\t\r.,;:!?()[]{}\"'“”‘’"
TOKEN_SPLIT_RE = re.compile(r"[\s,.;:!?()\[\]{}\"'“”‘’\-]+")


@dataclass(frozen=True, slots=True)
class SeedTerm:
    term_id: str
    term: str
    entity_type: str
    canonical_id: str
    canonical_name: str
    gloss: str
    source_seed_id: str
    source_file: str
    note: str
    confidence: float
    review_decision: str = "UNREVIEWED"
    v2_rule: str = ""
    observed_mentions_v1: int = 0
    entity_subtype: str = ""
    ontology_source: str = "pilot_seed"


@dataclass(frozen=True, slots=True)
class ReviewDecision:
    alias: str
    entity_type: str
    entity_id: str
    decision: str
    v2_rule: str
    observed_mentions: int


def stable_hash(*parts: object, length: int = 16) -> str:
    raw = "|".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:length]


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFC", value or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    return " ".join(text.strip(PUNCTUATION).split())


def slug_id(value: str) -> str:
    return stable_hash(normalize_text(value), length=12)


def parse_span_items(value: str) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for part in (value or "").split(";"):
        item = part.strip()
        if not item:
            continue
        if "=>" in item:
            span, gloss = item.split("=>", 1)
        else:
            span, gloss = item, ""
        span = normalize_text(span)
        gloss = normalize_text(gloss)
        if span:
            items.append((span, gloss))
    return items


def canonical_for(entity_type: str, term: str, row: dict[str, str]) -> tuple[str, str, float]:
    if entity_type == "DEITY":
        label = normalize_text(row.get("label", "")).upper()
        if label in DEITY_CANONICAL:
            canonical_id, canonical_name = DEITY_CANONICAL[label]
            return canonical_id, canonical_name, 0.92
        if label:
            return f"deity_{label.lower()}", label, 0.86
    return (
        f"{entity_type.lower()}_{slug_id(term)}",
        term,
        0.84 if len(term) >= 5 else 0.72,
    )


def load_review_decisions(review_dir: Path = DEFAULT_REVIEW_DIR) -> dict[tuple[str, str, str], ReviewDecision]:
    path = review_dir / "entity_v1_all_alias_review_decisions.csv"
    decisions: dict[tuple[str, str, str], ReviewDecision] = {}
    if not path.exists():
        return decisions
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            alias = normalize_text(row.get("alias", ""))
            entity_type = normalize_text(row.get("entity_type", "")).upper()
            entity_id = normalize_text(row.get("entity_id", ""))
            if not alias or not entity_type or not entity_id:
                continue
            decision = normalize_text(row.get("decision", "")).upper() or "UNREVIEWED"
            v2_rule = normalize_text(row.get("v2_rule", ""))
            # The alias sheet inherited the standalone கை exclusion onto a few
            # Ganga aliases. The main review table explicitly keeps these; the
            # real fix is token-boundary matching for கை, not deleting Ganga.
            if alias in {"கங்கை", "கங்கையைத்", "கங்கைப்புனல்"}:
                decision = "KEEP"
                if not v2_rule:
                    v2_rule = "Keep Ganga as NATURE/SACRED_OBJECT; block only false கை substring matches."
            decisions[(alias, entity_type, entity_id)] = ReviewDecision(
                alias=alias,
                entity_type=entity_type,
                entity_id=entity_id,
                decision=decision,
                v2_rule=v2_rule,
                observed_mentions=int(row.get("observed_mentions") or 0),
            )
    return decisions


def load_seed_terms(
    seed_dir: Path = DEFAULT_SEED_DIR,
    review_dir: Path = DEFAULT_REVIEW_DIR,
    apply_review_decisions: bool = True,
) -> list[SeedTerm]:
    terms: dict[tuple[str, str, str], SeedTerm] = {}
    review_decisions = load_review_decisions(review_dir) if apply_review_decisions else {}
    for entity_type, file_name in SEED_FILES.items():
        path = seed_dir / file_name
        if not path.exists():
            continue
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            for row in reader:
                seed_id = row.get("id") or row.get("sent_id") or stable_hash(row)
                span_items = (
                    [(normalize_text(row["span"]), normalize_text(row.get("note", "")))]
                    if row.get("span")
                    else parse_span_items(row.get("spans", ""))
                )
                for span, gloss in span_items:
                    if not span:
                        continue
                    canonical_id, canonical_name, confidence = canonical_for(entity_type, span, row)
                    review = review_decisions.get((span, entity_type, canonical_id))
                    term_id = f"term_{entity_type.lower()}_{slug_id(span + canonical_id)}"
                    key = (span, entity_type, canonical_id)
                    candidate = SeedTerm(
                        term_id=term_id,
                        term=span,
                        entity_type=entity_type,
                        canonical_id=canonical_id,
                        canonical_name=canonical_name,
                        gloss=gloss,
                        source_seed_id=str(seed_id),
                        source_file=file_name,
                        note=normalize_text(row.get("note", "")),
                        confidence=confidence,
                        review_decision=review.decision if review else "UNREVIEWED",
                        v2_rule=review.v2_rule if review else "",
                        observed_mentions_v1=review.observed_mentions if review else 0,
                    )
                    current = terms.get(key)
                    if current is None or (candidate.source_file, candidate.source_seed_id) < (
                        current.source_file,
                        current.source_seed_id,
                    ):
                        terms[key] = candidate
    return sorted(
        terms.values(),
        key=lambda item: (-len(item.term), item.entity_type, item.term, item.canonical_id),
    )


def is_token_char(char: str) -> bool:
    return char.isalnum() or "\u0B80" <= char <= "\u0BFF"


def has_token_boundaries(text: str, start: int, end: int) -> bool:
    before_ok = start == 0 or not is_token_char(text[start - 1])
    after_ok = end == len(text) or not is_token_char(text[end])
    return before_ok and after_ok


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


@lru_cache(maxsize=4096)
def flexible_pattern(term: str) -> re.Pattern[str]:
    pieces = [re.escape(piece) for piece in term.split()]
    pattern = r"\s+".join(pieces)
    return re.compile(pattern)


def find_term_matches(text: str, term: SeedTerm) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    if not text or not term.term:
        return matches
    for match in flexible_pattern(term.term).finditer(text):
        start, end = match.span()
        if term.term == "கை" and not has_token_boundaries(text, start, end):
            continue
        mention_text = text[start:end]
        if not mention_text.strip():
            continue
        matches.append(
            {
                "start_char": start,
                "end_char": end,
                "mention_text": mention_text,
                "matched_term": term.term,
                "term": term,
            }
        )
    return matches


def context_window(text: str, start: int, end: int, chars: int = 24) -> str:
    return text[max(0, start - chars) : min(len(text), end + chars)]


def context_supports_term(term: SeedTerm, text: str, start: int, end: int) -> bool:
    window = context_window(text, start, end)
    if term.review_decision == "KEEP":
        return True
    if term.term in {"அடி", "பாதம்", "தாள்", "திருவடி"}:
        return any(
            marker in window
            for marker in ("தொழ", "சேர", "பணி", "பணிந்து", "வணங்கு", "வழிபடு", "திரு", "மலர்")
        )
    if term.term == "உள்ளம்":
        return any(marker in window for marker in ("கவர்", "நினை", "உறை", "அன்ப", "புகு"))
    if term.term == "மெய்":
        return any(marker in window for marker in ("பூசி", "நீறு", "உடைய", "உரு", "உடல்"))
    if term.term == "பதி":
        return any(marker in window for marker in ("பசு", "பாச", "இறை", "அருள்", "சிவ", "நாத", "அடி"))
    if term.term == "பசு":
        return any(marker in window for marker in ("பதி", "பாச", "மலம்", "ஆன்ம", "சைவ"))
    if term.term == "மலம்":
        return any(marker in window for marker in ("ஆணவ", "கன்ம", "மாயை", "பாச", "நீங்"))
    if term.review_decision == "CONTEXT_ONLY":
        return len(term.term) > 3
    return False


def apply_review_policy(candidate: dict[str, Any], text: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    term: SeedTerm = candidate.pop("_term")
    candidate["review_decision"] = term.review_decision
    candidate["v2_rule"] = term.v2_rule
    candidate["observed_mentions_v1"] = term.observed_mentions_v1
    candidate["context_window"] = context_window(
        text, int(candidate["start_char"]), int(candidate["end_char"])
    )

    if term.review_decision == "REJECT_OR_EXCLUDE":
        return None, {**candidate, "suppression_reason": "review_decision_exclude"}

    context_supported = context_supports_term(
        term, text, int(candidate["start_char"]), int(candidate["end_char"])
    )
    candidate["context_supported"] = context_supported

    if term.review_decision == "KEEP":
        candidate["review_status"] = "auto_accepted"
    elif term.review_decision == "CONTEXT_ONLY":
        if context_supported:
            candidate["review_status"] = "context_supported"
            candidate["confidence"] = round(max(float(candidate["confidence"]), 0.78), 2)
        else:
            candidate["review_status"] = "needs_context_review"
            candidate["confidence"] = round(min(float(candidate["confidence"]), 0.55), 2)
    elif term.review_decision == "AMBIGUOUS_REVIEW":
        candidate["review_status"] = "ambiguous_review"
        candidate["confidence"] = round(min(float(candidate["confidence"]), 0.45), 2)
    else:
        candidate["review_status"] = "unreviewed_seed"
    candidate["method"] = "seed_lexicon_with_manual_review_decisions_v2"
    candidate["mention_id"] = mention_id(candidate)
    return candidate, None


def overlaps(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return int(a["start_char"]) < int(b["end_char"]) and int(b["start_char"]) < int(a["end_char"])


def select_mentions(candidates: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []
    ordered = sorted(
        candidates,
        key=lambda item: (
            item["target_table"],
            item["target_id"],
            item["field_name"],
            item["start_char"],
            -(item["end_char"] - item["start_char"]),
            item["entity_type"],
            item["canonical_id"],
        ),
    )
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in ordered:
        grouped[
            (
                str(item["target_table"]),
                str(item["target_id"]),
                str(item["field_name"]),
                str(item["entity_type"]),
            )
        ].append(item)

    for group_items in grouped.values():
        kept: list[dict[str, Any]] = []
        for candidate in sorted(
            group_items,
            key=lambda item: (
                item["start_char"],
                -(item["end_char"] - item["start_char"]),
                -float(item["confidence"]),
                item["canonical_id"],
            ),
        ):
            contained_by_existing = any(
                overlaps(candidate, existing)
                and candidate["start_char"] >= existing["start_char"]
                and candidate["end_char"] <= existing["end_char"]
                for existing in kept
            )
            if contained_by_existing:
                suppressed.append({**candidate, "suppression_reason": "same_type_overlap"})
            else:
                kept.append(candidate)
        selected.extend(kept)
    return (
        sorted(
            selected,
            key=lambda item: (
                item["target_table"],
                item["target_id"],
                item["field_name"],
                item["start_char"],
                item["entity_type"],
            ),
        ),
        suppressed,
    )


def mention_id(item: dict[str, Any]) -> str:
    return "ment_" + stable_hash(
        item["target_table"],
        item["target_id"],
        item["field_name"],
        item["start_char"],
        item["end_char"],
        item["entity_type"],
        item["canonical_id"],
        item["mention_text"],
    )


def build_mentions(
    table_root: Path,
    terms: list[SeedTerm],
    *,
    schema_version: str = SCHEMA_VERSION,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    suppressed_by_review: list[dict[str, Any]] = []
    paadal_rows = read_jsonl(table_root / "paadalgal.jsonl")
    thirumurai_by_paadal_id = {
        str(row.get("paadal_id", "")): row.get("thirumurai_no", "")
        for row in paadal_rows
    }
    for table, fields in TEXT_FIELDS.items():
        rows = paadal_rows if table == "paadalgal" else read_jsonl(table_root / f"{table}.jsonl")
        id_field = "paadal_id" if table == "paadalgal" else "commentary_id"
        for row in rows:
            target_id = str(row.get(id_field, ""))
            paadal_id = str(row.get("paadal_id", target_id))
            thirumurai_no = row.get("thirumurai_no", thirumurai_by_paadal_id.get(paadal_id, ""))
            for field in fields:
                text = str(row.get(field, ""))
                for term in terms:
                    for match in find_term_matches(text, term):
                        candidate = {
                            "schema_version": schema_version,
                            "mention_id": "",
                            "annotation_type": "entity_mention",
                            "target_table": table,
                            "target_id": target_id,
                            "paadal_id": paadal_id,
                            "thirumurai_no": thirumurai_no,
                            "field_name": field,
                            "start_char": match["start_char"],
                            "end_char": match["end_char"],
                            "mention_text": match["mention_text"],
                            "entity_type": term.entity_type,
                            "entity_subtype": term.entity_subtype,
                            "canonical_id": term.canonical_id,
                            "canonical_name": term.canonical_name,
                            "matched_term": term.term,
                            "term_id": term.term_id,
                            "confidence": term.confidence,
                            "method": "seed_lexicon_exact_or_whitespace_flexible",
                            "review_status": "pending",
                            "source_seed_id": term.source_seed_id,
                            "source_file": term.source_file,
                            "ontology_source": term.ontology_source,
                            "_term": term,
                        }
                        accepted, suppressed = apply_review_policy(candidate, text)
                        if accepted:
                            candidates.append(accepted)
                        if suppressed:
                            suppressed_by_review.append(suppressed)
    selected, suppressed_by_overlap = select_mentions(candidates)
    return selected, suppressed_by_review + suppressed_by_overlap


def registry_rows(
    terms: list[SeedTerm],
    *,
    schema_version: str = SCHEMA_VERSION,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    registry: dict[str, dict[str, Any]] = {}
    aliases: dict[tuple[str, str, str], dict[str, Any]] = {}
    for term in terms:
        registry.setdefault(
            term.canonical_id,
            {
                "schema_version": schema_version,
                "entity_id": term.canonical_id,
                "entity_type": term.entity_type,
                "entity_subtype": term.entity_subtype,
                "canonical_name": term.canonical_name,
                "seed_status": term.ontology_source,
            },
        )
        aliases[(term.term, term.entity_type, term.canonical_id)] = {
            "schema_version": schema_version,
            "alias_id": term.term_id,
            "entity_id": term.canonical_id,
            "entity_type": term.entity_type,
            "entity_subtype": term.entity_subtype,
            "alias": term.term,
            "gloss": term.gloss,
            "source_seed_id": term.source_seed_id,
            "source_file": term.source_file,
            "confidence": term.confidence,
            "review_decision": term.review_decision,
            "v2_rule": term.v2_rule,
            "observed_mentions_v1": term.observed_mentions_v1,
            "ontology_source": term.ontology_source,
        }
    return (
        sorted(registry.values(), key=lambda row: (row["entity_type"], row["entity_id"])),
        sorted(aliases.values(), key=lambda row: (row["entity_type"], row["alias"], row["entity_id"])),
    )


def validate_mentions(table_root: Path, mentions: list[dict[str, Any]]) -> dict[str, Any]:
    text_by_key: dict[tuple[str, str, str], str] = {}
    for table, fields in TEXT_FIELDS.items():
        id_field = "paadal_id" if table == "paadalgal" else "commentary_id"
        for row in read_jsonl(table_root / f"{table}.jsonl"):
            for field in fields:
                text_by_key[(table, str(row.get(id_field, "")), field)] = str(row.get(field, ""))

    mismatch_count = 0
    invalid_bounds = 0
    mention_ids: Counter[str] = Counter()
    cross_type_overlaps = 0
    by_parent_field: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for mention in mentions:
        mention_ids[str(mention["mention_id"])] += 1
        key = (
            str(mention["target_table"]),
            str(mention["target_id"]),
            str(mention["field_name"]),
        )
        text = text_by_key.get(key, "")
        start = int(mention["start_char"])
        end = int(mention["end_char"])
        if start < 0 or end < start or end > len(text):
            invalid_bounds += 1
            continue
        if text[start:end] != mention["mention_text"]:
            mismatch_count += 1
        by_parent_field[key].append(mention)

    for group in by_parent_field.values():
        sorted_group = sorted(group, key=lambda row: (row["start_char"], row["end_char"]))
        for index, current in enumerate(sorted_group):
            for other in sorted_group[index + 1 :]:
                if int(other["start_char"]) >= int(current["end_char"]):
                    break
                if current["entity_type"] != other["entity_type"] and overlaps(current, other):
                    cross_type_overlaps += 1

    duplicate_ids = sorted(item for item, count in mention_ids.items() if count > 1)
    return {
        "mention_count": len(mentions),
        "invalid_bounds": invalid_bounds,
        "span_text_mismatches": mismatch_count,
        "duplicate_mention_ids": duplicate_ids,
        "cross_type_overlap_pairs": cross_type_overlaps,
        "status": "VALID" if not invalid_bounds and not mismatch_count and not duplicate_ids else "INVALID",
    }


def render_report(
    *,
    terms: list[SeedTerm],
    registry: list[dict[str, Any]],
    aliases: list[dict[str, Any]],
    mentions: list[dict[str, Any]],
    suppressed: list[dict[str, Any]],
    validation: dict[str, Any],
    output_root: Path,
    schema_version: str = SCHEMA_VERSION,
    title: str = "Thevaram Entity Annotation Report",
) -> str:
    type_counts = Counter(row["entity_type"] for row in mentions)
    field_counts = Counter(f"{row['target_table']}.{row['field_name']}" for row in mentions)
    seed_counts = Counter(term.entity_type for term in terms)
    decision_counts = Counter(row.get("review_decision", "UNREVIEWED") for row in mentions)
    review_status_counts = Counter(row.get("review_status", "unknown") for row in mentions)
    suppressed_counts = Counter(row.get("suppression_reason", "unknown") for row in suppressed)
    subtype_counts = Counter(
        f"{row['entity_type']}:{row.get('entity_subtype') or 'unspecified'}" for row in mentions
    )
    type_rows = "\n".join(
        f"| `{key}` | {type_counts[key]} | {seed_counts[key]} |" for key in sorted(seed_counts)
    )
    subtype_rows = "\n".join(
        f"| `{key}` | {subtype_counts[key]} |" for key in sorted(subtype_counts)
    )
    field_rows = "\n".join(f"| `{key}` | {field_counts[key]} |" for key in sorted(field_counts))
    decision_rows = "\n".join(f"| `{key}` | {decision_counts[key]} |" for key in sorted(decision_counts))
    status_rows = "\n".join(f"| `{key}` | {review_status_counts[key]} |" for key in sorted(review_status_counts))
    suppressed_rows = "\n".join(f"| `{key}` | {suppressed_counts[key]} |" for key in sorted(suppressed_counts))
    examples = "\n".join(
        f"- `{row['entity_type']}` `{row['mention_text']}` -> `{row['canonical_name']}` "
        f"in `{row['target_id']}` `{row['field_name']}` `{row['start_char']}:{row['end_char']}` "
        f"status=`{row.get('review_status', '')}` decision=`{row.get('review_decision', '')}`"
        for row in mentions[:20]
    )
    return f"""# {title}

## Summary

- Schema version: `{schema_version}`
- Output root: `{output_root}`
- Entity registry rows: `{len(registry)}`
- Entity aliases: `{len(aliases)}`
- Seed terms loaded: `{len(terms)}`
- Entity mentions: `{len(mentions)}`
- Suppressed same-type overlapping candidates: `{len(suppressed)}`
- Validation status: `{validation['status']}`
- Invalid bounds: `{validation['invalid_bounds']}`
- Span text mismatches: `{validation['span_text_mismatches']}`
- Duplicate mention IDs: `{len(validation['duplicate_mention_ids'])}`
- Cross-type overlap pairs: `{validation['cross_type_overlap_pairs']}`

Cross-type overlaps are allowed for v2 when a poetic span is legitimately both, for example, `NATURE` and `SACRED_OBJECT`.

## Entity Type Coverage

| Entity type | Mentions | Seed terms |
| --- | ---: | ---: |
{type_rows}

## Entity Subtype Coverage

| Entity subtype | Mentions |
| --- | ---: |
{subtype_rows}

## Field Coverage

| Field | Mentions |
| --- | ---: |
{field_rows}

## Manual Review Decisions Applied

| Decision | Mentions |
| --- | ---: |
{decision_rows}

## Review Status

| Status | Mentions |
| --- | ---: |
{status_rows}

## Suppressed Candidates

| Reason | Candidates |
| --- | ---: |
{suppressed_rows or "| None | 0 |"}

## Sample Mentions

{examples or "- None"}

## Review Notes

- This is a deterministic seed-lexicon annotation pass based on the six pilot TSV datasets and the manual QA decision CSVs.
- `review_status` records whether each mention is `auto_accepted`, `context_supported`, `needs_context_review`, `ambiguous_review`, or `unreviewed_seed`.
- Exact offsets are calculated against `data/processed/thevaram_normalized`.
- Same-type nested overlaps are suppressed by preferring the longer phrase.
- Cross-type overlaps are retained because the pilot data intentionally uses multi-category poetic imagery.
"""


def annotate(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    seed_dir: Path = DEFAULT_SEED_DIR,
    review_dir: Path = DEFAULT_REVIEW_DIR,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_path: Path = DEFAULT_REPORT,
    apply_review_decisions: bool = True,
    extra_terms: list[SeedTerm] | None = None,
    schema_version: str = SCHEMA_VERSION,
    report_title: str = "Thevaram Entity Annotation Report",
) -> dict[str, Any]:
    terms = load_seed_terms(seed_dir, review_dir, apply_review_decisions)
    if extra_terms:
        deduped = {(term.term, term.entity_type, term.canonical_id): term for term in terms}
        deduped.update({(term.term, term.entity_type, term.canonical_id): term for term in extra_terms})
        terms = sorted(
            deduped.values(),
            key=lambda item: (-len(item.term), item.entity_type, item.term, item.canonical_id),
        )
    registry, aliases = registry_rows(terms, schema_version=schema_version)
    mentions, suppressed = build_mentions(table_root, terms, schema_version=schema_version)
    validation = validate_mentions(table_root, mentions)

    output_root.mkdir(parents=True, exist_ok=True)
    counts = {
        "entity_registry": write_jsonl(output_root / "entity_registry.jsonl", registry),
        "entity_aliases": write_jsonl(output_root / "entity_aliases.jsonl", aliases),
        "entity_mentions": write_jsonl(output_root / "entity_mentions.jsonl", mentions),
        "suppressed_candidates": write_jsonl(output_root / "suppressed_candidates.jsonl", suppressed),
    }
    summary = {
        "schema_version": schema_version,
        "table_root": str(table_root),
        "seed_dir": str(seed_dir),
        "review_dir": str(review_dir),
        "output_root": str(output_root),
        "counts": counts,
        "mention_counts_by_type": dict(sorted(Counter(row["entity_type"] for row in mentions).items())),
        "mention_counts_by_field": dict(sorted(Counter(f"{row['target_table']}.{row['field_name']}" for row in mentions).items())),
        "mention_counts_by_review_decision": dict(sorted(Counter(row.get("review_decision", "UNREVIEWED") for row in mentions).items())),
        "mention_counts_by_review_status": dict(sorted(Counter(row.get("review_status", "unknown") for row in mentions).items())),
        "suppressed_counts_by_reason": dict(sorted(Counter(row.get("suppression_reason", "unknown") for row in suppressed).items())),
        "validation": validation,
    }
    (output_root / "annotation_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
	        render_report(
            terms=terms,
            registry=registry,
            aliases=aliases,
            mentions=mentions,
	            suppressed=suppressed,
	            validation=validation,
	            output_root=output_root,
	            schema_version=schema_version,
	            title=report_title,
	        ),
        encoding="utf-8",
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Annotate Thevaram 1-8 entity mentions from pilot TSV seeds and manual QA decisions.")
    parser.add_argument("--table-root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--seed-dir", type=Path, default=DEFAULT_SEED_DIR)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--ignore-review-decisions", action="store_true")
    args = parser.parse_args(argv)
    summary = annotate(
        table_root=args.table_root,
        seed_dir=args.seed_dir,
        review_dir=args.review_dir,
        output_root=args.output_root,
        report_path=args.report,
        apply_review_decisions=not args.ignore_review_decisions,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["validation"]["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
