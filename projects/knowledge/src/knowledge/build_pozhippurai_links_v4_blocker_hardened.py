from __future__ import annotations

import argparse
import csv
import json
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
    is_linked_row,
    is_positive_v4,
    secondary_no_link_rows,
    validate_clean_links,
    validate_v4_links,
    write_iob_v4,
)
from knowledge.build_pozhippurai_links_v4_hardened import (
    char_ngram_score,
    confidence_rank,
    dedupe_primary_hardened,
    sequence_scores,
    target_granularity_score,
    token_overlap_score,
)
from knowledge.link_thevaram_pozhippurai import (
    DEFAULT_ENTITY_ROOT,
    DEFAULT_SEED_DIR,
    DEFAULT_TABLE_ROOT,
    compact_text,
    read_jsonl,
    tokens,
)
from knowledge.link_thevaram_pozhippurai_v3 import (
    ALLOWED_RELATIONSHIPS,
    build_manual_review_pack,
    clean_phrase,
    write_csv_file,
    write_jsonl,
)

SCHEMA_VERSION = "thevaram-pozhppurai-paadallink-v4-blocker-hardened"
DEFAULT_BLOCKER_PACK = Path("/Users/bhaveenthankajanikanth/Downloads/paadal_pozhippurai_v4_blocker_review_pack")
DEFAULT_V4_OUTPUT_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_hardened")
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_blocker_hardened")
DEFAULT_REPORT = DEFAULT_OUTPUT_ROOT / "paadal_pozhippurai_links_v4_blocker_hardened_report.md"

CONFIDENCE_ORDER = {"no_link": 0, "low": 1, "medium": 2, "high": 3}
SPLIT_RE = re.compile(r"[,;.!?\"'“”‘’\-।\n]+")
TAMIL_SUFFIX_RE = re.compile(r"(களையும்|ங்களையும்|த்தையும்|த்தினை|ங்களை|களை|மும்|மும்|யும்|வும்|ஆல்|இல்|ஐ|து|தை|ம்)$")
FRAGMENT_SOURCE_TOKENS = {"நகரே", "இலரே", "அல்லனே"}
ALLOWED_BLOCKER_RELATIONSHIPS = {
    "explains_line",
    "explains_phrase",
    "glosses_word",
    "interprets_image",
    "theological_explanation",
    "describes_entity",
}
REQUIRED_FEATURE_FIELDS = [
    "surface_token_overlap",
    "char_ngram_overlap",
    "semantic_lexicon_score",
    "morphology_stem_score",
    "shared_entity_anchor_score",
    "expanded_entity_anchor_score",
    "ontology_relation_score",
    "relationship_cue_score",
    "sequence_consistency_score",
    "neighbor_anchor_score",
    "gold_pattern_similarity",
    "target_granularity_score",
    "best_second_margin",
    "order_only_evidence_gate",
]
REQUIRED_PENALTIES = [
    "target_too_broad_penalty",
    "missing_entity_anchor_penalty",
    "ambiguous_margin_penalty",
    "order_only_penalty",
    "polysemy_without_context_penalty",
    "duplicate_link_penalty",
    "fragment_source_penalty",
]


@dataclass(frozen=True)
class BlockerAnchor:
    anchor_id: str
    entity_type: str
    subtype: str
    canonical: str
    aliases: tuple[str, ...]
    context_required: tuple[str, ...]
    negative_context: str


@dataclass(frozen=True)
class BlockerPattern:
    pattern_id: str
    pattern_name: str
    source_groups: tuple[tuple[str, ...], ...]
    target_groups: tuple[tuple[str, ...], ...]
    relationship_type: str
    confidence_rule: str


@dataclass(frozen=True)
class BlockerPack:
    root: Path
    profile: dict[str, Any]
    full_review_rows: list[dict[str, str]]
    split_child_rows: list[dict[str, str]]
    recovered_positive_rows: list[dict[str, str]]
    reject_rows: list[dict[str, str]]
    pattern_rows: list[dict[str, str]]
    anchors: list[BlockerAnchor]
    patterns: list[BlockerPattern]
    splitter_rules: list[dict[str, str]]
    test_cases: list[dict[str, Any]]
    strategy: dict[str, Any]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def split_pipe(value: str) -> tuple[str, ...]:
    return tuple(clean_phrase(part) for part in value.split("|") if clean_phrase(part))


def parse_cue_groups(value: str) -> tuple[tuple[str, ...], ...]:
    normalized = value.replace("/", "|")
    groups: list[tuple[str, ...]] = []
    for group in normalized.split("+"):
        cues = split_pipe(group)
        if cues:
            groups.append(cues)
    return tuple(groups)


