from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

from knowledge.build_pozhippurai_links_v4 import (
    DEFAULT_GOLD_SEED,
    DEFAULT_QA_BUNDLE,
    SCHEMA_VERSION as V4_SCHEMA_VERSION,
    build_v4_links,
    clean_primary_links,
    has_content_text,
    is_linked_row,
    is_positive_v4,
    secondary_no_link_rows,
    validate_clean_links,
    validate_v4_links,
    write_iob_v4,
)
from knowledge.link_thevaram_pozhippurai import (
    DEFAULT_ENTITY_ROOT,
    DEFAULT_SEED_DIR,
    DEFAULT_TABLE_ROOT,
    compact_text,
    normalize_text,
    read_jsonl,
    stable_hash,
    tokens,
)
from knowledge.link_thevaram_pozhippurai_v3 import (
    ALLOWED_RELATIONSHIPS,
    build_manual_review_pack,
    clean_phrase,
    write_csv_file,
    write_jsonl,
    write_tsv,
)

SCHEMA_VERSION = "thevaram-pozhppurai-paadallink-v4-hardened"
DEFAULT_HARDENING_PACK = Path("data/knowledge/paadal_pozhippurai_hardening/v4")
DEFAULT_V4_OUTPUT_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4")
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_hardened")
DEFAULT_REPORT = DEFAULT_OUTPUT_ROOT / "paadal_pozhippurai_links_v4_hardened_report.md"

CONFIDENCE_ORDER = {"no_link": 0, "low": 1, "medium": 2, "high": 3}
PUNCT_SPLIT_RE = re.compile(r"[,;.!?।\n]+")
TAMIL_WORD_RE = re.compile(r"[\u0B80-\u0BFF]+")
RELATIONSHIP_CUES = {
    "interprets_image": [
        "சூடி",
        "முடி",
        "சடை",
        "அணிந்த",
        "ஏறி",
        "பூசி",
        "தரித்த",
        "போர்த்த",
        "ஏந்தி",
        "பிறை",
        "கங்கை",
        "விடை",
        "அரவு",
    ],
    "theological_explanation": [
        "அருள்",
        "வினை",
        "நீங்கும்",
        "தொழ",
        "பணிந்து",
        "ஏத்தி",
        "வழிபட",
        "முத்தி",
        "பாசம்",
        "இன்பம்",
    ],
    "describes_entity": [
        "இறைவன்",
        "இறைவர்",
        "சிவபிரான்",
        "சிவபெருமான்",
        "பெருமான்",
        "தலைவன்",
        "உறை",
        "எழுந்தருளிய",
    ],
    "glosses_word": ["என்பது", "பொருள்", "அதாவது", "என்னும்"],
    "explains_phrase": ["என்பது", "என்னும்", "ஆகிய", "உடைய", "கொண்ட"],
    "explains_line": ["இப்பாடல்", "இவ்வாறு", "என்று", "முழுவதும்"],
}
POLYSEMY_TERMS = {"மதி", "விடை", "அரவு", "பதி", "அடி", "மலம்", "பசு"}
SAFE_ORDER_ONLY_NOTES = (
    "mainly supported by poem/commentary order",
    "share little surface vocabulary",
)


@dataclass(frozen=True)
class SemanticLexiconEntry:
    lexicon_id: str
    semantic_domain: str
    canonical_concept: str
    paadal_cues: tuple[str, ...]
    pozhppurai_cues: tuple[str, ...]
    relationship_bias: str
    ontology_relation: str
    suggested_weight: float


@dataclass(frozen=True)
class MorphologyRule:
    rule_id: str
    rule_type: str
    source_patterns: tuple[str, ...]
    target_variants: tuple[str, ...]
    score_value: float


@dataclass(frozen=True)
class OntologyCue:
    cue_id: str
    relation: str
    paadal_cues: tuple[str, ...]
    pozhppurai_cues: tuple[str, ...]
    relationship_bias: str
    score_value: float


@dataclass(frozen=True)
class EntityExpansion:
    entity_type: str
    subtype_l1: str
    subtype_l2: str
    canonical: str
    aliases: tuple[str, ...]
    linker_use: str


@dataclass(frozen=True)
class HardeningPack:
    semantic_lexicon: tuple[SemanticLexiconEntry, ...]
    morphology_rules: tuple[MorphologyRule, ...]
    ontology_cues: tuple[OntologyCue, ...]
    entity_expansions: tuple[EntityExpansion, ...]
    alignment_config: dict[str, Any]
    ambiguous_config: dict[str, Any]
    scoring_spec: dict[str, Any]
    review_policy: tuple[dict[str, str], ...]
    uploaded_review_samples: tuple[dict[str, str], ...]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def split_pipe(value: str) -> tuple[str, ...]:
    return tuple(clean_phrase(part) for part in (value or "").split("|") if clean_phrase(part))


