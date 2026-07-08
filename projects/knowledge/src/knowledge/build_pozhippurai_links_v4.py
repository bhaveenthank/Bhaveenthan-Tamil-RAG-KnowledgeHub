from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from knowledge.link_thevaram_pozhippurai import (
    DEFAULT_ENTITY_ROOT,
    DEFAULT_SEED_DIR,
    DEFAULT_TABLE_ROOT,
    compact_text,
    is_standalone_numbering_line,
    normalize_text,
    read_jsonl,
    stable_hash,
    tokens,
)
from knowledge.link_thevaram_pozhippurai_v3 import (
    ALLOWED_RELATIONSHIPS,
    CONFIDENCE_ORDER,
    DEFAULT_QA_BUNDLE,
    TOKEN_RE,
    build_manual_review_pack,
    build_v3_links,
    clean_phrase,
    dedupe_links,
    find_exact_span,
    is_positive_training_link,
    write_csv_file,
    write_jsonl,
    write_tsv,
)

SCHEMA_VERSION = "thevaram-pozhppurai-paadallink-v4"
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4")
DEFAULT_GOLD_SEED = DEFAULT_OUTPUT_ROOT / "gold" / "paadal_pozhippurai_v4_gold_seed.csv"
DEFAULT_REPORT = DEFAULT_OUTPUT_ROOT / "paadal_pozhippurai_links_v4_report.md"

MANUAL_DECISIONS = {
    "ACCEPT",
    "PARTIAL_MATCH",
    "WRONG_TARGET",
    "WRONG_RELATION_TYPE",
    "NEEDS_SPLIT",
    "NO_LINK_POSSIBLE",
}
CONFIDENCES = {"high", "medium", "low", "no_link"}
TARGET_FIELDS = {"pozhppurai", "kurippurai"}

ENTITY_CUES = {
    "சிவபிரான்",
    "சிவபெருமான்",
    "இறைவ",
    "இறைவன்",
    "இறைவர்",
    "அண்ணல்",
    "தலைவன்",
    "பெருமான்",
    "எந்தை",
    "உமையம்மை",
    "ஞானசம்பந்தன்",
    "எழுந்தருளிய",
    "விளங்கும்",
    "கோயிலிலுள்ள",
    "பதியில் தோன்றிய",
}
IMAGE_CUES = {
    "சூடி",
    "அணிந்து",
    "ஏந்தி",
    "போர்த்த",
    "தோல்",
    "தலையோடு",
    "தலையோட்டை",
    "கபாலம்",
    "சடை",
    "கங்கை",
    "பிறை",
    "திங்கள்",
    "மழு",
    "மான்",
    "யானை",
    "பாம்பு",
    "அரவு",
    "புனல்",
    "அருவி",
    "முத்து",
    "மணி",
    "ஆலநீழல்",
}
THEOLOGY_CUES = {
    "அருள்",
    "அருளுவீராக",
    "வழிபட",
    "பணிந்து",
    "தொழுது",
    "துதித்து",
    "ஏத்தி",
    "போற்றி",
    "அருச்சித்து",
    "மலர் தூவி",
    "இன்பம்",
    "செல்வம்",
    "உயர்வு",
    "வாழ்வர்",
    "பாசவினை",
    "வினை",
    "நீங்கும்",
    "பிணி",
    "எமபயம்",
    "வீடு",
    "முத்தி",
    "நினைவார்",
    "மனம் உருகி",
    "பிரிந்து வாழ்தல் இயலாது",
}
PHRASE_CUES = {"என்பது", "என்னும்", "அல்லனோ", "அஞ்சுமாறு", "திரிந்து ஏற்கும்", "உடைய"}
TRIM_CHARS = " \t\r\n,.;:!?-–—'\"“”‘’"
CONTENT_RE = re.compile(r"[\u0B80-\u0BFFA-Za-z0-9]")