def load_blocker_pack(root: Path = DEFAULT_BLOCKER_PACK) -> BlockerPack:
    anchor_rows = read_csv_rows(root / "06_anchor_dictionary_addendum_from_blockers.csv")
    pattern_rows = read_csv_rows(root / "05_blocker_pattern_groups_reviewed.csv")
    anchors = [
        BlockerAnchor(
            anchor_id=row["anchor_id"],
            entity_type=row["entity_type"],
            subtype=row["subtype"],
            canonical=row["canonical"],
            aliases=split_pipe(row["aliases"]),
            context_required=split_pipe(row["context_required"]),
            negative_context=row.get("negative_context", ""),
        )
        for row in anchor_rows
    ]
    patterns = [
        BlockerPattern(
            pattern_id=row["pattern_id"],
            pattern_name=row["pattern_name"],
            source_groups=parse_cue_groups(row["source_cues"]),
            target_groups=parse_cue_groups(row["target_cues"]),
            relationship_type=row["relationship_type"],
            confidence_rule=row["confidence_rule"],
        )
        for row in pattern_rows
        if row["relationship_type"] in ALLOWED_BLOCKER_RELATIONSHIPS
    ]
    return BlockerPack(
        root=root,
        profile=read_json(root / "00_blocker_review_profile.json"),
        full_review_rows=read_csv_rows(root / "01_blocker_examples_full_review_decisions.csv"),
        split_child_rows=read_csv_rows(root / "02_blocker_split_child_links.csv"),
        recovered_positive_rows=read_csv_rows(root / "03_blocker_recovered_positive_links.csv"),
        reject_rows=read_csv_rows(root / "04_blocker_reject_or_do_not_promote.csv"),
        pattern_rows=pattern_rows,
        anchors=anchors,
        patterns=patterns,
        splitter_rules=read_csv_rows(root / "07_commentary_clause_splitter_rules.csv"),
        test_cases=read_json(root / "08_blocker_hardening_test_cases.json"),
        strategy=read_json(root / "10_blocker_hardening_strategy_spec.json"),
    )


@lru_cache(maxsize=200000)
def cached_compact(text: str) -> str:
    return compact_text(text)


def compact_contains(text: str, cue: str) -> bool:
    cue = clean_phrase(cue)
    if not cue:
        return False
    return cached_compact(cue) in cached_compact(text)


@lru_cache(maxsize=200000)
def stemmed_forms(value: str) -> set[str]:
    forms = {cached_compact(value)}
    for token in tokens(value):
        compact = cached_compact(token)
        forms.add(compact)
        forms.add(TAMIL_SUFFIX_RE.sub("", compact))
    return {form for form in forms if form}


@lru_cache(maxsize=300000)
def cue_present(text: str, cue: str) -> bool:
    if compact_contains(text, cue):
        return True
    text_forms = stemmed_forms(text)
    return any(form in text_forms for form in stemmed_forms(cue))


def any_cue(text: str, cues: Iterable[str]) -> bool:
    return any(cue_present(text, cue) for cue in cues)


def all_cue_groups(text: str, groups: Iterable[Iterable[str]]) -> bool:
    return all(any_cue(text, group) for group in groups)


def anchor_context_present(anchor: BlockerAnchor, source: str, target: str) -> bool:
    required = anchor.context_required
    if not required:
        return True
    joined = f"{source} {target}"
    return any_cue(joined, required) or "deity/object/wearing cue" in required or "Siva/deity" in " ".join(required)


def resolve_anchor_ids(source: str, target: str, pack: BlockerPack) -> set[str]:
    resolved: set[str] = set()
    for anchor in pack.anchors:
        source_has = any_cue(source, anchor.aliases + (anchor.canonical,))
        target_has = any_cue(target, anchor.aliases + (anchor.canonical,))
        if source_has and target_has and anchor_context_present(anchor, source, target):
            resolved.add(anchor.anchor_id)
    return resolved


def matching_patterns(source: str, target: str, pack: BlockerPack) -> list[BlockerPattern]:
    return [
        pattern
        for pattern in pack.patterns
        if all_cue_groups(source, pattern.source_groups) and all_cue_groups(target, pattern.target_groups)
    ]


def relationship_cue_score(source: str, target: str, relationship: str, pack: BlockerPack) -> float:
    matched = sum(1 for pattern in pack.patterns if pattern.relationship_type == relationship and all_cue_groups(f"{source} {target}", pattern.target_groups))
    return min(1.0, matched / 2)


