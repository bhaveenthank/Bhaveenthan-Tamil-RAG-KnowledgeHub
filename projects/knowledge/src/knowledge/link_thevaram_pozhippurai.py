from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

SCHEMA_VERSION = "thevaram-pozhppurai-paadallink-v2"
DEFAULT_TABLE_ROOT = Path("data/processed/thevaram_normalized")
DEFAULT_ENTITY_ROOT = Path("data/processed/thevaram_entity_annotations_v3")
DEFAULT_SYNONYMS_PATH = Path("data/knowledge/synonyms.json")
DEFAULT_SEED_DIR = Path(
    "/Users/bhaveenthankajanikanth/Desktop/Tamil RAG/Paadal - Pozhippurai Annotation/"
    "thevaram_pozhippurai_paadallink_seed_dataset"
)
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_pozhippurai_links_v2")
DEFAULT_REPORT = Path("reports/thevaram-pozhppurai-paadallink-v2-report.md")

TOKEN_SPLIT_RE = re.compile(r"[\s,.;:!?()\[\]{}\"'“”‘’\-]+")
SEGMENT_END_RE = re.compile(r"[.!?।]+|[;,]+|[,，]")
STANDALONE_NUMBERING_RE = re.compile(r"^[0-9०-९௦-௯]+[.)]?$")
RELATION_TYPES = {
    "describes_entity",
    "explains_line",
    "explains_phrase",
    "glosses_word",
    "interprets_image",
    "theological_explanation",
}

THEOLOGY_HINTS = {
    "அருள்",
    "தொழு",
    "தொழுது",
    "வணங்கு",
    "பணி",
    "பணிந்து",
    "தவம்",
    "வினை",
    "பதி",
    "பாசம்",
    "மலம்",
    "ஞானம்",
    "முத்தி",
}
IMAGE_HINTS = {
    "மதி",
    "பிறை",
    "கங்கை",
    "சடை",
    "நீறு",
    "விடை",
    "பாம்பு",
    "அரவு",
    "கொன்றை",
    "மழு",
    "கடல்",
    "புனல்",
    "மலர்",
}
ENTITY_TYPES_FOR_DESCRIBES = {"DEITY", "BODY_PART", "SACRED_OBJECT", "TEMPLE"}


def stable_hash(*parts: object, length: int = 16) -> str:
    raw = "|".join(str(part) for part in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:length]


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFC", value or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    return " ".join(text.strip().split())


def compact_text(value: str) -> str:
    return re.sub(r"\s+", "", normalize_text(value))


def tokens(value: str) -> list[str]:
    return [token for token in TOKEN_SPLIT_RE.split(normalize_text(value)) if token]


def token_set(value: str) -> set[str]:
    return set(tokens(value))


def load_synonym_concepts(path: Path = DEFAULT_SYNONYMS_PATH) -> dict[str, set[str]]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    concepts: dict[str, set[str]] = {}
    for row in payload.get("records", []):
        concept_id = str(row.get("concept_id", ""))
        forms = {
            str(row.get("canonical_term", "")),
            *(str(item) for item in row.get("synonyms", [])),
            *(str(item) for item in row.get("variant_forms", [])),
        }
        forms = {normalize_text(form) for form in forms if normalize_text(form)}
        for form in forms:
            concepts.setdefault(form, set()).add(concept_id)
    return concepts


def concept_set(value: str, synonym_concepts: dict[str, set[str]]) -> set[str]:
    concepts: set[str] = set()
    for token in tokens(value):
        normalized = normalize_text(token)
        concepts.update(synonym_concepts.get(normalized, set()))
    compact = compact_text(value)
    for form, form_concepts in synonym_concepts.items():
        if compact_text(form) and compact_text(form) in compact:
            concepts.update(form_concepts)
    return concepts


def char_ngrams(value: str, n: int = 3) -> set[str]:
    compact = compact_text(value)
    if len(compact) <= n:
        return {compact} if compact else set()
    return {compact[index : index + n] for index in range(len(compact) - n + 1)}


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def containment_score(left: str, right: str) -> float:
    left_compact = compact_text(left)
    right_compact = compact_text(right)
    if not left_compact or not right_compact:
        return 0.0
    if left_compact in right_compact or right_compact in left_compact:
        return min(len(left_compact), len(right_compact)) / max(len(left_compact), len(right_compact))
    left_terms = tokens(left)
    right_joined = compact_text(right)
    if not left_terms:
        return 0.0
    covered = sum(1 for token in left_terms if compact_text(token) in right_joined)
    return covered / len(left_terms)


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


def is_standalone_numbering_line(text: str) -> bool:
    return bool(STANDALONE_NUMBERING_RE.fullmatch((text or "").strip()))


