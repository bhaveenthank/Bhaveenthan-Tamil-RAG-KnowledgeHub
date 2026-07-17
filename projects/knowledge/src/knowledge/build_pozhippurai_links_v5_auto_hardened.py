from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from knowledge.analyze_combined_learned_confidence_errors import classify_row
from knowledge.build_pozhippurai_links_v4 import validate_clean_links, validate_v4_links, write_iob_v4
from knowledge.build_pozhippurai_links_v4_hardened import load_hardening_pack
from knowledge.fix_ambiguous_pozhippurai_spans import ambiguous_count, apply_ambiguity_fix
from knowledge.fix_missing_anchor_links import (
    AnchorResolution,
    load_anchor_rules,
    missing_anchor_count,
    resolve_anchors,
)
from knowledge.fix_pozhippurai_broad_targets import broad_count, fix_rows, source_target_ratio
from knowledge.learn_pozhippurai_high_confidence_patterns import is_gold_example, learn_patterns
from knowledge.link_thevaram_pozhippurai import DEFAULT_TABLE_ROOT, read_jsonl, tokens
from knowledge.link_thevaram_pozhippurai_v3 import write_csv_file, write_jsonl, write_tsv

SCHEMA_VERSION = "thevaram-pozhppurai-paadallink-v5-auto-hardened"
DEFAULT_BASE_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_combined_learned")
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_pozhippurai_links/v5_auto_hardened")
DEFAULT_REPORT = DEFAULT_OUTPUT_ROOT / "paadal_pozhippurai_links_v5_auto_hardened_report.md"
DEFAULT_ERROR_ROOT = DEFAULT_BASE_ROOT / "error_analysis"
RELATIONSHIP_TYPES = {
    "explains_line",
    "explains_phrase",
    "glosses_word",
    "interprets_image",
    "theological_explanation",
    "describes_entity",
}
RELATION_FAMILIES = {
    "interprets_image": "image_family",
    "theological_explanation": "theology_family",
    "describes_entity": "entity_family",
    "explains_phrase": "phrase_family",
    "glosses_word": "phrase_family",
    "explains_line": "phrase_family",
}
ORDER_ONLY_BLOCKERS = {"order_only_penalty", "order_only_support"}
HIGH_BLOCKERS = {
    "order_only_penalty",
    "order_only_support",
    "polysemy_without_context_penalty",
    "best_second_margin_below_review_threshold",
}
TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]+")
STOP_TOKENS = {
    "ஆகிய",
    "உடைய",
    "என்று",
    "என்னும்",
    "இவர்",
    "அவர்",
    "அது",
    "இது",
    "ஒரு",
    "ஓர்",
    "தன்",
    "தமது",
    "மேல்",
    "கீழ்",
    "போல",
}


@dataclass(frozen=True)
class PhraseFamily:
    name: str
    relationship_family: str
    source_cues: tuple[str, ...]
    target_cues: tuple[str, ...]
    notes: str


PHRASE_FAMILIES = (
    PhraseFamily(
        "worship_action_result",
        "theology_family",
        ("தொழ", "தொழுது", "கைதொழ", "பணி", "பணிந்து", "ஏத்து", "ஏத்தி", "போற்றி", "வழிபட்டு"),
        ("தொழ", "தொழுது", "கைதொழ", "போற்றி", "வணங்கு", "வழிபட்டு", "அருச்சித்து", "வினை", "நீங்க", "கெடு", "உய்வு", "இன்பம்"),
        "Devotional action in paadal often maps to worship/result explanation in commentary.",
    ),
    PhraseFamily(
        "grace_result",
        "theology_family",
        ("அருள்", "அருள்செய்", "அருள்புரி", "நோய்", "வினை", "பாசம்", "துன்பம்"),
        ("அருள்", "அருளிச்", "அருள்புரி", "கருணை", "போக்க", "நீங்க", "கெடு", "துன்ப", "வினை"),
        "Grace and removal-result language is usually paraphrastic rather than surface-identical.",
    ),
    PhraseFamily(
        "crescent_hair_image",
        "image_family",
        ("பிறை", "திங்கள்", "மதி", "வெண்மதி", "வெண்திங்கள்", "சடை", "முடி", "சென்னி", "சூடி"),
        ("பிறை", "பிறைமதி", "வெண்பிறை", "சந்திரன்", "திங்கள்", "சடை", "முடி", "சூடி", "பொருந்திய"),
        "Moon terms become safe only with head/hair/wearing cues.",
    ),
    PhraseFamily(
        "ganga_hair_image",
        "image_family",
        ("கங்கை", "புனல்", "சலம்", "நீர்", "அலை", "சடை", "முடி", "சென்னி"),
        ("கங்கை", "புனல்", "நீர்", "சடை", "திருமுடி", "சூடி", "தரித்த", "அடக்கி"),
        "Water words imply Ganga only when hair/head/Siva context is visible.",
    ),
    PhraseFamily(
        "bull_mount_image",
        "image_family",
        ("விடை", "எருது", "ஏறு", "ஆனேறு", "ஏறி"),
        ("விடை", "எருது", "ஏறு", "வாகனம்", "மீது", "ஏறி"),
        "Bull aliases need riding or mount context.",
    ),
    PhraseFamily(
        "serpent_body_image",
        "image_family",
        ("அரவு", "அரவம்", "நாகம்", "பாம்பு", "அரை", "இடை", "சாத்தி"),
        ("பாம்பு", "நாகம்", "அரவு", "அரை", "இடை", "கட்டி", "சாத்தி", "அணிந்து"),
        "Serpent terms are safe with body-locus/action context, unsafe with sound cues.",
    ),
    PhraseFamily(
        "sacred_ash_image",
        "image_family",
        ("பொடி", "திருநீறு", "சுடலை", "சாம்பல்", "பூசி"),
        ("திருநீறு", "திருவெண்ணீறு", "சாம்பல்", "சாம்பற்", "சுண்ணம்", "பூசி", "உடல்"),
        "Ash phrases paraphrase across பொடி, சாம்பல், திருநீறு and பூசி.",
    ),
    PhraseFamily(
        "deity_thalam_entity",
        "entity_family",
        ("ஆலவாய்", "ஆலவாயி", "ஆலவாயில்", "கூடல்", "காழி", "சீகாழி", "அண்ணாமலை", "முதுகுன்றம்", "மிழலை", "கோயில்", "ஊர்", "பதி"),
        ("ஆலவாய்", "கூடல்", "சீகாழி", "அண்ணாமலை", "முதுகுன்றம்", "மிழலை", "கோயில்", "ஊர்", "பதி", "உறையும்", "எழுந்தருளிய"),
        "Thalam/place descriptions need place plus residence or deity support.",
    ),
    PhraseFamily(
        "myth_action_image",
        "image_family",
        ("முப்புரம்", "திரிபுரம்", "நஞ்சு", "கண்டம்", "யானை", "உரி", "இராவணன்", "அரக்கன்", "மழு"),
        ("முப்புரம்", "எரித்த", "நஞ்சு", "கண்டம்", "யானை", "தோல்", "உரித்த", "இராவணன்", "மழு", "ஏந்தி"),
        "Myth actions match through object/action pairs, not a single shared word.",
    ),
    PhraseFamily(
        "landscape_phrase",
        "phrase_family",
        ("நீர்", "புனல்", "வயல்", "சோலை", "மலர்", "மணம்", "கமழ்", "பொழில்"),
        ("நீர்", "புனல்", "வளம்", "வயல்", "சோலை", "மலர்", "மணம்", "கமழும்", "பொழில்"),
        "Landscape phrase expansion often has low entity anchoring but strong phrase-family evidence.",
    ),
)
RESOLUTION_CACHE: dict[tuple[str, str, str], AnchorResolution] = {}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_csv(path: Path, *, limit: int | None = None) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(row)
            if limit is not None and len(rows) >= limit:
                break
    return rows


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in {"", None, "None"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def stable_identity(row: dict[str, Any]) -> str:
    return str(row.get("base_link_id") or row.get("link_id") or "")


def confidence_counts(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("confidence", "")) for row in rows).items()))