def parse_score_effect(value: str, default: float) -> float:
    match = re.search(r"[-+]?\d+(?:\.\d+)?", value or "")
    if not match:
        return default
    return abs(float(match.group(0)))


def load_hardening_pack(pack_root: Path = DEFAULT_HARDENING_PACK) -> HardeningPack:
    semantic_rows = read_csv(pack_root / "01_surface_vocab_gap_semantic_lexicon.csv")
    morphology_rows = read_csv(pack_root / "01_morphology_aware_matching_rules.csv")
    ontology_rows = read_csv(pack_root / "01_ontology_relation_cues.csv")
    entity_rows = read_csv(pack_root / "03_entity_annotation_hierarchy_expansion.csv")
    policy_rows = read_csv(pack_root / "06_review_category_policy.csv")
    review_rows = read_csv(pack_root / "07_uploaded_review_samples_enriched_for_codex.csv")
    alignment_config = json.loads((pack_root / "02_order_only_support_alignment_algorithms.json").read_text(encoding="utf-8"))
    ambiguous_config = json.loads((pack_root / "04_ambiguous_multiple_targets_resolution_config.json").read_text(encoding="utf-8"))
    scoring_spec = json.loads((pack_root / "05_scoring_feature_spec.json").read_text(encoding="utf-8"))
    return HardeningPack(
        semantic_lexicon=tuple(
            SemanticLexiconEntry(
                lexicon_id=row.get("lexicon_id", ""),
                semantic_domain=row.get("semantic_domain", ""),
                canonical_concept=row.get("canonical_concept", ""),
                paadal_cues=split_pipe(row.get("paadal_cues", "")),
                pozhppurai_cues=split_pipe(row.get("pozhppurai_cues", "")),
                relationship_bias=row.get("relationship_bias", ""),
                ontology_relation=row.get("ontology_relation", ""),
                suggested_weight=float(row.get("suggested_weight") or 0.1),
            )
            for row in semantic_rows
        ),
        morphology_rules=tuple(
            MorphologyRule(
                rule_id=row.get("rule_id", ""),
                rule_type=row.get("rule_type", ""),
                source_patterns=split_pipe(row.get("source_pattern", "")),
                target_variants=split_pipe(row.get("target_variants", "")),
                score_value=parse_score_effect(row.get("score_effect", ""), 0.06),
            )
            for row in morphology_rows
        ),
        ontology_cues=tuple(
            OntologyCue(
                cue_id=row.get("cue_id", ""),
                relation=row.get("relation", ""),
                paadal_cues=split_pipe(row.get("paadal_cues", "")),
                pozhppurai_cues=split_pipe(row.get("pozhppurai_cues", "")),
                relationship_bias=row.get("relationship_bias", ""),
                score_value=parse_score_effect(row.get("score_effect", ""), 0.1),
            )
            for row in ontology_rows
        ),
        entity_expansions=tuple(
            EntityExpansion(
                entity_type=row.get("entity_type", ""),
                subtype_l1=row.get("subtype_l1", ""),
                subtype_l2=row.get("subtype_l2", ""),
                canonical=row.get("canonical", ""),
                aliases=split_pipe(row.get("aliases", "")),
                linker_use=row.get("linker_use", ""),
            )
            for row in entity_rows
        ),
        alignment_config=alignment_config,
        ambiguous_config=ambiguous_config,
        scoring_spec=scoring_spec,
        review_policy=tuple(policy_rows),
        uploaded_review_samples=tuple(review_rows),
    )


def compact_contains(text: str, cue: str) -> bool:
    text_norm = cached_normalize(text)
    cue_norm = clean_phrase(cue)
    if not cue_norm:
        return False
    return cue_norm in text_norm or cached_compact(cue_norm) in cached_compact(text_norm)


@lru_cache(maxsize=200_000)
def cached_normalize(value: str) -> str:
    return normalize_text(value)


@lru_cache(maxsize=200_000)
def cached_compact(value: str) -> str:
    return compact_text(value)


def cue_expression_present(text: str, expression: str) -> bool:
    expression = clean_phrase(expression)
    if not expression:
        return False
    groups = [group.strip() for group in expression.split("+") if group.strip()]
    if not groups:
        return False
    for group in groups:
        alternatives = [clean_phrase(part) for part in group.split("|") if clean_phrase(part)]
        if alternatives and not any(compact_contains(text, alt) for alt in alternatives):
            return False
    return True


def any_cue_present(text: str, cues: Iterable[str]) -> bool:
    return any(cue_expression_present(text, cue) for cue in cues)


def token_overlap_score(source: str, target: str) -> float:
    source_tokens = set(tokens(source))
    target_tokens = set(tokens(target))
    if not source_tokens or not target_tokens:
        return 0.0
    return len(source_tokens & target_tokens) / max(1, len(source_tokens | target_tokens))


