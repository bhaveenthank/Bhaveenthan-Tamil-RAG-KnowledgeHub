from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from knowledge.build_pozhippurai_links_v4 import validate_clean_links, validate_v4_links, write_iob_v4
from knowledge.build_pozhippurai_links_v4_hardened import (
    DEFAULT_HARDENING_PACK,
    base_features,
    load_hardening_pack,
    target_granularity_score,
)
from knowledge.learn_pozhippurai_high_confidence_patterns import load_jsonl
from knowledge.link_thevaram_pozhippurai import DEFAULT_TABLE_ROOT, read_jsonl, stable_hash, tokens
from knowledge.link_thevaram_pozhippurai_v3 import build_manual_review_pack, clean_phrase, write_csv_file, write_jsonl, write_tsv

SCHEMA_VERSION = "thevaram-pozhppurai-paadallink-v4-broad-target-fixed"
DEFAULT_BASE_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_hardened_learned")
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_broad_target_fixed")
DEFAULT_REPORT = DEFAULT_OUTPUT_ROOT / "paadal_pozhippurai_links_v4_broad_target_fixed_report.md"
PUNCT_RE = re.compile(r"[,;.!?:\-—“”‘’\n]+")
UNSAFE_ENDINGS = (
    "்",
    "உம்",
    "வும்",
    "களும்",
    "னும்",
    "தும்",
    "ரும்",
    "என",
    "விளைந்த",
    "வாழ்த்தி",
    "வழிபட்டு",
    "செலுத்தி",
    "போற்றி",
    "ஏத்தி",
    "தொழுது",
    "பணிந்து",
)

IMAGE_CUES = {
    "சூடி",
    "சூடிப்",
    "சூடிய",
    "அணிந்து",
    "ஏந்தி",
    "பூசி",
    "சடை",
    "முடி",
    "சென்னி",
    "பிறை",
    "திங்கள்",
    "மதி",
    "கங்கை",
    "பாம்பு",
    "நாகம்",
    "அரவு",
    "மழு",
    "தோல்",
    "கபாலம்",
    "விடை",
    "எருது",
}
ENTITY_CUES = {
    "சிவபிரான்",
    "சிவபெருமான்",
    "இறைவன்",
    "இறைவர்",
    "பெருமான்",
    "அண்ணல்",
    "தலைவன்",
    "எந்தை",
    "உமையம்மை",
    "ஞானசம்பந்தன்",
    "திருவீழிமிழலை",
    "திருமுதுகுன்றம்",
    "ஆலவாய்",
    "அண்ணாமலை",
    "காழி",
}
WORSHIP_CUES = {
    "தொழுது",
    "தொழ",
    "கைதொழ",
    "பணிந்து",
    "ஏத்தி",
    "போற்றி",
    "வழிபட்டு",
    "அருச்சித்து",
    "மலர் தூவி",
    "மனங்கொள்",
    "நினை",
}
RESULT_CUES = {
    "இன்பம்",
    "செல்வம்",
    "உயர்வு",
    "வாழ்வர்",
    "நீங்கும்",
    "கெடும்",
    "பிணி",
    "வினை",
    "பாசம்",
    "எமபயம்",
    "முத்தி",
    "வீடு",
}
PHRASE_CUES = {
    "என்பது",
    "என்னும்",
    "அல்லனோ",
    "அஞ்சுமாறு",
    "உடைய",
    "பொருந்திய",
    "நிறைந்த",
    "விளங்கும்",
}
CUE_FAMILIES = {
    "image": IMAGE_CUES,
    "entity": ENTITY_CUES,
    "worship": WORSHIP_CUES,
    "result": RESULT_CUES,
    "phrase": PHRASE_CUES,
}
BOUNDARY_CUES = sorted(
    set().union(*CUE_FAMILIES.values())
    | {
        "ஆகிய",
        "ஆகியவர்",
        "உடையவர்",
        "தரித்து",
        "விளங்கும்",
        "உறையும்",
        "எழுந்தருளிய",
        "வரின்",
        "ஆயின்",
        "எனில்",
        "அதனால்",
        "ஆகும்",
        "பெறுவர்",
    },
    key=len,
    reverse=True,
)


def source_target_ratio(source_text: str, target_text: str) -> float:
    return len(tokens(target_text)) / max(1, len(tokens(source_text)))


