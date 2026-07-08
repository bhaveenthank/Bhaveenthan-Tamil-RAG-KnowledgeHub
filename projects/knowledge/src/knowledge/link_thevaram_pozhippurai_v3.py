from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from knowledge.link_thevaram_pozhippurai import (
    DEFAULT_ENTITY_ROOT,
    DEFAULT_SEED_DIR,
    DEFAULT_TABLE_ROOT,
    RELATION_TYPES,
    build_link_id,
    build_links as build_v2_links,
    compact_text,
    is_standalone_numbering_line,
    normalize_text,
    read_jsonl,
    stable_hash,
    tokens,
)

SCHEMA_VERSION = "thevaram-pozhppurai-paadallink-v3"
DEFAULT_QA_BUNDLE = Path("/Users/bhaveenthankajanikanth/Downloads/paadal_pozhippurai_phase3_focused_manual_qa_outputs")
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_pozhippurai_links/v3")
DEFAULT_REPORT = Path("reports/thevaram-pozhppurai-paadallink-v3-report.md")

ALLOWED_RELATIONSHIPS = set(RELATION_TYPES)
CONFIDENCE_ORDER = {"no_link": 0, "low": 1, "medium": 2, "high": 3}
TOKEN_RE = re.compile(r"[\w\u0B80-\u0BFF]+|[^\s]", re.UNICODE)


@dataclass(frozen=True)
class LinkRule:
    rule_id: str
    source_text: str
    target_text: str
    relationship_type: str
    confidence: str
    source: str
    qa_id: str = ""
    parent_qa_id: str = ""
    paadal_id: str = ""
    commentary_id: str = ""
    reviewer_note: str = ""
    split_parent_id: str = ""


def should_anchor_rule(source_text: str) -> bool:
    source_tokens = tokens(source_text)
    compact = compact_text(source_text)
    if compact.isdigit():
        return True
    if len(source_tokens) <= 1:
        return True
    if len(compact) <= 5:
        return True
    return False


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def clean_phrase(value: str) -> str:
    return normalize_text(value).strip(" \t\r\n,.;:!?-–—'\"“”‘’")


def confidence_value(value: str) -> str:
    lowered = normalize_text(value).lower()
    if lowered in {"high", "medium", "low", "no_link"}:
        return lowered
    if lowered == "none":
        return "no_link"
    return "medium"


def first_value(row: dict[str, str], *names: str) -> str:
    for name in names:
        value = row.get(name, "")
        if value and value.strip():
            return value
    return ""


def find_exact_span(text: str, phrase: str) -> tuple[int, int] | None:
    phrase = clean_phrase(phrase)
    if not text or not phrase:
        return None
    direct = text.find(phrase)
    if direct >= 0:
        return direct, direct + len(phrase)
    for variant in {phrase + mark for mark in (",", ".", "!", ";", ":", "?", "।")}:
        direct = text.find(variant)
        if direct >= 0:
            return direct, direct + len(phrase)
    compact_phrase = compact_text(phrase)
    if not compact_phrase:
        return None
    compact_chars: list[str] = []
    compact_to_original: list[int] = []
    for index, char in enumerate(text):
        if not char.isspace() and char not in ",.;:!?-–—'\"“”‘’":
            compact_chars.append(char)
            compact_to_original.append(index)
    compact_text_value = "".join(compact_chars)
    compact_index = compact_text_value.find(compact_phrase)
    if compact_index < 0:
        return None
    start = compact_to_original[compact_index]
    end = compact_to_original[compact_index + len(compact_phrase) - 1] + 1
    return start, end