def char_ngram_score(source: str, target: str, n: int = 3) -> float:
    source_compact = compact_text(source)
    target_compact = compact_text(target)
    if len(source_compact) < n or len(target_compact) < n:
        return 0.0
    source_grams = {source_compact[index : index + n] for index in range(len(source_compact) - n + 1)}
    target_grams = {target_compact[index : index + n] for index in range(len(target_compact) - n + 1)}
    if not source_grams or not target_grams:
        return 0.0
    return len(source_grams & target_grams) / max(1, len(source_grams | target_grams))


def semantic_lexicon_score(source: str, target: str, relationship: str, pack: HardeningPack) -> tuple[float, list[str]]:
    matched: list[str] = []
    score = 0.0
    for entry in pack.semantic_lexicon:
        if any_cue_present(source, entry.paadal_cues) and any_cue_present(target, entry.pozhppurai_cues):
            bias_bonus = 0.05 if entry.relationship_bias == relationship else 0.0
            score += entry.suggested_weight + bias_bonus
            matched.append(entry.lexicon_id)
    return min(1.0, score), matched


def morphology_stem_score(source: str, target: str, pack: HardeningPack) -> tuple[float, list[str]]:
    matched: list[str] = []
    score = 0.0
    for rule in pack.morphology_rules:
        if any_cue_present(source, rule.source_patterns) and any_cue_present(target, rule.target_variants):
            score += rule.score_value
            matched.append(rule.rule_id)
    return min(1.0, score), matched


def ontology_relation_score(source: str, target: str, relationship: str, pack: HardeningPack) -> tuple[float, list[str]]:
    matched: list[str] = []
    score = 0.0
    for cue in pack.ontology_cues:
        if any_cue_present(source, cue.paadal_cues) and any_cue_present(target, cue.pozhppurai_cues):
            bias_bonus = 0.05 if cue.relationship_bias == relationship else 0.0
            score += cue.score_value + bias_bonus
            matched.append(cue.cue_id)
    return min(1.0, score), matched


def entity_anchors(text: str, pack: HardeningPack) -> set[str]:
    anchors: set[str] = set()
    text_norm = cached_normalize(text)
    text_compact = cached_compact(text_norm)
    for entry in pack.entity_expansions:
        for alias in entry.aliases + (entry.canonical,):
            alias_norm = clean_phrase(alias)
            if alias_norm and (alias_norm in text_norm or cached_compact(alias_norm) in text_compact):
                anchors.add(f"{entry.entity_type}.{entry.subtype_l1}.{entry.canonical}")
                break
    return anchors


def entity_anchor_score(source: str, target: str, pack: HardeningPack) -> tuple[float, list[str]]:
    source_anchors = entity_anchors(source, pack)
    target_anchors = entity_anchors(target, pack)
    shared = sorted(source_anchors & target_anchors)
    if shared:
        return min(1.0, 0.35 + 0.15 * len(shared)), shared
    source_families = {anchor.split(".", 1)[0] for anchor in source_anchors}
    target_families = {anchor.split(".", 1)[0] for anchor in target_anchors}
    family_shared = sorted(source_families & target_families)
    if family_shared:
        return min(0.45, 0.2 + 0.08 * len(family_shared)), family_shared
    return 0.0, []


def relationship_cue_score(source: str, target: str, relationship: str) -> float:
    cues = RELATIONSHIP_CUES.get(relationship, [])
    if not cues:
        return 0.0
    joined = f"{source} {target}"
    matches = sum(1 for cue in cues if compact_contains(joined, cue))
    return min(1.0, matches / 4)


def target_granularity_score(source: str, target: str, relationship: str) -> float:
    source_count = max(1, len(tokens(source)))
    target_count = max(1, len(tokens(target)))
    ratio = target_count / source_count
    if relationship == "explains_line":
        return 0.8 if ratio <= 8 else 0.5
    if ratio <= 2.5:
        return 1.0
    if ratio <= 4:
        return 0.6
    return 0.25


def field_preference_score(target_field: str) -> float:
    return 1.0 if target_field == "pozhppurai" else 0.85 if target_field == "kurippurai" else 0.5


def gold_pattern_similarity(row: dict[str, Any], source: str, target: str) -> float:
    method = str(row.get("method", ""))
    note = str(row.get("diagnostic_note", ""))
    if method.startswith("v4_gold"):
        return 1.0
    if "Focused QA rule matched" in note:
        return 0.9
    if row.get("confidence") == "high" and float(row.get("score") or 0) >= 0.75:
        return 0.75
    if token_overlap_score(source, target) >= 0.35:
        return 0.35
    return 0.0


