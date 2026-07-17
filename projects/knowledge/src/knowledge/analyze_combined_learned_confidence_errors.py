from __future__ import annotations

import argparse
import ast
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

DEFAULT_INPUT = Path(
    "data/processed/thevaram_pozhippurai_links/v4_combined_learned/"
    "paadal_pozhippurai_links_v4_combined_learned_primary_clean_links.csv"
)
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_combined_learned/error_analysis")
DEFAULT_TABLE_ROOT = Path("data/processed/thevaram/tables")

GENERIC_TAMIL_ANCHORS = {
    "இறைவன்",
    "இறைவர்",
    "பெருமான்",
    "சிவபிரான்",
    "அடிகள்",
    "கோயில்",
    "தலம்",
    "ஊர்",
    "பதி",
    "அருள்",
    "அடி",
    "திருவடி",
}
POLYSEMY_TERMS = {"மதி", "அரவு", "அரவம்", "புனல்", "நீர்", "கை", "அடி", "பொடி", "விடை", "தலை"}
TAMIL_TOKEN_RE = re.compile(r"[\u0B80-\u0BFF]+")
STOP_TOKENS = {
    "ஆகிய",
    "ஆகியன",
    "ஆகியவர்",
    "உடைய",
    "உடையவர்",
    "என்னும்",
    "என்பது",
    "என்று",
    "மற்றும்",
    "அவர்",
    "அவள்",
    "இவர்",
    "இவள்",
    "அது",
    "இது",
    "ஒரு",
    "ஓர்",
    "தன்",
    "தமது",
    "அந்த",
    "இந்த",
    "அங்கு",
    "இங்கு",
    "மேல்",
    "கீழ்",
    "போல",
    "போலும்",
}
WATCHLIST_TERMS = {
    "சடை",
    "முடி",
    "சென்னி",
    "பிறை",
    "திங்கள்",
    "மதி",
    "கங்கை",
    "புனல்",
    "நீர்",
    "அரவு",
    "அரவம்",
    "பாம்பு",
    "விடை",
    "எருது",
    "பொடி",
    "திருநீறு",
    "அடி",
    "திருவடி",
    "பாதம்",
    "தொழ",
    "தொழுது",
    "ஏத்தி",
    "போற்றி",
    "வினை",
    "இன்பம்",
    "அருள்",
    "இறைவன்",
    "இறைவர்",
    "பெருமான்",
    "சிவபிரான்",
    "கோயில்",
    "தலம்",
    "ஊர்",
    "பதி",
    "ஆலவாய்",
    "காழி",
    "முதுகுன்றம்",
    "அண்ணாமலை",
    "யானை",
    "மழு",
    "கபாலம்",
    "தலை",
    "நஞ்சு",
}
RELATION_FAMILIES = {
    "interprets_image": "image",
    "theological_explanation": "theology",
    "describes_entity": "entity",
    "explains_phrase": "phrase",
    "glosses_word": "phrase",
    "explains_line": "phrase",
}


def parse_literal(value: Any, default: Any) -> Any:
    if isinstance(value, (list, dict)):
        return value
    if value in {"", None}:
        return default
    try:
        return ast.literal_eval(str(value))
    except (SyntaxError, ValueError):
        return default


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in {"", None, "None"}:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def to_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def token_count(text: str) -> int:
    return len([part for part in str(text).replace(",", " ").replace(";", " ").split() if part])


def tamil_tokens(text: str) -> list[str]:
    tokens = []
    for token in TAMIL_TOKEN_RE.findall(str(text)):
        if len(token) < 2 or token in STOP_TOKENS:
            continue
        tokens.append(token)
    return tokens


def tamil_ngrams(text: str, max_n: int = 3) -> list[str]:
    toks = tamil_tokens(text)
    phrases = []
    for n in range(1, max_n + 1):
        for index in range(0, max(0, len(toks) - n + 1)):
            phrase = " ".join(toks[index : index + n])
            if phrase and not all(part in STOP_TOKENS for part in phrase.split()):
                phrases.append(phrase)
    return phrases