def line_spans(text: str) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    cursor = 0
    for line_no, line in enumerate(text.splitlines(), start=1):
        start = text.find(line, cursor)
        if start < 0:
            continue
        end = start + len(line)
        cursor = end
        if line.strip() and not is_standalone_numbering_line(line):
            spans.append(
                {
                    "line_no": line_no,
                    "start_char": start,
                    "end_char": end,
                    "text": line,
                }
            )
    return spans


def segment_spans(text: str) -> list[dict[str, Any]]:
    spans: list[dict[str, Any]] = []
    start = 0
    segment_no = 1
    for match in SEGMENT_END_RE.finditer(text):
        end = match.end()
        raw = text[start:end]
        stripped = raw.strip()
        if stripped:
            left_trim = len(raw) - len(raw.lstrip())
            right_trim = len(raw.rstrip())
            spans.append(
                {
                    "segment_no": segment_no,
                    "start_char": start + left_trim,
                    "end_char": start + right_trim,
                    "text": text[start + left_trim : start + right_trim],
                }
            )
            segment_no += 1
        start = end
    raw = text[start:]
    stripped = raw.strip()
    if stripped:
        left_trim = len(raw) - len(raw.lstrip())
        right_trim = len(raw.rstrip())
        spans.append(
            {
                "segment_no": segment_no,
                "start_char": start + left_trim,
                "end_char": start + right_trim,
                "text": text[start + left_trim : start + right_trim],
            }
        )
    if not spans and text.strip():
        left = len(text) - len(text.lstrip())
        right = len(text.rstrip())
        return [{"segment_no": 1, "start_char": left, "end_char": right, "text": text[left:right]}]
    return spans


def segment_windows(text: str, segments: list[dict[str, Any]], max_window: int = 3) -> list[dict[str, Any]]:
    windows: list[dict[str, Any]] = []
    for start_index, segment in enumerate(segments):
        for size in range(1, max_window + 1):
            group = segments[start_index : start_index + size]
            if len(group) != size:
                continue
            start = int(group[0]["start_char"])
            end = int(group[-1]["end_char"])
            windows.append(
                {
                    "segment_no": group[0]["segment_no"],
                    "segment_end_no": group[-1]["segment_no"],
                    "window_size": size,
                    "start_char": start,
                    "end_char": end,
                    "text": text[start:end],
                }
            )
    return windows


def segment_order_key(segment: dict[str, Any]) -> tuple[int, int, int]:
    return (
        int(segment.get("segment_no", 0)),
        int(segment.get("segment_end_no", segment.get("segment_no", 0))),
        int(segment.get("window_size", 1)),
    )


def load_seed_relations(seed_dir: Path = DEFAULT_SEED_DIR) -> list[dict[str, str]]:
    path = seed_dir / "thevaram_pozhippurai_paadallink_relations.tsv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def seed_phrase_patterns(seed_relations: list[dict[str, str]]) -> dict[str, Counter[str]]:
    patterns: dict[str, Counter[str]] = defaultdict(Counter)
    for row in seed_relations:
        relation = row.get("relationship_type", "")
        if relation not in RELATION_TYPES:
            continue
        for field in ("paadal_normalized", "pozhppurai_span", "annotation_note"):
            for token in tokens(row.get(field, "")):
                if len(token) >= 3:
                    patterns[token][relation] += 1
    return patterns


def load_entity_mentions(entity_root: Path = DEFAULT_ENTITY_ROOT) -> dict[tuple[str, str], list[dict[str, Any]]]:
    by_parent_field: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in read_jsonl(entity_root / "entity_mentions.jsonl"):
        by_parent_field[(str(row.get("target_id", "")), str(row.get("field_name", "")))].append(row)
    return by_parent_field