def gold_pattern_similarity(source: str, target: str, pack: BlockerPack) -> float:
    source_c = compact_text(source)
    target_c = compact_text(target)
    for row in pack.recovered_positive_rows:
        if compact_text(row.get("source_text", "")) == source_c and compact_text(row.get("target_text", "")) == target_c:
            return 1.0
    for row in pack.split_child_rows:
        if row.get("confidence") == "high" and compact_text(row.get("source_text", "")) == source_c and compact_text(row.get("target_text", "")) == target_c:
            return 0.95
    return 0.0


def blocker_base_features(row: dict[str, Any], source: str, target: str, pack: BlockerPack) -> tuple[dict[str, float], list[str]]:
    relationship = str(row.get("relationship_type", ""))
    anchors = resolve_anchor_ids(source, target, pack)
    patterns = matching_patterns(source, target, pack)
    semantic = min(1.0, 0.22 * len(patterns) + 0.10 * len(anchors))
    morphology = 0.35 if any(
        cue_present(source, alias) and cue_present(target, anchor.canonical)
        for anchor in pack.anchors
        for alias in anchor.aliases
    ) else 0.0
    shared = min(1.0, 0.24 * len(anchors))
    expanded = min(1.0, 0.28 * len(anchors) + 0.10 * len(patterns))
    ontology = min(1.0, 0.30 * len(patterns))
    relation = relationship_cue_score(source, target, relationship, pack)
    gold = gold_pattern_similarity(source, target, pack)
    margin = float((row.get("features") or {}).get("score_margin", 1.0)) if isinstance(row.get("features"), dict) else 1.0
    existing_confidence = str(row.get("confidence", ""))
    existing_score = float(row.get("score") or 0.0)
    inherited_evidence = existing_confidence in {"high", "medium"} and existing_score >= 0.45
    evidence_gate = 1.0 if semantic + shared + expanded + ontology + relation + gold >= 0.3 or inherited_evidence else 0.0
    features = {
        "surface_token_overlap": round(token_overlap_score(source, target), 4),
        "char_ngram_overlap": round(char_ngram_score(source, target), 4),
        "semantic_lexicon_score": round(semantic, 4),
        "morphology_stem_score": round(morphology, 4),
        "shared_entity_anchor_score": round(shared, 4),
        "expanded_entity_anchor_score": round(expanded, 4),
        "ontology_relation_score": round(ontology, 4),
        "relationship_cue_score": round(relation, 4),
        "sequence_consistency_score": 0.0,
        "neighbor_anchor_score": 0.0,
        "gold_pattern_similarity": round(gold, 4),
        "target_granularity_score": round(target_granularity_score(source, target, relationship), 4),
        "best_second_margin": round(margin, 4),
        "order_only_evidence_gate": evidence_gate,
    }
    return features, [anchor.anchor_id for anchor in pack.anchors if anchor.anchor_id in anchors] + [pattern.pattern_id for pattern in patterns]


def split_commentary_clauses(text: str) -> list[tuple[int, int, str]]:
    clauses: list[tuple[int, int, str]] = []
    for match in SPLIT_RE.finditer(text):
        pass
    start = 0
    for match in SPLIT_RE.finditer(text):
        end = match.start()
        clause = clean_phrase(text[start:end])
        if clause:
            clause_start = text.find(clause, start, end)
            clauses.append((clause_start, clause_start + len(clause), clause))
        start = match.end()
    clause = clean_phrase(text[start:])
    if clause:
        clause_start = text.find(clause, start)
        clauses.append((clause_start, clause_start + len(clause), clause))
    return clauses or [(0, len(text), text)]


def target_candidate_score(source: str, candidate: str, row: dict[str, Any], pack: BlockerPack) -> float:
    features, _rules = blocker_base_features(row, source, candidate, pack)
    return (
        features["gold_pattern_similarity"] * 2.4
        + features["semantic_lexicon_score"] * 1.8
        + features["expanded_entity_anchor_score"] * 1.6
        + features["ontology_relation_score"] * 1.5
        + features["relationship_cue_score"]
        + features["char_ngram_overlap"] * 0.6
        + features["target_granularity_score"] * 0.45
    )


def select_minimal_target(source: str, target: str, row: dict[str, Any], pack: BlockerPack) -> tuple[str, int | None, int | None, bool]:
    clauses = split_commentary_clauses(target)
    if len(clauses) <= 1:
        return target, row.get("target_start_char"), row.get("target_end_char"), False
    scored = sorted(
        ((target_candidate_score(source, clause, row, pack), start, end, clause) for start, end, clause in clauses),
        key=lambda item: (item[0], -len(tokens(item[3]))),
        reverse=True,
    )
    best_score, start, end, clause = scored[0]
    full_score = target_candidate_score(source, target, row, pack)
    if best_score + 0.15 >= full_score and len(tokens(clause)) < len(tokens(target)):
        base_start = row.get("target_start_char")
        if isinstance(base_start, int):
            return clause, base_start + start, base_start + end, True
        return clause, start, end, True
    return target, row.get("target_start_char"), row.get("target_end_char"), False


