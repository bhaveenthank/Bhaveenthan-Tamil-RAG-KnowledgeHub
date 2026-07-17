from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from knowledge.build_pozhippurai_links_v4 import validate_clean_links, validate_v4_links, write_iob_v4
from knowledge.build_pozhippurai_links_v4_hardened import (
    base_features,
    compact_contains,
    load_hardening_pack,
    target_candidates,
)
from knowledge.learn_pozhippurai_high_confidence_patterns import load_jsonl
from knowledge.link_thevaram_pozhippurai import DEFAULT_TABLE_ROOT, stable_hash, tokens
from knowledge.link_thevaram_pozhippurai_v3 import build_manual_review_pack, write_csv_file, write_jsonl, write_tsv

SCHEMA_VERSION = "thevaram-pozhppurai-paadallink-v4-ambiguous-span-fixed"
DEFAULT_BASE_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_hardened_learned")
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_ambiguous_span_fixed")
DEFAULT_REPORT = DEFAULT_OUTPUT_ROOT / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_report.md"

AMBIGUOUS_PENALTY = "ambiguous_margin_penalty"
AMBIGUOUS_WARNING = "best_second_margin_below_review_threshold"
HIGH_BLOCKING_FLAGS = {
    "order_only_penalty",
    "target_too_broad_penalty",
    "missing_entity_anchor_penalty",
    "polysemy_without_context_penalty",
    "order_only_support",
}
RELATION_FAMILIES = {
    "interprets_image": "image_family",
    "theological_explanation": "theology_family",
    "describes_entity": "entity_family",
    "explains_phrase": "phrase_family",
    "glosses_word": "phrase_family",
    "explains_line": "phrase_family",
}
FEATURE_CACHE: dict[tuple[str, str, str, str], tuple[dict[str, float], tuple[str, ...], tuple[str, ...]]] = {}


@dataclass(frozen=True)
class Candidate:
    start: int
    end: int
    text: str
    target_field: str
    local_score: float
    features: dict[str, float]
    rule_ids: tuple[str, ...]
    anchors: tuple[str, ...]
    pattern_score: float
    is_current: bool

    @property
    def target_key(self) -> tuple[str, int, int, str]:
        return (self.target_field, self.start, self.end, self.text)


@dataclass(frozen=True)
class AssignmentChoice:
    candidate: Candidate
    global_score: float
    best_score: float
    second_score: float
    margin: float
    local_best: Candidate
    local_second: Candidate | None
    prev_anchor_score: float
    next_anchor_score: float
    neighbor_window_score: float
    relation_family_consistency_score: float
    relation_family_conflict_penalty: float
    method: str
    forward_alignment_score: float
    reverse_alignment_score: float


def relation_family(row: dict[str, Any]) -> str:
    return RELATION_FAMILIES.get(str(row.get("relationship_type", "")), "unknown_family")


def is_linked(row: dict[str, Any]) -> bool:
    return row.get("relationship_type") != "unlinked" and row.get("confidence") != "no_link" and bool(row.get("target_text"))


def is_ambiguous(row: dict[str, Any]) -> bool:
    return AMBIGUOUS_PENALTY in set(map(str, row.get("penalties_applied") or []))


def raw_margin(row: dict[str, Any]) -> float:
    features = row.get("features") if isinstance(row.get("features"), dict) else {}
    try:
        return float(features.get("score_margin", 0.0) or 0.0)
    except (TypeError, ValueError):
        return 0.0


def has_high_blocker(row: dict[str, Any], penalties: Iterable[str], critical: Iterable[str]) -> bool:
    return bool((set(map(str, penalties)) | set(map(str, critical))) & HIGH_BLOCKING_FLAGS)


def cue_pattern_score(source: str, target: str, relationship: str) -> float:
    joined = f"{source} {target}"
    if relationship == "interprets_image":
        moon = any(compact_contains(source, cue) for cue in ("பிறை", "திங்கள்", "மதி", "வெண்மதி")) and any(
            compact_contains(target, cue) for cue in ("பிறை", "திங்கள்", "சந்திரன்", "பிறைமதி", "வெண்பிறை")
        )
        moon_hair = moon and any(compact_contains(joined, cue) for cue in ("சடை", "முடி", "சென்னி")) and any(
            compact_contains(joined, cue) for cue in ("சூடி", "அணிந்து", "பொருந்தி")
        )
        ganga = any(compact_contains(source, cue) for cue in ("கங்கை", "புனல்", "சலம்", "நீர்")) and any(
            compact_contains(target, cue) for cue in ("கங்கை", "சடை", "திருமுடி", "சூடி", "தரித்த")
        )
        if moon_hair:
            return 0.24
        if ganga:
            return 0.22
    if relationship == "theological_explanation":
        worship = any(compact_contains(source, cue) for cue in ("தொழ", "ஏத்து", "பணி", "கைதொழ", "அடி", "பாதம்")) and any(
            compact_contains(target, cue) for cue in ("தொழுது", "போற்றி", "வழிபட்டு", "திருவடி", "பாதம்", "நலம்", "வினை")
        )
        if worship:
            return 0.22
    if relationship == "describes_entity":
        place = any(compact_contains(source, cue) for cue in ("ஆலவாய்", "முதுகுன்றம்", "மிழலை", "அண்ணாமலை", "காழி")) and any(
            compact_contains(target, cue) for cue in ("இறைவன்", "சிவபிரான்", "ஞானசம்பந்தன்", "ஆலவாய்", "முதுகுன்றம்", "மிழலை", "அண்ணாமலை", "காழி")
        )
        if place:
            return 0.20
    return 0.0