def overlapping_entities(
    mentions_by_parent_field: dict[tuple[str, str], list[dict[str, Any]]],
    parent_id: str,
    field_name: str,
    start: int,
    end: int,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for mention in mentions_by_parent_field.get((parent_id, field_name), []):
        mention_start = int(mention.get("start_char", -1))
        mention_end = int(mention.get("end_char", -1))
        if mention_start < end and start < mention_end:
            result.append(mention)
    return result


def ranked_targets_for_line(
    line: dict[str, Any],
    segments: list[dict[str, Any]],
    *,
    paadal_id: str,
    commentary_id: str,
    line_count: int,
    pozhppurai_text: str,
    mentions_by_parent_field: dict[tuple[str, str], list[dict[str, Any]]],
    synonym_concepts: dict[str, set[str]] | None = None,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    synonym_concepts = synonym_concepts or {}
    line_tokens = token_set(str(line["text"]))
    line_ngrams = char_ngrams(str(line["text"]))
    line_concepts = concept_set(str(line["text"]), synonym_concepts)
    line_entities = overlapping_entities(
        mentions_by_parent_field,
        paadal_id,
        "paadal_text",
        int(line["start_char"]),
        int(line["end_char"]),
    )
    line_entity_keys = {
        (str(entity.get("entity_type")), str(entity.get("canonical_id")))
        for entity in line_entities
    }

    candidates = segment_windows(pozhppurai_text, segments)
    ranked: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for segment in candidates:
        segment_text = str(segment["text"])
        segment_tokens = token_set(segment_text)
        segment_ngrams = char_ngrams(segment_text)
        segment_concepts = concept_set(segment_text, synonym_concepts)
        segment_entities = overlapping_entities(
            mentions_by_parent_field,
            commentary_id,
            "pozhppurai",
            int(segment["start_char"]),
            int(segment["end_char"]),
        )
        segment_entity_keys = {
            (str(entity.get("entity_type")), str(entity.get("canonical_id")))
            for entity in segment_entities
        }
        shared_entity_types = sorted(
            entity_type
            for entity_type, canonical_id in (line_entity_keys & segment_entity_keys)
            if entity_type
        )
        token_score = jaccard(line_tokens, segment_tokens)
        char_score = jaccard(line_ngrams, segment_ngrams)
        synonym_score = jaccard(line_concepts, segment_concepts)
        entity_score = jaccard(line_entity_keys, segment_entity_keys)
        contains_score = containment_score(str(line["text"]), segment_text)
        if len(segments) == 1 or line_count <= 1:
            order_score = 0.6
        else:
            line_position = (int(line["line_no"]) - 1) / max(1, line_count - 1)
            segment_position = (
                ((int(segment["segment_no"]) + int(segment["segment_end_no"])) / 2) - 1
            ) / max(1, len(segments) - 1)
            order_score = max(0.0, 1.0 - abs(line_position - segment_position))
        score = round(
            (0.22 * token_score)
            + (0.15 * char_score)
            + (0.13 * synonym_score)
            + (0.20 * entity_score)
            + (0.15 * contains_score)
            + (0.20 * order_score),
            4,
        )
        features = {
            "score": score,
            "base_score": score,
            "token_score": round(token_score, 4),
            "char_score": round(char_score, 4),
            "synonym_score": round(synonym_score, 4),
            "entity_score": round(entity_score, 4),
            "containment_score": round(contains_score, 4),
            "order_score": round(order_score, 4),
            "window_size": segment["window_size"],
            "paadal_entity_count": len(line_entities),
            "pozhppurai_entity_count": len(segment_entities),
            "shared_entity_types": shared_entity_types,
        }
        ranked.append((segment, features))
    ranked = sorted(ranked, key=lambda item: (item[1]["score"], -int(item[0]["window_size"])), reverse=True)
    if ranked:
        best_score = float(ranked[0][1]["score"])
        second_best = float(ranked[1][1]["score"]) if len(ranked) > 1 else 0.0
        for _, features in ranked:
            features["second_best_score"] = second_best
            features["score_margin"] = round(best_score - second_best, 4)
            features["candidate_count"] = len(ranked)
    return ranked


def transition_bonus(previous: dict[str, Any] | None, current: dict[str, Any], *, direction: str = "forward") -> float:
    if previous is None:
        return 0.0
    if direction == "reverse":
        previous_start = int(previous.get("segment_no", 0))
        current_end = int(current.get("segment_end_no", current.get("segment_no", 0)))
        if current_end >= previous_start:
            return -10.0
        gap = previous_start - current_end - 1
    else:
        previous_end = int(previous.get("segment_end_no", previous.get("segment_no", 0)))
        current_start = int(current.get("segment_no", 0))
        if current_start <= previous_end:
            return -10.0
        gap = current_start - previous_end - 1
    if gap == 0:
        return 0.12
    if gap == 1:
        return 0.08
    if gap == 2:
        return 0.04
    return 0.0


def align_lines_to_targets(
    lines: list[dict[str, Any]],
    segments: list[dict[str, Any]],
    *,
    paadal_id: str,
    commentary_id: str,
    pozhppurai_text: str,
    mentions_by_parent_field: dict[tuple[str, str], list[dict[str, Any]]],
    synonym_concepts: dict[str, set[str]] | None = None,
    direction: str = "forward",
) -> dict[int, tuple[dict[str, Any], dict[str, Any]]]:
    """Choose a globally monotonic line->pozhppurai path.

    This is a Viterbi/Needleman-Wunsch style dynamic program over candidate
    target windows. It keeps poem/commentary order intact, so a weak middle
    line can be resolved by strong neighboring anchors.
    """
    if not lines or not segments:
        return {}
    ranked_by_line = [
        ranked_targets_for_line(
            line,
            segments,
            paadal_id=paadal_id,
            commentary_id=commentary_id,
            line_count=len(lines),
            pozhppurai_text=pozhppurai_text,
            mentions_by_parent_field=mentions_by_parent_field,
            synonym_concepts=synonym_concepts,
        )
        for line in lines
    ]
    if any(not ranked for ranked in ranked_by_line):
        return {}

    scores: list[list[float]] = []
    back: list[list[int | None]] = []
    for line_index, ranked in enumerate(ranked_by_line):
        line_scores: list[float] = []
        line_back: list[int | None] = []
        if line_index == 0:
            for _, features in ranked:
                line_scores.append(float(features["score"]))
                line_back.append(None)
        else:
            previous_ranked = ranked_by_line[line_index - 1]
            for segment, features in ranked:
                best_score = -1_000_000.0
                best_previous: int | None = None
                for previous_index, (previous_segment, _) in enumerate(previous_ranked):
                    bonus = transition_bonus(previous_segment, segment, direction=direction)
                    if bonus < -1:
                        continue
                    candidate_score = scores[line_index - 1][previous_index] + float(features["score"]) + bonus
                    if candidate_score > best_score:
                        best_score = candidate_score
                        best_previous = previous_index
                line_scores.append(best_score)
                line_back.append(best_previous)
        scores.append(line_scores)
        back.append(line_back)

    final_index = max(range(len(scores[-1])), key=lambda idx: scores[-1][idx])
    chosen_indices = [final_index]
    for line_index in range(len(lines) - 1, 0, -1):
        previous = back[line_index][chosen_indices[-1]]
        if previous is None:
            previous = max(range(len(scores[line_index - 1])), key=lambda idx: scores[line_index - 1][idx])
        chosen_indices.append(previous)
    chosen_indices.reverse()

    aligned: dict[int, tuple[dict[str, Any], dict[str, Any]]] = {}
    chosen_segments = [ranked_by_line[index][chosen_index][0] for index, chosen_index in enumerate(chosen_indices)]
    for line_index, (line, ranked, chosen_index) in enumerate(zip(lines, ranked_by_line, chosen_indices)):
        segment, features = ranked[chosen_index]
        adjusted = dict(features)
        previous_segment = chosen_segments[line_index - 1] if line_index > 0 else None
        next_segment = chosen_segments[line_index + 1] if line_index + 1 < len(chosen_segments) else None
        previous_bonus = max(0.0, transition_bonus(previous_segment, segment, direction=direction))
        next_bonus = max(0.0, transition_bonus(segment, next_segment, direction=direction)) if next_segment is not None else 0.0
        bonus = max(previous_bonus, next_bonus)
        adjusted["sequence_alignment_bonus"] = round(bonus, 4)
        adjusted["previous_sequence_alignment_bonus"] = round(previous_bonus, 4)
        adjusted["next_sequence_alignment_bonus"] = round(next_bonus, 4)
        adjusted["sequence_alignment_method"] = f"{direction}_dynamic_programming"
        adjusted["score"] = round(min(0.99, float(adjusted["base_score"]) + bonus), 4)
        aligned[int(line["line_no"])] = (segment, adjusted)
    return aligned


def assignment_conflict(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_start = int(left.get("segment_no", 0))
    left_end = int(left.get("segment_end_no", left_start))
    right_start = int(right.get("segment_no", 0))
    right_end = int(right.get("segment_end_no", right_start))
    return left_start <= right_end and right_start <= left_end


def align_lines_by_assignment(
    lines: list[dict[str, Any]],
    segments: list[dict[str, Any]],
    *,
    paadal_id: str,
    commentary_id: str,
    pozhppurai_text: str,
    mentions_by_parent_field: dict[tuple[str, str], list[dict[str, Any]]],
    synonym_concepts: dict[str, set[str]] | None = None,
    top_k: int = 8,
) -> dict[int, tuple[dict[str, Any], dict[str, Any]]]:
    if not lines or not segments:
        return {}
    ranked_by_line = [
        ranked_targets_for_line(
            line,
            segments,
            paadal_id=paadal_id,
            commentary_id=commentary_id,
            line_count=len(lines),
            pozhppurai_text=pozhppurai_text,
            mentions_by_parent_field=mentions_by_parent_field,
            synonym_concepts=synonym_concepts,
        )[:top_k]
        for line in lines
    ]
    states: dict[tuple[int, ...], tuple[float, list[int]]] = {(): (0.0, [])}
    for ranked in ranked_by_line:
        next_states: dict[tuple[int, ...], tuple[float, list[int]]] = {}
        for used_indices, (score_so_far, choices) in states.items():
            used_segments = [ranked_by_line[line_idx][choice_idx][0] for line_idx, choice_idx in enumerate(choices)]
            for candidate_index, (segment, features) in enumerate(ranked):
                if any(assignment_conflict(segment, used) for used in used_segments):
                    continue
                key = tuple(sorted((*used_indices, candidate_index + (len(choices) * top_k))))
                score = score_so_far + float(features.get("score", 0.0))
                current = next_states.get(key)
                if current is None or score > current[0]:
                    next_states[key] = (score, [*choices, candidate_index])
        if not next_states:
            return {}
        states = dict(sorted(next_states.items(), key=lambda item: item[1][0], reverse=True)[:500])
    _, best_choices = max(states.values(), key=lambda item: item[0])
    aligned: dict[int, tuple[dict[str, Any], dict[str, Any]]] = {}
    for line, ranked, choice in zip(lines, ranked_by_line, best_choices):
        segment, features = ranked[choice]
        adjusted = dict(features)
        adjusted["sequence_alignment_bonus"] = 0.06
        adjusted["sequence_alignment_method"] = "unordered_assignment"
        adjusted["score"] = round(min(0.99, float(adjusted["base_score"]) + 0.06), 4)
        aligned[int(line["line_no"])] = (segment, adjusted)
    return aligned


def alignment_total(aligned: dict[int, tuple[dict[str, Any], dict[str, Any]]]) -> float:
    return sum(float(features.get("score", 0.0)) for _, features in aligned.values())


def choose_best_alignment(
    lines: list[dict[str, Any]],
    segments: list[dict[str, Any]],
    *,
    paadal_id: str,
    commentary_id: str,
    pozhppurai_text: str,
    mentions_by_parent_field: dict[tuple[str, str], list[dict[str, Any]]],
    synonym_concepts: dict[str, set[str]] | None = None,
) -> dict[int, tuple[dict[str, Any], dict[str, Any]]]:
    candidates = [
        align_lines_to_targets(
            lines,
            segments,
            paadal_id=paadal_id,
            commentary_id=commentary_id,
            pozhppurai_text=pozhppurai_text,
            mentions_by_parent_field=mentions_by_parent_field,
            synonym_concepts=synonym_concepts,
            direction="forward",
        ),
        align_lines_to_targets(
            lines,
            segments,
            paadal_id=paadal_id,
            commentary_id=commentary_id,
            pozhppurai_text=pozhppurai_text,
            mentions_by_parent_field=mentions_by_parent_field,
            synonym_concepts=synonym_concepts,
            direction="reverse",
        ),
        align_lines_by_assignment(
            lines,
            segments,
            paadal_id=paadal_id,
            commentary_id=commentary_id,
            pozhppurai_text=pozhppurai_text,
            mentions_by_parent_field=mentions_by_parent_field,
            synonym_concepts=synonym_concepts,
        ),
    ]
    return max(candidates, key=alignment_total)


def best_target_for_line(
    line: dict[str, Any],
    segments: list[dict[str, Any]],
    *,
    paadal_id: str,
    commentary_id: str,
    line_count: int,
    pozhppurai_text: str,
    mentions_by_parent_field: dict[tuple[str, str], list[dict[str, Any]]],
    synonym_concepts: dict[str, set[str]] | None = None,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    ranked = ranked_targets_for_line(
        line,
        segments,
        paadal_id=paadal_id,
        commentary_id=commentary_id,
        line_count=line_count,
        pozhppurai_text=pozhppurai_text,
        mentions_by_parent_field=mentions_by_parent_field,
        synonym_concepts=synonym_concepts,
    )
    if not ranked:
        return None, {}
    return ranked[0]


def confidence_for(features: dict[str, Any], pozhppurai_text: str) -> str:
    if not pozhppurai_text.strip():
        return "none"
    score = float(features.get("score", 0.0))
    strong_evidence = (
        float(features.get("token_score", 0.0)) >= 0.18
        or float(features.get("synonym_score", 0.0)) >= 0.5
        or float(features.get("entity_score", 0.0)) >= 0.5
        or float(features.get("containment_score", 0.0)) >= 0.45
    )
    if score >= 0.52 and strong_evidence:
        return "high"
    if score >= 0.32 or (score >= 0.27 and strong_evidence):
        return "medium"
    return "low"


def diagnostic_category(confidence: str, features: dict[str, Any], pozhppurai_text: str) -> str:
    if confidence == "none" or not pozhppurai_text.strip():
        return "missing_pozhippurai"
    if confidence == "high":
        return "strong_link"
    if confidence == "medium":
        return "usable_review"
    token_score = float(features.get("token_score", 0.0))
    char_score = float(features.get("char_score", 0.0))
    synonym_score = float(features.get("synonym_score", 0.0))
    entity_score = float(features.get("entity_score", 0.0))
    containment = float(features.get("containment_score", 0.0))
    order_score = float(features.get("order_score", 0.0))
    margin = float(features.get("score_margin", 0.0))
    alignment_bonus = float(features.get("sequence_alignment_bonus", 0.0))
    if max(token_score, char_score, synonym_score, entity_score, containment) == 0 and order_score > 0:
        return "order_only_weak_match"
    if margin < 0.03 and alignment_bonus < 0.08:
        return "ambiguous_multiple_targets"
    if token_score == 0 and synonym_score == 0 and containment < 0.15:
        return "low_lexical_overlap"
    if entity_score == 0:
        return "no_shared_entity_anchor"
    return "weak_similarity"


def problem_reason_for(category: str) -> str:
    reasons = {
        "strong_link": "High-confidence link with strong lexical/entity/containment evidence.",
        "usable_review": "Medium-confidence link; likely useful but should be sampled before scholarly use.",
        "missing_pozhippurai": "The commentary row has no pozhppurai text.",
        "order_only_weak_match": "The selected target is mainly supported by poem/commentary order, with little lexical or entity evidence.",
        "ambiguous_multiple_targets": "The best target is close to the second-best target, so several pozhppurai spans may be plausible.",
        "low_lexical_overlap": "The paadal line and selected pozhppurai target share little surface vocabulary.",
        "no_shared_entity_anchor": "No accepted Entity v2 anchor overlaps both source and target spans.",
        "weak_similarity": "The link has only weak combined similarity evidence.",
    }
    return reasons.get(category, "Unclassified diagnostic category.")


def relationship_for(
    line_text: str,
    segment_text: str,
    *,
    line_entities: list[dict[str, Any]],
    seed_patterns: dict[str, Counter[str]],
) -> str:
    joined = f"{line_text} {segment_text}"
    relation_votes: Counter[str] = Counter()
    for token in tokens(joined):
        relation_votes.update(seed_patterns.get(token, {}))
    if relation_votes:
        return relation_votes.most_common(1)[0][0]
    token_count = len(tokens(line_text))
    if any(hint in joined for hint in THEOLOGY_HINTS):
        return "theological_explanation"
    if any(entity.get("entity_type") in ENTITY_TYPES_FOR_DESCRIBES for entity in line_entities):
        return "describes_entity"
    if any(hint in joined for hint in IMAGE_HINTS):
        return "interprets_image"
    if token_count <= 3:
        return "glosses_word"
    if token_count >= 7:
        return "explains_line"
    return "explains_phrase"


def build_link_id(paadal_id: str, line_no: int, target_start: int, relationship_type: str) -> str:
    return "ppl_" + stable_hash(paadal_id, line_no, target_start, relationship_type)


def build_links(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    entity_root: Path = DEFAULT_ENTITY_ROOT,
    seed_dir: Path = DEFAULT_SEED_DIR,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    paadal_rows = read_jsonl(table_root / "paadalgal.jsonl")
    commentary_rows = read_jsonl(table_root / "commentaries.jsonl")
    commentary_by_paadal_id = {str(row.get("paadal_id", "")): row for row in commentary_rows}
    seed_relations = load_seed_relations(seed_dir)
    seed_patterns = seed_phrase_patterns(seed_relations)
    mentions_by_parent_field = load_entity_mentions(entity_root)
    synonym_concepts = load_synonym_concepts()

    links: list[dict[str, Any]] = []
    for paadal in paadal_rows:
        paadal_id = str(paadal.get("paadal_id", ""))
        commentary = commentary_by_paadal_id.get(paadal_id, {})
        commentary_id = str(commentary.get("commentary_id") or f"{paadal_id}_commentary")
        paadal_text = str(paadal.get("paadal_text", ""))
        pozhppurai = str(commentary.get("pozhppurai", ""))
        lines = line_spans(paadal_text)
        segments = segment_spans(pozhppurai)
        aligned_targets = choose_best_alignment(
            lines,
            segments,
            paadal_id=paadal_id,
            commentary_id=commentary_id,
            pozhppurai_text=pozhppurai,
            mentions_by_parent_field=mentions_by_parent_field,
            synonym_concepts=synonym_concepts,
        )
        for line in lines:
            if not pozhppurai.strip():
                link = {
                    "schema_version": SCHEMA_VERSION,
                    "link_id": build_link_id(paadal_id, int(line["line_no"]), -1, "no_pozhippurai"),
                    "paadal_id": paadal_id,
                    "commentary_id": commentary_id,
                    "thirumurai_no": paadal.get("thirumurai_no", ""),
                    "source_field": "paadal_text",
                    "source_start_char": line["start_char"],
                    "source_end_char": line["end_char"],
                    "source_text": line["text"],
                    "source_line_no": line["line_no"],
                    "target_field": "pozhppurai",
                    "target_start_char": None,
                    "target_end_char": None,
                    "target_text": "",
                    "target_segment_no": None,
                    "relationship_type": "unlinked",
                    "confidence": "none",
                    "score": 0.0,
                    "link_status": "no_pozhippurai",
                    "diagnostic_category": "missing_pozhippurai",
                    "problem_reason": "The normalized commentary row has empty pozhppurai text, so no target span can be linked.",
                    "method": "coverage_record_no_pozhippurai",
                    "features": {},
                }
                links.append(link)
                continue
            segment, features = aligned_targets.get(int(line["line_no"]), (None, {}))
            if segment is None:
                segment, features = best_target_for_line(
                    line,
                    segments,
                    paadal_id=paadal_id,
                    commentary_id=commentary_id,
                    line_count=len(lines),
                    pozhppurai_text=pozhppurai,
                    mentions_by_parent_field=mentions_by_parent_field,
                    synonym_concepts=synonym_concepts,
                )
            if segment is None:
                continue
            line_entities = overlapping_entities(
                mentions_by_parent_field,
                paadal_id,
                "paadal_text",
                int(line["start_char"]),
                int(line["end_char"]),
            )
            relation = relationship_for(
                str(line["text"]),
                str(segment["text"]),
                line_entities=line_entities,
                seed_patterns=seed_patterns,
            )
            score = float(features.get("score", 0.0))
            confidence = confidence_for(features, pozhppurai)
            diagnostic = diagnostic_category(confidence, features, pozhppurai)
            link = {
                "schema_version": SCHEMA_VERSION,
                "link_id": build_link_id(paadal_id, int(line["line_no"]), int(segment["start_char"]), relation),
                "paadal_id": paadal_id,
                "commentary_id": commentary_id,
                "thirumurai_no": paadal.get("thirumurai_no", ""),
                "source_field": "paadal_text",
                "source_start_char": line["start_char"],
                "source_end_char": line["end_char"],
                "source_text": line["text"],
                "source_line_no": line["line_no"],
                "target_field": "pozhppurai",
                "target_start_char": segment["start_char"],
                "target_end_char": segment["end_char"],
                "target_text": segment["text"],
                "target_segment_no": segment["segment_no"],
                "target_segment_end_no": segment.get("segment_end_no", segment["segment_no"]),
                "target_window_size": segment.get("window_size", 1),
                "relationship_type": relation,
                "confidence": confidence,
                "score": score,
                "link_status": "linked" if confidence != "low" else "linked_low_confidence",
                "diagnostic_category": diagnostic,
                "problem_reason": problem_reason_for(diagnostic),
                "method": "line_to_pozhippurai_window_similarity_with_entity_overlap_v2",
                "features": features,
            }
            links.append(link)
    summary = summarize_links(links, paadal_rows, commentary_rows, seed_relations)
    return links, summary


def summarize_links(
    links: list[dict[str, Any]],
    paadal_rows: list[dict[str, Any]],
    commentary_rows: list[dict[str, Any]],
    seed_relations: list[dict[str, str]],
) -> dict[str, Any]:
    linked_paadal_ids = {row["paadal_id"] for row in links if row["link_status"] != "no_pozhippurai"}
    no_pozhippurai_ids = {
        str(row.get("paadal_id", ""))
        for row in commentary_rows
        if not str(row.get("pozhppurai", "")).strip()
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "paadal_count": len(paadal_rows),
        "commentary_count": len(commentary_rows),
        "seed_relation_count": len(seed_relations),
        "link_count": len(links),
        "linked_paadal_count": len(linked_paadal_ids),
        "no_pozhippurai_paadal_count": len(no_pozhippurai_ids),
        "line_count_by_status": dict(sorted(Counter(row["link_status"] for row in links).items())),
        "line_count_by_confidence": dict(sorted(Counter(row["confidence"] for row in links).items())),
        "line_count_by_relationship_type": dict(sorted(Counter(row["relationship_type"] for row in links).items())),
        "line_count_by_diagnostic_category": dict(sorted(Counter(row.get("diagnostic_category", "unknown") for row in links).items())),
        "line_count_by_thirumurai": dict(sorted(Counter(str(row["thirumurai_no"]) for row in links).items())),
    }


def validate_links(table_root: Path, links: list[dict[str, Any]]) -> dict[str, Any]:
    paadal_text_by_id = {
        str(row.get("paadal_id", "")): str(row.get("paadal_text", ""))
        for row in read_jsonl(table_root / "paadalgal.jsonl")
    }
    pozh_by_commentary_id = {
        str(row.get("commentary_id", "")): str(row.get("pozhppurai", ""))
        for row in read_jsonl(table_root / "commentaries.jsonl")
    }
    invalid_bounds = 0
    span_mismatches = 0
    duplicate_ids: Counter[str] = Counter()
    for link in links:
        duplicate_ids[str(link.get("link_id", ""))] += 1
        paadal_text = paadal_text_by_id.get(str(link["paadal_id"]), "")
        source_start = int(link["source_start_char"])
        source_end = int(link["source_end_char"])
        if source_start < 0 or source_end < source_start or source_end > len(paadal_text):
            invalid_bounds += 1
        elif paadal_text[source_start:source_end] != link["source_text"]:
            span_mismatches += 1
        if link["target_start_char"] is not None:
            pozhppurai = pozh_by_commentary_id.get(str(link["commentary_id"]), "")
            target_start = int(link["target_start_char"])
            target_end = int(link["target_end_char"])
            if target_start < 0 or target_end < target_start or target_end > len(pozhppurai):
                invalid_bounds += 1
            elif pozhppurai[target_start:target_end] != link["target_text"]:
                span_mismatches += 1
    duplicate_link_ids = sorted(link_id for link_id, count in duplicate_ids.items() if count > 1)
    return {
        "invalid_bounds": invalid_bounds,
        "span_mismatches": span_mismatches,
        "duplicate_link_ids": duplicate_link_ids,
        "status": "VALID" if not invalid_bounds and not span_mismatches and not duplicate_link_ids else "INVALID",
    }


def render_report(summary: dict[str, Any], validation: dict[str, Any], output_root: Path) -> str:
    status_rows = "\n".join(f"| `{key}` | {value} |" for key, value in summary["line_count_by_status"].items())
    confidence_rows = "\n".join(f"| `{key}` | {value} |" for key, value in summary["line_count_by_confidence"].items())
    relationship_rows = "\n".join(f"| `{key}` | {value} |" for key, value in summary["line_count_by_relationship_type"].items())
    diagnostic_rows = "\n".join(f"| `{key}` | {value} | {problem_reason_for(key)} |" for key, value in summary["line_count_by_diagnostic_category"].items())
    thirumurai_rows = "\n".join(f"| `{key}` | {value} |" for key, value in summary["line_count_by_thirumurai"].items())
    return f"""# Thevaram Pozhippurai Paadal-Link Report

## Strategy

This pass creates corpus-wide `paadal_text` line to `pozhppurai` segment links. The seed
dataset is used to guide relation labels, but the full corpus pass is deterministic and
reviewable: exact spans are stored, confidence is explicit, and paadal lines without
available `pozhppurai` are retained as `no_pozhippurai` coverage records.

The linker scores candidate `pozhppurai` windows using token overlap, Tamil character
n-gram overlap, phrase containment, entity overlap from Entity Annotation v2, and
paadal/commentary order alignment. It then classifies each link as `explains_line`,
`explains_phrase`, `glosses_word`, `interprets_image`, `theological_explanation`, or
`describes_entity`.

## Summary

- Schema version: `{summary['schema_version']}`
- Output root: `{output_root}`
- Paadal rows: `{summary['paadal_count']}`
- Commentary rows: `{summary['commentary_count']}`
- Seed relation examples: `{summary['seed_relation_count']}`
- Link / coverage rows: `{summary['link_count']}`
- Paadal with linked `pozhppurai`: `{summary['linked_paadal_count']}`
- Paadal with no `pozhppurai`: `{summary['no_pozhippurai_paadal_count']}`
- Validation status: `{validation['status']}`
- Invalid bounds: `{validation['invalid_bounds']}`
- Span mismatches: `{validation['span_mismatches']}`
- Duplicate link IDs: `{len(validation['duplicate_link_ids'])}`

## Link Status

| Status | Lines |
| --- | ---: |
{status_rows}

## Confidence

| Confidence | Lines |
| --- | ---: |
{confidence_rows}

## Relationship Types

| Relationship | Lines |
| --- | ---: |
{relationship_rows}

## Diagnostic Categories

| Category | Lines | Meaning |
| --- | ---: | --- |
{diagnostic_rows}

## Thirumurai Coverage

| Thirumurai | Lines |
| --- | ---: |
{thirumurai_rows}

## Review Guidance

- Treat `high` and `medium` as useful automatic links.
- Review `low` links before using them for scholarly claims.
- `no_pozhippurai` rows are not failures; they document missing commentary text in the current corpus.
- This is a complete corpus-wide first pass, not a final gold commentary alignment.
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
    counts = {"links": write_jsonl(output_root / "paadal_pozhippurai_links.jsonl", links)}
    payload = {**summary, "counts": counts, "validation": validation}
    (output_root / "link_summary.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary, validation, output_root), encoding="utf-8")


def run_linking(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    entity_root: Path = DEFAULT_ENTITY_ROOT,
    seed_dir: Path = DEFAULT_SEED_DIR,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    links, summary = build_links(table_root=table_root, entity_root=entity_root, seed_dir=seed_dir)
    validation = validate_links(table_root, links)
    write_outputs(
        links=links,
        summary=summary,
        validation=validation,
        output_root=output_root,
        report_path=report_path,
    )
    return {**summary, "validation": validation, "output_root": str(output_root), "report": str(report_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create corpus-wide Thevaram paadal to pozhppurai links.")
    parser.add_argument("--table-root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--entity-root", type=Path, default=DEFAULT_ENTITY_ROOT)
    parser.add_argument("--seed-dir", type=Path, default=DEFAULT_SEED_DIR)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = run_linking(
        table_root=args.table_root,
        entity_root=args.entity_root,
        seed_dir=args.seed_dir,
        output_root=args.output_root,
        report_path=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["validation"]["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