def is_full_line_source(row: dict[str, Any], paadal_by_id: dict[str, str]) -> bool:
    source = str(row.get("source_text", ""))
    paadal = paadal_by_id.get(str(row.get("paadal_id", "")), "")
    if not source or not paadal:
        return False
    source_chars = len(source.replace(" ", ""))
    paadal_chars = len(paadal.replace(" ", ""))
    return paadal_chars > 0 and source_chars / paadal_chars >= 0.95


def cue_families(text: str) -> set[str]:
    families = set()
    for name, cues in CUE_FAMILIES.items():
        if any(cue in text for cue in cues):
            families.add(name)
    return families


def cue_terms(text: str) -> set[str]:
    return {cue for cues in CUE_FAMILIES.values() for cue in cues if cue in text}


def is_broad_target(row: dict[str, Any], paadal_by_id: dict[str, str]) -> bool:
    if row.get("relationship_type") == "unlinked" or not row.get("target_text"):
        return False
    if is_full_line_source(row, paadal_by_id):
        return False
    source = str(row.get("source_text", ""))
    target = str(row.get("target_text", ""))
    if "target_too_broad_penalty" in set(map(str, row.get("penalties_applied") or [])):
        return True
    if source_target_ratio(source, target) > 3.0:
        return True
    if len(cue_families(target)) >= 3 and len(tokens(target)) >= max(8, len(tokens(source)) * 2):
        return True
    if len([part for part in PUNCT_RE.split(target) if clean_phrase(part)]) >= 2 and source_target_ratio(source, target) > 2.5:
        return True
    return False


def punct_spans(text: str) -> list[tuple[int, int, str]]:
    spans = []
    start = 0
    for match in PUNCT_RE.finditer(text):
        end = match.start()
        part = clean_phrase(text[start:end])
        if part:
            local_start = text.find(part, start, end)
            spans.append((local_start, local_start + len(part), part))
        start = match.end()
    part = clean_phrase(text[start:])
    if part:
        local_start = text.find(part, start)
        spans.append((local_start, local_start + len(part), part))
    return spans


def cue_phrase_spans(text: str) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    for cue in BOUNDARY_CUES:
        for match in re.finditer(re.escape(cue), text):
            start = match.start()
            end = match.end()
            left = max(text.rfind(",", 0, start), text.rfind(";", 0, start), text.rfind(".", 0, start), text.rfind(" ", 0, start - 18))
            right_candidates = [index for index in [text.find(",", end), text.find(";", end), text.find(".", end)] if index >= 0]
            if right_candidates:
                right = min(right_candidates)
            else:
                soft_right = min(len(text), end + 36)
                right = text.find(" ", soft_right)
                if right < 0:
                    right = len(text)
            phrase = clean_phrase(text[left + 1 : right])
            if phrase and len(tokens(phrase)) >= 2:
                local_start = text.find(phrase, max(0, left + 1))
                phrase, right = extend_to_safe_clause_end(text, local_start, right)
                spans.append((local_start, local_start + len(phrase), phrase))
    return spans


def unsafe_clause_ending(text: str) -> bool:
    toks = tokens(text)
    if not toks:
        return True
    last = toks[-1]
    return last.endswith(UNSAFE_ENDINGS)


def extend_to_safe_clause_end(text: str, start: int, right: int) -> tuple[str, int]:
    phrase = clean_phrase(text[start:right])
    if not phrase or not unsafe_clause_ending(phrase):
        return phrase, right
    current_right = right
    for _ in range(4):
        if current_right >= len(text):
            break
        next_space = text.find(" ", current_right + 1)
        next_puncts = [idx for idx in (text.find(",", current_right), text.find(";", current_right), text.find(".", current_right)) if idx >= 0]
        next_stop = min([idx for idx in [next_space, *next_puncts] if idx >= 0], default=len(text))
        if next_stop <= current_right:
            next_stop = len(text)
        phrase = clean_phrase(text[start:next_stop])
        current_right = next_stop
        if not unsafe_clause_ending(phrase):
            break
    return phrase, current_right