def non_order_support(candidate: Candidate, prev_anchor: float, next_anchor: float) -> float:
    features = candidate.features
    direct = (
        features.get("semantic_lexicon_score", 0.0)
        + features.get("morphology_stem_score", 0.0)
        + features.get("shared_entity_anchor_score", 0.0)
        + features.get("ontology_relation_score", 0.0)
        + features.get("relationship_cue_score", 0.0)
        + features.get("gold_pattern_similarity", 0.0)
        + candidate.pattern_score
    )
    neighbor = max(prev_anchor, next_anchor)
    return max(direct, neighbor)


def weighted_candidate_score(row: dict[str, Any], candidate: Candidate) -> float:
    features = candidate.features
    score = (
        0.18 * features.get("surface_token_overlap", 0.0)
        + 0.10 * features.get("char_ngram_overlap", 0.0)
        + 0.20 * features.get("semantic_lexicon_score", 0.0)
        + 0.12 * features.get("morphology_stem_score", 0.0)
        + 0.18 * features.get("shared_entity_anchor_score", 0.0)
        + 0.17 * features.get("ontology_relation_score", 0.0)
        + 0.11 * features.get("relationship_cue_score", 0.0)
        + 0.08 * features.get("gold_pattern_similarity", 0.0)
        + 0.08 * features.get("target_granularity_score", 0.0)
        + 0.16 * candidate.pattern_score
    )
    if candidate.is_current:
        score += min(0.08, max(0.0, float(row.get("score") or 0.0) * 0.06))
    return round(score, 4)


def candidate_from_span(
    row: dict[str, Any],
    target_field: str,
    start: int,
    end: int,
    text: str,
    pack: Any,
) -> Candidate:
    source = str(row.get("source_text", ""))
    cache_key = (str(row.get("relationship_type", "")), target_field, source, text)
    cached = FEATURE_CACHE.get(cache_key)
    if cached is None:
        features, rule_ids, anchors = base_features(row, source, text, target_field, pack)
        cached = (features, tuple(rule_ids), tuple(anchors))
        FEATURE_CACHE[cache_key] = cached
    features, rule_ids, anchors = cached
    pattern_score = cue_pattern_score(source, text, str(row.get("relationship_type", "")))
    provisional = Candidate(
        start=start,
        end=end,
        text=text,
        target_field=target_field,
        local_score=0.0,
        features=features,
        rule_ids=tuple(rule_ids),
        anchors=tuple(anchors),
        pattern_score=pattern_score,
        is_current=start == int(row.get("target_start_char") or -1)
        and end == int(row.get("target_end_char") or -1)
        and text == str(row.get("target_text", "")),
    )
    return Candidate(
        start=provisional.start,
        end=provisional.end,
        text=provisional.text,
        target_field=provisional.target_field,
        local_score=weighted_candidate_score(row, provisional),
        features=provisional.features,
        rule_ids=provisional.rule_ids,
        anchors=provisional.anchors,
        pattern_score=provisional.pattern_score,
        is_current=provisional.is_current,
    )


def add_span_candidate(spans: dict[tuple[str, int, int, str], tuple[int, int, str]], target_field: str, start: Any, end: Any, text: str) -> None:
    try:
        start_int = int(start)
        end_int = int(end)
    except (TypeError, ValueError):
        return
    clean = str(text or "").strip()
    if not clean or end_int <= start_int:
        return
    spans[(target_field, start_int, end_int, clean)] = (start_int, end_int, clean)


def build_candidates_for_row(
    row: dict[str, Any],
    group_rows: list[dict[str, Any]],
    commentary: dict[str, Any],
    pack: Any,
    *,
    top_k: int = 10,
) -> list[Candidate]:
    target_field = str(row.get("target_field") or "pozhppurai")
    if not is_ambiguous(row):
        return [static_candidate_for_row(row, target_field)]
    full_text = str(commentary.get(target_field, ""))
    spans: dict[tuple[str, int, int, str], tuple[int, int, str]] = {}
    add_span_candidate(spans, target_field, row.get("target_start_char"), row.get("target_end_char"), str(row.get("target_text", "")))
    center = int(row.get("target_start_char") or 0) if row.get("target_start_char") is not None else None
    for other in group_rows:
        if str(other.get("target_field") or "pozhppurai") != target_field:
            continue
        if center is not None and other.get("target_start_char") is not None:
            try:
                if abs(int(other.get("target_start_char") or 0) - center) > 650:
                    continue
            except (TypeError, ValueError):
                pass
        add_span_candidate(spans, target_field, other.get("target_start_char"), other.get("target_end_char"), str(other.get("target_text", "")))
    if full_text:
        for start, end, text in target_candidates(full_text, center=center, window=360):
            add_span_candidate(spans, target_field, start, end, text)

    candidates: list[Candidate] = []
    source_count = max(1, len(tokens(str(row.get("source_text", "")))))
    for key, (start, end, text) in spans.items():
        is_current = start == int(row.get("target_start_char") or -1) and end == int(row.get("target_end_char") or -1)
        if not is_current and len(tokens(text)) > max(28, source_count * 8):
            continue
        candidates.append(candidate_from_span(row, key[0], start, end, text, pack))
    candidates = sorted(candidates, key=lambda item: (item.local_score, item.is_current), reverse=True)
    current = [candidate for candidate in candidates if candidate.is_current]
    limited = candidates[:top_k]
    for candidate in current:
        if candidate not in limited:
            limited.append(candidate)
    return sorted(limited, key=lambda item: (item.local_score, item.is_current), reverse=True)