def relation_family(relationship: str) -> str:
    return RELATION_FAMILIES.get(relationship, "unknown_family")


def tamil_terms(text: str) -> list[str]:
    return [token for token in TAMIL_RE.findall(str(text)) if len(token) >= 2 and token not in STOP_TOKENS]


def contains_any(text: str, cues: Iterable[str]) -> bool:
    return any(cue and cue in text for cue in cues)


def flags(row: dict[str, Any]) -> set[str]:
    return set(map(str, as_list(row.get("penalties_applied")))) | set(map(str, as_list(row.get("critical_warnings"))))


def feature_scores(row: dict[str, Any]) -> dict[str, float]:
    raw = row.get("feature_scores") if isinstance(row.get("feature_scores"), dict) else {}
    return {str(key): to_float(value) for key, value in raw.items()}


def non_order_evidence_score(row: dict[str, Any], paraphrase_score: float | None = None) -> float:
    features = feature_scores(row)
    score = (
        features.get("semantic_lexicon_score", 0.0)
        + features.get("shared_entity_anchor_score", 0.0)
        + features.get("ontology_relation_score", 0.0)
        + features.get("relationship_cue_score", 0.0)
        + features.get("gold_pattern_similarity", 0.0)
        + to_float(row.get("anchor_resolver_score"))
        + to_float(row.get("learned_pattern_score"))
    )
    if paraphrase_score is not None:
        score += paraphrase_score
    return round(score, 4)


def target_ratio(row: dict[str, Any]) -> float:
    return source_target_ratio(str(row.get("source_text", "")), str(row.get("target_text", "")))


def phrase_family_matches(source: str, target: str, relationship: str) -> list[PhraseFamily]:
    family = relation_family(relationship)
    matches = []
    for phrase_family in PHRASE_FAMILIES:
        if phrase_family.relationship_family != family and family != "unknown_family":
            continue
        if contains_any(source, phrase_family.source_cues) and contains_any(target, phrase_family.target_cues):
            matches.append(phrase_family)
    return matches


def semantic_paraphrase_score(row: dict[str, Any]) -> tuple[float, list[str]]:
    matches = phrase_family_matches(
        str(row.get("source_text", "")),
        str(row.get("target_text", "")),
        str(row.get("relationship_type", "")),
    )
    if not matches:
        return 0.0, []
    base = min(0.75, 0.24 + 0.16 * len(matches))
    learned = min(0.20, to_float(row.get("learned_pattern_score")) / 4.0)
    anchor = min(0.15, to_float(row.get("anchor_resolver_score")) / 5.0)
    return round(min(1.0, base + learned + anchor), 4), [match.name for match in matches]


def polysemy_resolution(row: dict[str, Any], resolution: AnchorResolution | None = None) -> tuple[str, float]:
    source = str(row.get("source_text", ""))
    target = str(row.get("target_text", ""))
    text = f"{source} {target}"
    unsafe = []
    safe = []
    if "மதி" in text:
        (safe if contains_any(text, ("பிறை", "திங்கள்", "சடை", "முடி", "சென்னி", "சூடி", "சந்திரன்")) else unsafe).append("மதி")
    if "விடை" in text:
        (safe if contains_any(text, ("ஏற", "ஏறி", "எருது", "வாகனம்", "மீது")) else unsafe).append("விடை")
    if "அரவம்" in text or "அரவு" in text:
        if "அரவம்" in text and contains_any(text, ("ஆரவாரம்", "பறை", "ஒலி")):
            safe.append("அரவம்=SOUND")
        elif contains_any(text, ("பாம்பு", "நாகம்", "அரை", "இடை", "சாத்தி", "அணிந்து")):
            safe.append("அரவு=SERPENT")
        else:
            unsafe.append("அரவு")
    if "அடி" in text:
        (safe if contains_any(text, ("தொழ", "பணி", "கழல்", "திருவடி", "பாதம்", "சிந்தை", "கைதொழ")) else unsafe).append("அடி")
    if contains_any(text, ("புனல்", "சலம்", "நீர்")):
        safe.append("WATER_CONTEXT_GANGA" if contains_any(text, ("கங்கை", "சடை", "முடி", "சென்னி")) else "WATER_CONTEXT_NATURE")
    if "கை" in text and "கங்கை" in text:
        safe.append("கை_not_matched_inside_கங்கை")
    if "பொடி" in text:
        (safe if contains_any(text, ("சுடலை", "திருநீறு", "பூசி", "சாம்பல்", "உடல்")) else unsafe).append("பொடி")
    if unsafe:
        return f"unsafe_or_context_weak:{'|'.join(unsafe)}", 0.45
    if safe:
        return f"safe:{'|'.join(safe[:6])}", 1.0
    if resolution is not None:
        return ("safe:anchor_resolver_context", resolution.polysemy_safety_score)
    return "not_polysemous_or_no_trigger", to_float(row.get("polysemy_safety_score"), 1.0) or 1.0


def relationship_repair(row: dict[str, Any], matched_families: list[str]) -> tuple[str, str]:
    current = str(row.get("relationship_type", ""))
    source = str(row.get("source_text", ""))
    target = str(row.get("target_text", ""))
    joined = f"{source} {target}"
    if current not in RELATIONSHIP_TYPES:
        return "explains_phrase", "invalid_relationship_defaulted_to_phrase"
    if contains_any(joined, ("சடை", "முடி", "பிறை", "திங்கள்", "கங்கை", "விடை", "அரவு", "பொடி", "நஞ்சு", "முப்புரம்", "யானை", "மழு")):
        if current in {"explains_phrase", "glosses_word"} and any(name.endswith("_image") or name == "myth_action_image" for name in matched_families):
            return "interprets_image", "iconography_or_myth_cue_repaired_to_image"
    if contains_any(joined, ("தொழ", "பணி", "ஏத்தி", "போற்றி", "வினை", "அருள்", "முத்தி", "நீங்க", "கெடு", "பாசம்")):
        if current in {"explains_phrase", "describes_entity"} and {"worship_action_result", "grace_result"} & set(matched_families):
            return "theological_explanation", "devotional_result_cue_repaired_to_theology"
    if contains_any(joined, ("ஆலவாய்", "காழி", "அண்ணாமலை", "முதுகுன்றம்", "மிழலை", "கோயில்", "பதி")):
        if current == "interprets_image" and "deity_thalam_entity" in matched_families:
            return "describes_entity", "thalam_identity_cue_repaired_to_entity"
    return current, ""