def load_rules(qa_bundle: Path = DEFAULT_QA_BUNDLE) -> tuple[list[LinkRule], dict[str, Any]]:
    usable_rows = read_csv(qa_bundle / "paadal_pozhippurai_links_v3_corrected_usable.csv")
    split_rows = read_csv(qa_bundle / "paadal_pozhippurai_links_v3_split_suggestions.csv")
    unresolved_rows = read_csv(qa_bundle / "paadal_pozhippurai_links_v3_unresolved_only.csv")
    decision_rows = read_csv(qa_bundle / "paadal_pozhippurai_phase3_clean_decision_table.csv")
    focused_rows = read_csv(qa_bundle / "paadal_pozhippurai_link_qa_samples_focused_reviewed.csv")

    rules: list[LinkRule] = []
    seen: set[tuple[str, str, str]] = set()
    for row in usable_rows:
        status = first_value(row, "clean_phase3_status")
        if status != "usable_corrected":
            continue
        source = clean_phrase(first_value(row, "final_source_text", "corrected_source_text", "source_text"))
        target = clean_phrase(first_value(row, "final_target_text", "corrected_target_text_clean", "correct_target_text_or_note", "target_text"))
        relationship = first_value(row, "final_relationship_type", "corrected_relationship_type_final", "correct_relationship_type")
        confidence = confidence_value(first_value(row, "updated_confidence"))
        if not source or not target or relationship not in ALLOWED_RELATIONSHIPS or confidence not in {"high", "medium"}:
            continue
        key = (compact_text(source), compact_text(target), relationship)
        if key in seen:
            continue
        seen.add(key)
        qa_id = first_value(row, "qa_id", "\ufeffqa_id", "split_link_id")
        rule_source = "focused_qa_corrected_usable"
        paadal_id = first_value(row, "paadal_id") if should_anchor_rule(source) else ""
        commentary_id = first_value(row, "commentary_id") if should_anchor_rule(source) else ""
        rules.append(
            LinkRule(
                rule_id="qa_" + stable_hash(qa_id, source, target, relationship, length=12),
                source_text=source,
                target_text=target,
                relationship_type=relationship,
                confidence=confidence,
                source=rule_source,
                qa_id=qa_id,
                parent_qa_id="",
                paadal_id=paadal_id,
                commentary_id=commentary_id,
                reviewer_note=first_value(row, "reviewer_notes"),
                split_parent_id="",
            )
        )

    parent_by_qa_id = {
        first_value(row, "qa_id", "\ufeffqa_id"): row
        for row in decision_rows
        if first_value(row, "qa_id", "\ufeffqa_id")
    }
    focused_parent_by_qa_id = {
        first_value(row, "qa_id", "\ufeffqa_id"): row
        for row in focused_rows
        if first_value(row, "qa_id", "\ufeffqa_id")
    }
    for row in split_rows:
        if first_value(row, "manual_decision") != "ACCEPT_SPLIT_LINK":
            continue
        source = clean_phrase(first_value(row, "source_text"))
        target = clean_phrase(first_value(row, "target_text"))
        relationship = first_value(row, "relationship_type")
        confidence = confidence_value(first_value(row, "updated_confidence"))
        if not source or not target or relationship not in ALLOWED_RELATIONSHIPS or confidence not in {"high", "medium"}:
            continue
        parent_qa_id = first_value(row, "parent_qa_id", "\ufeffparent_qa_id")
        split_link_id = first_value(row, "split_link_id")
        key = (compact_text(source), compact_text(target), relationship)
        if key in seen:
            continue
        seen.add(key)
        parent = parent_by_qa_id.get(parent_qa_id, {})
        focused_parent = focused_parent_by_qa_id.get(parent_qa_id, {})
        rules.append(
            LinkRule(
                rule_id="split_" + stable_hash(split_link_id, source, target, relationship, length=12),
                source_text=source,
                target_text=target,
                relationship_type=relationship,
                confidence=confidence,
                source="focused_qa_accepted_split",
                qa_id=split_link_id,
                parent_qa_id=parent_qa_id,
                paadal_id=first_value(focused_parent, "paadal_id"),
                commentary_id=first_value(focused_parent, "commentary_id"),
                split_parent_id=first_value(parent, "link_id") or parent_qa_id,
                reviewer_note=first_value(row, "reviewer_notes"),
            )
        )

    metadata = {
        "decision_table_rows": len(decision_rows),
        "corrected_usable_rows": len(usable_rows),
        "accepted_split_rows": len(split_rows),
        "unresolved_rows": len(unresolved_rows),
        "rules_loaded": len(rules),
        "rules_by_source": dict(sorted(Counter(rule.source for rule in rules).items())),
        "rules_by_relationship": dict(sorted(Counter(rule.relationship_type for rule in rules).items())),
    }
    return rules, metadata