def static_candidate_for_row(row: dict[str, Any], target_field: str) -> Candidate:
    start = int(row.get("target_start_char") or 0)
    end = int(row.get("target_end_char") or start)
    text = str(row.get("target_text", ""))
    features = row.get("feature_scores") if isinstance(row.get("feature_scores"), dict) else {}
    local_score = max(0.05, min(0.95, float(row.get("score") or 0.0) * 0.45))
    return Candidate(
        start=start,
        end=end,
        text=text,
        target_field=target_field,
        local_score=round(local_score, 4),
        features={key: float(value or 0.0) for key, value in features.items() if isinstance(value, int | float)},
        rule_ids=tuple(map(str, row.get("rule_ids_applied") or [])),
        anchors=tuple(map(str, row.get("expanded_entity_anchors") or [])),
        pattern_score=0.0,
        is_current=True,
    )


def transition_score(left: Candidate | None, right: Candidate, *, direction: str) -> float:
    if left is None:
        return 0.0
    if left.target_key == right.target_key:
        return -0.16
    if direction == "reverse":
        if right.end <= left.start:
            gap = left.start - right.end
            return 0.10 if gap <= 3 else 0.06 if gap <= 80 else 0.02
        return -0.30
    if right.start >= left.end:
        gap = right.start - left.end
        return 0.10 if gap <= 3 else 0.06 if gap <= 80 else 0.02
    return -0.30


def run_dp(candidate_lists: list[list[Candidate]], *, direction: str) -> tuple[list[int], float]:
    if not candidate_lists or any(not items for items in candidate_lists):
        return [], 0.0
    scores: list[list[float]] = []
    back: list[list[int | None]] = []
    for row_index, candidates in enumerate(candidate_lists):
        row_scores: list[float] = []
        row_back: list[int | None] = []
        if row_index == 0:
            for candidate in candidates:
                row_scores.append(candidate.local_score)
                row_back.append(None)
        else:
            for candidate in candidates:
                best_score = -1_000_000.0
                best_previous: int | None = None
                for previous_index, previous in enumerate(candidate_lists[row_index - 1]):
                    relation_bonus = 0.03
                    value = scores[row_index - 1][previous_index] + candidate.local_score + transition_score(previous, candidate, direction=direction) + relation_bonus
                    if value > best_score:
                        best_score = value
                        best_previous = previous_index
                row_scores.append(best_score)
                row_back.append(best_previous)
        scores.append(row_scores)
        back.append(row_back)

    final_index = max(range(len(scores[-1])), key=lambda index: scores[-1][index])
    selected = [final_index]
    for row_index in range(len(candidate_lists) - 1, 0, -1):
        previous = back[row_index][selected[-1]]
        if previous is None:
            previous = max(range(len(scores[row_index - 1])), key=lambda index: scores[row_index - 1][index])
        selected.append(previous)
    selected.reverse()
    return selected, round(max(scores[-1]) / max(1, len(candidate_lists)), 4)


def neighbor_scores(selected: list[Candidate], index: int, candidate: Candidate, rows: list[dict[str, Any]]) -> tuple[float, float, float, float, float]:
    previous = selected[index - 1] if index > 0 else None
    next_item = selected[index + 1] if index + 1 < len(selected) else None
    prev_anchor = 0.0
    next_anchor = 0.0
    if previous is not None:
        prev_anchor = max(0.0, min(1.0, transition_score(previous, candidate, direction="forward") + 0.30)) if candidate.start >= previous.start else 0.15
    if next_item is not None:
        next_anchor = max(0.0, min(1.0, transition_score(candidate, next_item, direction="forward") + 0.30)) if candidate.start <= next_item.start else 0.15
    if previous is not None and next_item is not None:
        lower, upper = sorted((previous.start, next_item.start))
        neighbor_window = 1.0 if lower <= candidate.start <= upper else 0.2
    elif previous is not None or next_item is not None:
        neighbor_window = max(prev_anchor, next_anchor)
    else:
        neighbor_window = 0.5
    family = relation_family(rows[index])
    neighbor_families = []
    if index > 0:
        neighbor_families.append(relation_family(rows[index - 1]))
    if index + 1 < len(rows):
        neighbor_families.append(relation_family(rows[index + 1]))
    consistency = 1.0 if family in neighbor_families else 0.5 if not neighbor_families else 0.25
    conflict = 0.0 if consistency >= 0.5 else 0.15
    return round(prev_anchor, 4), round(next_anchor, 4), round(neighbor_window, 4), round(consistency, 4), round(conflict, 4)