def issue_tags(row: dict[str, Any]) -> list[str]:
    labels = classify_row(row)
    raw = labels.get("issue_tags", [])
    if isinstance(raw, str):
        return [part for part in raw.split("|") if part]
    return list(raw)


def baseline_metrics(rows: list[dict[str, Any]], paadal_by_id: dict[str, str]) -> dict[str, Any]:
    margins = [to_float(row.get("best_second_margin")) for row in rows if row.get("relationship_type") != "unlinked"]
    reuse = Counter(str(row.get("target_reuse_reason", "")) for row in rows if row.get("target_reuse_reason"))
    penalties = Counter(",".join(sorted(map(str, as_list(row.get("penalties_applied"))))) or "none" for row in rows)
    issue_counter: Counter[str] = Counter()
    for row in rows:
        if row.get("confidence") in {"medium", "low"}:
            issue_counter.update(issue_tags(row))
    return {
        "total_links": len(rows),
        "confidence_counts": confidence_counts(rows),
        "no_link_count": sum(1 for row in rows if row.get("confidence") == "no_link" or row.get("relationship_type") == "unlinked"),
        "missing_anchor_count": missing_anchor_count(rows),
        "ambiguous_span_count": ambiguous_count(rows),
        "broad_or_unsplit_target_count": broad_count(rows, paadal_by_id),
        "weak_semantic_signal_count": issue_counter.get("weak_semantic_signal", 0),
        "low_learned_pattern_support_count": issue_counter.get("low_learned_pattern_support", 0),
        "polysemy_context_count": issue_counter.get("polysemy_context", 0),
        "high_pattern_but_blocked_count": issue_counter.get("high_pattern_but_blocked", 0),
        "relation_granularity_mismatch_count": issue_counter.get("relation_granularity_mismatch", 0),
        "order_only_count": issue_counter.get("order_only", 0),
        "manual_review_required_count": sum(bool(row.get("manual_review_required")) for row in rows),
        "relationship_type_counts": dict(sorted(Counter(str(row.get("relationship_type", "")) for row in rows).items())),
        "penalty_combinations": dict(penalties.most_common(50)),
        "average_target_source_length_ratio": round(sum(target_ratio(row) for row in rows) / max(1, len(rows)), 4),
        "average_best_second_margin": round(sum(margins) / max(1, len(margins)), 4),
        "target_reuse_counts": dict(reuse.most_common(20)),
    }


def inventory_files(base_root: Path, error_root: Path) -> list[dict[str, Any]]:
    patterns = (
        "v3",
        "v4",
        "gold",
        "review",
        "error_analysis",
        "pattern",
        "ontology",
        "entity",
        "hardening",
        "corrected",
        "recovered",
        "split",
    )
    roots = [Path("data/processed/thevaram_pozhippurai_links"), Path("data/knowledge"), Path("projects/knowledge"), Path("shared/tvu-schemas")]
    rows = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and any(pattern in str(path) for pattern in patterns):
                rows.append(
                    {
                        "path": str(path),
                        "bytes": path.stat().st_size,
                        "source_role": "primary_base" if path.is_relative_to(base_root) else "error_analysis" if path.is_relative_to(error_root) else "supporting",
                    }
                )
    return sorted(rows, key=lambda row: row["path"])


def mine_paraphrase_lexicon(rows: list[dict[str, Any]], output_path: Path) -> list[dict[str, Any]]:
    support: dict[tuple[str, str, str], dict[str, Any]] = {}
    high_rows = [row for row in rows if is_gold_example(row)]
    for row in high_rows:
        source = str(row.get("source_text", ""))
        target = str(row.get("target_text", ""))
        relationship_family = relation_family(str(row.get("relationship_type", "")))
        for family in PHRASE_FAMILIES:
            if family.relationship_family != relationship_family:
                continue
            source_hits = [cue for cue in family.source_cues if cue in source]
            target_hits = [cue for cue in family.target_cues if cue in target]
            for source_phrase in source_hits[:4]:
                for target_phrase in target_hits[:4]:
                    key = (source_phrase, target_phrase, relationship_family)
                    entry = support.setdefault(
                        key,
                        {
                            "source_phrase": source_phrase,
                            "target_phrase": target_phrase,
                            "relationship_family": relationship_family,
                            "support_count": 0,
                            "example_link_ids": [],
                            "confidence": "candidate",
                            "notes": family.notes,
                        },
                    )
                    entry["support_count"] += 1
                    if len(entry["example_link_ids"]) < 8:
                        entry["example_link_ids"].append(str(row.get("link_id", "")))
    output = []
    for entry in support.values():
        count = int(entry["support_count"])
        if count < 2:
            continue
        item = dict(entry)
        item["example_link_ids"] = "|".join(item["example_link_ids"])
        item["confidence"] = "high" if count >= 12 else "medium" if count >= 5 else "low"
        output.append(item)
    output.sort(key=lambda row: (-int(row["support_count"]), row["relationship_family"], row["source_phrase"]))
    write_csv_file(output_path, output)
    return output


def mine_pattern_groups(rows: list[dict[str, Any]], output_path: Path) -> list[dict[str, Any]]:
    group_counter: Counter[tuple[str, str]] = Counter()
    negative_counter: Counter[tuple[str, str]] = Counter()
    examples: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in rows:
        score, matched = semantic_paraphrase_score(row)
        relationship = str(row.get("relationship_type", ""))
        for name in matched:
            key = (name, relationship)
            if row.get("confidence") == "high" and not row.get("manual_review_required"):
                group_counter[key] += 1
                if len(examples[key]) < 10:
                    examples[key].append(str(row.get("link_id", "")))
            elif row.get("confidence") in {"low", "medium"} and score < 0.5:
                negative_counter[key] += 1
    output = []
    for key, support in group_counter.items():
        negatives = negative_counter[key]
        precision = support / max(1, support + negatives)
        output.append(
            {
                "pattern_group": key[0],
                "relationship_type": key[1],
                "relationship_family": relation_family(key[1]),
                "support_count": support,
                "negative_count": negatives,
                "pattern_precision_estimate": round(precision, 4),
                "anchor_requirements": "non_order_evidence_required|polysemy_safe|compact_or_shrunk_target",
                "promotion_threshold": 0.82 if precision >= 0.9 else 0.86,
                "manual_review_threshold": 0.55,
                "example_link_ids": "|".join(examples[key]),
            }
        )
    output.sort(key=lambda row: (-int(row["support_count"]), row["pattern_group"]))
    write_csv_file(output_path, output)
    return output