def base_features(
    row: dict[str, Any],
    source: str,
    target: str,
    target_field: str,
    pack: HardeningPack,
) -> tuple[dict[str, float], list[str], list[str]]:
    relationship = str(row.get("relationship_type", ""))
    semantic_score, semantic_rules = semantic_lexicon_score(source, target, relationship, pack)
    morph_score, morph_rules = morphology_stem_score(source, target, pack)
    ontology_score, ontology_rules = ontology_relation_score(source, target, relationship, pack)
    entity_score, shared_anchors = entity_anchor_score(source, target, pack)
    features = {
        "surface_token_overlap": round(token_overlap_score(source, target), 4),
        "char_ngram_overlap": round(char_ngram_score(source, target), 4),
        "semantic_lexicon_score": round(semantic_score, 4),
        "morphology_stem_score": round(morph_score, 4),
        "shared_entity_anchor_score": round(entity_score, 4),
        "ontology_relation_score": round(ontology_score, 4),
        "relationship_cue_score": round(relationship_cue_score(source, target, relationship), 4),
        "sequence_consistency_score": 0.0,
        "neighbor_anchor_score": 0.0,
        "gold_pattern_similarity": round(gold_pattern_similarity(row, source, target), 4),
        "target_granularity_score": round(target_granularity_score(source, target, relationship), 4),
        "field_preference_score": round(field_preference_score(target_field), 4),
    }
    return features, semantic_rules + morph_rules + ontology_rules, shared_anchors


def feature_weights(pack: HardeningPack) -> dict[str, float]:
    return {
        str(feature.get("name")): float(feature.get("weight") or 0)
        for feature in pack.scoring_spec.get("features", [])
        if feature.get("name")
    }


def penalty_values(pack: HardeningPack) -> dict[str, float]:
    return {
        str(penalty.get("name")): float(penalty.get("value") or 0)
        for penalty in pack.scoring_spec.get("penalties", [])
        if penalty.get("name")
    }


def only_order_supported(features: dict[str, float], row: dict[str, Any]) -> bool:
    support = (
        features.get("semantic_lexicon_score", 0)
        + features.get("morphology_stem_score", 0)
        + features.get("shared_entity_anchor_score", 0)
        + features.get("ontology_relation_score", 0)
        + features.get("relationship_cue_score", 0)
        + features.get("neighbor_anchor_score", 0)
    )
    note = str(row.get("diagnostic_note", ""))
    return support < 0.2 and any(fragment in note for fragment in SAFE_ORDER_ONLY_NOTES)


def score_margin(row: dict[str, Any]) -> float:
    raw_features = row.get("features") if isinstance(row.get("features"), dict) else {}
    try:
        return float(raw_features.get("score_margin", 1.0))
    except (TypeError, ValueError):
        return 1.0


def target_too_broad(source: str, target: str, relationship: str) -> bool:
    source_count = max(1, len(tokens(source)))
    target_count = len(tokens(target))
    return relationship != "explains_line" and target_count / source_count > 3.0


def polysemy_without_context(source: str, target: str, features: dict[str, float]) -> bool:
    if not any(compact_contains(source, term) for term in POLYSEMY_TERMS):
        return False
    return (
        features.get("ontology_relation_score", 0)
        + features.get("relationship_cue_score", 0)
        + features.get("shared_entity_anchor_score", 0)
        < 0.25
    )


def apply_penalties(
    row: dict[str, Any],
    features: dict[str, float],
    source: str,
    target: str,
    pack: HardeningPack,
) -> tuple[float, list[str], list[str]]:
    values = penalty_values(pack)
    penalties: list[str] = []
    critical: list[str] = []
    relationship = str(row.get("relationship_type", ""))
    if only_order_supported(features, row):
        penalties.append("order_only_penalty")
        critical.append("order_only_support")
    margin = score_margin(row)
    note = str(row.get("diagnostic_note", ""))
    ambiguous_threshold = float(pack.ambiguous_config.get("margin_thresholds", {}).get("ambiguous_if_margin_below", 0.08))
    ambiguity_context = "best target is close" in note or (
        row.get("confidence") == "low" and margin < float(pack.ambiguous_config.get("manual_review_trigger", {}).get("if_best_second_margin_below", 0.05))
    )
    if ambiguity_context and margin < ambiguous_threshold:
        penalties.append("ambiguous_margin_penalty")
        if margin < float(pack.ambiguous_config.get("manual_review_trigger", {}).get("if_best_second_margin_below", 0.05)):
            critical.append("best_second_margin_below_review_threshold")
    if features.get("shared_entity_anchor_score", 0) == 0 and features.get("ontology_relation_score", 0) == 0:
        penalties.append("missing_entity_anchor_penalty")
    if target_too_broad(source, target, relationship):
        penalties.append("target_too_broad_penalty")
    if polysemy_without_context(source, target, features):
        penalties.append("polysemy_without_context_penalty")
    total = sum(values.get(name, 0) for name in penalties)
    return total, penalties, critical