@dataclass(frozen=True)
class GoldRule:
    gold_id: str
    source_text: str
    target_text: str
    manual_decision: str
    relationship_type: str
    confidence: str
    target_field: str
    reviewer_note: str


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_int(value: Any) -> int | None:
    try:
        if value in {"", None, "None"}:
            return None
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def load_v4_gold_seed(path: Path = DEFAULT_GOLD_SEED) -> tuple[list[GoldRule], dict[str, Any]]:
    rows = read_csv(path)
    rules: list[GoldRule] = []
    invalid: list[str] = []
    for index, row in enumerate(rows, start=2):
        decision = row.get("manual_decision", "")
        relationship = row.get("primary_relationship_type", "")
        confidence = row.get("updated_confidence", "").lower()
        target_field = row.get("target_field_preference", "pozhppurai") or "pozhppurai"
        if decision not in MANUAL_DECISIONS:
            invalid.append(f"line {index}: invalid manual_decision {decision!r}")
        if relationship not in ALLOWED_RELATIONSHIPS:
            invalid.append(f"line {index}: invalid relationship {relationship!r}")
        if confidence not in CONFIDENCES:
            invalid.append(f"line {index}: invalid confidence {confidence!r}")
        if target_field not in TARGET_FIELDS:
            invalid.append(f"line {index}: invalid target_field_preference {target_field!r}")
        if decision != "NO_LINK_POSSIBLE":
            rules.append(
                GoldRule(
                    gold_id=row.get("gold_id", ""),
                    source_text=clean_phrase(row.get("paadal_phrase", "")),
                    target_text=clean_phrase(row.get("correct_pozhippurai_span", "")),
                    manual_decision=decision,
                    relationship_type=relationship,
                    confidence=confidence,
                    target_field=target_field,
                    reviewer_note=row.get("reviewer_note", ""),
                )
            )
    return rules, {
        "gold_seed_rows": len(rows),
        "gold_rules_loaded": len(rules),
        "invalid_rows": invalid,
        "manual_decisions": dict(sorted(Counter(row.get("manual_decision", "") for row in rows).items())),
        "relationships": dict(sorted(Counter(row.get("primary_relationship_type", "") for row in rows).items())),
        "target_fields": dict(sorted(Counter(row.get("target_field_preference", "pozhppurai") for row in rows).items())),
    }


def split_source_phrase_v4(text: str) -> list[str]:
    cleaned = normalize_text(text)
    if not cleaned:
        return []
    split_ready = re.sub(r"[!?;]+", "|", cleaned)
    pieces = split_ready.split("|")
    expanded: list[str] = []
    for piece in pieces:
        piece = clean_phrase(piece)
        if not piece:
            continue
        # Split comma-heavy deity/image lists, but avoid atomizing short ordinary phrases.
        comma_parts = [clean_phrase(part) for part in re.split(r",+", piece) if clean_phrase(part)]
        if len(comma_parts) >= 3:
            expanded.extend(comma_parts)
        else:
            expanded.append(piece)
    return expanded or [cleaned]


def classify_relationship_v4(source_text: str, target_text: str) -> str:
    joined = f"{normalize_text(source_text)} {normalize_text(target_text)}"
    source_token_count = len(tokens(source_text))
    if any(cue in joined for cue in THEOLOGY_CUES):
        return "theological_explanation"
    if any(cue in joined for cue in IMAGE_CUES):
        return "interprets_image"
    if any(cue in joined for cue in ENTITY_CUES):
        return "describes_entity"
    if source_token_count <= 1 and len(tokens(target_text)) <= 3:
        return "glosses_word"
    if any(cue in joined for cue in PHRASE_CUES):
        return "explains_phrase"
    if source_token_count >= 8:
        return "explains_line"
    return "explains_phrase"


def find_morphology_aware_span(text: str, phrase: str) -> tuple[int, int] | None:
    exact = find_exact_span(text, phrase)
    if exact is not None:
        return exact
    base = clean_phrase(phrase)
    endings = ["ஐ", "ை", "இன்", "உடைய", "து", "தை", "னை", "ரை", "னது", "னுடைய", "ரும்"]
    for ending in endings:
        span = find_exact_span(text, base + ending)
        if span is not None:
            return span
    compact_phrase = compact_text(base)
    for match in re.finditer(r"[\u0B80-\u0BFF]+", text):
        word = match.group(0)
        if compact_text(word).startswith(compact_phrase) and len(compact_text(word)) <= len(compact_phrase) + 8:
            return match.start(), match.end()
    return None