def replace_target_span(item: dict[str, Any], new_target: str) -> None:
    old_target = str(item.get("target_text", ""))
    old_start = item.get("target_start_char")
    if isinstance(old_start, int) and old_target and new_target in old_target:
        offset = old_target.find(new_target)
        item["target_start_char"] = old_start + offset
        item["target_end_char"] = old_start + offset + len(new_target)
    else:
        item["target_start_char"] = item.get("target_start_char")
        item["target_end_char"] = item.get("target_end_char")
    item["target_text"] = new_target


def broad_target(source: str, target: str, relationship: str) -> bool:
    ratio = len(tokens(target)) / max(1, len(tokens(source)))
    return relationship != "explains_line" and ratio > 3


def blocker_penalties(row: dict[str, Any], features: dict[str, float], source: str, target: str, duplicate: bool) -> tuple[list[str], list[str]]:
    penalties: list[str] = []
    critical: list[str] = []
    base_confidence = str(row.get("confidence", ""))
    note = str(row.get("diagnostic_note", "")).lower()
    weak_existing_link = base_confidence in {"low", "no_link", ""}
    if broad_target(source, target, str(row.get("relationship_type", ""))):
        penalties.append("target_too_broad_penalty")
    if weak_existing_link and features["expanded_entity_anchor_score"] == 0 and features["ontology_relation_score"] == 0:
        penalties.append("missing_entity_anchor_penalty")
    if weak_existing_link and features["best_second_margin"] < 0.05:
        penalties.append("ambiguous_margin_penalty")
        critical.append("best_second_margin_below_review_threshold")
    looks_order_only = "order" in note or "do-not-promote" in note or "wrong target" in note
    if features["order_only_evidence_gate"] == 0 and (weak_existing_link or looks_order_only):
        penalties.append("order_only_penalty")
        critical.append("order_only_support")
    if weak_existing_link and any(cue_present(source, cue) for cue in ("மதி", "அரவு", "அடி")) and features["ontology_relation_score"] == 0:
        penalties.append("polysemy_without_context_penalty")
    if duplicate:
        penalties.append("duplicate_link_penalty")
    if cached_compact(source) in {cached_compact(item) for item in FRAGMENT_SOURCE_TOKENS}:
        penalties.append("fragment_source_penalty")
        critical.append("fragment_source")
    return penalties, critical


def blocker_score_and_confidence(
    row: dict[str, Any],
    features: dict[str, float],
    penalties: list[str],
    critical: list[str],
) -> tuple[float, str, bool]:
    base_score = float(row.get("score") or 0.0)
    base_confidence = str(row.get("confidence", ""))
    positive_evidence = (
        features["semantic_lexicon_score"]
        + features["expanded_entity_anchor_score"]
        + features["ontology_relation_score"]
        + features["relationship_cue_score"]
        + features["gold_pattern_similarity"]
    )
    penalty_weight = 0.06 * len(penalties) + (0.05 if "target_too_broad_penalty" in penalties else 0.0)
    score = max(
        0.0,
        min(
            0.99,
            0.78 * base_score
            + 0.14 * positive_evidence
            + 0.08 * features["target_granularity_score"]
            - penalty_weight,
        ),
    )
    confidence = base_confidence if base_confidence in CONFIDENCE_ORDER else "low"
    if "fragment_source" in critical or base_confidence == "no_link":
        return round(score, 4), "no_link", True
    if features["gold_pattern_similarity"] >= 0.95 and "fragment_source" not in critical:
        score = max(score, 0.86 if features["target_granularity_score"] >= 0.6 else 0.72)
        confidence = "high" if features["target_granularity_score"] >= 0.6 else "medium"
    elif score >= 0.74 and positive_evidence >= 0.45 and "order_only_support" not in critical:
        confidence = "high"
    elif score >= 0.42 and (positive_evidence >= 0.2 or base_confidence in {"high", "medium"}):
        confidence = "medium"
    if base_confidence == "high" and "order_only_support" not in critical:
        confidence = "high"
        score = max(score, base_score)
    elif base_confidence == "medium" and confidence == "low" and "order_only_support" not in critical:
        confidence = "medium"
        score = max(score, min(base_score, 0.74))
    manual_review = bool(row.get("manual_review_required")) or confidence == "low" or bool(critical)
    if "order_only_support" in critical and confidence == "high":
        confidence = "low"
        manual_review = True
    return round(score, 4), confidence, manual_review


def reviewed_row_index(pack: BlockerPack) -> dict[str, dict[str, str]]:
    return {row["link_id"]: row for row in pack.full_review_rows if row.get("link_id")}