def source_target_ratio(row: dict[str, Any]) -> float:
    return token_count(row.get("target_text", "")) / max(1, token_count(row.get("source_text", "")))


def feature_scores(row: dict[str, Any]) -> dict[str, float]:
    raw = parse_literal(row.get("feature_scores"), {})
    if not isinstance(raw, dict):
        return {}
    scores: dict[str, float] = {}
    for key, value in raw.items():
        if isinstance(value, dict):
            continue
        scores[str(key)] = to_float(value)
    return scores


def list_field(row: dict[str, Any], name: str) -> list[str]:
    value = parse_literal(row.get(name), [])
    if isinstance(value, list):
        return [str(item) for item in value]
    if value:
        return [str(value)]
    return []


def evidence_signal(row: dict[str, Any], features: dict[str, float]) -> float:
    return (
        features.get("semantic_lexicon_score", 0)
        + features.get("shared_entity_anchor_score", 0)
        + features.get("ontology_relation_score", 0)
        + features.get("relationship_cue_score", 0)
        + features.get("gold_pattern_similarity", 0)
    )


def best_margin(row: dict[str, Any]) -> float:
    explicit = to_float(row.get("best_second_margin"), -1.0)
    if explicit >= 0:
        return explicit
    features = parse_literal(row.get("features"), {})
    if isinstance(features, dict):
        return to_float(features.get("score_margin"), 0.0)
    return 0.0