def candidate_subspans(target_text: str) -> list[tuple[int, int, str, str]]:
    raw: list[tuple[int, int, str, str]] = []
    clauses = punct_spans(target_text)
    for index, (start, end, text) in enumerate(clauses):
        raw.append((start, end, text, "single_clause"))
        if index + 1 < len(clauses):
            two_start = start
            two_end = clauses[index + 1][1]
            two_text = clean_phrase(target_text[two_start:two_end])
            if two_text:
                raw.append((two_start, two_end, two_text, "two_neighboring_clauses"))
    for start, end, text in cue_phrase_spans(target_text):
        raw.append((start, end, text, "cue_phrase"))
    raw.append((0, len(target_text), target_text, "full_target_fallback"))
    dedup: dict[str, tuple[int, int, str, str]] = {}
    for start, end, text, kind in raw:
        if start < 0 or end <= start:
            continue
        key = text
        current = dedup.get(key)
        if current is None or (end - start) < (current[1] - current[0]):
            dedup[key] = (start, end, text, kind)
    return sorted(dedup.values(), key=lambda item: (len(tokens(item[2])), item[0]))


def score_candidate(row: dict[str, Any], candidate_text: str, pack: Any) -> tuple[float, dict[str, float], set[str]]:
    features, _rules, anchors = base_features(row, str(row.get("source_text", "")), candidate_text, str(row.get("target_field") or "pozhppurai"), pack)
    original_features = row.get("feature_scores") if isinstance(row.get("feature_scores"), dict) else {}
    source_families = cue_families(str(row.get("source_text", "")))
    candidate_families = cue_families(candidate_text)
    family_overlap = len(source_families & candidate_families) / max(1, len(source_families)) if source_families else 0.0
    source_cues = cue_terms(str(row.get("source_text", "")))
    candidate_cues = cue_terms(candidate_text)
    direct_cue_overlap = len(source_cues & candidate_cues) / max(1, len(source_cues)) if source_cues else 0.0
    score = (
        0.20 * features.get("surface_token_overlap", 0.0)
        + 0.20 * features.get("semantic_lexicon_score", 0.0)
        + 0.20 * features.get("shared_entity_anchor_score", 0.0)
        + 0.15 * features.get("ontology_relation_score", 0.0)
        + 0.10 * features.get("relationship_cue_score", 0.0)
        + 0.10 * float(original_features.get("neighbor_anchor_score", features.get("neighbor_anchor_score", 0.0)) or 0.0)
        + 0.05 * target_granularity_score(str(row.get("source_text", "")), candidate_text, str(row.get("relationship_type", "")))
        + 0.10 * family_overlap
        + 0.15 * direct_cue_overlap
    )
    if not candidate_families and source_families:
        score -= 0.12
    if len(tokens(candidate_text)) < 2 and len(tokens(str(row.get("source_text", "")))) > 2:
        score -= 0.10
    return round(max(0.0, min(1.0, score)), 4), features, set(anchors)


def core_supported(row: dict[str, Any], candidate_text: str, features: dict[str, float]) -> bool:
    source_families = cue_families(str(row.get("source_text", "")))
    candidate_families = cue_families(candidate_text)
    if source_families and not (source_families & candidate_families):
        return False
    source_cues = cue_terms(str(row.get("source_text", "")))
    candidate_cues = cue_terms(candidate_text)
    if source_cues and not (source_cues & candidate_cues):
        return False
    evidence = (
        features.get("semantic_lexicon_score", 0.0)
        + features.get("shared_entity_anchor_score", 0.0)
        + features.get("ontology_relation_score", 0.0)
        + features.get("relationship_cue_score", 0.0)
    )
    return evidence >= 0.15 or bool(source_families & candidate_families)


def select_minimal_target(row: dict[str, Any], pack: Any) -> dict[str, Any]:
    original = str(row.get("target_text", ""))
    source = str(row.get("source_text", ""))
    original_score, original_features, _anchors = score_candidate(row, original, pack)
    comparison_original_score = original_score
    if "target_too_broad_penalty" in set(map(str, row.get("penalties_applied") or [])):
        comparison_original_score = max(0.0, original_score - 0.08)
    best: dict[str, Any] | None = None
    for start, end, candidate, kind in candidate_subspans(original):
        if candidate == original:
            continue
        if len(candidate) >= len(original) * 0.75:
            continue
        score, features, anchors = score_candidate(row, candidate, pack)
        if score + 0.03 < comparison_original_score:
            continue
        if not core_supported(row, candidate, features):
            continue
        ratio = len(candidate) / max(1, len(original))
        candidate_payload = {
            "local_start": start,
            "local_end": end,
            "text": candidate,
            "kind": kind,
            "score": score,
            "features": features,
            "anchors": sorted(anchors),
            "ratio": ratio,
        }
        if best is None or (score, -ratio) > (best["score"], -best["ratio"]):
            best = candidate_payload
    return {
        "selected": best,
        "original_score": original_score,
        "comparison_original_score": comparison_original_score,
        "original_features": original_features,
        "candidate_count": len(candidate_subspans(original)),
        "original_ratio": source_target_ratio(source, original),
    }