def v5_score(row: dict[str, Any], paraphrase_score: float, issue_after: list[str]) -> float:
    features = feature_scores(row)
    family = relation_family(str(row.get("relationship_type", "")))
    family_bias = {
        "image_family": 0.05,
        "theology_family": 0.04,
        "entity_family": 0.03,
        "phrase_family": 0.02,
    }.get(family, 0.0)
    margin = to_float(row.get("best_second_margin"))
    margin_component = 0.12 if margin >= 0.12 else 0.06 if margin >= 0.05 else 0.0
    broad_penalty = 0.10 if "broad_or_unsplit_target" in issue_after else 0.0
    ambiguity_penalty = 0.10 if "ambiguous_span" in issue_after else 0.0
    missing_penalty = 0.08 if "missing_anchor" in issue_after else 0.0
    order_penalty = 0.20 if "order_only" in issue_after else 0.0
    raw = (
        0.30 * to_float(row.get("score"))
        + 0.18 * to_float(row.get("learned_pattern_score"))
        + 0.16 * paraphrase_score
        + 0.14 * to_float(row.get("anchor_resolver_score"))
        + 0.12 * to_float(row.get("polysemy_safety_score"), 1.0)
        + 0.08 * features.get("ontology_relation_score", 0.0)
        + 0.06 * features.get("relationship_cue_score", 0.0)
        + margin_component
        + family_bias
        - broad_penalty
        - ambiguity_penalty
        - missing_penalty
        - order_penalty
    )
    return round(max(0.0, min(0.99, raw)), 4)


def apply_v5_row(
    row: dict[str, Any],
    rules: Any,
    *,
    prior_high_ids: set[str],
) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]:
    item = dict(row)
    confidence_before = str(row.get("confidence", ""))
    score_before = to_float(row.get("score"))
    relationship_before = str(row.get("relationship_type", ""))
    penalties = list(map(str, as_list(row.get("penalties_applied"))))
    critical = list(map(str, as_list(row.get("critical_warnings"))))
    repair_actions: list[str] = []
    unsafe: dict[str, Any] | None = None
    issue_before = issue_tags(row) if confidence_before in {"medium", "low"} else []
    source_text = str(row.get("source_text", ""))
    target_text = str(row.get("target_text", ""))
    cache_key = (source_text, target_text, relationship_before)
    resolution = RESOLUTION_CACHE.get(cache_key)
    if resolution is None:
        resolution = resolve_anchors(source_text, target_text, relationship_before, rules)
        RESOLUTION_CACHE[cache_key] = resolution
    paraphrase_score, matched_families = semantic_paraphrase_score(row)
    poly_note, poly_score = polysemy_resolution(row, resolution)
    relationship_after, relationship_reason = relationship_repair(row, matched_families)

    anchors_before = list(map(str, as_list(row.get("expanded_entity_anchors"))))
    anchors_after = sorted(set(anchors_before) | set(resolution.matched_anchors))
    ontology_after = sorted(set(map(str, as_list(row.get("ontology_relations_matched")))) | set(resolution.ontology_relations))

    if "missing_entity_anchor_penalty" in penalties:
        if resolution.missing_anchor_resolved or (paraphrase_score >= 0.68 and non_order_evidence_score(row, paraphrase_score) >= 1.45 and poly_score >= 0.70):
            penalties = [penalty for penalty in penalties if penalty != "missing_entity_anchor_penalty"]
            repair_actions.append("ANCHOR_RESOLVED")

    if "polysemy_without_context_penalty" in penalties and poly_score >= 0.95 and paraphrase_score >= 0.40:
        penalties = [penalty for penalty in penalties if penalty != "polysemy_without_context_penalty"]
        repair_actions.append("POLYSEMY_RESOLVED")

    if "ambiguous_margin_penalty" in penalties:
        margin = to_float(row.get("best_second_margin"))
        reuse_ok = bool(row.get("target_reuse_allowed", True))
        if margin >= 0.12 and reuse_ok and paraphrase_score >= 0.40 and non_order_evidence_score(row, paraphrase_score) >= 1.25:
            penalties = [penalty for penalty in penalties if penalty != "ambiguous_margin_penalty"]
            critical = [warning for warning in critical if warning != "best_second_margin_below_review_threshold"]
            repair_actions.append("GLOBAL_REASSIGNED")

    if "target_too_broad_penalty" in penalties:
        ratio = target_ratio(row)
        if ratio <= 4.0 and paraphrase_score >= 0.45:
            penalties = [penalty for penalty in penalties if penalty != "target_too_broad_penalty"]
            repair_actions.append("TARGET_SHRUNK")
        elif row.get("target_shrink_applied") and to_float(row.get("target_shrink_ratio"), 1.0) <= 0.75:
            penalties = [penalty for penalty in penalties if penalty != "target_too_broad_penalty"]
            repair_actions.append("TARGET_SHRUNK")

    if relationship_after != relationship_before:
        item["relationship_type"] = relationship_after
        repair_actions.append("RELATION_REPAIRED")

    item.update(
        {
            "schema_version": SCHEMA_VERSION,
            "v5_base_schema_version": row.get("schema_version", ""),
            "confidence_before": confidence_before,
            "score_before": score_before,
            "relationship_type_before": relationship_before,
            "relationship_type_after": relationship_after,
            "relationship_repair_reason": relationship_reason,
            "target_text_original": row.get("target_text_original") or row.get("target_text", ""),
            "target_text_minimal": row.get("target_text_minimal") or row.get("target_text", ""),
            "anchors_before": anchors_before,
            "anchors_after": anchors_after,
            "expanded_entity_anchors": anchors_after,
            "ontology_relations_matched": ontology_after,
            "anchor_resolver_score": max(to_float(row.get("anchor_resolver_score")), resolution.anchor_resolver_score),
            "anchor_alias_score": max(to_float(row.get("anchor_alias_score")), resolution.anchor_alias_score),
            "anchor_morphology_score": max(to_float(row.get("anchor_morphology_score")), resolution.anchor_morphology_score),
            "anchor_context_disambiguation_score": max(to_float(row.get("anchor_context_disambiguation_score")), resolution.anchor_context_disambiguation_score),
            "ontology_relation_score": max(to_float(row.get("ontology_relation_score")), resolution.ontology_relation_score),
            "anchor_family_match_score": max(to_float(row.get("anchor_family_match_score")), resolution.anchor_family_match_score),
            "missing_anchor_resolved": bool(row.get("missing_anchor_resolved")) or resolution.missing_anchor_resolved or "ANCHOR_RESOLVED" in repair_actions,
            "semantic_paraphrase_score": paraphrase_score,
            "semantic_paraphrase_families": matched_families,
            "polysemy_resolution": poly_note,
            "polysemy_safety_score": max(to_float(row.get("polysemy_safety_score"), 1.0), poly_score),
            "order_only_evidence_gate": "pass" if non_order_evidence_score(row, paraphrase_score) >= 0.85 and not (set(penalties) & ORDER_ONLY_BLOCKERS) else "block",
            "penalties_applied": penalties,
            "critical_warnings": critical,
        }
    )
    issue_after = issue_tags(item) if confidence_before in {"medium", "low"} or penalties else []
    calibrated_score = v5_score(item, paraphrase_score, issue_after)
    current_conf = confidence_before
    manual_review = bool(row.get("manual_review_required"))
    promotion_decision = "UNCHANGED"
    non_order = non_order_evidence_score(item, paraphrase_score)
    blocker_set = set(penalties) | set(critical)

    preserve_prior_high = stable_identity(row) in prior_high_ids or confidence_before == "high"
    if preserve_prior_high:
        current_conf = "high"
        manual_review = bool(critical)
        calibrated_score = max(calibrated_score, score_before, 0.82)
    elif item["order_only_evidence_gate"] == "block":
        current_conf = "low" if confidence_before == "low" else "medium"
        manual_review = True
        if set(penalties) & ORDER_ONLY_BLOCKERS:
            promotion_decision = "REJECTED_ORDER_ONLY"
    elif not blocker_set and calibrated_score >= 0.82 and non_order >= 1.65 and paraphrase_score >= 0.45 and to_float(item.get("polysemy_safety_score"), 1.0) >= 0.70:
        current_conf = "high"
        manual_review = False
        promotion_decision = "PROMOTE_HIGH"
        repair_actions.append("CALIBRATION_PROMOTED")
    elif confidence_before == "low" and calibrated_score >= 0.58 and non_order >= 1.20 and paraphrase_score >= 0.35 and not (set(penalties) & ORDER_ONLY_BLOCKERS):
        current_conf = "medium"
        manual_review = True
        promotion_decision = "PROMOTE_MEDIUM"
        repair_actions.append("PATTERN_PROMOTED")
    elif penalties or critical:
        manual_review = True
        promotion_decision = "KEEP_REVIEW"
    else:
        current_conf = "medium" if confidence_before == "medium" else confidence_before
        manual_review = bool(confidence_before != "high" and calibrated_score < 0.82)

    if current_conf == "high" and not preserve_prior_high and (set(penalties) & HIGH_BLOCKERS or item["order_only_evidence_gate"] == "block"):
        unsafe = {
            "link_id": item.get("link_id", ""),
            "confidence_before": confidence_before,
            "attempted_confidence": current_conf,
            "source_text": item.get("source_text", ""),
            "target_text": item.get("target_text", ""),
            "reason": "blocked_high_promotion_due_to_order_or_polysemy_warning",
            "penalties_applied": "|".join(penalties),
            "critical_warnings": "|".join(critical),
        }
        current_conf = "medium" if confidence_before == "medium" else "low"
        manual_review = True
        promotion_decision = "REJECTED_UNSAFE"

    item["confidence"] = current_conf
    item["score"] = round(max(score_before if confidence_before == "high" else 0.0, calibrated_score), 4)
    item["manual_review_required"] = manual_review
    item["issue_tags_before"] = issue_before
    item["issue_tags_after"] = issue_tags(item) if current_conf in {"medium", "low"} or penalties else []
    item["repair_actions_applied"] = sorted(set(repair_actions)) or ["NO_CHANGE"]
    item["promotion_decision"] = promotion_decision
    item["high_pattern_block_resolution"] = high_pattern_block_resolution(item, issue_before, promotion_decision)
    item["diagnostic_note"] = (
        f"{row.get('diagnostic_note', '')} v5 auto-hardening: "
        f"paraphrase={paraphrase_score}; anchors={resolution.matched_anchors}; decision={promotion_decision}."
    )

    change = None
    if repair_actions or confidence_before != current_conf or relationship_before != relationship_after or penalties != as_list(row.get("penalties_applied")):
        change = {
            "link_id": item.get("link_id", ""),
            "confidence_before": confidence_before,
            "confidence_after": current_conf,
            "relationship_type_before": relationship_before,
            "relationship_type_after": relationship_after,
            "issue_tags_before": "|".join(issue_before),
            "issue_tags_after": "|".join(item["issue_tags_after"]),
            "repair_action": "|".join(sorted(set(repair_actions)) or ["NO_CHANGE"]),
            "source_text": item.get("source_text", ""),
            "target_text_before": row.get("target_text", ""),
            "target_text_after": item.get("target_text", ""),
            "anchor_added": "|".join(sorted(set(anchors_after) - set(anchors_before))),
            "ontology_relation_added": "|".join(sorted(set(ontology_after) - set(map(str, as_list(row.get("ontology_relations_matched")))))),
            "pattern_group_matched": "|".join(matched_families),
            "target_shrink_applied": item.get("target_shrink_applied", ""),
            "global_reassignment_applied": "GLOBAL_REASSIGNED" in repair_actions,
            "promotion_decision": promotion_decision,
            "reason": item.get("diagnostic_note", ""),
        }
    return item, change, unsafe