def reject_index(pack: BlockerPack) -> dict[str, dict[str, str]]:
    return {row["link_id"]: row for row in pack.reject_rows if row.get("link_id")}


def recovered_index(pack: BlockerPack) -> dict[str, dict[str, str]]:
    return {row["link_id"]: row for row in pack.recovered_positive_rows if row.get("link_id")}


def apply_review_overrides(
    row: dict[str, Any],
    *,
    reviewed_rows: dict[str, dict[str, str]],
    recovered_rows: dict[str, dict[str, str]],
    reject_rows: dict[str, dict[str, str]],
) -> dict[str, Any]:
    base_id = str(row.get("base_link_id") or row.get("link_id"))
    reviewed = reviewed_rows.get(base_id)
    recovered = recovered_rows.get(base_id)
    reject = reject_rows.get(base_id)
    item = dict(row)
    if recovered:
        item["relationship_type"] = recovered["relationship_type"]
        replace_target_span(item, recovered["target_text"])
        item["confidence"] = recovered["confidence"]
        item["score"] = max(float(item.get("score") or 0), 0.86 if recovered["confidence"] == "high" else 0.62)
        item["manual_review_required"] = recovered["confidence"] not in {"high", "medium"}
        item["diagnostic_note"] = f"{item.get('diagnostic_note', '')} Blocker reviewed positive: {recovered.get('note', '')}".strip()
    elif reviewed and reviewed.get("corrected_or_minimal_target_text"):
        item["relationship_type"] = reviewed.get("final_relationship_type") or item.get("relationship_type")
        replace_target_span(item, reviewed["corrected_or_minimal_target_text"])
        item["confidence"] = reviewed.get("confidence_after_fix") or item.get("confidence")
        item["manual_review_required"] = item["confidence"] not in {"high", "medium"}
    if reject and reject.get("algorithm_action") != "deduplicate_then_use_row_8_decision":
        fixed = reject.get("confidence_after_fix") or "low"
        item["confidence"] = fixed if fixed in CONFIDENCE_ORDER else "low"
        item["manual_review_required"] = True
        if item["confidence"] == "no_link":
            item["relationship_type"] = "unlinked"
            item["target_text"] = ""
            item["target_start_char"] = None
            item["target_end_char"] = None
        item["diagnostic_note"] = f"{item.get('diagnostic_note', '')} Blocker reject/do-not-promote: {reject.get('reviewer_note', '')}".strip()
    return item


def append_split_children(rows: list[dict[str, Any]], pack: BlockerPack) -> list[dict[str, Any]]:
    by_base_id = {str(row.get("base_link_id") or row.get("link_id")): row for row in rows}
    output = list(rows)
    for child in pack.split_child_rows:
        if child.get("confidence") not in {"high", "medium"} or not child.get("target_text"):
            continue
        parent = by_base_id.get(child["parent_link_id"], {})
        parent_target = str(parent.get("target_text", ""))
        parent_target_start = parent.get("target_start_char", 0)
        child_offset = parent_target.find(child["target_text"]) if parent_target else -1
        child_start = parent_target_start + child_offset if isinstance(parent_target_start, int) and child_offset >= 0 else parent.get("target_start_char", 0)
        child_end = child_start + len(child["target_text"]) if isinstance(child_start, int) else parent.get("target_end_char", len(child["target_text"]))
        output.append(
            {
                **parent,
                "schema_version": SCHEMA_VERSION,
                "base_schema_version": V4_SCHEMA_VERSION,
                "base_link_id": child["parent_link_id"],
                "link_id": child["child_link_id"],
                "source_text": child["source_text"],
                "source_text_normalized": child["source_text"],
                "target_text": child["target_text"],
                "relationship_type": child["relationship_type"],
                "confidence": child["confidence"],
                "score": 0.88 if child["confidence"] == "high" else 0.62,
                "manual_review_required": False,
                "target_field": parent.get("target_field", "pozhppurai"),
                "source_start_char": parent.get("source_start_char", 0),
                "source_end_char": parent.get("source_end_char", len(child["source_text"])),
                "target_start_char": child_start,
                "target_end_char": child_end,
                "method": "v4_blocker_review_split_child",
                "diagnostic_note": child.get("note", ""),
                "split_parent_id": child["parent_link_id"],
            }
        )
    return output


def dedupe_blocker_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], set[str]]:
    duplicate_ids = {link_id for link_id, count in Counter(str(row.get("link_id")) for row in rows).items() if count > 1}
    best: dict[str, dict[str, Any]] = {}
    for row in rows:
        link_id = str(row.get("link_id"))
        if link_id not in best or confidence_rank(row) > confidence_rank(best[link_id]):
            best[link_id] = row
    return list(best.values()), duplicate_ids