def add_default_broad_fields(row: dict[str, Any], broad_before: bool, original_score: float = 0.0, clause_count: int = 0) -> dict[str, Any]:
    item = dict(row)
    original = str(row.get("target_text", ""))
    item.update(
        {
            "schema_version": SCHEMA_VERSION,
            "base_schema_version": row.get("schema_version", ""),
            "broad_target_before": broad_before,
            "target_text_original": original,
            "target_text_minimal": original,
            "target_shrink_applied": False,
            "target_shrink_ratio": 1.0,
            "target_clause_index": "",
            "target_clause_count": clause_count,
            "minimal_target_score": original_score,
            "original_target_score": original_score,
            "target_granularity_score": target_granularity_score(str(row.get("source_text", "")), original, str(row.get("relationship_type", ""))),
            "target_shrink_reason": "not_broad_target" if not broad_before else "no_safe_smaller_span",
            "target_shrink_warning": "",
        }
    )
    return item


def fix_row(row: dict[str, Any], paadal_by_id: dict[str, str], pack: Any) -> dict[str, Any]:
    broad_before = is_broad_target(row, paadal_by_id)
    selection = select_minimal_target(row, pack) if broad_before else {"original_score": 0.0, "candidate_count": 0, "selected": None}
    item = add_default_broad_fields(row, broad_before, selection["original_score"], selection["candidate_count"])
    if not broad_before:
        return item
    selected = selection["selected"]
    if selected is None:
        return item
    original_target_start = int(row.get("target_start_char") or 0)
    old_penalties = list(row.get("penalties_applied") or [])
    new_penalties = [penalty for penalty in old_penalties if penalty != "target_too_broad_penalty"]
    local_start = int(selected["local_start"])
    local_end = int(selected["local_end"])
    minimal = str(selected["text"])
    item.update(
        {
            "link_id": "ppl_v4bt_" + stable_hash(row.get("link_id", ""), local_start, local_end, minimal),
            "target_text": minimal,
            "target_text_minimal": minimal,
            "target_start_char": original_target_start + local_start,
            "target_end_char": original_target_start + local_end,
            "target_shrink_applied": True,
            "target_shrink_ratio": round(len(minimal) / max(1, len(str(row.get("target_text", "")))), 4),
            "target_clause_index": local_start,
            "minimal_target_score": selected["score"],
            "target_granularity_score": target_granularity_score(str(row.get("source_text", "")), minimal, str(row.get("relationship_type", ""))),
            "target_shrink_reason": f"selected_{selected['kind']}_with_core_cue",
            "target_shrink_warning": "",
            "penalties_applied": new_penalties,
            "feature_scores": {**(row.get("feature_scores") if isinstance(row.get("feature_scores"), dict) else {}), "minimal_target_features": selected["features"]},
            "expanded_entity_anchors": sorted(set(map(str, row.get("expanded_entity_anchors") or [])) | set(selected["anchors"])),
            "diagnostic_note": f"{row.get('diagnostic_note', '')} Broad target fixed by minimal span selector.",
        }
    )
    return item