def make_v3_link(
    *,
    paadal: dict[str, Any],
    commentary: dict[str, Any],
    source_start: int,
    source_end: int,
    target_start: int | None,
    target_end: int | None,
    source_text: str,
    target_text: str,
    relationship_type: str,
    confidence: str,
    score: float,
    rule_ids: list[str],
    method: str,
    manual_review_required: bool,
    diagnostic_note: str,
    split_parent_id: str = "",
) -> dict[str, Any]:
    paadal_id = str(paadal.get("paadal_id", ""))
    commentary_id = str(commentary.get("commentary_id") or f"{paadal_id}_commentary")
    if confidence == "no_link":
        link_id = build_link_id(paadal_id, source_start, -1, "no_link")
    else:
        link_id = "ppl_v3_" + stable_hash(
            paadal_id,
            source_start,
            source_end,
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
        "target_field": "pozhppurai",
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
        "reviewer_note": "",
        "diagnostic_note": diagnostic_note,
        "method": method,
    }


def rule_score(rule: LinkRule) -> float:
    return 0.92 if rule.confidence == "high" else 0.78


def build_rule_links(
    paadal_rows: list[dict[str, Any]],
    commentary_by_paadal_id: dict[str, dict[str, Any]],
    rules: list[LinkRule],
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    links: list[dict[str, Any]] = []
    rule_counts: Counter[str] = Counter()
    for paadal in paadal_rows:
        paadal_text = str(paadal.get("paadal_text", ""))
        commentary = commentary_by_paadal_id.get(str(paadal.get("paadal_id", "")), {})
        pozhppurai = str(commentary.get("pozhppurai", ""))
        if not pozhppurai.strip():
            continue
        for rule in rules:
            if rule.paadal_id and str(paadal.get("paadal_id", "")) != rule.paadal_id:
                continue
            if rule.commentary_id and str(commentary.get("commentary_id", "")) != rule.commentary_id:
                continue
            source_span = find_exact_span(paadal_text, rule.source_text)
            if source_span is None:
                continue
            target_span = find_exact_span(pozhppurai, rule.target_text)
            if target_span is None:
                continue
            source_start, source_end = source_span
            target_start, target_end = target_span
            link = make_v3_link(
                paadal=paadal,
                commentary=commentary,
                source_start=source_start,
                source_end=source_end,
                target_start=target_start,
                target_end=target_end,
                source_text=paadal_text[source_start:source_end],
                target_text=pozhppurai[target_start:target_end],
                relationship_type=rule.relationship_type,
                confidence=rule.confidence,
                score=rule_score(rule),
                rule_ids=[rule.rule_id],
                method="focused_qa_rule_exact_span_v3",
                manual_review_required=False,
                diagnostic_note=f"Focused QA rule matched: {rule.source}.",
                split_parent_id=rule.split_parent_id,
            )
            link["reviewer_note"] = rule.reviewer_note
            link["qa_rule_source"] = rule.source
            link["qa_id"] = rule.qa_id
            link["parent_qa_id"] = rule.parent_qa_id
            links.append(link)
            rule_counts[rule.rule_id] += 1
    return links, dict(rule_counts)


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


def convert_v2_link(
    row: dict[str, Any],
    *,
    paadal_by_id: dict[str, dict[str, Any]],
    commentary_by_id: dict[str, dict[str, Any]],
    split_parent: bool,
) -> dict[str, Any]:
    paadal = paadal_by_id.get(str(row.get("paadal_id", "")), {"paadal_id": row.get("paadal_id", "")})
    commentary = commentary_by_id.get(
        str(row.get("commentary_id", "")),
        {"commentary_id": row.get("commentary_id", "")},
    )
    confidence = str(row.get("confidence", "low"))
    if confidence == "none":
        confidence = "no_link"
    relationship = str(row.get("relationship_type", "unlinked"))
    if relationship not in ALLOWED_RELATIONSHIPS:
        relationship = "unlinked"
    manual_review = confidence in {"low", "no_link"} or split_parent
    diagnostic_note = str(row.get("problem_reason") or row.get("diagnostic_category") or "")
    if split_parent:
        diagnostic_note = "Broad v2 parent overlaps a focused QA split/phrase rule; keep for diagnostics, not positive training."
    return {
        "schema_version": SCHEMA_VERSION,
        "link_id": "ppl_v3_base_" + stable_hash(row.get("link_id", ""), row.get("paadal_id", ""), row.get("source_start_char", "")),
        "thirumurai_no": row.get("thirumurai_no", ""),
        "pathigam_id": paadal.get("thogupu_id", ""),
        "hymn_id": paadal.get("thogupu_id", ""),
        "paadal_id": row.get("paadal_id", ""),
        "commentary_id": row.get("commentary_id", ""),
        "source_field": row.get("source_field", "paadal_text"),
        "target_field": row.get("target_field", "pozhppurai"),
        "source_text": row.get("source_text", ""),
        "source_text_normalized": normalize_text(str(row.get("source_text", ""))),
        "target_text": row.get("target_text", ""),
        "relationship_type": relationship,
        "confidence": confidence,
        "score": row.get("score", 0.0),
        "features": row.get("features", {}),
        "source_start_char": row.get("source_start_char"),
        "source_end_char": row.get("source_end_char"),
        "target_start_char": row.get("target_start_char"),
        "target_end_char": row.get("target_end_char"),
        "rule_ids_applied": ["v2_window_similarity_baseline"],
        "split_parent_id": row.get("link_id", "") if split_parent else "",
        "manual_review_required": manual_review,
        "reviewer_note": "",
        "diagnostic_note": diagnostic_note,
        "method": "v2_baseline_carried_forward_v3",
    }


def should_carry_forward_v2_link(row: dict[str, Any]) -> bool:
    return not is_standalone_numbering_line(str(row.get("source_text", "")))


def dedupe_links(links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    for link in links:
        key = (
            link.get("paadal_id"),
            link.get("source_start_char"),
            link.get("source_end_char"),
            link.get("target_start_char"),
            link.get("target_end_char"),
            link.get("relationship_type"),
        )
        current = best_by_key.get(key)
        if current is None:
            best_by_key[key] = link
            continue
        current_rank = CONFIDENCE_ORDER.get(str(current.get("confidence")), 0), float(current.get("score") or 0)
        next_rank = CONFIDENCE_ORDER.get(str(link.get("confidence")), 0), float(link.get("score") or 0)
        if next_rank > current_rank:
            best_by_key[key] = link
    return sorted(
        best_by_key.values(),
        key=lambda row: (
            int(float(row.get("thirumurai_no") or 0)),
            str(row.get("paadal_id", "")),
            int(row.get("source_start_char") or 0),
            int(row.get("target_start_char") or -1),
            str(row.get("link_id", "")),
        ),
    )


def build_v3_links(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    entity_root: Path = DEFAULT_ENTITY_ROOT,
    seed_dir: Path = DEFAULT_SEED_DIR,
    qa_bundle: Path = DEFAULT_QA_BUNDLE,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paadal_rows = read_jsonl(table_root / "paadalgal.jsonl")
    commentary_rows = read_jsonl(table_root / "commentaries.jsonl")
    paadal_by_id = {str(row.get("paadal_id", "")): row for row in paadal_rows}
    commentary_by_paadal_id = {str(row.get("paadal_id", "")): row for row in commentary_rows}
    commentary_by_id = {str(row.get("commentary_id", "")): row for row in commentary_rows}
    rules, qa_metadata = load_rules(qa_bundle)
    rule_links, rule_counts = build_rule_links(paadal_rows, commentary_by_paadal_id, rules)

    v2_links, v2_summary = build_v2_links(table_root=table_root, entity_root=entity_root, seed_dir=seed_dir)
    suppressed_numeric_baseline_rows = [
        row for row in v2_links if not should_carry_forward_v2_link(row)
    ]
    converted_v2: list[dict[str, Any]] = []
    for row in v2_links:
        if not should_carry_forward_v2_link(row):
            continue
        converted_v2.append(
            convert_v2_link(
                row,
                paadal_by_id=paadal_by_id,
                commentary_by_id=commentary_by_id,
                split_parent=overlaps_any(row, rule_links),
            )
        )

    links = dedupe_links(rule_links + converted_v2)
    summary = summarize_v3(links, paadal_rows, commentary_rows, qa_metadata, rule_counts, v2_summary)
    summary["suppressed_numeric_baseline_rows"] = len(suppressed_numeric_baseline_rows)
    return links, summary


def is_positive_training_link(row: dict[str, Any]) -> bool:
    return (
        row.get("relationship_type") in ALLOWED_RELATIONSHIPS
        and row.get("confidence") in {"high", "medium"}
        and not row.get("manual_review_required")
        and row.get("target_text")
    )


def summarize_v3(
    links: list[dict[str, Any]],
    paadal_rows: list[dict[str, Any]],
    commentary_rows: list[dict[str, Any]],
    qa_metadata: dict[str, Any],
    rule_counts: dict[str, int],
    v2_summary: dict[str, Any],
) -> dict[str, Any]:
    top_sources = Counter(normalize_text(str(row.get("source_text", ""))) for row in links if row.get("source_text"))
    top_targets = Counter(normalize_text(str(row.get("target_text", ""))) for row in links if row.get("target_text"))
    diagnostics = Counter(str(row.get("diagnostic_note", ""))[:120] for row in links if row.get("diagnostic_note"))
    return {
        "schema_version": SCHEMA_VERSION,
        "paadal_count": len(paadal_rows),
        "commentary_count": len(commentary_rows),
        "total_links": len(links),
        "positive_training_links": sum(1 for row in links if is_positive_training_link(row)),
        "links_by_confidence": dict(sorted(Counter(str(row.get("confidence", "")) for row in links).items())),
        "links_by_relationship_type": dict(sorted(Counter(str(row.get("relationship_type", "")) for row in links).items())),
        "links_by_thirumurai": dict(sorted(Counter(str(row.get("thirumurai_no", "")) for row in links).items())),
        "split_links_count": sum(1 for row in links if row.get("split_parent_id")),
        "manual_review_required_count": sum(1 for row in links if row.get("manual_review_required")),
        "no_link_count": sum(1 for row in links if row.get("confidence") == "no_link"),
        "rules_applied_count": sum(1 for row in links if "focused_qa" in str(row.get("method", ""))),
        "rules_loaded_count": qa_metadata["rules_loaded"],
        "rules_matched_count": len(rule_counts),
        "rules_applied_frequency": dict(sorted(rule_counts.items())),
        "top_source_patterns": dict(top_sources.most_common(20)),
        "top_target_patterns": dict(top_targets.most_common(20)),
        "top_error_warning_patterns": dict(diagnostics.most_common(20)),
        "qa_metadata": qa_metadata,
        "v2_baseline": {
            "schema_version": v2_summary.get("schema_version"),
            "link_count": v2_summary.get("link_count"),
            "confidence": v2_summary.get("line_count_by_confidence", {}),
        },
    }


def validate_v3_links(table_root: Path, links: list[dict[str, Any]]) -> dict[str, Any]:
    paadal_text_by_id = {
        str(row.get("paadal_id", "")): str(row.get("paadal_text", ""))
        for row in read_jsonl(table_root / "paadalgal.jsonl")
    }
    pozh_by_commentary_id = {
        str(row.get("commentary_id", "")): str(row.get("pozhppurai", ""))
        for row in read_jsonl(table_root / "commentaries.jsonl")
    }
    invalid_relationships = sorted(
        {str(row.get("relationship_type", "")) for row in links}
        - ALLOWED_RELATIONSHIPS
        - {"unlinked"}
    )
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
            pozhppurai = pozh_by_commentary_id.get(str(link.get("commentary_id", "")), "")
            target_start = int(link.get("target_start_char") or 0)
            target_end = int(link.get("target_end_char") or 0)
            if target_start < 0 or target_end < target_start or target_end > len(pozhppurai):
                invalid_bounds += 1
            elif pozhppurai[target_start:target_end] != link.get("target_text"):
                span_mismatches += 1
    duplicate_link_ids = sorted(link_id for link_id, count in duplicate_ids.items() if count > 1)
    return {
        "invalid_relationships": invalid_relationships,
        "invalid_bounds": invalid_bounds,
        "span_mismatches": span_mismatches,
        "duplicate_link_ids": duplicate_link_ids,
        "status": "VALID" if not invalid_relationships and not invalid_bounds and not span_mismatches and not duplicate_link_ids else "INVALID",
    }


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "link_id",
        "thirumurai_no",
        "pathigam_id",
        "paadal_id",
        "commentary_id",
        "source_text",
        "target_text",
        "relationship_type",
        "confidence",
        "score",
        "manual_review_required",
        "diagnostic_note",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_csv_file(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def iob_tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def write_iob(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            if not is_positive_training_link(row):
                continue
            handle.write(f"# link_id = {row['link_id']}\n")
            handle.write(f"# relationship_type = {row['relationship_type']}\n")
            handle.write(f"# confidence = {row['confidence']}\n")
            for side, label_prefix, text in (
                ("paadal", "PAADAL_SPAN", str(row.get("source_text", ""))),
                ("pozhppurai", "POZHIP_SPAN", str(row.get("target_text", ""))),
            ):
                toks = iob_tokens(text)
                for index, token in enumerate(toks):
                    label = "B-" + label_prefix if index == 0 else "I-" + label_prefix
                    handle.write(
                        "\t".join(
                            [
                                token,
                                label,
                                str(row["link_id"]),
                                side,
                                str(row["relationship_type"]),
                                str(row["confidence"]),
                            ]
                        )
                        + "\n"
                    )
            handle.write("\n")


def build_manual_review_pack(links: list[dict[str, Any]], limit: int = 240) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}

    def add(reason: str, candidates: list[dict[str, Any]], count: int) -> None:
        for row in candidates[:count]:
            if row["link_id"] not in selected:
                item = dict(row)
                item["review_reason"] = reason
                selected[row["link_id"]] = item

    sorted_links = sorted(
        links,
        key=lambda row: (
            int(float(row.get("thirumurai_no") or 0)),
            str(row.get("paadal_id", "")),
            float(row.get("score") or 0),
        ),
    )
    add("low_confidence", [row for row in sorted_links if row.get("confidence") == "low"], 80)
    add("manual_review_required", [row for row in sorted_links if row.get("manual_review_required")], 80)
    add("split_candidate_or_parent", [row for row in sorted_links if row.get("split_parent_id")], 40)
    add("wrong_target_risk", [row for row in sorted_links if "order" in str(row.get("diagnostic_note", "")).lower()], 30)
    for relationship in sorted(ALLOWED_RELATIONSHIPS):
        add(f"relationship_{relationship}", [row for row in sorted_links if row.get("relationship_type") == relationship], 8)
    for thirumurai_no in sorted({str(row.get("thirumurai_no", "")) for row in sorted_links}):
        add(f"thirumurai_{thirumurai_no}", [row for row in sorted_links if str(row.get("thirumurai_no", "")) == thirumurai_no], 5)
    return list(selected.values())[:limit]


def render_report(summary: dict[str, Any], validation: dict[str, Any], output_root: Path) -> str:
    def table(mapping: dict[str, Any]) -> str:
        return "\n".join(f"| `{key}` | {value} |" for key, value in mapping.items()) or "| None | 0 |"

    return f"""# Thevaram Paadal-Pozhippurai Linker v3 Report

## What Changed From v2

v3 keeps the v2 full-corpus coverage layer, then adds focused QA-derived exact phrase
rules and accepted split links. Human-corrected rows are used only when they are marked
usable, accepted split links, and high/medium confidence. Unresolved/no-link rows remain
diagnostics and are not promoted to positive training data.

## Outputs

- Output root: `{output_root}`
- Schema version: `{summary['schema_version']}`
- Total links / coverage rows: `{summary['total_links']}`
- Positive training links: `{summary['positive_training_links']}`
- Manual review required: `{summary['manual_review_required_count']}`
- No-link rows: `{summary['no_link_count']}`
- Split/child or split-parent diagnostic rows: `{summary['split_links_count']}`
- Rules loaded: `{summary['rules_loaded_count']}`
- Rules matched in corpus: `{summary['rules_matched_count']}`
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

## How QA Decisions Were Used

- `usable_corrected` single rows became source-target phrase rules.
- `ACCEPT_SPLIT_LINK` rows became split-child rules.
- `NO_LINK_POSSIBLE`, unresolved wrong-target rows, and manual-review-only rows were excluded from positive training.
- v2 line links that overlap focused split/phrase rules are retained only as review diagnostics.

## Remaining Error Patterns

- Some human-corrected targets are not visible verbatim in the current normalized commentary, so they do not become exact-span rules.
- Low-confidence v2 baseline rows still require manual review before scholarly use.
- Broad theological explanations may still need trimming to the exact explanatory clause.
- Split coverage is rule-based and conservative; it does not infer every possible sub-phrase yet.

## Next Manual QA Recommendation

Review `paadal_pozhippurai_links_v3_manual_review_pack.csv`, prioritizing low-confidence,
split-parent, and wrong-target-risk rows. Treat v3 as a stronger training/evaluation
layer, not final scholarly gold.
"""


def write_outputs(
    *,
    links: list[dict[str, Any]],
    summary: dict[str, Any],
    validation: dict[str, Any],
    output_root: Path,
    report_path: Path,
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    full_jsonl = output_root / "paadal_pozhippurai_links_v3_full.jsonl"
    write_jsonl(full_jsonl, links)
    write_tsv(output_root / "paadal_pozhippurai_links_v3_full.tsv", links)
    high = [row for row in links if row.get("confidence") == "high" and not row.get("manual_review_required")]
    medium = [row for row in links if row.get("confidence") == "medium" and not row.get("manual_review_required")]
    low = [row for row in links if row.get("confidence") == "low" or row.get("manual_review_required")]
    no_link = [row for row in links if row.get("confidence") == "no_link" or row.get("relationship_type") == "unlinked"]
    write_jsonl(output_root / "paadal_pozhippurai_links_v3_high_confidence.jsonl", high)
    write_jsonl(output_root / "paadal_pozhippurai_links_v3_medium_confidence.jsonl", medium)
    write_csv_file(output_root / "paadal_pozhippurai_links_v3_low_confidence_review.csv", low)
    write_csv_file(output_root / "paadal_pozhippurai_links_v3_no_link_or_unresolved.csv", no_link)
    positive = [row for row in links if is_positive_training_link(row)]
    write_iob(output_root / "paadal_pozhippurai_links_v3_corrected_usable.iob.conll", positive)
    write_csv_file(output_root / "paadal_pozhippurai_links_v3_manual_review_pack.csv", build_manual_review_pack(links))
    payload = {**summary, "validation": validation}
    (output_root / "paadal_pozhippurai_links_v3_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary, validation, output_root), encoding="utf-8")


def run_linking_v3(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    entity_root: Path = DEFAULT_ENTITY_ROOT,
    seed_dir: Path = DEFAULT_SEED_DIR,
    qa_bundle: Path = DEFAULT_QA_BUNDLE,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    links, summary = build_v3_links(
        table_root=table_root,
        entity_root=entity_root,
        seed_dir=seed_dir,
        qa_bundle=qa_bundle,
    )
    validation = validate_v3_links(table_root, links)
    write_outputs(links=links, summary=summary, validation=validation, output_root=output_root, report_path=report_path)
    return {**summary, "validation": validation, "output_root": str(output_root), "report": str(report_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create Thevaram paadal-pozhppurai v3 links from focused QA rules.")
    parser.add_argument("--input-root", "--table-root", dest="table_root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--entity-root", type=Path, default=DEFAULT_ENTITY_ROOT)
    parser.add_argument("--seed-dir", type=Path, default=DEFAULT_SEED_DIR)
    parser.add_argument("--qa-bundle", type=Path, default=DEFAULT_QA_BUNDLE)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = run_linking_v3(
        table_root=args.table_root,
        entity_root=args.entity_root,
        seed_dir=args.seed_dir,
        qa_bundle=args.qa_bundle,
        output_root=args.output_root,
        report_path=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["validation"]["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