def final_score_and_confidence(
    row: dict[str, Any],
    features: dict[str, float],
    source: str,
    target: str,
    pack: HardeningPack,
) -> tuple[float, str, list[str], list[str]]:
    if not is_linked_row(row):
        return 0.0, "no_link", ["empty_pozhippurai_penalty"], ["no_usable_target"]
    weights = feature_weights(pack)
    weighted_features = sum(weights.get(name, 0.0) * value for name, value in features.items())
    base_score = float(row.get("score") or 0.0)
    penalty_total, penalties, critical = apply_penalties(row, features, source, target, pack)
    final_score = max(0.0, min(0.99, (0.45 * base_score) + (1.9 * weighted_features) + 0.04 - penalty_total))
    relation_support = (
        features.get("semantic_lexicon_score", 0)
        + features.get("ontology_relation_score", 0)
        + features.get("relationship_cue_score", 0)
        + features.get("shared_entity_anchor_score", 0)
    )
    if final_score >= 0.78 and not critical and relation_support >= 0.35:
        confidence = "high"
    elif final_score >= 0.5:
        confidence = "medium"
    elif final_score >= 0.25:
        confidence = "low"
    else:
        confidence = "low"
    if "order_only_support" in critical and confidence == "high":
        confidence = "low"
    if "ambiguous_margin_penalty" in penalties and confidence == "high":
        confidence = "medium"
    if row.get("confidence") == "high" and features.get("gold_pattern_similarity", 0) >= 0.75 and not critical:
        final_score = max(final_score, 0.82)
        confidence = "high"
    return round(final_score, 4), confidence, penalties, critical


def target_candidates(full_text: str, *, center: int | None = None, window: int = 500) -> list[tuple[int, int, str]]:
    candidates: list[tuple[int, int, str]] = []
    lower = 0 if center is None else max(0, center - window)
    upper = len(full_text) if center is None else min(len(full_text), center + window)
    for match in re.finditer(r"[^,;.!?।\n]+", full_text):
        if match.end() < lower or match.start() > upper:
            continue
        text = clean_phrase(match.group(0))
        if has_content_text(text):
            start = full_text.find(text, match.start(), match.end())
            if start >= 0:
                candidates.append((start, start + len(text), text))
    return candidates


def should_rerank(row: dict[str, Any]) -> bool:
    if not is_linked_row(row):
        return False
    if str(row.get("method", "")).startswith("v4_gold"):
        return False
    note = str(row.get("diagnostic_note", ""))
    return row.get("confidence") == "low" and any(
        fragment in note
        for fragment in (
            "mainly supported by poem/commentary order",
            "best target is close",
        )
    )


def rerank_target(
    row: dict[str, Any],
    commentary: dict[str, Any],
    pack: HardeningPack,
) -> tuple[dict[str, Any], bool]:
    if not should_rerank(row):
        return row, False
    target_field = str(row.get("target_field") or "pozhppurai")
    full_text = str(commentary.get(target_field, ""))
    if not full_text:
        return row, False
    source = str(row.get("source_text", ""))
    current_target = str(row.get("target_text", ""))
    current_features, _, _ = base_features(row, source, current_target, target_field, pack)
    current_signal = sum(current_features.values())
    best: tuple[float, int, int, str, dict[str, float]] | None = None
    center = int(row.get("target_start_char") or 0) if row.get("target_start_char") is not None else None
    for start, end, candidate in target_candidates(full_text, center=center):
        if len(tokens(candidate)) > max(18, len(tokens(source)) * 6):
            continue
        features, _, _ = base_features(row, source, candidate, target_field, pack)
        signal = (
            features["semantic_lexicon_score"] * 2.0
            + features["ontology_relation_score"] * 2.0
            + features["shared_entity_anchor_score"] * 1.5
            + features["relationship_cue_score"]
            + features["surface_token_overlap"]
            + features["char_ngram_overlap"] * 0.5
            + features["target_granularity_score"] * 0.2
        )
        if best is None or signal > best[0]:
            best = (signal, start, end, candidate, features)
    if best is None:
        return row, False
    best_signal, start, end, candidate, _features = best
    if candidate == current_target:
        return row, False
    if best_signal < current_signal + 0.35:
        return row, False
    item = dict(row)
    item["target_start_char"] = start
    item["target_end_char"] = end
    item["target_text"] = candidate
    item["link_id"] = "ppl_v4h_" + stable_hash(row.get("link_id", ""), source, target_field, start, end)
    item["method"] = "v4_hardened_global_sequence_rerank"
    item["diagnostic_note"] = f"{row.get('diagnostic_note', '')} Hardened reranker selected a more compact semantic/ontology-supported target."
    return item, True


def group_direction(rows: list[dict[str, Any]]) -> str:
    ordered = [
        row
        for row in sorted(rows, key=lambda item: int(item.get("source_start_char") or 0))
        if row.get("target_start_char") is not None
    ]
    if len(ordered) < 3:
        return "forward"
    forward = 0
    reverse = 0
    for left, right in zip(ordered, ordered[1:]):
        left_target = int(left.get("target_start_char") or 0)
        right_target = int(right.get("target_start_char") or 0)
        if right_target >= left_target:
            forward += 1
        else:
            reverse += 1
    return "reverse" if reverse > forward else "forward"