def make_v4_link(
    *,
    paadal: dict[str, Any],
    commentary: dict[str, Any],
    source_start: int,
    source_end: int,
    target_start: int | None,
    target_end: int | None,
    target_field: str,
    source_text: str,
    target_text: str,
    relationship_type: str,
    confidence: str,
    score: float,
    rule_ids: list[str],
    method: str,
    manual_review_required: bool,
    diagnostic_note: str,
    reviewer_note: str = "",
    split_parent_id: str = "",
) -> dict[str, Any]:
    paadal_id = str(paadal.get("paadal_id", ""))
    commentary_id = str(commentary.get("commentary_id") or f"{paadal_id}_commentary")
    link_id = "ppl_v4_" + stable_hash(
        paadal_id,
        source_start,
        source_end,
        target_field,
        target_start,
        target_end,
        relationship_type,
        ",".join(rule_ids),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "link_id": link_id,
        "thirumurai_no": paadal.get("thirumurai_no", ""),
        "pathigam_id": paadal.get("thogupu_id", ""),
        "hymn_id": paadal.get("thogupu_id", ""),
        "paadal_id": paadal_id,
        "commentary_id": commentary_id,
        "source_field": "paadal_text",
        "target_field": target_field,
        "source_text": source_text,
        "source_text_normalized": normalize_text(source_text),
        "target_text": target_text,
        "relationship_type": relationship_type,
        "confidence": confidence,
        "score": round(score, 4),
        "source_start_char": source_start,
        "source_end_char": source_end,
        "target_start_char": target_start,
        "target_end_char": target_end,
        "rule_ids_applied": rule_ids,
        "split_parent_id": split_parent_id,
        "manual_review_required": manual_review_required,
        "reviewer_note": reviewer_note,
        "diagnostic_note": diagnostic_note,
        "method": method,
    }