def repair_spans_from_tables(rows: list[dict[str, Any]], *, table_root: Path) -> list[dict[str, Any]]:
    paadal_by_id = {str(row.get("paadal_id", "")): row for row in read_jsonl(table_root / "paadalgal.jsonl")}
    commentary_by_id = {str(row.get("commentary_id", "")): row for row in read_jsonl(table_root / "commentaries.jsonl")}
    repaired: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        source = str(item.get("source_text", ""))
        paadal = paadal_by_id.get(str(item.get("paadal_id", "")), {})
        source_field = str(item.get("source_field") or "paadal_text")
        source_full = str(paadal.get(source_field, "") or paadal.get("paadal_text", ""))
        if source and source_full:
            source_start = source_full.find(source)
            if source_start >= 0:
                item["source_start_char"] = source_start
                item["source_end_char"] = source_start + len(source)

        target = str(item.get("target_text", ""))
        commentary = commentary_by_id.get(str(item.get("commentary_id", "")), {})
        target_field = str(item.get("target_field") or "pozhppurai")
        target_full = str(commentary.get(target_field, ""))
        if target and target_full:
            target_start = target_full.find(target)
            if target_start >= 0:
                item["target_start_char"] = target_start
                item["target_end_char"] = target_start + len(target)
        repaired.append(item)
    return repaired


def harden_links_with_blocker_pack(links: list[dict[str, Any]], *, pack: BlockerPack) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    reviewed_rows = reviewed_row_index(pack)
    recovered_rows = recovered_index(pack)
    reject_rows = reject_index(pack)
    minimal_targets = 0
    reviewed_positive = 0
    demoted = 0
    for row in links:
        item = {
            **row,
            "schema_version": SCHEMA_VERSION,
            "base_schema_version": V4_SCHEMA_VERSION,
            "base_link_id": row.get("link_id", ""),
            "target_field_preference": row.get("target_field") or "pozhppurai",
        }
        before_confidence = str(item.get("confidence", ""))
        item = apply_review_overrides(
            item,
            reviewed_rows=reviewed_rows,
            recovered_rows=recovered_rows,
            reject_rows=reject_rows,
        )
        if is_linked_row(item):
            target, start, end, changed = select_minimal_target(str(item.get("source_text", "")), str(item.get("target_text", "")), item, pack)
            if changed:
                minimal_targets += 1
                item["target_text"] = target
                item["target_start_char"] = start
                item["target_end_char"] = end
                item["method"] = "v4_blocker_minimal_target_selector"
        prepared.append(item)
        reviewed_positive += int(str(item.get("confidence")) in {"high", "medium"} and before_confidence != str(item.get("confidence")))

    prepared = append_split_children(prepared, pack)
    deduped, duplicate_ids = dedupe_blocker_rows(prepared)
    by_paadal: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in deduped:
        by_paadal[str(row.get("paadal_id", ""))].append(row)
    seq_lookup: dict[str, tuple[float, float, str]] = {}
    for group in by_paadal.values():
        seq_lookup.update(sequence_scores([row for row in group if is_linked_row(row)]))

    hardened: list[dict[str, Any]] = []
    recovered_anchor_rows = 0
    order_only_blocked = 0
    for row in deduped:
        source = str(row.get("source_text", ""))
        target = str(row.get("target_text", ""))
        features, rule_ids = blocker_base_features(row, source, target, pack)
        sequence_score, neighbor_score, sequence_method = seq_lookup.get(str(row.get("link_id")), (0.0, 0.0, "rule_or_unavailable"))
        features["sequence_consistency_score"] = sequence_score
        features["neighbor_anchor_score"] = neighbor_score
        penalties, critical = blocker_penalties(row, features, source, target, str(row.get("link_id")) in duplicate_ids)
        score, confidence, manual_review = blocker_score_and_confidence(row, features, penalties, critical)
        if row.get("confidence") in {"high", "medium"} and features["gold_pattern_similarity"] >= 0.95:
            confidence = str(row["confidence"])
            manual_review = False
            score = max(score, float(row.get("score") or 0))
        if "order_only_support" in critical:
            order_only_blocked += 1
        if features["expanded_entity_anchor_score"] > 0:
            recovered_anchor_rows += 1
        if CONFIDENCE_ORDER.get(confidence, 0) < CONFIDENCE_ORDER.get(str(row.get("confidence")), 0):
            demoted += 1
        item = {
            **row,
            "confidence": confidence,
            "score": score,
            "previous_confidence": row.get("confidence"),
            "feature_scores": {field: features.get(field, 0.0) for field in REQUIRED_FEATURE_FIELDS},
            "penalties_applied": penalties,
            "critical_warnings": critical,
            "rule_ids_applied": list(row.get("rule_ids_applied") or []) + rule_ids,
            "sequence_alignment_method": sequence_method,
            "expanded_entity_anchors": rule_ids,
            "manual_review_required": manual_review,
        }
        if item["relationship_type"] not in ALLOWED_BLOCKER_RELATIONSHIPS:
            item["relationship_type"] = "unlinked" if confidence == "no_link" else "explains_phrase"
        hardened.append(item)

    return hardened, {
        "minimal_target_selected_rows": minimal_targets,
        "reviewed_positive_promoted_rows": reviewed_positive,
        "reviewed_split_child_rows": sum(1 for row in hardened if row.get("method") == "v4_blocker_review_split_child"),
        "duplicate_link_ids_deduped": len(duplicate_ids),
        "anchor_resolver_recovered_rows": recovered_anchor_rows,
        "order_only_blocked_rows": order_only_blocked,
        "demoted_rows": demoted,
    }