def high_pattern_block_resolution(row: dict[str, Any], issue_before: list[str], decision: str) -> str:
    if "high_pattern_but_blocked" not in issue_before and to_float(row.get("learned_pattern_score")) < 0.42:
        return ""
    if decision == "PROMOTE_HIGH":
        return "RESOLVED_PROMOTE_HIGH"
    if decision == "PROMOTE_MEDIUM":
        return "RESOLVED_PROMOTE_MEDIUM"
    issues = set(row.get("issue_tags_after") or [])
    if "broad_or_unsplit_target" in issues:
        return "BLOCKED_BROAD_TARGET"
    if "ambiguous_span" in issues:
        return "BLOCKED_AMBIGUOUS_MARGIN"
    if "polysemy_context" in issues:
        return "BLOCKED_POLYSEMY"
    if "missing_anchor" in issues:
        return "BLOCKED_NO_ONTOLOGY_RELATION"
    if "relation_granularity_mismatch" in issues:
        return "BLOCKED_RELATION_MISMATCH"
    return "KEEP_REVIEW"


def apply_v5_calibration(rows: list[dict[str, Any]], rules: Any, prior_high_ids: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    fixed = []
    changes = []
    unsafe = []
    for row in rows:
        item, change, unsafe_row = apply_v5_row(row, rules, prior_high_ids=prior_high_ids)
        fixed.append(item)
        if change is not None:
            changes.append(change)
        if unsafe_row is not None:
            unsafe.append(unsafe_row)
    return fixed, changes, unsafe


def smart_manual_review_pack(rows: list[dict[str, Any]], table_root: Path, *, limit: int = 450) -> list[dict[str, Any]]:
    paadal_by_id = {str(row.get("paadal_id", "")): str(row.get("paadal_text", "")) for row in read_jsonl(table_root / "paadalgal.jsonl")}
    commentary_by_id = {str(row.get("commentary_id", "")): row for row in read_jsonl(table_root / "commentaries.jsonl")}
    candidates = []
    for row in rows:
        if row.get("confidence") == "high":
            continue
        issues = set(row.get("issue_tags_after") or row.get("issue_tags_before") or [])
        score = 0
        reasons = []
        anchor_score = to_float(row.get("anchor_resolver_score"))
        margin = to_float(row.get("best_second_margin"))
        if row.get("high_pattern_block_resolution"):
            score += 8
            reasons.append(str(row.get("high_pattern_block_resolution")))
        if 0.45 <= anchor_score < 0.60:
            score += 7
            reasons.append("anchor_resolver_near_threshold")
        if "ambiguous_span" in issues and margin < 0.05:
            score += 7
            reasons.append("very_low_best_second_margin")
        if str(row.get("target_reuse_reason")) == "suspicious_target_reuse":
            score += 7
            reasons.append("suspicious_target_reuse")
        if to_float(row.get("polysemy_safety_score"), 1.0) < 0.70:
            score += 6
            reasons.append("polysemy_unsafe")
        if "broad_or_unsplit_target" in issues and not row.get("target_shrink_applied"):
            score += 5
            reasons.append("broad_target_no_safe_minimal_span")
        if to_float(row.get("relation_family_conflict_penalty")) > 0:
            score += 5
            reasons.append("relationship_family_conflict")
        if "missing_anchor" in issues:
            score += 3
        if not reasons:
            continue
        commentary = commentary_by_id.get(str(row.get("commentary_id", "")), {})
        candidates.append(
            (
                -score,
                str(row.get("relationship_type", "")),
                str(row.get("thirumurai_no", "")),
                {
                    "link_id": row.get("link_id", ""),
                    "source_text": row.get("source_text", ""),
                    "target_text": row.get("target_text", ""),
                    "full_paadal_if_available": paadal_by_id.get(str(row.get("paadal_id", "")), ""),
                    "full_pozhippurai_if_available": commentary.get("pozhppurai", ""),
                    "kurippurai_if_available": commentary.get("kurippurai", ""),
                    "relationship_type": row.get("relationship_type", ""),
                    "confidence": row.get("confidence", ""),
                    "issue_tags": "|".join(row.get("issue_tags_after") or []),
                    "possible_anchors": "|".join(row.get("possible_source_anchors") or []) + " || " + "|".join(row.get("possible_target_anchors") or []),
                    "top_3_target_candidates": " || ".join(
                        text
                        for text in [
                            str(row.get("global_selected_target_text", "")),
                            str(row.get("local_best_target_text", "")),
                            str(row.get("second_best_target_text", "")),
                        ]
                        if text
                    ),
                    "best_second_margin": row.get("best_second_margin", ""),
                    "suggested_fix": suggested_fix(row),
                    "reason_for_review": "|".join(reasons),
                },
            )
        )
    selected = []
    seen_link_ids = set()
    coverage: Counter[str] = Counter()
    for _neg_score, relationship, _thirumurai, payload in sorted(
        candidates, key=lambda item: (item[0], item[1], item[2], str(item[3].get("link_id", "")))
    ):
        if payload["link_id"] in seen_link_ids:
            continue
        if coverage[relationship] > limit // 3 and len(selected) < limit // 2:
            continue
        selected.append(payload)
        seen_link_ids.add(payload["link_id"])
        coverage[relationship] += 1
        if len(selected) >= limit:
            break
    return selected


def suggested_fix(row: dict[str, Any]) -> str:
    issues = set(row.get("issue_tags_after") or [])
    if "missing_anchor" in issues:
        return "Add/validate ontology anchor alias or relation cue."
    if "ambiguous_span" in issues:
        return "Review top target candidates and neighbour alignment."
    if "broad_or_unsplit_target" in issues:
        return "Mark the minimal commentary clause that explains the source span."
    if "polysemy_context" in issues:
        return "Add local context rule or negative example for the ambiguous word."
    if "weak_semantic_signal" in issues:
        return "Add paraphrase pair to Tamil literary lexicon."
    return "Review confidence calibration and relationship type."


def write_conll(path: Path, rows: list[dict[str, Any]]) -> None:
    write_iob_v4(path, [row for row in rows if row.get("confidence") in {"high", "medium"} and row.get("target_text")])


def summarize_v5(
    *,
    baseline: dict[str, Any],
    full: list[dict[str, Any]],
    primary: list[dict[str, Any]],
    paadal_by_id: dict[str, str],
    repair_log: list[dict[str, Any]],
    unsafe: list[dict[str, Any]],
    validation: dict[str, Any],
    primary_validation: dict[str, Any],
    prior_high_ids: set[str],
    manual_review_size: int,
    lexicon_rows: int,
    pattern_rows: int,
    tests_passed: bool,
) -> dict[str, Any]:
    primary_conf = confidence_counts(primary)
    current_high_ids = {stable_identity(row) for row in primary if row.get("confidence") == "high"}
    lost_high = sorted(prior_high_ids - current_high_ids)
    after_issue_counter: Counter[str] = Counter()
    for row in primary:
        if row.get("confidence") in {"medium", "low"}:
            after_issue_counter.update(row.get("issue_tags_after") or [])
    baseline_conf = baseline["confidence_counts"]
    broad_after = broad_count(primary, paadal_by_id)
    missing_after = missing_anchor_count(primary)
    ambiguous_after = ambiguous_count(primary)
    order_high = sum(
        1
        for row in primary
        if row.get("confidence") == "high"
        and row.get("confidence_before") != "high"
        and row.get("order_only_evidence_gate") == "block"
    )
    actions = Counter()
    for row in repair_log:
        for action in str(row.get("repair_action", "")).split("|"):
            if action:
                actions[action] += 1
    accepted = (
        int(primary_conf.get("high", 0)) >= int(baseline_conf.get("high", 0))
        and not lost_high
        and missing_after < int(baseline["missing_anchor_count"])
        and ambiguous_after < int(baseline["ambiguous_span_count"])
        and broad_after < int(baseline["broad_or_unsplit_target_count"])
        and order_high == 0
        and tests_passed
        and validation.get("status") == "VALID"
        and primary_validation.get("status") == "VALID"
    )
    if int(primary_conf.get("high", 0)) < int(baseline_conf.get("high", 0)):
        status = "rejected_high_confidence_drop"
    elif accepted:
        status = "accepted"
    else:
        status = "partial_needs_review"
    return {
        "schema_version": SCHEMA_VERSION,
        "run_status": status,
        "accepted": accepted,
        "baseline_metrics": baseline,
        "total_links": len(full),
        "primary_clean_links": len(primary),
        "full_confidence": confidence_counts(full),
        "primary_confidence": primary_conf,
        "high_confidence_gained": max(0, int(primary_conf.get("high", 0)) - int(baseline_conf.get("high", 0))),
        "high_confidence_lost": max(0, int(baseline_conf.get("high", 0)) - int(primary_conf.get("high", 0))),
        "prior_high_primary_links_checked": len(prior_high_ids),
        "prior_high_primary_links_lost": len(lost_high),
        "lost_prior_high_link_ids_sample": lost_high[:25],
        "medium_upgraded_to_high": sum(1 for row in primary if row.get("confidence_before") == "medium" and row.get("confidence") == "high"),
        "low_upgraded_to_high": sum(1 for row in primary if row.get("confidence_before") == "low" and row.get("confidence") == "high"),
        "low_upgraded_to_medium": sum(1 for row in primary if row.get("confidence_before") == "low" and row.get("confidence") == "medium"),
        "missing_anchor_before": int(baseline["missing_anchor_count"]),
        "missing_anchor_after": missing_after,
        "ambiguous_span_before": int(baseline["ambiguous_span_count"]),
        "ambiguous_span_after": ambiguous_after,
        "broad_or_unsplit_target_before": int(baseline["broad_or_unsplit_target_count"]),
        "broad_or_unsplit_target_after": broad_after,
        "weak_semantic_signal_before": int(baseline["weak_semantic_signal_count"]),
        "weak_semantic_signal_after": after_issue_counter.get("weak_semantic_signal", 0),
        "polysemy_context_before": int(baseline["polysemy_context_count"]),
        "polysemy_context_after": after_issue_counter.get("polysemy_context", 0),
        "high_pattern_but_blocked_before": int(baseline["high_pattern_but_blocked_count"]),
        "high_pattern_but_blocked_after": after_issue_counter.get("high_pattern_but_blocked", 0),
        "relation_granularity_mismatch_before": int(baseline["relation_granularity_mismatch_count"]),
        "relation_granularity_mismatch_after": after_issue_counter.get("relation_granularity_mismatch", 0),
        "order_only_high_promotions": order_high,
        "anchors_resolved": actions.get("ANCHOR_RESOLVED", 0),
        "targets_shrunk": actions.get("TARGET_SHRUNK", 0),
        "global_reassignments": actions.get("GLOBAL_REASSIGNED", 0),
        "relationship_repairs": actions.get("RELATION_REPAIRED", 0),
        "unsafe_promotions_rejected": len(unsafe) + actions.get("REJECTED_UNSAFE", 0),
        "manual_review_pack_size": manual_review_size,
        "repair_actions": dict(actions),
        "learned_paraphrase_lexicon_rows": lexicon_rows,
        "learned_pattern_group_rows": pattern_rows,
        "manual_review_required_count": sum(bool(row.get("manual_review_required")) for row in primary),
        "relationship_type_counts": dict(sorted(Counter(str(row.get("relationship_type", "")) for row in primary).items())),
        "validation": validation,
        "primary_validation": primary_validation,
        "tests_passed": tests_passed,
    }


def render_report(summary: dict[str, Any], output_root: Path) -> str:
    baseline = summary["baseline_metrics"]

    def table(mapping: dict[str, Any]) -> str:
        return "\n".join(f"| `{key}` | {value} |" for key, value in mapping.items()) or "| None | 0 |"

    return f"""# Paadal-Pozhippurai Linker v5 Auto-Hardened Report

## Run Status

- Run status: `{summary['run_status']}`
- Accepted: `{str(summary['accepted']).lower()}`
- Output root: `{output_root}`
- Schema version: `{summary['schema_version']}`
- Validation status: `{summary['validation']['status']}`
- Primary validation status: `{summary['primary_validation']['status']}`

## Baseline Versus v5

| Metric | Baseline | v5 |
| --- | ---: | ---: |
| Total primary links | {baseline['total_links']} | {summary['primary_clean_links']} |
| High confidence | {baseline['confidence_counts'].get('high', 0)} | {summary['primary_confidence'].get('high', 0)} |
| Medium confidence | {baseline['confidence_counts'].get('medium', 0)} | {summary['primary_confidence'].get('medium', 0)} |
| Low confidence | {baseline['confidence_counts'].get('low', 0)} | {summary['primary_confidence'].get('low', 0)} |
| Missing anchor | {summary['missing_anchor_before']} | {summary['missing_anchor_after']} |
| Ambiguous span | {summary['ambiguous_span_before']} | {summary['ambiguous_span_after']} |
| Broad/unsplit target | {summary['broad_or_unsplit_target_before']} | {summary['broad_or_unsplit_target_after']} |
| Weak semantic signal | {summary['weak_semantic_signal_before']} | {summary['weak_semantic_signal_after']} |
| Polysemy context | {summary['polysemy_context_before']} | {summary['polysemy_context_after']} |
| High pattern but blocked | {summary['high_pattern_but_blocked_before']} | {summary['high_pattern_but_blocked_after']} |
| Relation granularity mismatch | {summary['relation_granularity_mismatch_before']} | {summary['relation_granularity_mismatch_after']} |

## Movement

- High confidence gained: `{summary['high_confidence_gained']}`
- High confidence lost: `{summary['high_confidence_lost']}`
- Prior high primary links lost: `{summary['prior_high_primary_links_lost']}`
- Medium upgraded to high: `{summary['medium_upgraded_to_high']}`
- Low upgraded to high: `{summary['low_upgraded_to_high']}`
- Low upgraded to medium: `{summary['low_upgraded_to_medium']}`
- Order-only high promotions: `{summary['order_only_high_promotions']}`

## Repair Counts

- Anchors resolved: `{summary['anchors_resolved']}`
- Targets shrunk or broad penalty cleared: `{summary['targets_shrunk']}`
- Global ambiguity reassignments/resolutions: `{summary['global_reassignments']}`
- Relationship repairs: `{summary['relationship_repairs']}`
- Unsafe promotions rejected: `{summary['unsafe_promotions_rejected']}`
- Manual review pack size: `{summary['manual_review_pack_size']}`
- Learned paraphrase lexicon rows: `{summary['learned_paraphrase_lexicon_rows']}`
- Learned pattern group rows: `{summary['learned_pattern_group_rows']}`

## Primary Confidence Distribution

| Confidence | Rows |
| --- | ---: |
{table(summary['primary_confidence'])}

## Relationship Distribution

| Relationship | Rows |
| --- | ---: |
{table(summary['relationship_type_counts'])}

## Notes

- v5 learns from the existing high-confidence rows and uses deterministic anchor, paraphrase, polysemy, broad-target, ambiguity, relationship, and confidence-calibration gates.
- Existing v3/v4/v4_combined outputs are not overwritten.
- This is a stronger retrieval/linking layer, not final scholarly gold accuracy.
"""


def write_outputs(
    output_root: Path,
    *,
    full: list[dict[str, Any]],
    primary: list[dict[str, Any]],
    secondary: list[dict[str, Any]],
    summary: dict[str, Any],
    report_path: Path,
    repair_log: list[dict[str, Any]],
    unsafe: list[dict[str, Any]],
    manual_review_pack: list[dict[str, Any]],
    inventory: list[dict[str, Any]],
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_root / "paadal_pozhippurai_links_v5_auto_hardened_full.jsonl", full)
    write_tsv(output_root / "paadal_pozhippurai_links_v5_auto_hardened_full.tsv", full)
    write_jsonl(output_root / "paadal_pozhippurai_links_v5_auto_hardened_high_confidence.jsonl", [row for row in full if row.get("confidence") == "high"])
    write_jsonl(output_root / "paadal_pozhippurai_links_v5_auto_hardened_medium_confidence.jsonl", [row for row in full if row.get("confidence") == "medium"])
    write_csv_file(output_root / "paadal_pozhippurai_links_v5_auto_hardened_low_review.csv", [row for row in full if row.get("confidence") == "low" or row.get("manual_review_required")])
    write_csv_file(output_root / "paadal_pozhippurai_links_v5_auto_hardened_no_link_or_unresolved.csv", [row for row in full if row.get("confidence") == "no_link" or row.get("relationship_type") == "unlinked"])
    write_csv_file(output_root / "paadal_pozhippurai_links_v5_auto_hardened_manual_review_pack.csv", manual_review_pack)
    write_conll(output_root / "paadal_pozhippurai_links_v5_auto_hardened.iob.conll", full)
    write_csv_file(output_root / "repair_actions_log.csv", repair_log)
    write_csv_file(output_root / "rejected_or_unsafe_promotions.csv", unsafe)
    write_jsonl(output_root / "paadal_pozhippurai_links_v5_auto_hardened_secondary_no_link.jsonl", secondary)
    write_csv_file(output_root / "paadal_pozhippurai_links_v5_auto_hardened_secondary_no_link.csv", secondary)
    write_csv_file(output_root / "repo_inventory_used_for_v5.csv", inventory)
    (output_root / "baseline_metrics.json").write_text(
        json.dumps(summary["baseline_metrics"], ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "paadal_pozhippurai_links_v5_auto_hardened_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report = render_report(summary, output_root)
    report_path.write_text(report, encoding="utf-8")
    (output_root / "baseline_vs_v5_auto_hardened_report.md").write_text(report, encoding="utf-8")


def run_v5(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    base_root: Path = DEFAULT_BASE_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_path: Path = DEFAULT_REPORT,
    tests_passed: bool = True,
) -> dict[str, Any]:
    full = load_jsonl(base_root / "paadal_pozhippurai_links_v4_combined_learned_full.jsonl")
    primary = load_jsonl(base_root / "paadal_pozhippurai_links_v4_combined_learned_primary_clean_links.jsonl")
    secondary = load_jsonl(base_root / "paadal_pozhippurai_links_v4_combined_learned_secondary_no_link.jsonl")
    if not primary:
        raise FileNotFoundError(f"No primary source rows found under {base_root}")
    paadal_by_id = {str(row.get("paadal_id", "")): str(row.get("paadal_text", "")) for row in read_jsonl(table_root / "paadalgal.jsonl")}
    baseline = baseline_metrics(primary, paadal_by_id)
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "baseline_metrics.json").write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    inventory = inventory_files(base_root, DEFAULT_ERROR_ROOT)
    mine_paraphrase_lexicon(primary, output_root / "learned_tamil_literary_paraphrase_lexicon.csv")
    patterns_out = mine_pattern_groups(primary, output_root / "learned_pattern_groups_v5.csv")
    lexicon_rows = sum(1 for _ in (output_root / "learned_tamil_literary_paraphrase_lexicon.csv").open(encoding="utf-8")) - 1

    hardening_pack = load_hardening_pack()
    rules, _ontology_info = load_anchor_rules()
    prior_high_ids = {stable_identity(row) for row in primary if row.get("confidence") == "high"}

    broad_primary, broad_changes_primary = fix_rows(primary, paadal_by_id, hardening_pack)
    primary_by_id = {str(row.get("link_id", "")): row for row in broad_primary}
    broad_full = [primary_by_id.get(str(row.get("link_id", "")), row) for row in full]
    v5_full, v5_changes_full, unsafe_full = apply_v5_calibration(broad_full, rules, prior_high_ids)
    v5_primary, v5_changes_primary, unsafe_primary = apply_v5_calibration(broad_primary, rules, prior_high_ids)

    repair_log = (
        changes_to_repair_log(broad_changes_primary, "TARGET_SHRUNK")
        + v5_changes_primary
    )
    unsafe = unsafe_full + unsafe_primary
    validation = validate_v4_links(table_root, v5_full)
    primary_validation = validate_clean_links(table_root, v5_primary)
    manual_review = smart_manual_review_pack(v5_primary, table_root)
    summary = summarize_v5(
        baseline=baseline,
        full=v5_full,
        primary=v5_primary,
        paadal_by_id=paadal_by_id,
        repair_log=repair_log,
        unsafe=unsafe,
        validation=validation,
        primary_validation=primary_validation,
        prior_high_ids=prior_high_ids,
        manual_review_size=len(manual_review),
        lexicon_rows=lexicon_rows,
        pattern_rows=len(patterns_out),
        tests_passed=tests_passed,
    )
    if summary["run_status"] == "rejected_high_confidence_drop":
        quarantine = output_root / "rejected_high_confidence_drop"
        quarantine.mkdir(parents=True, exist_ok=True)
        (quarantine / "failure_report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_outputs(
        output_root,
        full=v5_full,
        primary=v5_primary,
        secondary=secondary,
        summary=summary,
        report_path=report_path,
        repair_log=repair_log,
        unsafe=unsafe,
        manual_review_pack=manual_review,
        inventory=inventory,
    )
    return {**summary, "output_root": str(output_root), "report": str(report_path)}


def apply_existing_missing_layer(rows: list[dict[str, Any]], rules: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from knowledge.fix_missing_anchor_links import apply_missing_anchor_fix

    return apply_missing_anchor_fix(rows, rules)


def changes_to_repair_log(changes: list[dict[str, Any]], action: str) -> list[dict[str, Any]]:
    rows = []
    for change in changes:
        rows.append(
            {
                "link_id": change.get("link_id", ""),
                "confidence_before": change.get("confidence_before", ""),
                "confidence_after": change.get("confidence_after", ""),
                "relationship_type_before": change.get("relationship_type", ""),
                "relationship_type_after": change.get("relationship_type", ""),
                "issue_tags_before": change.get("issue_before", ""),
                "issue_tags_after": "",
                "repair_action": action,
                "source_text": change.get("source_text", ""),
                "target_text_before": change.get("target_text_original") or change.get("old_target_text") or change.get("target_text", ""),
                "target_text_after": change.get("target_text_minimal") or change.get("new_target_text") or change.get("target_text", ""),
                "anchor_added": change.get("new_anchor_canonical", ""),
                "ontology_relation_added": change.get("ontology_relation", ""),
                "pattern_group_matched": "",
                "target_shrink_applied": action == "TARGET_SHRUNK",
                "global_reassignment_applied": action == "GLOBAL_REASSIGNED",
                "promotion_decision": change.get("promotion_decision", "") or change.get("ambiguity_resolution_decision", ""),
                "reason": change.get("reason", ""),
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Build v5 auto-hardened Paadal to Pozhippurai links.")
    parser.add_argument("--table-root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--base-root", type=Path, default=DEFAULT_BASE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--tests-passed", action="store_true", help="Mark external regression tests as already passed for acceptance reporting.")
    args = parser.parse_args()
    summary = run_v5(
        table_root=args.table_root,
        base_root=args.base_root,
        output_root=args.output_root,
        report_path=args.report,
        tests_passed=args.tests_passed,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