def build_gold_links(
    paadal_rows: list[dict[str, Any]],
    commentary_by_paadal_id: dict[str, dict[str, Any]],
    rules: list[GoldRule],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    links: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    for paadal in paadal_rows:
        paadal_text = str(paadal.get("paadal_text", ""))
        commentary = commentary_by_paadal_id.get(str(paadal.get("paadal_id", "")), {})
        for rule in rules:
            source_span = find_morphology_aware_span(paadal_text, rule.source_text)
            if source_span is None:
                continue
            target_text_full = str(commentary.get(rule.target_field, ""))
            target_span = find_morphology_aware_span(target_text_full, rule.target_text)
            if target_span is None:
                continue
            source_start, source_end = source_span
            target_start, target_end = target_span
            actual_source = paadal_text[source_start:source_end]
            actual_target = target_text_full[target_start:target_end]
            relation = rule.relationship_type or classify_relationship_v4(actual_source, actual_target)
            confidence = rule.confidence
            if rule.target_field == "kurippurai":
                confidence = "high" if confidence == "high" else "medium"
            link = make_v4_link(
                paadal=paadal,
                commentary=commentary,
                source_start=source_start,
                source_end=source_end,
                target_start=target_start,
                target_end=target_end,
                target_field=rule.target_field,
                source_text=actual_source,
                target_text=actual_target,
                relationship_type=relation,
                confidence=confidence,
                score=0.96 if confidence == "high" else 0.82,
                rule_ids=["v4_gold_" + rule.gold_id],
                method="v4_gold_seed_exact_or_morphology_match",
                manual_review_required=False,
                diagnostic_note=f"v4 gold seed matched using {rule.target_field}.",
                reviewer_note=rule.reviewer_note,
            )
            link["gold_id"] = rule.gold_id
            links.append(link)
            counts[rule.gold_id] += 1
    return links, dict(counts)


def convert_v3_to_v4(row: dict[str, Any], *, split_parent: bool) -> dict[str, Any]:
    item = dict(row)
    item["schema_version"] = SCHEMA_VERSION
    item["link_id"] = "ppl_v4_base_" + stable_hash(row.get("link_id", ""), row.get("paadal_id", ""), row.get("source_start_char", ""))
    item["method"] = "v3_baseline_carried_forward_v4"
    if split_parent:
        item["manual_review_required"] = True
        item["split_parent_id"] = row.get("link_id", "")
        item["diagnostic_note"] = "Broad v3 parent overlaps a v4 gold phrase; keep for diagnostics, not positive training."
    return item


def should_carry_forward_v3_link(row: dict[str, Any]) -> bool:
    return not is_standalone_numbering_line(str(row.get("source_text", "")))


def overlaps_any(link: dict[str, Any], positive_links: list[dict[str, Any]]) -> bool:
    paadal_id = str(link.get("paadal_id", ""))
    start = int(link.get("source_start_char") or 0)
    end = int(link.get("source_end_char") or 0)
    for other in positive_links:
        if str(other.get("paadal_id", "")) != paadal_id:
            continue
        other_start = int(other.get("source_start_char") or 0)
        other_end = int(other.get("source_end_char") or 0)
        if start < other_end and other_start < end:
            return True
    return False


def build_v4_links(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    entity_root: Path = DEFAULT_ENTITY_ROOT,
    seed_dir: Path = DEFAULT_SEED_DIR,
    qa_bundle: Path = DEFAULT_QA_BUNDLE,
    gold_seed: Path = DEFAULT_GOLD_SEED,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paadal_rows = read_jsonl(table_root / "paadalgal.jsonl")
    commentary_rows = read_jsonl(table_root / "commentaries.jsonl")
    commentary_by_paadal_id = {str(row.get("paadal_id", "")): row for row in commentary_rows}
    gold_rules, gold_metadata = load_v4_gold_seed(gold_seed)
    gold_links, gold_counts = build_gold_links(paadal_rows, commentary_by_paadal_id, gold_rules)
    v3_links, v3_summary = build_v3_links(
        table_root=table_root,
        entity_root=entity_root,
        seed_dir=seed_dir,
        qa_bundle=qa_bundle,
    )
    suppressed_numeric_baseline_rows = [
        row for row in v3_links if not should_carry_forward_v3_link(row)
    ]
    converted = [
        convert_v3_to_v4(row, split_parent=overlaps_any(row, gold_links))
        for row in v3_links
        if should_carry_forward_v3_link(row)
    ]
    links = dedupe_links(gold_links + converted)
    summary = summarize_v4(links, paadal_rows, commentary_rows, gold_metadata, gold_counts, v3_summary)
    summary["suppressed_numeric_baseline_rows"] = len(suppressed_numeric_baseline_rows)
    return links, summary


def is_positive_v4(row: dict[str, Any]) -> bool:
    return (
        row.get("relationship_type") in ALLOWED_RELATIONSHIPS
        and row.get("confidence") in {"high", "medium"}
        and not row.get("manual_review_required")
        and row.get("target_text")
    )


def has_content_text(text: str) -> bool:
    return bool(CONTENT_RE.search(text or ""))


def trim_span(full_text: str, start: Any, end: Any) -> tuple[int | None, int | None, str]:
    start_int = normalize_int(start)
    end_int = normalize_int(end)
    if start_int is None or end_int is None or start_int < 0 or end_int < start_int or end_int > len(full_text):
        return start_int, end_int, ""
    while start_int < end_int and full_text[start_int] in TRIM_CHARS:
        start_int += 1
    while end_int > start_int and full_text[end_int - 1] in TRIM_CHARS:
        end_int -= 1
    return start_int, end_int, full_text[start_int:end_int]


def confidence_rank(row: dict[str, Any]) -> tuple[int, float, int, int]:
    return (
        CONFIDENCE_ORDER.get(str(row.get("confidence", "")), 0),
        float(row.get("score") or 0.0),
        1 if not row.get("manual_review_required") else 0,
        1 if str(row.get("method", "")).startswith("v4_gold") else 0,
    )


def is_linked_row(row: dict[str, Any]) -> bool:
    return (
        row.get("relationship_type") != "unlinked"
        and row.get("confidence") != "no_link"
        and bool(row.get("target_text"))
        and bool(row.get("source_text"))
    )


def parent_overlap_keys(rows: list[dict[str, Any]]) -> set[str]:
    linked = [row for row in rows if is_linked_row(row)]
    suppress: set[str] = set()
    by_paadal: dict[str, list[dict[str, Any]]] = {}
    for row in linked:
        by_paadal.setdefault(str(row.get("paadal_id", "")), []).append(row)
    for group in by_paadal.values():
        for row in group:
            row_start = normalize_int(row.get("source_start_char"))
            row_end = normalize_int(row.get("source_end_char"))
            if row_start is None or row_end is None:
                continue
            contained = 0
            for other in group:
                if other is row:
                    continue
                other_start = normalize_int(other.get("source_start_char"))
                other_end = normalize_int(other.get("source_end_char"))
                if other_start is None or other_end is None:
                    continue
                strictly_smaller = (other_start, other_end) != (row_start, row_end)
                if row_start <= other_start and other_end <= row_end and strictly_smaller:
                    contained += 1
            if row.get("split_parent_id") or contained >= 2:
                suppress.add(str(row.get("link_id", "")))
    return suppress


def clean_primary_links(
    links: list[dict[str, Any]],
    *,
    paadal_rows: list[dict[str, Any]],
    commentary_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    paadal_by_id = {str(row.get("paadal_id", "")): row for row in paadal_rows}
    commentary_by_id = {str(row.get("commentary_id", "")): row for row in commentary_rows}
    suppress_parent_ids = parent_overlap_keys(links)
    cleaned: list[dict[str, Any]] = []
    for row in links:
        if not is_linked_row(row):
            continue
        if str(row.get("link_id", "")) in suppress_parent_ids:
            continue
        paadal = paadal_by_id.get(str(row.get("paadal_id", "")), {})
        commentary = commentary_by_id.get(str(row.get("commentary_id", "")), {})
        source_start, source_end, source_text = trim_span(
            str(paadal.get("paadal_text", "")),
            row.get("source_start_char"),
            row.get("source_end_char"),
        )
        target_field = str(row.get("target_field") or "pozhppurai")
        target_start, target_end, target_text = trim_span(
            str(commentary.get(target_field, "")),
            row.get("target_start_char"),
            row.get("target_end_char"),
        )
        if not has_content_text(source_text) or not has_content_text(target_text):
            continue
        item = dict(row)
        item.update(
            {
                "source_start_char": source_start,
                "source_end_char": source_end,
                "source_text": source_text,
                "source_text_normalized": normalize_text(source_text),
                "target_start_char": target_start,
                "target_end_char": target_end,
                "target_text": target_text,
                "cleaning_status": "primary_clean_link",
            }
        )
        cleaned.append(item)

    best_by_source: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in cleaned:
        key = (
            row.get("paadal_id"),
            row.get("source_start_char"),
            row.get("source_end_char"),
        )
        current = best_by_source.get(key)
        if current is None or confidence_rank(row) > confidence_rank(current):
            best_by_source[key] = row
    return sorted(
        best_by_source.values(),
        key=lambda row: (
            int(row.get("thirumurai_no") or 0),
            str(row.get("paadal_id", "")),
            int(row.get("source_start_char") or 0),
            int(row.get("target_start_char") or 0),
        ),
    )


def secondary_no_link_rows(links: list[dict[str, Any]], commentary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    commentary_by_id = {str(row.get("commentary_id", "")): row for row in commentary_rows}
    rows: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for row in links:
        if is_linked_row(row):
            continue
        key = (
            row.get("paadal_id"),
            row.get("source_start_char"),
            row.get("source_end_char"),
            row.get("commentary_id"),
        )
        if key in seen:
            continue
        seen.add(key)
        commentary = commentary_by_id.get(str(row.get("commentary_id", "")), {})
        pozhppurai = str(commentary.get("pozhppurai", ""))
        reason = "empty_pozhippurai" if not pozhppurai.strip() else "unresolved_link"
        item = dict(row)
        item["secondary_table_reason"] = reason
        rows.append(item)
    return rows


def summarize_v4(
    links: list[dict[str, Any]],
    paadal_rows: list[dict[str, Any]],
    commentary_rows: list[dict[str, Any]],
    gold_metadata: dict[str, Any],
    gold_counts: dict[str, int],
    v3_summary: dict[str, Any],
) -> dict[str, Any]:
    diagnostics = Counter(str(row.get("diagnostic_note", ""))[:120] for row in links if row.get("diagnostic_note"))
    primary_clean = clean_primary_links(links, paadal_rows=paadal_rows, commentary_rows=commentary_rows)
    secondary = secondary_no_link_rows(links, commentary_rows)
    alignment_methods = Counter(
        str((row.get("features") or {}).get("sequence_alignment_method", "rule_or_unavailable"))
        for row in links
    )
    synonym_supported = sum(
        1 for row in links if float((row.get("features") or {}).get("synonym_score", 0.0) or 0.0) > 0
    )
    temple_entity_supported = sum(
        1
        for row in links
        if "TEMPLE" in ((row.get("features") or {}).get("shared_entity_types") or [])
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "paadal_count": len(paadal_rows),
        "commentary_count": len(commentary_rows),
        "total_links": len(links),
        "primary_clean_links": len(primary_clean),
        "secondary_no_link_rows": len(secondary),
        "secondary_no_link_reasons": dict(sorted(Counter(str(row.get("secondary_table_reason", "")) for row in secondary).items())),
        "links_by_alignment_method": dict(sorted(alignment_methods.items())),
        "synonym_supported_rows": synonym_supported,
        "temple_entity_supported_rows": temple_entity_supported,
        "positive_training_links": sum(1 for row in links if is_positive_v4(row)),
        "links_by_confidence": dict(sorted(Counter(str(row.get("confidence", "")) for row in links).items())),
        "links_by_relationship_type": dict(sorted(Counter(str(row.get("relationship_type", "")) for row in links).items())),
        "links_by_thirumurai": dict(sorted(Counter(str(row.get("thirumurai_no", "")) for row in links).items())),
        "split_links_count": sum(1 for row in links if row.get("split_parent_id")),
        "kurippurai_fallback_count": sum(1 for row in links if row.get("target_field") == "kurippurai"),
        "manual_review_required_count": sum(1 for row in links if row.get("manual_review_required")),
        "no_link_count": sum(1 for row in links if row.get("confidence") == "no_link"),
        "rules_applied_count": sum(1 for row in links if str(row.get("method", "")).startswith("v4_gold")),
        "gold_seed": gold_metadata,
        "gold_rules_matched_count": len(gold_counts),
        "gold_rules_applied_frequency": dict(sorted(gold_counts.items())),
        "top_source_patterns": dict(Counter(normalize_text(str(row.get("source_text", ""))) for row in links if row.get("source_text")).most_common(20)),
        "top_target_patterns": dict(Counter(normalize_text(str(row.get("target_text", ""))) for row in links if row.get("target_text")).most_common(20)),
        "top_error_warning_patterns": dict(diagnostics.most_common(20)),
        "v3_baseline": {
            "schema_version": v3_summary.get("schema_version"),
            "total_links": v3_summary.get("total_links"),
            "confidence": v3_summary.get("links_by_confidence", {}),
        },
    }


def validate_v4_links(table_root: Path, links: list[dict[str, Any]]) -> dict[str, Any]:
    paadal_text_by_id = {str(row.get("paadal_id", "")): str(row.get("paadal_text", "")) for row in read_jsonl(table_root / "paadalgal.jsonl")}
    commentary_by_id = {str(row.get("commentary_id", "")): row for row in read_jsonl(table_root / "commentaries.jsonl")}
    invalid_relationships = sorted({str(row.get("relationship_type", "")) for row in links} - ALLOWED_RELATIONSHIPS - {"unlinked"})
    invalid_bounds = 0
    span_mismatches = 0
    duplicate_ids: Counter[str] = Counter()
    for link in links:
        duplicate_ids[str(link.get("link_id", ""))] += 1
        paadal_text = paadal_text_by_id.get(str(link.get("paadal_id", "")), "")
        source_start = int(link.get("source_start_char") or 0)
        source_end = int(link.get("source_end_char") or 0)
        if source_start < 0 or source_end < source_start or source_end > len(paadal_text):
            invalid_bounds += 1
        elif paadal_text[source_start:source_end] != link.get("source_text"):
            span_mismatches += 1
        if link.get("target_start_char") is not None:
            commentary = commentary_by_id.get(str(link.get("commentary_id", "")), {})
            target_field = str(link.get("target_field") or "pozhppurai")
            target_text_full = str(commentary.get(target_field, ""))
            target_start = int(link.get("target_start_char") or 0)
            target_end = int(link.get("target_end_char") or 0)
            if target_start < 0 or target_end < target_start or target_end > len(target_text_full):
                invalid_bounds += 1
            elif target_text_full[target_start:target_end] != link.get("target_text"):
                span_mismatches += 1
    duplicate_link_ids = sorted(link_id for link_id, count in duplicate_ids.items() if count > 1)
    return {
        "invalid_relationships": invalid_relationships,
        "invalid_bounds": invalid_bounds,
        "span_mismatches": span_mismatches,
        "duplicate_link_ids": duplicate_link_ids,
        "status": "VALID" if not invalid_relationships and not invalid_bounds and not span_mismatches and not duplicate_link_ids else "INVALID",
    }


def validate_clean_links(table_root: Path, links: list[dict[str, Any]]) -> dict[str, Any]:
    base = validate_v4_links(table_root, links)
    duplicate_source_spans = [
        key
        for key, count in Counter(
            (
                str(row.get("paadal_id", "")),
                str(row.get("source_start_char", "")),
                str(row.get("source_end_char", "")),
            )
            for row in links
        ).items()
        if count > 1
    ]
    unlinked_rows = sum(1 for row in links if not is_linked_row(row))
    punctuation_only_rows = sum(
        1
        for row in links
        if not has_content_text(str(row.get("source_text", "")))
        or not has_content_text(str(row.get("target_text", "")))
    )
    status = (
        "VALID"
        if base["status"] == "VALID"
        and not duplicate_source_spans
        and not unlinked_rows
        and not punctuation_only_rows
        else "INVALID"
    )
    return {
        **base,
        "duplicate_source_spans": len(duplicate_source_spans),
        "unlinked_rows": unlinked_rows,
        "punctuation_only_rows": punctuation_only_rows,
        "status": status,
    }


def iob_tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def write_iob_v4(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            if not is_positive_v4(row):
                continue
            handle.write(f"# link_id = {row['link_id']}\n")
            handle.write(f"# relationship_type = {row['relationship_type']}\n")
            handle.write(f"# confidence = {row['confidence']}\n")
            target_side = "kurippurai" if row.get("target_field") == "kurippurai" else "pozhppurai"
            for side, label_prefix, text in (
                ("paadal", "PAADAL_SPAN", str(row.get("source_text", ""))),
                (target_side, "POZHIP_SPAN", str(row.get("target_text", ""))),
            ):
                for index, token in enumerate(iob_tokens(text)):
                    label = "B-" + label_prefix if index == 0 else "I-" + label_prefix
                    handle.write("\t".join([token, label, str(row["link_id"]), side, str(row["relationship_type"]), str(row["confidence"])]) + "\n")
            handle.write("\n")


def render_report(summary: dict[str, Any], validation: dict[str, Any], output_root: Path) -> str:
    def table(mapping: dict[str, Any]) -> str:
        return "\n".join(f"| `{key}` | {value} |" for key, value in mapping.items()) or "| None | 0 |"

    return f"""# Thevaram Paadal-Pozhippurai Linker v4 Report

## What Changed From v3

v4 keeps the v3 full-corpus coverage layer and adds 60 manually corrected gold seed
examples. The new layer supports exact pozhppurai matching, morphology-aware case-ending
matches, punctuation-guided split seeds, deterministic relationship cues, and kurippurai
fallback when the meaning is absent from pozhppurai.

## Summary

- Output root: `{output_root}`
- Schema version: `{summary['schema_version']}`
- Total links / coverage rows: `{summary['total_links']}`
- Primary clean linked rows: `{summary['primary_clean_links']}`
- Secondary no-link rows: `{summary['secondary_no_link_rows']}`
- Synonym-supported rows: `{summary['synonym_supported_rows']}`
- Temple/thalam entity-supported rows: `{summary['temple_entity_supported_rows']}`
- Positive training links: `{summary['positive_training_links']}`
- Gold seed rows: `{summary['gold_seed']['gold_seed_rows']}`
- Gold rules loaded: `{summary['gold_seed']['gold_rules_loaded']}`
- Gold rules matched in corpus: `{summary['gold_rules_matched_count']}`
- v4 rule applications: `{summary['rules_applied_count']}`
- Kurippurai fallback links: `{summary['kurippurai_fallback_count']}`
- Manual review required: `{summary['manual_review_required_count']}`
- No-link rows: `{summary['no_link_count']}`
- Validation status: `{validation['status']}`
- Invalid bounds: `{validation['invalid_bounds']}`
- Span mismatches: `{validation['span_mismatches']}`
- Duplicate link IDs: `{len(validation['duplicate_link_ids'])}`

## Confidence Distribution

| Confidence | Rows |
| --- | ---: |
{table(summary['links_by_confidence'])}

## Relationship Distribution

| Relationship | Rows |
| --- | ---: |
{table(summary['links_by_relationship_type'])}

## Thirumurai Distribution

| Thirumurai | Rows |
| --- | ---: |
{table(summary['links_by_thirumurai'])}

## Secondary No-Link Reasons

| Reason | Rows |
| --- | ---: |
{table(summary['secondary_no_link_reasons'])}

## Alignment Methods

| Method | Rows |
| --- | ---: |
{table(summary['links_by_alignment_method'])}

## Remaining Limitations

- v4 still prefers exact corpus substrings; gold targets not visible in either pozhppurai
  or kurippurai cannot be promoted automatically.
- `paadal_pozhippurai_links_v4_full.*` remains a diagnostic coverage layer.
- `paadal_pozhippurai_links_v4_primary_clean_links.*` is the downstream linked corpus table.
- `paadal_pozhippurai_links_v4_secondary_no_link.*` separates empty or unresolved pozhippurai cases.
"""


def write_outputs(
    *,
    links: list[dict[str, Any]],
    primary_clean: list[dict[str, Any]],
    secondary_no_link: list[dict[str, Any]],
    summary: dict[str, Any],
    validation: dict[str, Any],
    output_root: Path,
    report_path: Path,
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_full.jsonl", links)
    write_tsv(output_root / "paadal_pozhippurai_links_v4_full.tsv", links)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_primary_clean_links.jsonl", primary_clean)
    write_tsv(output_root / "paadal_pozhippurai_links_v4_primary_clean_links.tsv", primary_clean)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_primary_clean_links.csv", primary_clean)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_secondary_no_link.jsonl", secondary_no_link)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_secondary_no_link.csv", secondary_no_link)
    high = [row for row in links if row.get("confidence") == "high" and not row.get("manual_review_required")]
    medium = [row for row in links if row.get("confidence") == "medium" and not row.get("manual_review_required")]
    low = [row for row in links if row.get("confidence") == "low" or row.get("manual_review_required")]
    no_link = [row for row in links if row.get("confidence") == "no_link" or row.get("relationship_type") == "unlinked"]
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_high_confidence.jsonl", high)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_medium_confidence.jsonl", medium)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_low_confidence_review.csv", low)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_no_link_or_unresolved.csv", no_link)
    write_iob_v4(output_root / "paadal_pozhippurai_links_v4_corrected_usable.iob.conll", [row for row in links if is_positive_v4(row)])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_manual_review_pack.csv", build_manual_review_pack(links))
    payload = {**summary, "validation": validation}
    (output_root / "paadal_pozhippurai_links_v4_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary, validation, output_root), encoding="utf-8")


def run_linking_v4(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    entity_root: Path = DEFAULT_ENTITY_ROOT,
    seed_dir: Path = DEFAULT_SEED_DIR,
    qa_bundle: Path = DEFAULT_QA_BUNDLE,
    gold_seed: Path = DEFAULT_GOLD_SEED,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    links, summary = build_v4_links(
        table_root=table_root,
        entity_root=entity_root,
        seed_dir=seed_dir,
        qa_bundle=qa_bundle,
        gold_seed=gold_seed,
    )
    validation = validate_v4_links(table_root, links)
    paadal_rows = read_jsonl(table_root / "paadalgal.jsonl")
    commentary_rows = read_jsonl(table_root / "commentaries.jsonl")
    primary_clean = clean_primary_links(links, paadal_rows=paadal_rows, commentary_rows=commentary_rows)
    secondary_no_link = secondary_no_link_rows(links, commentary_rows)
    primary_validation = validate_clean_links(table_root, primary_clean)
    summary = {
        **summary,
        "primary_clean_links": len(primary_clean),
        "secondary_no_link_rows": len(secondary_no_link),
        "secondary_no_link_reasons": dict(
            sorted(Counter(str(row.get("secondary_table_reason", "")) for row in secondary_no_link).items())
        ),
        "primary_validation": primary_validation,
    }
    write_outputs(
        links=links,
        primary_clean=primary_clean,
        secondary_no_link=secondary_no_link,
        summary=summary,
        validation=validation,
        output_root=output_root,
        report_path=report_path,
    )
    return {**summary, "validation": validation, "output_root": str(output_root), "report": str(report_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create Thevaram paadal-pozhppurai v4 links from v4 gold seeds.")
    parser.add_argument("--input-root", "--table-root", dest="table_root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--entity-root", type=Path, default=DEFAULT_ENTITY_ROOT)
    parser.add_argument("--seed-dir", type=Path, default=DEFAULT_SEED_DIR)
    parser.add_argument("--qa-bundle", type=Path, default=DEFAULT_QA_BUNDLE)
    parser.add_argument("--gold-seed", type=Path, default=DEFAULT_GOLD_SEED)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = run_linking_v4(
        table_root=args.table_root,
        entity_root=args.entity_root,
        seed_dir=args.seed_dir,
        qa_bundle=args.qa_bundle,
        gold_seed=args.gold_seed,
        output_root=args.output_root,
        report_path=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["validation"]["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