def sequence_scores(rows: list[dict[str, Any]]) -> dict[str, tuple[float, float, str]]:
    ordered = sorted(rows, key=lambda item: int(item.get("source_start_char") or 0))
    direction = group_direction(ordered)
    scores: dict[str, tuple[float, float, str]] = {}
    for index, row in enumerate(ordered):
        if row.get("target_start_char") is None:
            scores[str(row.get("link_id"))] = (0.0, 0.0, "rule_or_unavailable")
            continue
        target = int(row.get("target_start_char") or 0)
        previous_target = (
            int(ordered[index - 1].get("target_start_char") or 0)
            if index > 0 and ordered[index - 1].get("target_start_char") is not None
            else None
        )
        next_target = (
            int(ordered[index + 1].get("target_start_char") or 0)
            if index + 1 < len(ordered) and ordered[index + 1].get("target_start_char") is not None
            else None
        )
        comparisons = 0
        coherent = 0
        if previous_target is not None:
            comparisons += 1
            coherent += int(target >= previous_target if direction == "forward" else target <= previous_target)
        if next_target is not None:
            comparisons += 1
            coherent += int(target <= next_target if direction == "forward" else target >= next_target)
        sequence_score = coherent / comparisons if comparisons else 0.5
        neighbor_score = 0.0
        if previous_target is not None and next_target is not None:
            lower, upper = sorted((previous_target, next_target))
            neighbor_score = 1.0 if lower <= target <= upper else 0.25
        elif comparisons:
            neighbor_score = sequence_score * 0.6
        method = "reverse_order_alignment" if direction == "reverse" else "global_sequence_assignment"
        scores[str(row.get("link_id"))] = (round(sequence_score, 4), round(neighbor_score, 4), method)
    return scores