def classify_row(row: dict[str, Any]) -> dict[str, Any]:
    penalties = set(list_field(row, "penalties_applied"))
    warnings = set(list_field(row, "critical_warnings"))
    evidence = set(list_field(row, "learned_pattern_evidence"))
    anchors_after = list_field(row, "anchors_after") or list_field(row, "expanded_entity_anchors")
    ontology_relations = list_field(row, "ontology_relations_matched")
    features = feature_scores(row)
    margin = best_margin(row)
    learned_score = to_float(row.get("learned_pattern_score"))
    ratio = source_target_ratio(row)
    support = evidence_signal(row, features)
    tags: list[str] = []
    sub_reasons: list[str] = []

    if "missing_entity_anchor_penalty" in penalties:
        tags.append("missing_anchor")
        if not to_bool(row.get("missing_anchor_resolved")):
            sub_reasons.append("anchor_unresolved_after_resolver")
        if not anchors_after:
            sub_reasons.append("no_entity_anchor_after_expansion")
        elif len(anchors_after) <= 1:
            sub_reasons.append("single_or_weak_anchor_only")
        if not ontology_relations and features.get("ontology_relation_score", 0) <= 0:
            sub_reasons.append("no_ontology_relation_support")
        if any(anchor in str(row.get("source_text", "")) or anchor in str(row.get("target_text", "")) for anchor in GENERIC_TAMIL_ANCHORS):
            sub_reasons.append("generic_deity_or_place_anchor")

    if "ambiguous_margin_penalty" in penalties or to_bool(row.get("ambiguous_span_before")):
        tags.append("ambiguous_span")
        if margin < 0.05:
            sub_reasons.append("very_low_best_second_margin")
        elif margin < 0.12:
            sub_reasons.append("low_best_second_margin")
        else:
            sub_reasons.append("margin_improved_but_warning_remains")
        if str(row.get("target_reuse_reason")) == "suspicious_target_reuse":
            sub_reasons.append("suspicious_target_reuse")
        if to_float(row.get("relation_family_conflict_penalty")) > 0:
            sub_reasons.append("relation_family_conflict")
        if str(row.get("ambiguity_resolution_decision")) == "KEEP_REVIEW":
            sub_reasons.append("global_assignment_kept_review")

    if "target_too_broad_penalty" in penalties or to_bool(row.get("broad_target_before")) or ratio > 3.0:
        tags.append("broad_or_unsplit_target")
        if not to_bool(row.get("target_shrink_applied")):
            sub_reasons.append("minimal_span_selector_found_no_safe_subspan")
        if ratio > 6.0:
            sub_reasons.append("extreme_target_to_source_length_ratio")
        elif ratio > 3.0:
            sub_reasons.append("high_target_to_source_length_ratio")
        if "," in str(row.get("target_text", "")) or ";" in str(row.get("target_text", "")):
            sub_reasons.append("multi_clause_target_needs_split")

    if "polysemy_without_context_penalty" in penalties:
        tags.append("polysemy_context")
        terms = sorted(term for term in POLYSEMY_TERMS if term in row.get("source_text", "") or term in row.get("target_text", ""))
        sub_reasons.append("polysemous_terms_" + "_".join(terms[:3]) if terms else "polysemous_term_without_context")

    if "order_only_penalty" in penalties or "order_only_support" in warnings:
        tags.append("order_only")
        sub_reasons.append("sequence_position_support_without_semantic_evidence")

    if support < 0.2:
        tags.append("weak_semantic_signal")
        if features.get("semantic_lexicon_score", 0) == 0:
            sub_reasons.append("semantic_lexicon_gap")
        if features.get("relationship_cue_score", 0) == 0:
            sub_reasons.append("relationship_cue_gap")
        if features.get("shared_entity_anchor_score", 0) == 0:
            sub_reasons.append("shared_entity_anchor_gap")

    if learned_score < 0.3:
        tags.append("low_learned_pattern_support")
        sub_reasons.append("not_similar_to_current_high_confidence_patterns")
    elif learned_score >= 0.42 and row.get("confidence") != "high":
        tags.append("high_pattern_but_blocked")
        if penalties:
            sub_reasons.append("pattern_score_high_but_penalty_blocked_promotion")
        if to_bool(row.get("manual_review_required")):
            sub_reasons.append("pattern_score_high_but_manual_review_required")

    relationship = str(row.get("relationship_type", ""))
    if relationship in {"glosses_word", "explains_phrase"} and token_count(row.get("target_text", "")) > 14:
        tags.append("relation_granularity_mismatch")
        sub_reasons.append("phrase_or_gloss_relation_has_long_target")
    if relationship == "explains_line" and token_count(row.get("source_text", "")) < 5:
        tags.append("relation_granularity_mismatch")
        sub_reasons.append("explains_line_with_short_source_span")

    if not tags:
        tags.append("borderline_score_calibration")
        sub_reasons.append("medium_low_without_explicit_blocker")

    primary_category = choose_primary_category(tags, sub_reasons)
    subcategory = choose_subcategory(primary_category, sub_reasons)
    return {
        "primary_category": primary_category,
        "subcategory": subcategory,
        "issue_tags": "|".join(sorted(set(tags))),
        "sub_reasons": "|".join(sorted(set(sub_reasons))),
        "penalty_key": ",".join(sorted(penalties)) or "none",
        "warning_key": ",".join(sorted(warnings)) or "none",
        "learned_evidence_key": ",".join(sorted(evidence)) or "none",
        "support_score": round(support, 4),
        "best_second_margin": round(margin, 4),
        "source_target_ratio": round(ratio, 4),
        "learned_pattern_score": round(learned_score, 4),
        "relation_family": RELATION_FAMILIES.get(relationship, "unknown"),
    }


def choose_primary_category(tags: list[str], sub_reasons: list[str]) -> str:
    priority = [
        "ambiguous_span",
        "missing_anchor",
        "broad_or_unsplit_target",
        "polysemy_context",
        "order_only",
        "relation_granularity_mismatch",
        "weak_semantic_signal",
        "high_pattern_but_blocked",
        "low_learned_pattern_support",
        "borderline_score_calibration",
    ]
    for name in priority:
        if name in tags:
            return name
    return "uncategorized"