def adjusted_scores_for_row(
    candidates: list[Candidate],
    selected_path: list[Candidate],
    index: int,
    rows: list[dict[str, Any]],
) -> list[tuple[Candidate, float, tuple[float, float, float, float, float]]]:
    scored = []
    for candidate in candidates:
        prev_anchor, next_anchor, neighbor_window, consistency, conflict = neighbor_scores(selected_path, index, candidate, rows)
        support = non_order_support(candidate, prev_anchor, next_anchor)
        score = candidate.local_score + 0.10 * neighbor_window + 0.06 * consistency - conflict + min(0.12, support * 0.12)
        scored.append((candidate, round(score, 4), (prev_anchor, next_anchor, neighbor_window, consistency, conflict)))
    return sorted(scored, key=lambda item: item[1], reverse=True)


def choose_assignments(rows: list[dict[str, Any]], commentary_by_id: dict[str, dict[str, Any]], pack: Any) -> dict[str, AssignmentChoice]:
    linked_rows = [row for row in rows if is_linked(row)]
    if not linked_rows:
        return {}
    ordered = sorted(linked_rows, key=lambda row: (int(row.get("source_start_char") or 0), int(row.get("target_start_char") or 0)))
    candidate_lists = [
        build_candidates_for_row(row, ordered, commentary_by_id.get(str(row.get("commentary_id", "")), {}), pack)
        for row in ordered
    ]
    forward_indices, forward_score = run_dp(candidate_lists, direction="forward")
    reverse_indices, reverse_score = run_dp(candidate_lists, direction="reverse")
    use_reverse = reverse_score > forward_score + 0.08
    chosen_indices = reverse_indices if use_reverse and reverse_indices else forward_indices
    method = "global_reverse" if use_reverse else "global_forward"
    if not chosen_indices:
        return {}
    selected_path = [candidate_lists[index][chosen] for index, chosen in enumerate(chosen_indices)]
    choices: dict[str, AssignmentChoice] = {}
    for index, row in enumerate(ordered):
        local_sorted = sorted(candidate_lists[index], key=lambda candidate: candidate.local_score, reverse=True)
        adjusted = adjusted_scores_for_row(candidate_lists[index], selected_path, index, ordered)
        selected = selected_path[index]
        selected_adjusted = next((score for candidate, score, _ in adjusted if candidate.target_key == selected.target_key), selected.local_score)
        alternatives = [score for candidate, score, _ in adjusted if candidate.target_key != selected.target_key]
        second_score = alternatives[0] if alternatives else 0.0
        selected_neighbor = next((payload for candidate, _, payload in adjusted if candidate.target_key == selected.target_key), (0.0, 0.0, 0.5, 0.5, 0.0))
        choices[str(row.get("link_id", ""))] = AssignmentChoice(
            candidate=selected,
            global_score=round(selected_adjusted, 4),
            best_score=round(selected_adjusted, 4),
            second_score=round(second_score, 4),
            margin=round(selected_adjusted - second_score, 4),
            local_best=local_sorted[0],
            local_second=local_sorted[1] if len(local_sorted) > 1 else None,
            prev_anchor_score=selected_neighbor[0],
            next_anchor_score=selected_neighbor[1],
            neighbor_window_score=selected_neighbor[2],
            relation_family_consistency_score=selected_neighbor[3],
            relation_family_conflict_penalty=selected_neighbor[4],
            method=method,
            forward_alignment_score=forward_score,
            reverse_alignment_score=reverse_score,
        )
    return choices


def target_reuse_allowed(row: dict[str, Any], count: int) -> tuple[bool, str]:
    if count <= 1:
        return True, "unique_target"
    if row.get("relationship_type") == "explains_line":
        return True, "explains_line_allows_shared_target"
    if row.get("split_parent_id"):
        return True, "split_parent_allows_shared_target"
    target_count = len(tokens(str(row.get("target_text", ""))))
    source_count = max(1, len(tokens(str(row.get("source_text", "")))))
    if target_count / source_count >= 6:
        return True, "broad_context_target_reuse_reviewed"
    return False, "suspicious_target_reuse"