def fix_rows(rows: list[dict[str, Any]], paadal_by_id: dict[str, str], pack: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fixed = [fix_row(row, paadal_by_id, pack) for row in rows]
    changes = [
        {
            "link_id": row.get("link_id", ""),
            "base_link_id": row.get("base_link_id", ""),
            "confidence": row.get("confidence", ""),
            "relationship_type": row.get("relationship_type", ""),
            "source_text": row.get("source_text", ""),
            "target_text_original": row.get("target_text_original", ""),
            "target_text_minimal": row.get("target_text_minimal", ""),
            "target_shrink_ratio": row.get("target_shrink_ratio", ""),
            "minimal_target_score": row.get("minimal_target_score", ""),
            "original_target_score": row.get("original_target_score", ""),
            "target_shrink_reason": row.get("target_shrink_reason", ""),
        }
        for row in fixed
        if row.get("target_shrink_applied")
    ]
    return fixed, changes


def broad_count(rows: list[dict[str, Any]], paadal_by_id: dict[str, str]) -> int:
    return sum(is_broad_target(row, paadal_by_id) for row in rows)


def summarize(
    full_rows: list[dict[str, Any]],
    primary_rows: list[dict[str, Any]],
    changes: list[dict[str, Any]],
    baseline: dict[str, Any],
    paadal_by_id: dict[str, str],
    validation: dict[str, Any],
    primary_validation: dict[str, Any],
) -> dict[str, Any]:
    high_ids_before = int(baseline.get("primary_confidence", {}).get("high", 0))
    high_after = Counter(row.get("confidence", "") for row in primary_rows).get("high", 0)
    broad_after = broad_count(primary_rows, paadal_by_id)
    accepted = (
        broad_after < int(baseline.get("primary_broad_target_count", 0))
        and high_after >= high_ids_before
        and validation.get("status") == "VALID"
        and primary_validation.get("status") == "VALID"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "accepted": accepted,
        "rejection_reason": "" if accepted else "acceptance rule failed; inspect baseline/current counts",
        "baseline": baseline,
        "total_links": len(full_rows),
        "primary_clean_links": len(primary_rows),
        "full_confidence": dict(sorted(Counter(row.get("confidence", "") for row in full_rows).items())),
        "primary_confidence": dict(sorted(Counter(row.get("confidence", "") for row in primary_rows).items())),
        "full_broad_target_count": broad_count(full_rows, paadal_by_id),
        "primary_broad_target_count": broad_after,
        "broad_target_delta": int(baseline.get("primary_broad_target_count", 0)) - broad_after,
        "target_shrink_applied_count": len(changes),
        "manual_review_required_count": sum(bool(row.get("manual_review_required")) for row in full_rows),
        "relationship_type_counts": dict(sorted(Counter(row.get("relationship_type", "") for row in full_rows).items())),
        "validation": validation,
        "primary_validation": primary_validation,
    }


def render_report(summary: dict[str, Any], output_root: Path) -> str:
    def table(mapping: dict[str, Any]) -> str:
        return "\n".join(f"| `{key}` | {value} |" for key, value in mapping.items()) or "| None | 0 |"

    baseline = summary["baseline"]
    return f"""# Paadal-Pozhippurai v4 Broad Target Fix Report

## Acceptance

- Accepted: `{str(summary['accepted']).lower()}`
- Rejection reason: `{summary['rejection_reason']}`
- Output root: `{output_root}`
- Schema version: `{summary['schema_version']}`

## Baseline Versus Current

- Baseline primary broad target rows: `{baseline['primary_broad_target_count']}`
- Current primary broad target rows: `{summary['primary_broad_target_count']}`
- Broad target decrease: `{summary['broad_target_delta']}`
- Baseline primary high confidence: `{baseline['primary_confidence'].get('high', 0)}`
- Current primary high confidence: `{summary['primary_confidence'].get('high', 0)}`
- Target shrink applied rows: `{summary['target_shrink_applied_count']}`
- Validation status: `{summary['validation']['status']}`
- Primary validation status: `{summary['primary_validation']['status']}`

## Confidence Distribution

| Confidence | Rows |
| --- | ---: |
{table(summary['full_confidence'])}

## Relationship Distribution

| Relationship | Rows |
| --- | ---: |
{table(summary['relationship_type_counts'])}

## Notes

- This pass fixes only `broad_target`.
- Missing anchors, ambiguous spans, order-only rows, UI, scraper, and parser were not changed.
- Existing confidence labels are preserved; targets are shrunk only when a smaller span keeps core cue evidence.
"""


def write_outputs(
    output_root: Path,
    full_rows: list[dict[str, Any]],
    primary_rows: list[dict[str, Any]],
    secondary_rows: list[dict[str, Any]],
    changes: list[dict[str, Any]],
    summary: dict[str, Any],
    report_path: Path,
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_broad_target_fixed_full.jsonl", full_rows)
    write_tsv(output_root / "paadal_pozhippurai_links_v4_broad_target_fixed_full.tsv", full_rows)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_broad_target_fixed_primary_clean_links.csv", primary_rows)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_broad_target_fixed_primary_clean_links.jsonl", primary_rows)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_broad_target_fixed_high_confidence.jsonl", [row for row in full_rows if row.get("confidence") == "high" and not row.get("manual_review_required")])
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_broad_target_fixed_medium_confidence.jsonl", [row for row in full_rows if row.get("confidence") == "medium" and not row.get("manual_review_required")])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_broad_target_fixed_low_review.csv", [row for row in full_rows if row.get("confidence") == "low" or row.get("manual_review_required")])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_broad_target_fixed_no_link_or_unresolved.csv", [row for row in full_rows if row.get("confidence") == "no_link" or row.get("relationship_type") == "unlinked"])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_broad_target_fixed_broad_target_changes.csv", changes)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_broad_target_fixed_manual_review_pack.csv", build_manual_review_pack(full_rows))
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_broad_target_fixed_secondary_no_link.jsonl", secondary_rows)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_broad_target_fixed_secondary_no_link.csv", secondary_rows)
    write_iob_v4(output_root / "paadal_pozhippurai_links_v4_broad_target_fixed_corrected_usable.iob.conll", [row for row in full_rows if row.get("confidence") in {"high", "medium"} and row.get("target_text")])
    (output_root / "paadal_pozhippurai_links_v4_broad_target_fixed_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary, output_root), encoding="utf-8")


def baseline_counts(root: Path, paadal_by_id: dict[str, str]) -> dict[str, Any]:
    full_rows = load_jsonl(root / "paadal_pozhippurai_links_v4_hardened_learned_full.jsonl")
    primary_rows = load_jsonl(root / "paadal_pozhippurai_links_v4_hardened_learned_primary_clean_links.jsonl")
    return {
        "total_links": len(full_rows),
        "primary_links": len(primary_rows),
        "full_confidence": dict(sorted(Counter(row.get("confidence", "") for row in full_rows).items())),
        "primary_confidence": dict(sorted(Counter(row.get("confidence", "") for row in primary_rows).items())),
        "full_broad_target_count": broad_count(full_rows, paadal_by_id),
        "primary_broad_target_count": broad_count(primary_rows, paadal_by_id),
        "manual_review_required_count": sum(bool(row.get("manual_review_required")) for row in full_rows),
        "relationship_type_counts": dict(sorted(Counter(row.get("relationship_type", "") for row in full_rows).items())),
    }


def run_fix(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    base_root: Path = DEFAULT_BASE_ROOT,
    hardening_pack: Path = DEFAULT_HARDENING_PACK,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    pack = load_hardening_pack(hardening_pack)
    paadal_by_id = {str(row.get("paadal_id", "")): str(row.get("paadal_text", "")) for row in read_jsonl(table_root / "paadalgal.jsonl")}
    full_rows = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_full.jsonl")
    primary_rows = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_primary_clean_links.jsonl")
    secondary_rows = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_secondary_no_link.jsonl")
    baseline = baseline_counts(base_root, paadal_by_id)
    fixed_full, changes_full = fix_rows(full_rows, paadal_by_id, pack)
    fixed_primary, changes_primary = fix_rows(primary_rows, paadal_by_id, pack)
    validation = validate_v4_links(table_root, fixed_full)
    primary_validation = validate_clean_links(table_root, fixed_primary)
    summary = summarize(fixed_full, fixed_primary, changes_primary, baseline, paadal_by_id, validation, primary_validation)
    write_outputs(output_root, fixed_full, fixed_primary, secondary_rows, changes_primary, summary, report_path)
    return {**summary, "output_root": str(output_root), "report": str(report_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fix only broad target spans in v4 hardened learned paadal-pozhppurai links.")
    parser.add_argument("--table-root", "--input-root", dest="table_root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--base-root", type=Path, default=DEFAULT_BASE_ROOT)
    parser.add_argument("--hardening-pack", type=Path, default=DEFAULT_HARDENING_PACK)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = run_fix(
        table_root=args.table_root,
        base_root=args.base_root,
        hardening_pack=args.hardening_pack,
        output_root=args.output_root,
        report_path=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