def summarize_blocker_hardened(
    links: list[dict[str, Any]],
    primary_clean: list[dict[str, Any]],
    secondary_no_link: list[dict[str, Any]],
    pack: BlockerPack,
    improvement_counts: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "blocker_pack_root": str(pack.root),
        "blocker_issue_type_counts": pack.profile.get("issue_type_counts", {}),
        "blocker_review_decision_counts": pack.profile.get("review_decision_counts", {}),
        "blocker_positive_recovered_links": pack.profile.get("positive_recovered_links"),
        "blocker_split_child_links": pack.profile.get("split_child_links"),
        "blocker_reject_or_do_not_promote_rows": pack.profile.get("reject_or_do_not_promote_rows"),
        "required_feature_fields": REQUIRED_FEATURE_FIELDS,
        "required_penalties": REQUIRED_PENALTIES,
        "total_links": len(links),
        "primary_clean_links": len(primary_clean),
        "secondary_no_link_rows": len(secondary_no_link),
        "links_by_confidence": dict(sorted(Counter(str(row.get("confidence", "")) for row in links).items())),
        "primary_links_by_confidence": dict(sorted(Counter(str(row.get("confidence", "")) for row in primary_clean).items())),
        "links_by_relationship_type": dict(sorted(Counter(str(row.get("relationship_type", "")) for row in links).items())),
        "manual_review_required_count": sum(1 for row in links if row.get("manual_review_required")),
        "no_link_count": sum(1 for row in links if row.get("confidence") == "no_link"),
        **improvement_counts,
    }