def choose_subcategory(primary: str, sub_reasons: list[str]) -> str:
    preferred = {
        "ambiguous_span": [
            "suspicious_target_reuse",
            "very_low_best_second_margin",
            "low_best_second_margin",
            "relation_family_conflict",
            "global_assignment_kept_review",
        ],
        "missing_anchor": [
            "no_ontology_relation_support",
            "no_entity_anchor_after_expansion",
            "generic_deity_or_place_anchor",
            "single_or_weak_anchor_only",
            "anchor_unresolved_after_resolver",
        ],
        "broad_or_unsplit_target": [
            "extreme_target_to_source_length_ratio",
            "multi_clause_target_needs_split",
            "minimal_span_selector_found_no_safe_subspan",
            "high_target_to_source_length_ratio",
        ],
        "weak_semantic_signal": [
            "semantic_lexicon_gap",
            "relationship_cue_gap",
            "shared_entity_anchor_gap",
        ],
    }
    for reason in preferred.get(primary, []):
        if reason in sub_reasons:
            return reason
    return sub_reasons[0] if sub_reasons else "general"


def pct(count: int, total: int) -> float:
    return round(count / total * 100, 2) if total else 0.0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        fieldnames = keys
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize_groups(enriched: list[dict[str, Any]], total: int) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in enriched:
        grouped[(row["primary_category"], row["subcategory"], row["relationship_type"])].append(row)
    rows = []
    for (category, subcategory, relationship), items in grouped.items():
        rows.append(
            {
                "primary_category": category,
                "subcategory": subcategory,
                "relationship_type": relationship,
                "row_count": len(items),
                "pct_of_medium_low": pct(len(items), total),
                "medium_count": sum(1 for row in items if row["confidence"] == "medium"),
                "low_count": sum(1 for row in items if row["confidence"] == "low"),
                "manual_review_count": sum(1 for row in items if to_bool(row.get("manual_review_required"))),
                "avg_learned_pattern_score": round(mean(float(row["learned_pattern_score_analysis"]) for row in items), 4),
                "avg_support_score": round(mean(float(row["support_score"]) for row in items), 4),
                "avg_margin": round(mean(float(row["best_second_margin_analysis"]) for row in items), 4),
                "avg_source_target_ratio": round(mean(float(row["source_target_ratio"]) for row in items), 4),
                "sample_link_id": items[0]["link_id"],
                "sample_source_text": items[0]["source_text"],
                "sample_target_text": items[0]["target_text"],
            }
        )
    return sorted(rows, key=lambda row: (-int(row["row_count"]), row["primary_category"], row["subcategory"]))


def top_examples(enriched: list[dict[str, Any]], limit_per_group: int = 3) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in enriched:
        grouped[(row["primary_category"], row["subcategory"])].append(row)
    output = []
    for (category, subcategory), rows in grouped.items():
        rows = sorted(
            rows,
            key=lambda row: (
                -float(row["learned_pattern_score_analysis"]),
                -float(row["support_score"]),
                float(row["best_second_margin_analysis"]),
            ),
        )
        for row in rows[:limit_per_group]:
            output.append(
                {
                    "primary_category": category,
                    "subcategory": subcategory,
                    "confidence": row["confidence"],
                    "relationship_type": row["relationship_type"],
                    "learned_pattern_score": row["learned_pattern_score_analysis"],
                    "support_score": row["support_score"],
                    "best_second_margin": row["best_second_margin_analysis"],
                    "penalty_key": row["penalty_key"],
                    "issue_tags": row["issue_tags"],
                    "sub_reasons": row["sub_reasons"],
                    "source_text": row["source_text"],
                    "target_text": row["target_text"],
                    "link_id": row["link_id"],
                }
            )
    return sorted(output, key=lambda row: (row["primary_category"], row["subcategory"], row["relationship_type"]))