def update_row(row: dict[str, Any], choice: AssignmentChoice | None, reuse_count: int, reuse_ok: bool, reuse_reason: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    item = dict(row)
    ambiguous_before = is_ambiguous(row)
    penalties = list(row.get("penalties_applied") or [])
    critical = list(row.get("critical_warnings") or [])
    confidence_before = str(row.get("confidence", ""))
    confidence_after = confidence_before
    manual_review = bool(row.get("manual_review_required"))
    decision = "KEEP_REVIEW" if ambiguous_before else ""
    reason = "not_ambiguous_span"
    old_target = str(row.get("target_text", ""))

    if choice is None:
        item.update(
            {
                "schema_version": SCHEMA_VERSION,
                "base_schema_version": row.get("schema_version", ""),
                "ambiguous_span_before": ambiguous_before,
                "best_target_score": 0.0,
                "second_best_target_score": 0.0,
                "best_second_margin": raw_margin(row),
                "local_best_target_text": old_target,
                "second_best_target_text": "",
                "global_selected_target_text": old_target,
                "global_assignment_score": 0.0,
                "forward_alignment_score": 0.0,
                "reverse_alignment_score": 0.0,
                "sequence_alignment_method": "local_only",
                "prev_anchor_score": 0.0,
                "next_anchor_score": 0.0,
                "neighbor_window_score": 0.0,
                "relation_family_consistency_score": 0.0,
                "relation_family_conflict_penalty": 0.0,
                "target_reuse_count": reuse_count,
                "target_reuse_allowed": reuse_ok,
                "target_reuse_reason": reuse_reason,
                "ambiguity_resolution_decision": decision,
                "ambiguity_resolution_reason": reason,
            }
        )
        return item, None

    selected = choice.candidate
    local_disagrees = selected.target_key != choice.local_best.target_key
    target_changed = selected.text != old_target or selected.start != int(row.get("target_start_char") or -1) or selected.end != int(row.get("target_end_char") or -1)
    support = non_order_support(selected, choice.prev_anchor_score, choice.next_anchor_score)
    very_low_margin = choice.margin < 0.05
    family_conflict = choice.relation_family_conflict_penalty > 0
    safe_resolution = (
        ambiguous_before
        and choice.margin >= 0.05
        and support >= 0.18
        and reuse_ok
        and not family_conflict
        and (not target_changed or (choice.margin >= 0.12 and support >= 0.25))
    )

    if ambiguous_before and safe_resolution:
        penalties = [penalty for penalty in penalties if penalty != AMBIGUOUS_PENALTY]
        if choice.margin >= 0.05:
            critical = [warning for warning in critical if warning != AMBIGUOUS_WARNING]
        if target_changed:
            item["target_start_char"] = selected.start
            item["target_end_char"] = selected.end
            item["target_text"] = selected.text
            item["target_field"] = selected.target_field
            decision = "REASSIGN_TARGET"
            reason = "global_assignment_selected_better_supported_target"
        elif confidence_before == "medium" and choice.margin >= 0.12 and not has_high_blocker(row, penalties, critical):
            confidence_after = "high"
            manual_review = False
            decision = "PROMOTE_TO_HIGH"
            reason = "global_margin_and_non_order_support_clear_ambiguity"
        elif confidence_before == "low" and choice.margin >= 0.05:
            confidence_after = "medium"
            manual_review = bool(penalties or critical)
            decision = "PROMOTE_TO_MEDIUM"
            reason = "global_assignment_margin_supports_medium_confidence"
        else:
            manual_review = bool(penalties or critical)
            decision = "KEEP_REVIEW" if manual_review else "PROMOTE_TO_MEDIUM"
            reason = "ambiguity_penalty_removed_but_other_review_flags_remain"
    elif ambiguous_before:
        decision = "KEEP_REVIEW"
        if very_low_margin:
            reason = "best_second_margin_below_0_05"
        elif local_disagrees:
            reason = "global_assignment_disagrees_with_local_best"
        elif not reuse_ok:
            reason = "suspicious_target_reuse"
        elif family_conflict:
            reason = "relation_family_conflict"
        else:
            reason = "insufficient_non_order_support"

    score_after = float(row.get("score") or 0.0)
    if confidence_after == "high":
        score_after = max(score_after, 0.83)
    elif confidence_after == "medium":
        score_after = max(score_after, 0.58)

    item.update(
        {
            "schema_version": SCHEMA_VERSION,
            "base_schema_version": row.get("schema_version", ""),
            "ambiguous_span_before": ambiguous_before,
            "best_target_score": choice.best_score,
            "second_best_target_score": choice.second_score,
            "best_second_margin": choice.margin,
            "local_best_target_text": choice.local_best.text,
            "second_best_target_text": choice.local_second.text if choice.local_second else "",
            "global_selected_target_text": selected.text,
            "global_assignment_score": choice.global_score,
            "forward_alignment_score": choice.forward_alignment_score,
            "reverse_alignment_score": choice.reverse_alignment_score,
            "sequence_alignment_method": choice.method,
            "prev_anchor_score": choice.prev_anchor_score,
            "next_anchor_score": choice.next_anchor_score,
            "neighbor_window_score": choice.neighbor_window_score,
            "relation_family_consistency_score": choice.relation_family_consistency_score,
            "relation_family_conflict_penalty": choice.relation_family_conflict_penalty,
            "target_reuse_count": reuse_count,
            "target_reuse_allowed": reuse_ok,
            "target_reuse_reason": reuse_reason,
            "ambiguity_resolution_decision": decision,
            "ambiguity_resolution_reason": reason,
            "penalties_applied": penalties,
            "critical_warnings": critical,
            "confidence": confidence_after,
            "score": round(score_after, 4),
            "manual_review_required": manual_review,
            "rule_ids_applied": list(row.get("rule_ids_applied") or []) + (["ambiguous_span_global_assignment_reranker"] if safe_resolution else []),
            "diagnostic_note": f"{row.get('diagnostic_note', '')} Ambiguous-span reranker: {reason}.",
        }
    )
    change = None
    if ambiguous_before:
        change = {
            "link_id": item.get("link_id", ""),
            "issue_before": "ambiguous_span",
            "source_text": item.get("source_text", ""),
            "old_target_text": old_target,
            "new_target_text": item.get("target_text", ""),
            "local_best_target_text": choice.local_best.text,
            "second_best_target_text": choice.local_second.text if choice.local_second else "",
            "best_target_score": choice.best_score,
            "second_best_target_score": choice.second_score,
            "best_second_margin": choice.margin,
            "global_assignment_score": choice.global_score,
            "sequence_alignment_method": choice.method,
            "prev_anchor_score": choice.prev_anchor_score,
            "next_anchor_score": choice.next_anchor_score,
            "relation_family_consistency_score": choice.relation_family_consistency_score,
            "target_reuse_count": reuse_count,
            "confidence_before": confidence_before,
            "confidence_after": confidence_after,
            "ambiguity_resolution_decision": decision,
            "reason": reason,
        }
    return item, change


def apply_ambiguity_fix(rows: list[dict[str, Any]], table_root: Path, pack: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    commentary_by_id = {str(row.get("commentary_id", "")): row for row in load_jsonl(table_root / "commentaries.jsonl")}
    by_group: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_group[(str(row.get("paadal_id", "")), str(row.get("commentary_id", "")))].append(row)

    choices_by_id: dict[str, AssignmentChoice] = {}
    for group_rows in by_group.values():
        if any(is_ambiguous(row) for row in group_rows):
            choices_by_id.update(choose_assignments(group_rows, commentary_by_id, pack))

    selected_target_counts: Counter[tuple[str, str, int, int, str]] = Counter()
    for row in rows:
        choice = choices_by_id.get(str(row.get("link_id", "")))
        if choice is None:
            continue
        key = (str(row.get("paadal_id", "")), choice.candidate.target_field, choice.candidate.start, choice.candidate.end, choice.candidate.text)
        selected_target_counts[key] += 1

    fixed = []
    changes = []
    for row in rows:
        choice = choices_by_id.get(str(row.get("link_id", "")))
        if choice is None:
            item, change = update_row(row, None, 0, True, "not_linked_or_no_group_assignment")
        else:
            key = (str(row.get("paadal_id", "")), choice.candidate.target_field, choice.candidate.start, choice.candidate.end, choice.candidate.text)
            reuse_count = selected_target_counts[key]
            reuse_ok, reuse_reason = target_reuse_allowed(row, reuse_count)
            item, change = update_row(row, choice, reuse_count, reuse_ok, reuse_reason)
        fixed.append(item)
        if change is not None:
            changes.append(change)
    return fixed, changes


def ambiguous_count(rows: list[dict[str, Any]]) -> int:
    return sum(is_ambiguous(row) for row in rows)


def average_margin(rows: list[dict[str, Any]]) -> float:
    margins = [raw_margin(row) for row in rows if is_ambiguous(row)]
    return round(sum(margins) / len(margins), 4) if margins else 0.0


def baseline_counts(base_root: Path) -> dict[str, Any]:
    full = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_full.jsonl")
    primary = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_primary_clean_links.jsonl")
    return {
        "total_links": len(full),
        "primary_links": len(primary),
        "full_confidence": dict(sorted(Counter(row.get("confidence", "") for row in full).items())),
        "primary_confidence": dict(sorted(Counter(row.get("confidence", "") for row in primary).items())),
        "full_ambiguous_span_count": ambiguous_count(full),
        "primary_ambiguous_span_count": ambiguous_count(primary),
        "manual_review_required_count": sum(bool(row.get("manual_review_required")) for row in full),
        "relationship_type_counts": dict(sorted(Counter(row.get("relationship_type", "") for row in full).items())),
        "average_best_second_margin": average_margin(full),
        "primary_average_best_second_margin": average_margin(primary),
    }


def manual_review_rows(rows: list[dict[str, Any]], table_root: Path) -> list[dict[str, Any]]:
    paadal_by_id = {str(row.get("paadal_id", "")): str(row.get("paadal_text", "")) for row in load_jsonl(table_root / "paadalgal.jsonl")}
    commentary_by_id = {str(row.get("commentary_id", "")): row for row in load_jsonl(table_root / "commentaries.jsonl")}
    sorted_rows = sorted([row for row in rows if is_linked(row)], key=lambda row: (str(row.get("paadal_id", "")), int(row.get("source_start_char") or 0)))
    index_by_link = {str(row.get("link_id", "")): index for index, row in enumerate(sorted_rows)}
    review = []
    for row in rows:
        if not row.get("ambiguous_span_before"):
            continue
        reason = str(row.get("ambiguity_resolution_reason", ""))
        if AMBIGUOUS_PENALTY not in (row.get("penalties_applied") or []) and reason not in {
            "best_second_margin_below_0_05",
            "global_assignment_disagrees_with_local_best",
            "suspicious_target_reuse",
            "relation_family_conflict",
        }:
            continue
        commentary = commentary_by_id.get(str(row.get("commentary_id", "")), {})
        idx = index_by_link.get(str(row.get("link_id", "")), -1)
        previous = sorted_rows[idx - 1] if idx > 0 and sorted_rows[idx - 1].get("paadal_id") == row.get("paadal_id") else {}
        next_item = sorted_rows[idx + 1] if idx >= 0 and idx + 1 < len(sorted_rows) and sorted_rows[idx + 1].get("paadal_id") == row.get("paadal_id") else {}
        review.append(
            {
                "link_id": row.get("link_id", ""),
                "source_text": row.get("source_text", ""),
                "local_best_target_text": row.get("local_best_target_text", ""),
                "second_best_target_text": row.get("second_best_target_text", ""),
                "global_selected_target_text": row.get("global_selected_target_text", ""),
                "best_second_margin": row.get("best_second_margin", ""),
                "source_relationship_type": row.get("relationship_type", ""),
                "candidate_relationship_types": row.get("relationship_type", ""),
                "prev_link_summary": f"{previous.get('source_text', '')} -> {previous.get('target_text', '')}",
                "next_link_summary": f"{next_item.get('source_text', '')} -> {next_item.get('target_text', '')}",
                "reason_for_review": reason,
                "full_paadal_if_available": paadal_by_id.get(str(row.get("paadal_id", "")), ""),
                "full_pozhippurai_if_available": commentary.get("pozhppurai", ""),
                "kurippurai_if_available": commentary.get("kurippurai", ""),
            }
        )
    return review[:5000]


def summarize(
    full: list[dict[str, Any]],
    primary: list[dict[str, Any]],
    changes: list[dict[str, Any]],
    baseline: dict[str, Any],
    validation: dict[str, Any],
    primary_validation: dict[str, Any],
    prior_high_link_ids: set[str],
) -> dict[str, Any]:
    primary_confidence = Counter(row.get("confidence", "") for row in primary)
    high_before = int(baseline.get("primary_confidence", {}).get("high", 0))
    high_after = primary_confidence.get("high", 0)
    current_high_link_ids = {str(row.get("link_id", "")) for row in primary if row.get("confidence") == "high"}
    lost_prior_high = sorted(prior_high_link_ids - current_high_link_ids)
    ambiguous_before = int(baseline.get("primary_ambiguous_span_count", 0))
    ambiguous_after = ambiguous_count(primary)
    decision_counts = Counter(row.get("ambiguity_resolution_decision", "") for row in changes)
    accepted = (
        ambiguous_after < ambiguous_before
        and high_after >= high_before
        and not lost_prior_high
        and validation.get("status") == "VALID"
        and primary_validation.get("status") == "VALID"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "run_status": "accepted" if accepted else "rejected_acceptance_rule_failed",
        "accepted": accepted,
        "baseline": baseline,
        "total_links": len(full),
        "primary_clean_links": len(primary),
        "full_confidence": dict(sorted(Counter(row.get("confidence", "") for row in full).items())),
        "primary_confidence": dict(sorted(primary_confidence.items())),
        "full_ambiguous_span_count": ambiguous_count(full),
        "primary_ambiguous_span_count": ambiguous_after,
        "ambiguous_rows_resolved": ambiguous_before - ambiguous_after,
        "high_confidence_gained": max(0, high_after - high_before),
        "high_confidence_lost": max(0, high_before - high_after),
        "prior_high_primary_links_checked": len(prior_high_link_ids),
        "prior_high_primary_links_lost": len(lost_prior_high),
        "lost_prior_high_link_ids_sample": lost_prior_high[:25],
        "medium_upgraded_to_high": decision_counts.get("PROMOTE_TO_HIGH", 0),
        "low_upgraded_to_medium": decision_counts.get("PROMOTE_TO_MEDIUM", 0),
        "rows_kept_in_review_due_to_low_margin": sum(1 for row in changes if row.get("reason") == "best_second_margin_below_0_05"),
        "rows_reassigned_to_different_target": decision_counts.get("REASSIGN_TARGET", 0),
        "rows_with_reverse_alignment": sum(1 for row in primary if row.get("sequence_alignment_method") == "global_reverse"),
        "rows_with_suspicious_target_reuse": sum(1 for row in primary if row.get("target_reuse_reason") == "suspicious_target_reuse"),
        "manual_review_required_count": sum(bool(row.get("manual_review_required")) for row in full),
        "relationship_type_counts": dict(sorted(Counter(row.get("relationship_type", "") for row in full).items())),
        "ambiguity_resolution_decisions": dict(sorted(decision_counts.items())),
        "anchor_change_rows": len(changes),
        "validation": validation,
        "primary_validation": primary_validation,
    }


def render_report(summary: dict[str, Any], output_root: Path, changes: list[dict[str, Any]]) -> str:
    def table(mapping: dict[str, Any]) -> str:
        return "\n".join(f"| `{key}` | {value} |" for key, value in mapping.items()) or "| None | 0 |"

    safe_examples = [row for row in changes if row.get("ambiguity_resolution_decision") in {"PROMOTE_TO_HIGH", "PROMOTE_TO_MEDIUM", "REASSIGN_TARGET"}][:5]
    unresolved = [row for row in changes if row.get("ambiguity_resolution_decision") == "KEEP_REVIEW"][:5]
    baseline = summary["baseline"]
    return f"""# Paadal-Pozhippurai v4 Ambiguous Span Fix Report

## Acceptance

- Run status: `{summary['run_status']}`
- Accepted: `{str(summary['accepted']).lower()}`
- Output root: `{output_root}`
- Schema version: `{summary['schema_version']}`

## Baseline Versus Current

- Baseline total links: `{baseline['total_links']}`
- New total links: `{summary['total_links']}`
- Baseline primary high confidence: `{baseline['primary_confidence'].get('high', 0)}`
- New primary high confidence: `{summary['primary_confidence'].get('high', 0)}`
- Baseline primary ambiguous span count: `{baseline['primary_ambiguous_span_count']}`
- New primary ambiguous span count: `{summary['primary_ambiguous_span_count']}`
- Ambiguous rows resolved: `{summary['ambiguous_rows_resolved']}`
- High confidence gained: `{summary['high_confidence_gained']}`
- High confidence lost: `{summary['high_confidence_lost']}`
- Medium upgraded to high: `{summary['medium_upgraded_to_high']}`
- Low upgraded to medium: `{summary['low_upgraded_to_medium']}`
- Rows kept in review due to low margin: `{summary['rows_kept_in_review_due_to_low_margin']}`
- Rows reassigned to different target: `{summary['rows_reassigned_to_different_target']}`
- Rows with reverse alignment: `{summary['rows_with_reverse_alignment']}`
- Rows with suspicious target reuse: `{summary['rows_with_suspicious_target_reuse']}`
- Validation status: `{summary['validation']['status']}`
- Primary validation status: `{summary['primary_validation']['status']}`

## Confidence Distribution

| Confidence | Rows |
| --- | ---: |
{table(summary['full_confidence'])}

## Decisions

| Decision | Rows |
| --- | ---: |
{table(summary['ambiguity_resolution_decisions'])}

## Safe Resolution Examples

{json.dumps(safe_examples, ensure_ascii=False, indent=2)}

## Unresolved Examples

{json.dumps(unresolved, ensure_ascii=False, indent=2)}

## Notes

- This pass fixes only `ambiguous_span`.
- Missing anchors, broad targets, order-only rows, UI, scraper, and parser were not changed.
- High confidence is protected by count and prior-link preservation gates.
- This is a deterministic linker hardening pass, not final scholarly gold accuracy.
"""


def write_outputs(
    output_root: Path,
    full: list[dict[str, Any]],
    primary: list[dict[str, Any]],
    secondary: list[dict[str, Any]],
    changes: list[dict[str, Any]],
    review_rows: list[dict[str, Any]],
    summary: dict[str, Any],
    report_path: Path,
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_full.jsonl", full)
    write_tsv(output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_full.tsv", full)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_primary_clean_links.jsonl", primary)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_primary_clean_links.csv", primary)
    high_rows = [row for row in full if row.get("confidence") == "high" and not row.get("manual_review_required")]
    medium_rows = [row for row in full if row.get("confidence") == "medium" and not row.get("manual_review_required")]
    low_review_rows = [row for row in full if row.get("confidence") == "low" or row.get("manual_review_required")]
    no_link_rows = [row for row in full if row.get("confidence") == "no_link" or row.get("relationship_type") == "unlinked"]
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_high_confidence.jsonl", high_rows)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_medium_confidence.jsonl", medium_rows)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_low_review.csv", low_review_rows)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_no_link_or_unresolved.csv", no_link_rows)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_ambiguity_changes.csv", changes)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_manual_review_pack.csv", review_rows)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_general_manual_review_pack.csv", build_manual_review_pack(full))
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_secondary_no_link.jsonl", secondary)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_secondary_no_link.csv", secondary)
    write_iob_v4(output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_corrected_usable.iob.conll", [row for row in full if row.get("confidence") in {"high", "medium"} and row.get("target_text")])
    (output_root / "paadal_pozhippurai_links_v4_ambiguous_span_fixed_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report = render_report(summary, output_root, changes)
    report_path.write_text(report, encoding="utf-8")
    (output_root / "baseline_vs_ambiguous_span_fixed_report.md").write_text(report, encoding="utf-8")


def run_fix(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    base_root: Path = DEFAULT_BASE_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    pack = load_hardening_pack()
    full = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_full.jsonl")
    primary = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_primary_clean_links.jsonl")
    secondary = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_secondary_no_link.jsonl")
    baseline = baseline_counts(base_root)
    (base_root / "paadal_pozhippurai_links_v4_ambiguous_span_baseline_counts.json").write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    prior_high_link_ids = {str(row.get("link_id", "")) for row in primary if row.get("confidence") == "high"}
    fixed_full, changes_full = apply_ambiguity_fix(full, table_root, pack)
    fixed_primary, changes_primary = apply_ambiguity_fix(primary, table_root, pack)
    validation = validate_v4_links(table_root, fixed_full)
    primary_validation = validate_clean_links(table_root, fixed_primary)
    summary = summarize(fixed_full, fixed_primary, changes_primary, baseline, validation, primary_validation, prior_high_link_ids)
    review_rows = manual_review_rows(fixed_full, table_root)
    write_outputs(output_root, fixed_full, fixed_primary, secondary, changes_primary, review_rows, summary, report_path)
    return {**summary, "output_root": str(output_root), "report": str(report_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fix ambiguous paadal-pozhppurai spans with global assignment reranking.")
    parser.add_argument("--table-root", "--input-root", dest="table_root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--base-root", type=Path, default=DEFAULT_BASE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = run_fix(table_root=args.table_root, base_root=args.base_root, output_root=args.output_root, report_path=args.report)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