def render_report(summary: dict[str, Any], validation: dict[str, Any], output_root: Path) -> str:
    def table(mapping: dict[str, Any]) -> str:
        return "\n".join(f"| `{key}` | {value} |" for key, value in mapping.items()) or "| None | 0 |"

    return f"""# Thevaram Paadal-Pozhippurai Linker v4 Blocker-Hardened Report

## Summary

- Output root: `{output_root}`
- Schema version: `{summary['schema_version']}`
- Full links: `{summary['total_links']}`
- Primary clean links: `{summary['primary_clean_links']}`
- Manual review required: `{summary['manual_review_required_count']}`
- No-link rows: `{summary['no_link_count']}`
- Validation status: `{validation['status']}`
- Anchor resolver recovered rows: `{summary['anchor_resolver_recovered_rows']}`
- Minimal targets selected: `{summary['minimal_target_selected_rows']}`
- Reviewed split children: `{summary['reviewed_split_child_rows']}`
- Order-only rows blocked: `{summary['order_only_blocked_rows']}`

## Blocker Pack Inputs

- Issue counts: `{summary['blocker_issue_type_counts']}`
- Review decisions: `{summary['blocker_review_decision_counts']}`
- Positive recovered links: `{summary['blocker_positive_recovered_links']}`
- Split child links: `{summary['blocker_split_child_links']}`
- Reject / do-not-promote rows: `{summary['blocker_reject_or_do_not_promote_rows']}`

## Confidence Distribution

| Confidence | Rows |
| --- | ---: |
{table(summary['links_by_confidence'])}

## Relationship Distribution

| Relationship | Rows |
| --- | ---: |
{table(summary['links_by_relationship_type'])}

## Methods Used

- Anchor Resolver: blocker alias dictionary, Tamil suffix normalization, context checks, and pattern groups.
- Commentary Clause Splitter: punctuation/cue-family splitting and smallest sufficient target selection.
- Global Assignment Reranker: neighbour and sequence scores from grouped paadal links.
- Evidence-Gated Confidence Scoring: order cannot produce high confidence without semantic/entity/ontology/gold evidence.
- Pattern-Group Promotion Rules: reviewed positive links and split children are promoted only when their reviewed evidence is present.

Existing v1-v4 outputs are not overwritten. This run writes additively to `v4_blocker_hardened`.
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
    prefix = "paadal_pozhippurai_links_v4_blocker_hardened"
    write_jsonl(output_root / f"{prefix}_full.jsonl", links)
    write_jsonl(output_root / f"{prefix}_high_confidence.jsonl", [row for row in links if row.get("confidence") == "high" and not row.get("manual_review_required")])
    write_jsonl(output_root / f"{prefix}_medium_confidence.jsonl", [row for row in links if row.get("confidence") == "medium" and not row.get("manual_review_required")])
    write_csv_file(output_root / f"{prefix}_low_review.csv", [row for row in links if row.get("confidence") == "low" or row.get("manual_review_required")])
    write_csv_file(output_root / f"{prefix}_no_link_or_unresolved.csv", [row for row in links if row.get("confidence") == "no_link" or row.get("relationship_type") == "unlinked"])
    write_csv_file(output_root / f"{prefix}_manual_review_pack.csv", build_manual_review_pack(links))
    write_iob_v4(output_root / f"{prefix}.iob.conll", [row for row in links if is_positive_v4(row)])
    (output_root / f"{prefix}_summary.json").write_text(
        json.dumps({**summary, "validation": validation}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary, validation, output_root), encoding="utf-8")


def run_linking_v4_blocker_hardened(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    entity_root: Path = DEFAULT_ENTITY_ROOT,
    seed_dir: Path = DEFAULT_SEED_DIR,
    qa_bundle: Path = DEFAULT_QA_BUNDLE,
    gold_seed: Path = DEFAULT_GOLD_SEED,
    blocker_pack: Path = DEFAULT_BLOCKER_PACK,
    v4_output_root: Path = DEFAULT_V4_OUTPUT_ROOT,
    rebuild_base_v4: bool = False,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    pack = load_blocker_pack(blocker_pack)
    existing_base_files = [
        v4_output_root / "paadal_pozhippurai_links_v4_hardened_full.jsonl",
        v4_output_root / "paadal_pozhippurai_links_v4_full.jsonl",
    ]
    existing_base_file = next((path for path in existing_base_files if path.exists()), None)
    if existing_base_file is not None and not rebuild_base_v4:
        links = read_jsonl(existing_base_file)
    else:
        links, _summary = build_v4_links(
            table_root=table_root,
            entity_root=entity_root,
            seed_dir=seed_dir,
            qa_bundle=qa_bundle,
            gold_seed=gold_seed,
        )
    links, improvement_counts = harden_links_with_blocker_pack(links, pack=pack)
    links = repair_spans_from_tables(links, table_root=table_root)
    paadal_rows = read_jsonl(table_root / "paadalgal.jsonl")
    commentary_rows = read_jsonl(table_root / "commentaries.jsonl")
    primary_clean = dedupe_primary_hardened(clean_primary_links(links, paadal_rows=paadal_rows, commentary_rows=commentary_rows))
    secondary_no_link = secondary_no_link_rows(links, commentary_rows)
    validation = validate_v4_links(table_root, links)
    primary_validation = validate_clean_links(table_root, primary_clean)
    summary = summarize_blocker_hardened(links, primary_clean, secondary_no_link, pack, improvement_counts)
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
    parser = argparse.ArgumentParser(description="Create blocker-hardened Thevaram paadal-pozhppurai v4 links.")
    parser.add_argument("--input-root", "--table-root", dest="table_root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--entity-root", type=Path, default=DEFAULT_ENTITY_ROOT)
    parser.add_argument("--seed-dir", type=Path, default=DEFAULT_SEED_DIR)
    parser.add_argument("--qa-bundle", type=Path, default=DEFAULT_QA_BUNDLE)
    parser.add_argument("--gold-seed", type=Path, default=DEFAULT_GOLD_SEED)
    parser.add_argument("--blocker-pack", type=Path, default=DEFAULT_BLOCKER_PACK)
    parser.add_argument("--v4-output-root", type=Path, default=DEFAULT_V4_OUTPUT_ROOT)
    parser.add_argument("--rebuild-base-v4", action="store_true")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = run_linking_v4_blocker_hardened(
        table_root=args.table_root,
        entity_root=args.entity_root,
        seed_dir=args.seed_dir,
        qa_bundle=args.qa_bundle,
        gold_seed=args.gold_seed,
        blocker_pack=args.blocker_pack,
        v4_output_root=args.v4_output_root,
        rebuild_base_v4=args.rebuild_base_v4,
        output_root=args.output_root,
        report_path=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["validation"]["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