def fix_recommendations(summary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    category_counts = Counter()
    for row in summary_rows:
        category_counts[row["primary_category"]] += int(row["row_count"])
    fixes = {
        "ambiguous_span": (
            "Build a supervised pairwise target-ranker over top-k target spans using reviewed ambiguous examples; "
            "add constrained bipartite/DP decoding with target-reuse priors learned per relationship family; "
            "train margin calibration so high requires stable separation under paraphrase perturbations."
        ),
        "missing_anchor": (
            "Expand ontology aliases with reviewed Tamil surface variants; add a morphology/sandhi analyzer for case, "
            "euphonic joins, and devotional epithets; learn anchor co-occurrence rules such as Siva-hair-Ganga, "
            "feet-worship-result, deity-thalam; validate with relation constraints before promotion."
        ),
        "broad_or_unsplit_target": (
            "Create a clause/semantic-role segmenter for pozhippurai; split commentary into minimal explainable spans; "
            "use dependency-like cue boundaries around verbs such as சூடி/அணிந்து/தொழுது/நீங்கும்; penalize multi-clause "
            "targets unless the source is a full-line explanation."
        ),
        "weak_semantic_signal": (
            "Build Tamil literary paraphrase lexicons from high-confidence aligned pairs; add embedding-based semantic "
            "similarity as a feature but gate it with anchors/relations; mine synonym clusters for devotional result, "
            "iconography, myth action, and place-description language."
        ),
        "polysemy_context": (
            "Use context-sensitive word-sense rules and eventually a small WSD classifier for மதி/அரவு/புனல்/அடி/கை; "
            "require local cue windows and ontology-compatible relation before accepting a sense."
        ),
        "order_only": (
            "Keep order as a transition prior only; never certify by order alone. Add negative examples where neighbouring "
            "clauses repeat deity words but explain different source spans."
        ),
        "relation_granularity_mismatch": (
            "Audit relationship labels with a classifier that separates gloss_word, phrase, line, image, entity, and theology; "
            "force target-length priors by relationship and send label/length contradictions to review."
        ),
        "high_pattern_but_blocked": (
            "Review these first: they look like learned high-confidence patterns but have a blocker. Human decisions here "
            "should become explicit override rules or blocker-specific repairs."
        ),
        "low_learned_pattern_support": (
            "Do not promote automatically. Use these to discover new pattern families after the high-pattern blocker groups "
            "are reviewed."
        ),
        "borderline_score_calibration": (
            "Fit calibrated confidence thresholds using reviewed labels and report precision/recall per relationship family."
        ),
    }
    rows = []
    for category, count in category_counts.most_common():
        rows.append(
            {
                "primary_category": category,
                "row_count": count,
                "recommended_fix": fixes.get(category, "Manual review and feature inspection required."),
            }
        )
    return rows


def phrase_error_rows(enriched: list[dict[str, Any]], max_examples: int = 5) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in enriched:
        fields = {
            "source": row.get("source_text", ""),
            "target": row.get("target_text", ""),
        }
        for field, text in fields.items():
            for phrase in tamil_ngrams(str(text), max_n=3):
                if len(phrase.split()) == 1 and phrase not in WATCHLIST_TERMS:
                    continue
                key = (row["primary_category"], row["subcategory"], field, phrase)
                grouped[key].append(row)

    output = []
    for (category, subcategory, field, phrase), rows in grouped.items():
        if len(rows) < 3 and phrase not in WATCHLIST_TERMS:
            continue
        relationships = Counter(row["relationship_type"] for row in rows)
        penalties = Counter(row["penalty_key"] for row in rows)
        examples = []
        for row in rows[:max_examples]:
            examples.append(
                {
                    "link_id": row.get("link_id", ""),
                    "confidence": row.get("confidence", ""),
                    "relationship_type": row.get("relationship_type", ""),
                    "source_text": row.get("source_text", ""),
                    "target_text": row.get("target_text", ""),
                    "penalty_key": row.get("penalty_key", ""),
                }
            )
        output.append(
            {
                "primary_category": category,
                "subcategory": subcategory,
                "field": field,
                "term_or_phrase": phrase,
                "row_count": len(rows),
                "relationship_distribution": json.dumps(dict(relationships.most_common()), ensure_ascii=False),
                "top_penalty_keys": json.dumps(dict(penalties.most_common(5)), ensure_ascii=False),
                "example_rows_json": json.dumps(examples, ensure_ascii=False),
                "why_it_fails": phrase_failure_reason(category, subcategory, phrase),
                "recommended_fix": phrase_fix(category, subcategory, phrase),
            }
        )
    return sorted(output, key=lambda row: (-int(row["row_count"]), row["primary_category"], row["term_or_phrase"]))


def phrase_failure_reason(category: str, subcategory: str, phrase: str) -> str:
    if phrase in {"இறைவன்", "இறைவர்", "பெருமான்", "சிவபிரான்", "கோயில்", "தலம்", "ஊர்", "பதி", "அருள்"}:
        return "Generic devotional/place vocabulary appears across many unrelated commentary clauses, so surface overlap creates false anchors and ambiguous candidates."
    if phrase in {"மதி", "அடி", "கை", "தலை", "பொடி", "விடை", "புனல்", "நீர்", "அரவு", "அரவம்"}:
        return "The term is polysemous or context-dependent; without a local cue window the linker cannot safely choose the intended ontology sense."
    if phrase in {"சடை", "முடி", "சென்னி", "பிறை", "திங்கள்", "கங்கை", "திருநீறு", "பாம்பு", "மழு", "கபாலம்"}:
        return "Iconographic words repeat in clusters; the correct target depends on a combined attribute/action pattern, not one token."
    if phrase in {"திருவடி", "பாதம்", "தொழ", "தொழுது", "ஏத்தி", "போற்றி", "வினை", "இன்பம்"}:
        return "Devotional action/result language is paraphrastic; source may mention worship while target mentions result, or vice versa."
    if category == "broad_or_unsplit_target":
        return "The phrase appears inside a longer multi-clause commentary span; the current row needs a smaller target segment."
    if category == "ambiguous_span":
        return "The phrase occurs in neighbouring candidate targets, making best and second-best spans too close."
    if category == "missing_anchor":
        return "The phrase lacks a validated source-target ontology relation or alias mapping."
    return "The phrase is statistically associated with medium/low rows and needs pattern-level review."


def phrase_fix(category: str, subcategory: str, phrase: str) -> str:
    if phrase in {"இறைவன்", "இறைவர்", "பெருமான்", "சிவபிரான்", "கோயில்", "தலம்", "ஊர்", "பதி", "அருள்"}:
        return "Downweight as generic anchors unless paired with thalam name, deity attribute, myth action, or explicit relation cue."
    if phrase in {"மதி", "அடி", "கை", "தலை", "பொடி", "விடை", "புனல்", "நீர்", "அரவு", "அரவம்"}:
        return "Add word-sense rules with required cue windows and negative examples; promote only if ontology-compatible context is present."
    if phrase in {"சடை", "முடி", "சென்னி", "பிறை", "திங்கள்", "கங்கை", "திருநீறு", "பாம்பு", "மழு", "கபாலம்"}:
        return "Create compound iconography templates: object + body locus + action, e.g. பிறை+சடை+சூடி or கங்கை+சடை+தரித்த."
    if phrase in {"திருவடி", "பாதம்", "தொழ", "தொழுது", "ஏத்தி", "போற்றி", "வினை", "இன்பம்"}:
        return "Add devotional-result relation patterns linking worship action to benefit/removal result; train theology paraphrase pairs."
    if category == "broad_or_unsplit_target":
        return "Use this phrase as a segmentation boundary/cue in a supervised commentary clause splitter."
    if category == "ambiguous_span":
        return "Add reviewed top-k negative/positive target examples for this phrase and learn a reranker margin."
    if category == "missing_anchor":
        return "Add alias/ontology relation examples for this phrase; require source and target co-support."
    return "Review examples and decide whether the phrase should become an anchor, a weak generic cue, or a negative cue."


def render_report(
    *,
    output_root: Path,
    total_primary: int,
    medium_low_total: int,
    confidence_counts: Counter[str],
    category_counts: Counter[str],
    tag_counts: Counter[str],
    relationship_counts: Counter[str],
    penalty_counts: Counter[str],
    phrase_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
) -> str:
    def md_table(rows: list[tuple[Any, Any, Any | None]], headers: tuple[str, str, str | None]) -> str:
        if headers[2] is None:
            lines = [f"| {headers[0]} | {headers[1]} |", "| --- | ---: |"]
            lines.extend(f"| `{a}` | {b} |" for a, b, _ in rows)
        else:
            lines = [f"| {headers[0]} | {headers[1]} | {headers[2]} |", "| --- | ---: | ---: |"]
            lines.extend(f"| `{a}` | {b} | {c} |" for a, b, c in rows)
        return "\n".join(lines)

    top_summary = summary_rows[:20]
    top_groups = "\n".join(
        f"| `{row['primary_category']}` | `{row['subcategory']}` | `{row['relationship_type']}` | {row['row_count']} | {row['pct_of_medium_low']} |"
        for row in top_summary
    )
    phrase_lines = "\n".join(
        f"| `{row['primary_category']}` | `{row['term_or_phrase']}` | `{row['field']}` | {row['row_count']} | {row['why_it_fails']} |"
        for row in phrase_rows[:25]
    )
    return f"""# Deep Error Analysis: v4 Combined Learned Medium/Low Links

## Scope

- Source table: `data/processed/thevaram_pozhippurai_links/v4_combined_learned/paadal_pozhippurai_links_v4_combined_learned_primary_clean_links.csv`
- Primary rows analysed: `{total_primary}`
- Medium/low rows analysed: `{medium_low_total}` (`{pct(medium_low_total, total_primary)}%`)
- Output root: `{output_root}`

## Confidence Distribution Inside Analysed Rows

{md_table([(key, value, pct(value, medium_low_total)) for key, value in confidence_counts.most_common()], ('Confidence', 'Rows', '%'))}

## Primary Error Categories

{md_table([(key, value, pct(value, medium_low_total)) for key, value in category_counts.most_common()], ('Category', 'Rows', '%'))}

## Issue Tags, Including Overlaps

{md_table([(key, value, pct(value, medium_low_total)) for key, value in tag_counts.most_common(20)], ('Issue Tag', 'Rows', '%'))}

## Relationship Type Distribution

{md_table([(key, value, pct(value, medium_low_total)) for key, value in relationship_counts.most_common()], ('Relationship', 'Rows', '%'))}

## Penalty Combinations

{md_table([(key, value, pct(value, medium_low_total)) for key, value in penalty_counts.most_common(15)], ('Penalty Key', 'Rows', '%'))}

## Top Subcategory Groups

| Category | Subcategory | Relationship | Rows | % |
| --- | --- | --- | ---: | ---: |
{top_groups}

## Frequent Error-Prone Words And Phrases

| Category | Word/Phrase | Field | Rows | Why It Fails |
| --- | --- | --- | ---: | --- |
{phrase_lines}

## Interpretation

The remaining medium/low set is not one problem. It is mostly an interaction of:

1. **Target ambiguity and reuse**: many rows still have close competing targets or reused explanation clauses. These need supervised target-ranking and stricter one-target-per-source constraints.
2. **Ontology anchor gaps**: many spans still lack a validated source-target anchor relation even after alias expansion. This is a lexicon, morphology, and relation-cue problem.
3. **Broad or unsplit commentary spans**: some targets are multi-clause explanations where the right answer is inside the span, but the current segmenter cannot safely isolate it.
4. **Weak semantic/paraphrase coverage**: many valid Tamil literary explanations do not overlap surface vocabulary. These need learned paraphrase features, not just direct token overlap.
5. **Granularity and relationship mismatch**: phrase/gloss/line/image/theology labels need relationship-specific span-length and cue constraints.

## Research-Level Fix Direction

- Move from heuristic thresholds to a **review-trained confidence calibrator** per relationship family.
- Train a **top-k target span reranker** from reviewed examples using lexical, ontology, morphology, learned pattern, embedding, target length, and neighbour features.
- Build a **Tamil literary paraphrase lexicon** mined from high-confidence pairs and accepted review rows.
- Add **commentary clause segmentation** with cue-aware boundaries and minimal-span supervision.
- Add **ontology relation validation** as a hard gate for entity/iconography/theology promotions.
- Use the 100-row manual review file as the first active-learning batch, then retrain pattern decisions by group.

## Generated Files

- `medium_low_deep_error_rows.csv`: row-level issue labels for all medium/low rows.
- `medium_low_error_group_summary.csv`: grouped statistics by category/subcategory/relationship.
- `medium_low_error_examples.csv`: representative examples per subcategory.
- `medium_low_error_terms_phrases.csv`: recurring Tamil words/phrases that appear in error clusters, with examples and fixes.
- `medium_low_fix_recommendations.csv`: category-level repair plan.
- `medium_low_error_analysis_summary.json`: machine-readable summary.
"""


def run_analysis(input_csv: Path = DEFAULT_INPUT, output_root: Path = DEFAULT_OUTPUT_ROOT) -> dict[str, Any]:
    rows = read_csv(input_csv)
    medium_low = [row for row in rows if row.get("confidence") in {"medium", "low"}]
    enriched = []
    for row in medium_low:
        labels = classify_row(row)
        item = dict(row)
        item.update(
            {
                **labels,
                "learned_pattern_score_analysis": labels["learned_pattern_score"],
                "best_second_margin_analysis": labels["best_second_margin"],
            }
        )
        enriched.append(item)

    total = len(enriched)
    category_counts = Counter(row["primary_category"] for row in enriched)
    tag_counts: Counter[str] = Counter()
    for row in enriched:
        for tag in row["issue_tags"].split("|"):
            if tag:
                tag_counts[tag] += 1
    confidence_counts = Counter(row["confidence"] for row in enriched)
    relationship_counts = Counter(row["relationship_type"] for row in enriched)
    penalty_counts = Counter(row["penalty_key"] for row in enriched)
    summary_rows = summarize_groups(enriched, total)
    examples = top_examples(enriched)
    fixes = fix_recommendations(summary_rows)
    phrase_rows = phrase_error_rows(enriched)

    output_root.mkdir(parents=True, exist_ok=True)
    write_csv(output_root / "medium_low_deep_error_rows.csv", enriched)
    write_csv(output_root / "medium_low_error_group_summary.csv", summary_rows)
    write_csv(output_root / "medium_low_error_examples.csv", examples)
    write_csv(output_root / "medium_low_error_terms_phrases.csv", phrase_rows)
    write_csv(output_root / "medium_low_fix_recommendations.csv", fixes)
    summary = {
        "input_csv": str(input_csv),
        "output_root": str(output_root),
        "total_primary_rows": len(rows),
        "medium_low_rows": total,
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "category_counts": dict(category_counts.most_common()),
        "issue_tag_counts": dict(tag_counts.most_common()),
        "relationship_counts": dict(relationship_counts.most_common()),
        "penalty_counts": dict(penalty_counts.most_common()),
        "top_error_terms_phrases": phrase_rows[:50],
        "top_groups": summary_rows[:30],
    }
    (output_root / "medium_low_error_analysis_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_root / "medium_low_deep_error_analysis_report.md").write_text(
        render_report(
            output_root=output_root,
            total_primary=len(rows),
            medium_low_total=total,
            confidence_counts=confidence_counts,
            category_counts=category_counts,
            tag_counts=tag_counts,
            relationship_counts=relationship_counts,
            penalty_counts=penalty_counts,
            phrase_rows=phrase_rows,
            summary_rows=summary_rows,
        ),
        encoding="utf-8",
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deep error analysis for v4_combined_learned medium/low paadal-pozhppurai links.")
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    args = parser.parse_args(argv)
    summary = run_analysis(input_csv=args.input_csv, output_root=args.output_root)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