def harden_links(
    links: list[dict[str, Any]],
    *,
    table_root: Path,
    pack: HardeningPack,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    commentary_rows = read_jsonl(table_root / "commentaries.jsonl")
    commentary_by_id = {str(row.get("commentary_id", "")): row for row in commentary_rows}
    reranked = 0
    prepared: list[dict[str, Any]] = []
    for row in links:
        item = dict(row)
        item["schema_version"] = SCHEMA_VERSION
        item["base_schema_version"] = V4_SCHEMA_VERSION
        item["base_link_id"] = row.get("link_id", "")
        item["target_field_preference"] = item.get("target_field") or "pozhppurai"
        commentary = commentary_by_id.get(str(item.get("commentary_id", "")), {})
        item, changed = rerank_target(item, commentary, pack)
        if changed:
            reranked += 1
        prepared.append(item)

    by_paadal: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in prepared:
        by_paadal[str(row.get("paadal_id", ""))].append(row)
    seq_lookup: dict[str, tuple[float, float, str]] = {}
    for group in by_paadal.values():
        seq_lookup.update(sequence_scores([row for row in group if is_linked_row(row)]))

    hardened: list[dict[str, Any]] = []
    semantic_improved = 0
    entity_improved = 0
    sequence_improved = 0
    ambiguous_manual = 0
    for row in prepared:
        source = str(row.get("source_text", ""))
        target = str(row.get("target_text", ""))
        target_field = str(row.get("target_field") or "pozhppurai")
        features, rule_ids, shared_anchors = base_features(row, source, target, target_field, pack)
        sequence_score, neighbor_score, sequence_method = seq_lookup.get(str(row.get("link_id")), (0.0, 0.0, "rule_or_unavailable"))
        features["sequence_consistency_score"] = sequence_score
        features["neighbor_anchor_score"] = neighbor_score
        final_score, confidence, penalties, critical = final_score_and_confidence(row, features, source, target, pack)
        old_score = float(row.get("score") or 0.0)
        old_confidence = str(row.get("confidence", ""))
        manual_review = bool(row.get("manual_review_required")) or confidence == "low" or bool(critical)
        if "ambiguous_margin_penalty" in penalties:
            ambiguous_manual += int(manual_review)
        item = dict(row)
        item.update(
            {
                "schema_version": SCHEMA_VERSION,
                "confidence": confidence,
                "score": final_score,
                "previous_confidence": old_confidence,
                "previous_score": old_score,
                "feature_scores": features,
                "penalties_applied": penalties,
                "critical_warnings": critical,
                "rule_ids_applied": list(row.get("rule_ids_applied") or []) + rule_ids,
                "sequence_alignment_method": sequence_method,
                "expanded_entity_anchors": shared_anchors,
                "manual_review_required": manual_review,
                "hardened_score_delta": round(final_score - old_score, 4),
            }
        )
        if features["semantic_lexicon_score"] > 0:
            semantic_improved += 1
        if features["shared_entity_anchor_score"] > 0:
            entity_improved += 1
        if sequence_score > 0.75 or row.get("method") == "v4_hardened_global_sequence_rerank":
            sequence_improved += 1
        hardened.append(item)

    return hardened, {
        "semantic_lexicon_improved_rows": semantic_improved,
        "entity_anchor_expansion_improved_rows": entity_improved,
        "sequence_alignment_improved_rows": sequence_improved,
        "target_reranked_rows": reranked,
        "ambiguous_rows_still_requiring_manual_review": ambiguous_manual,
    }


def confidence_rank(row: dict[str, Any]) -> tuple[int, float, int]:
    return (
        CONFIDENCE_ORDER.get(str(row.get("confidence")), 0),
        float(row.get("score") or 0),
        0 if row.get("manual_review_required") else 1,
    )


def dedupe_primary_hardened(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best_by_source: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in rows:
        key = (row.get("paadal_id"), row.get("source_start_char"), row.get("source_end_char"))
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


def summarize_hardened(
    links: list[dict[str, Any]],
    primary_clean: list[dict[str, Any]],
    secondary_no_link: list[dict[str, Any]],
    pack: HardeningPack,
    improvement_counts: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "hardening_pack_root": str(DEFAULT_HARDENING_PACK),
        "semantic_lexicon_entries": len(pack.semantic_lexicon),
        "morphology_rules": len(pack.morphology_rules),
        "ontology_relation_cues": len(pack.ontology_cues),
        "entity_expansion_entries": len(pack.entity_expansions),
        "uploaded_review_samples": len(pack.uploaded_review_samples),
        "total_links": len(links),
        "primary_clean_links": len(primary_clean),
        "secondary_no_link_rows": len(secondary_no_link),
        "secondary_no_link_reasons": dict(sorted(Counter(str(row.get("secondary_table_reason", "")) for row in secondary_no_link).items())),
        "links_by_confidence": dict(sorted(Counter(str(row.get("confidence", "")) for row in links).items())),
        "primary_links_by_confidence": dict(sorted(Counter(str(row.get("confidence", "")) for row in primary_clean).items())),
        "links_by_relationship_type": dict(sorted(Counter(str(row.get("relationship_type", "")) for row in links).items())),
        "links_by_sequence_alignment_method": dict(sorted(Counter(str(row.get("sequence_alignment_method", "")) for row in links).items())),
        "manual_review_required_count": sum(1 for row in links if row.get("manual_review_required")),
        "no_link_count": sum(1 for row in links if row.get("confidence") == "no_link"),
        "empty_pozhippurai_rows_excluded": sum(1 for row in secondary_no_link if row.get("secondary_table_reason") == "empty_pozhippurai"),
        **improvement_counts,
    }


def render_report(summary: dict[str, Any], validation: dict[str, Any], output_root: Path) -> str:
    def table(mapping: dict[str, Any]) -> str:
        return "\n".join(f"| `{key}` | {value} |" for key, value in mapping.items()) or "| None | 0 |"

    return f"""# Thevaram Paadal-Pozhippurai Linker v4 Hardened Report

## Summary

- Output root: `{output_root}`
- Schema version: `{summary['schema_version']}`
- Full corpus links: `{summary['total_links']}`
- Primary clean linked rows: `{summary['primary_clean_links']}`
- Secondary no-link rows: `{summary['secondary_no_link_rows']}`
- Empty pozhppurai rows excluded: `{summary['empty_pozhippurai_rows_excluded']}`
- Manual review required: `{summary['manual_review_required_count']}`
- Validation status: `{validation['status']}`
- Semantic lexicon improved rows: `{summary['semantic_lexicon_improved_rows']}`
- Entity anchor expansion improved rows: `{summary['entity_anchor_expansion_improved_rows']}`
- Sequence alignment improved rows: `{summary['sequence_alignment_improved_rows']}`
- Target reranked rows: `{summary['target_reranked_rows']}`
- Ambiguous rows still requiring manual review: `{summary['ambiguous_rows_still_requiring_manual_review']}`

## Hardening Pack Loaded

- Semantic lexicon entries: `{summary['semantic_lexicon_entries']}`
- Morphology rules: `{summary['morphology_rules']}`
- Ontology relation cues: `{summary['ontology_relation_cues']}`
- Entity expansion entries: `{summary['entity_expansion_entries']}`
- Uploaded review samples: `{summary['uploaded_review_samples']}`

## Confidence Distribution

| Confidence | Rows |
| --- | ---: |
{table(summary['links_by_confidence'])}

## Primary Clean Confidence Distribution

| Confidence | Rows |
| --- | ---: |
{table(summary['primary_links_by_confidence'])}

## Relationship Distribution

| Relationship | Rows |
| --- | ---: |
{table(summary['links_by_relationship_type'])}

## Sequence Alignment Methods

| Method | Rows |
| --- | ---: |
{table(summary['links_by_sequence_alignment_method'])}

## Secondary No-Link Reasons

| Reason | Rows |
| --- | ---: |
{table(summary['secondary_no_link_reasons'])}

## Notes

- Existing v3 and v4 outputs are not overwritten.
- The hardened layer recalibrates and reranks for RAG/retrieval readiness; it is not a claim of final scholarly gold accuracy.
- Order-only support is capped and routed to review unless semantic, entity, ontology, relation, or neighbour evidence supports the target.
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
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_hardened_full.jsonl", links)
    write_tsv(output_root / "paadal_pozhippurai_links_v4_hardened_full.tsv", links)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_hardened_primary_clean_links.jsonl", primary_clean)
    write_tsv(output_root / "paadal_pozhippurai_links_v4_hardened_primary_clean_links.tsv", primary_clean)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_hardened_primary_clean_links.csv", primary_clean)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_hardened_secondary_no_link.jsonl", secondary_no_link)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_hardened_secondary_no_link.csv", secondary_no_link)
    high = [row for row in links if row.get("confidence") == "high" and not row.get("manual_review_required")]
    medium = [row for row in links if row.get("confidence") == "medium" and not row.get("manual_review_required")]
    low = [row for row in links if row.get("confidence") == "low" or row.get("manual_review_required")]
    no_link = [row for row in links if row.get("confidence") == "no_link" or row.get("relationship_type") == "unlinked"]
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_hardened_high_confidence.jsonl", high)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_hardened_medium_confidence.jsonl", medium)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_hardened_low_confidence_review.csv", low)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_hardened_no_link_or_unresolved.csv", no_link)
    write_iob_v4(output_root / "paadal_pozhippurai_links_v4_hardened_corrected_usable.iob.conll", [row for row in links if is_positive_v4(row)])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_hardened_manual_review_pack.csv", build_manual_review_pack(links))
    (output_root / "paadal_pozhippurai_links_v4_hardened_summary.json").write_text(
        json.dumps({**summary, "validation": validation}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary, validation, output_root), encoding="utf-8")


def run_linking_v4_hardened(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    entity_root: Path = DEFAULT_ENTITY_ROOT,
    seed_dir: Path = DEFAULT_SEED_DIR,
    qa_bundle: Path = DEFAULT_QA_BUNDLE,
    gold_seed: Path = DEFAULT_GOLD_SEED,
    hardening_pack: Path = DEFAULT_HARDENING_PACK,
    v4_output_root: Path = DEFAULT_V4_OUTPUT_ROOT,
    rebuild_base_v4: bool = False,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    pack = load_hardening_pack(hardening_pack)
    existing_v4_full = v4_output_root / "paadal_pozhippurai_links_v4_full.jsonl"
    if existing_v4_full.exists() and not rebuild_base_v4:
        links = read_jsonl(existing_v4_full)
    else:
        links, _summary = build_v4_links(
            table_root=table_root,
            entity_root=entity_root,
            seed_dir=seed_dir,
            qa_bundle=qa_bundle,
            gold_seed=gold_seed,
        )
    links, improvement_counts = harden_links(links, table_root=table_root, pack=pack)
    paadal_rows = read_jsonl(table_root / "paadalgal.jsonl")
    commentary_rows = read_jsonl(table_root / "commentaries.jsonl")
    primary_clean = dedupe_primary_hardened(
        clean_primary_links(links, paadal_rows=paadal_rows, commentary_rows=commentary_rows)
    )
    secondary_no_link = secondary_no_link_rows(links, commentary_rows)
    validation = validate_v4_links(table_root, links)
    primary_validation = validate_clean_links(table_root, primary_clean)
    summary = summarize_hardened(links, primary_clean, secondary_no_link, pack, improvement_counts)
    summary["primary_validation"] = primary_validation
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
    parser = argparse.ArgumentParser(description="Create hardened Thevaram paadal-pozhppurai v4 links.")
    parser.add_argument("--input-root", "--table-root", dest="table_root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--entity-root", type=Path, default=DEFAULT_ENTITY_ROOT)
    parser.add_argument("--seed-dir", type=Path, default=DEFAULT_SEED_DIR)
    parser.add_argument("--qa-bundle", type=Path, default=DEFAULT_QA_BUNDLE)
    parser.add_argument("--gold-seed", type=Path, default=DEFAULT_GOLD_SEED)
    parser.add_argument("--hardening-pack", type=Path, default=DEFAULT_HARDENING_PACK)
    parser.add_argument("--v4-output-root", type=Path, default=DEFAULT_V4_OUTPUT_ROOT)
    parser.add_argument("--rebuild-base-v4", action="store_true")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = run_linking_v4_hardened(
        table_root=args.table_root,
        entity_root=args.entity_root,
        seed_dir=args.seed_dir,
        qa_bundle=args.qa_bundle,
        gold_seed=args.gold_seed,
        hardening_pack=args.hardening_pack,
        v4_output_root=args.v4_output_root,
        rebuild_base_v4=args.rebuild_base_v4,
        output_root=args.output_root,
        report_path=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["validation"]["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
