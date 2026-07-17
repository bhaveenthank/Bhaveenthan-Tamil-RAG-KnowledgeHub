from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from knowledge.build_pozhippurai_links_v4 import (
    secondary_no_link_rows,
    validate_clean_links,
    validate_v4_links,
    write_iob_v4,
)
from knowledge.build_pozhippurai_links_v4_hardened import SCHEMA_VERSION as HARDENED_SCHEMA_VERSION
from knowledge.link_thevaram_pozhippurai import DEFAULT_TABLE_ROOT, read_jsonl, tokens
from knowledge.link_thevaram_pozhippurai_v3 import build_manual_review_pack, write_csv_file, write_jsonl, write_tsv

SCHEMA_VERSION = "thevaram-pozhppurai-paadallink-v4-hardened-learned"
DEFAULT_HARDENED_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_hardened")
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_hardened_learned")
DEFAULT_REPORT = DEFAULT_OUTPUT_ROOT / "paadal_pozhippurai_links_v4_hardened_learned_report.md"

BLOCKING_PENALTIES = {
    "order_only_penalty",
    "ambiguous_margin_penalty",
    "target_too_broad_penalty",
    "polysemy_without_context_penalty",
}
LEARNABLE_RULE_PREFIXES = ("LEX_", "ONTO_", "MORPH_", "v4_gold_", "qa_", "split_")
HIGH_CONFIDENCE_THRESHOLD = 0.82
MEDIUM_CONFIDENCE_THRESHOLD = 0.58


@dataclass(frozen=True)
class LearnedPatterns:
    high_example_count: int
    rule_counts: Counter[tuple[str, str]]
    anchor_counts: Counter[tuple[str, str]]
    source_token_counts: Counter[tuple[str, str]]
    target_token_counts: Counter[tuple[str, str]]
    relationship_counts: Counter[str]
    sequence_method_counts: Counter[tuple[str, str]]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def feature_scores(row: dict[str, Any]) -> dict[str, float]:
    value = row.get("feature_scores")
    if not isinstance(value, dict):
        return {}
    scores: dict[str, float] = {}
    for key, raw in value.items():
        try:
            scores[str(key)] = float(raw)
        except (TypeError, ValueError):
            continue
    return scores


def learnable_rules(row: dict[str, Any]) -> list[str]:
    rules = []
    for raw in as_list(row.get("rule_ids_applied")):
        value = str(raw)
        if value.startswith(LEARNABLE_RULE_PREFIXES):
            rules.append(value)
    return rules


def anchor_families(row: dict[str, Any]) -> list[str]:
    families: list[str] = []
    for raw in as_list(row.get("expanded_entity_anchors")):
        value = str(raw)
        parts = value.split(".")
        if len(parts) >= 2:
            families.append(".".join(parts[:2]))
        elif value:
            families.append(value)
    return families


def content_tokens(text: str) -> list[str]:
    return [token for token in tokens(text) if len(token) >= 3 and not token.isdigit()]


def is_gold_example(row: dict[str, Any]) -> bool:
    return (
        row.get("confidence") == "high"
        and not row.get("manual_review_required")
        and row.get("relationship_type") != "unlinked"
        and row.get("target_text")
        and row.get("source_text")
    )


def learn_patterns(high_rows: Iterable[dict[str, Any]]) -> LearnedPatterns:
    rule_counts: Counter[tuple[str, str]] = Counter()
    anchor_counts: Counter[tuple[str, str]] = Counter()
    source_token_counts: Counter[tuple[str, str]] = Counter()
    target_token_counts: Counter[tuple[str, str]] = Counter()
    relationship_counts: Counter[str] = Counter()
    sequence_method_counts: Counter[tuple[str, str]] = Counter()
    high_count = 0
    for row in high_rows:
        if not is_gold_example(row):
            continue
        high_count += 1
        relationship = str(row.get("relationship_type", ""))
        relationship_counts[relationship] += 1
        sequence_method_counts[(relationship, str(row.get("sequence_alignment_method", "")))] += 1
        for rule_id in learnable_rules(row):
            rule_counts[(relationship, rule_id)] += 1
        for anchor in anchor_families(row):
            anchor_counts[(relationship, anchor)] += 1
        for token in set(content_tokens(str(row.get("source_text", "")))):
            source_token_counts[(relationship, token)] += 1
        for token in set(content_tokens(str(row.get("target_text", "")))):
            target_token_counts[(relationship, token)] += 1
    return LearnedPatterns(
        high_example_count=high_count,
        rule_counts=rule_counts,
        anchor_counts=anchor_counts,
        source_token_counts=source_token_counts,
        target_token_counts=target_token_counts,
        relationship_counts=relationship_counts,
        sequence_method_counts=sequence_method_counts,
    )


def normalized_counter_score(counts: list[int], cap: float) -> float:
    if not counts:
        return 0.0
    return min(cap, sum(math.log1p(count) for count in counts) / 35.0)


def learned_pattern_score(row: dict[str, Any], patterns: LearnedPatterns) -> tuple[float, dict[str, float], list[str]]:
    relationship = str(row.get("relationship_type", ""))
    matched_rules = [patterns.rule_counts[(relationship, rule)] for rule in learnable_rules(row) if patterns.rule_counts[(relationship, rule)]]
    matched_anchors = [patterns.anchor_counts[(relationship, anchor)] for anchor in anchor_families(row) if patterns.anchor_counts[(relationship, anchor)]]
    source_matches = [
        patterns.source_token_counts[(relationship, token)]
        for token in set(content_tokens(str(row.get("source_text", ""))))
        if patterns.source_token_counts[(relationship, token)] >= 3
    ]
    target_matches = [
        patterns.target_token_counts[(relationship, token)]
        for token in set(content_tokens(str(row.get("target_text", ""))))
        if patterns.target_token_counts[(relationship, token)] >= 3
    ]
    sequence_count = patterns.sequence_method_counts[(relationship, str(row.get("sequence_alignment_method", "")))]
    features = feature_scores(row)
    semantic_signal = (
        features.get("semantic_lexicon_score", 0.0)
        + features.get("shared_entity_anchor_score", 0.0)
        + features.get("ontology_relation_score", 0.0)
        + features.get("relationship_cue_score", 0.0)
        + features.get("gold_pattern_similarity", 0.0)
    )
    components = {
        "learned_rule_score": normalized_counter_score(matched_rules, 0.35),
        "learned_anchor_score": normalized_counter_score(matched_anchors, 0.25),
        "learned_source_token_score": normalized_counter_score(source_matches, 0.15),
        "learned_target_token_score": normalized_counter_score(target_matches, 0.15),
        "learned_sequence_score": min(0.1, math.log1p(sequence_count) / 60.0) if sequence_count else 0.0,
        "existing_semantic_signal": min(0.25, semantic_signal / 5.0),
    }
    matched_evidence: list[str] = []
    if matched_rules:
        matched_evidence.append("rule")
    if matched_anchors:
        matched_evidence.append("anchor")
    if source_matches or target_matches:
        matched_evidence.append("token")
    if semantic_signal >= 0.75:
        matched_evidence.append("semantic")
    score = round(sum(components.values()), 4)
    return score, components, matched_evidence


def has_blocking_warning(row: dict[str, Any]) -> bool:
    return bool(as_list(row.get("critical_warnings"))) or bool(BLOCKING_PENALTIES & set(map(str, as_list(row.get("penalties_applied")))))


def recalibrate_row(row: dict[str, Any], patterns: LearnedPatterns) -> dict[str, Any]:
    item = dict(row)
    item["schema_version"] = SCHEMA_VERSION
    item["base_schema_version"] = row.get("schema_version") or HARDENED_SCHEMA_VERSION
    item["base_link_id"] = row.get("link_id", "")
    item["learned_from_high_confidence_examples"] = patterns.high_example_count
    if row.get("relationship_type") == "unlinked" or row.get("confidence") == "no_link":
        item["learned_pattern_score"] = 0.0
        item["learned_pattern_components"] = {}
        item["learned_pattern_evidence"] = []
        return item

    pattern_score, components, evidence = learned_pattern_score(row, patterns)
    old_confidence = str(row.get("confidence", ""))
    old_score = float(row.get("score") or 0.0)
    blocked = has_blocking_warning(row)
    new_confidence = old_confidence
    new_score = old_score
    review_required = bool(row.get("manual_review_required"))
    promotion_reason = ""

    if not blocked and old_confidence == "medium" and pattern_score >= 0.42 and len(evidence) >= 2:
        new_confidence = "high"
        new_score = max(old_score, HIGH_CONFIDENCE_THRESHOLD + min(0.12, pattern_score / 5))
        review_required = False
        promotion_reason = "medium_to_high_by_learned_high_pattern"
    elif not blocked and old_confidence == "low" and pattern_score >= 0.6 and {"rule", "anchor"} & set(evidence):
        new_confidence = "high"
        new_score = max(old_score, HIGH_CONFIDENCE_THRESHOLD)
        review_required = False
        promotion_reason = "low_to_high_by_strong_learned_high_pattern"
    elif not blocked and old_confidence == "low" and pattern_score >= 0.38 and len(evidence) >= 2:
        new_confidence = "medium"
        new_score = max(old_score, MEDIUM_CONFIDENCE_THRESHOLD + min(0.1, pattern_score / 6))
        review_required = True
        promotion_reason = "low_to_medium_by_learned_high_pattern"

    item.update(
        {
            "previous_confidence": old_confidence,
            "previous_score": old_score,
            "confidence": new_confidence,
            "score": round(min(0.99, new_score), 4),
            "manual_review_required": review_required,
            "learned_pattern_score": pattern_score,
            "learned_pattern_components": components,
            "learned_pattern_evidence": evidence,
            "learned_promotion_reason": promotion_reason,
        }
    )
    if promotion_reason:
        item["diagnostic_note"] = f"{row.get('diagnostic_note', '')} Learned from high-confidence pattern: {promotion_reason}."
        item["rule_ids_applied"] = as_list(row.get("rule_ids_applied")) + ["learned_high_confidence_pattern"]
    return item


def apply_learned_patterns(rows: list[dict[str, Any]], patterns: LearnedPatterns) -> list[dict[str, Any]]:
    return [recalibrate_row(row, patterns) for row in rows]


def summarize(rows: list[dict[str, Any]], primary_rows: list[dict[str, Any]], secondary_rows: list[dict[str, Any]], patterns: LearnedPatterns) -> dict[str, Any]:
    promoted_to_high = sum(1 for row in rows if row.get("confidence") == "high" and row.get("previous_confidence") != "high")
    low_to_medium = sum(1 for row in rows if row.get("confidence") == "medium" and row.get("previous_confidence") == "low")
    return {
        "schema_version": SCHEMA_VERSION,
        "learned_high_examples": patterns.high_example_count,
        "learned_rule_patterns": len(patterns.rule_counts),
        "learned_anchor_patterns": len(patterns.anchor_counts),
        "learned_source_token_patterns": len(patterns.source_token_counts),
        "learned_target_token_patterns": len(patterns.target_token_counts),
        "total_links": len(rows),
        "primary_clean_links": len(primary_rows),
        "secondary_no_link_rows": len(secondary_rows),
        "links_by_confidence": dict(sorted(Counter(str(row.get("confidence", "")) for row in rows).items())),
        "primary_links_by_confidence": dict(sorted(Counter(str(row.get("confidence", "")) for row in primary_rows).items())),
        "links_by_relationship_type": dict(sorted(Counter(str(row.get("relationship_type", "")) for row in rows).items())),
        "promoted_to_high": promoted_to_high,
        "primary_promoted_to_high": sum(1 for row in primary_rows if row.get("confidence") == "high" and row.get("previous_confidence") != "high"),
        "low_to_medium": low_to_medium,
        "manual_review_required_count": sum(1 for row in rows if row.get("manual_review_required")),
        "empty_pozhippurai_rows_excluded": sum(1 for row in secondary_rows if row.get("secondary_table_reason") == "empty_pozhippurai"),
        "secondary_no_link_reasons": dict(sorted(Counter(str(row.get("secondary_table_reason", "")) for row in secondary_rows).items())),
    }


def penalty_key(row: dict[str, Any]) -> str:
    penalties = sorted(map(str, row.get("penalties_applied") or []))
    warnings = sorted(map(str, row.get("critical_warnings") or []))
    return ",".join(penalties + warnings) or "none"


def evidence_key(row: dict[str, Any]) -> str:
    evidence = sorted(map(str, row.get("learned_pattern_evidence") or []))
    return ",".join(evidence) or "none"


def review_priority(row: dict[str, Any]) -> str:
    score = float(row.get("learned_pattern_score") or 0)
    if row.get("confidence") == "medium" and score >= 0.42 and not has_blocking_warning(row):
        return "accept_candidate"
    if score >= 0.6:
        return "review_strong_pattern"
    if score >= 0.42:
        return "review_pattern_with_blocker"
    if score >= 0.3:
        return "review_possible_pattern"
    return "low_priority"


def promotion_candidates(primary_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = []
    for row in primary_rows:
        if row.get("confidence") == "high" or row.get("confidence") == "no_link":
            continue
        score = float(row.get("learned_pattern_score") or 0)
        if score < 0.3:
            continue
        candidates.append(
            {
                "review_priority": review_priority(row),
                "learned_pattern_score": score,
                "confidence": row.get("confidence", ""),
                "previous_confidence": row.get("previous_confidence", ""),
                "relationship_type": row.get("relationship_type", ""),
                "evidence_key": evidence_key(row),
                "penalty_key": penalty_key(row),
                "manual_review_required": row.get("manual_review_required", ""),
                "thirumurai_no": row.get("thirumurai_no", ""),
                "paadal_id": row.get("paadal_id", ""),
                "source_text": row.get("source_text", ""),
                "target_text": row.get("target_text", ""),
                "feature_scores": row.get("feature_scores", {}),
                "expanded_entity_anchors": row.get("expanded_entity_anchors", []),
                "rule_ids_applied": row.get("rule_ids_applied", []),
                "link_id": row.get("link_id", ""),
            }
        )
    return sorted(
        candidates,
        key=lambda row: (
            {"accept_candidate": 0, "review_strong_pattern": 1, "review_pattern_with_blocker": 2, "review_possible_pattern": 3}.get(str(row["review_priority"]), 9),
            -float(row["learned_pattern_score"]),
            str(row["relationship_type"]),
        ),
    )


def pattern_groups(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        key = (
            str(row["review_priority"]),
            str(row["relationship_type"]),
            str(row["evidence_key"]),
            str(row["penalty_key"]),
        )
        grouped[key].append(row)
    groups = []
    for (priority, relationship, evidence, penalties), rows in grouped.items():
        scores = [float(row["learned_pattern_score"]) for row in rows]
        sample = rows[0]
        groups.append(
            {
                "review_priority": priority,
                "relationship_type": relationship,
                "evidence_key": evidence,
                "penalty_key": penalties,
                "row_count": len(rows),
                "avg_learned_pattern_score": round(sum(scores) / len(scores), 4),
                "max_learned_pattern_score": round(max(scores), 4),
                "sample_source_text": sample["source_text"],
                "sample_target_text": sample["target_text"],
                "recommended_decision": "",
                "reviewer_note": "",
            }
        )
    return sorted(groups, key=lambda row: (-int(row["row_count"]), str(row["review_priority"]), str(row["relationship_type"])))


def gold_rule_template() -> list[dict[str, str]]:
    return [
        {
            "pattern_group_decision": "ACCEPT_PATTERN|REJECT_PATTERN|NEEDS_SPLIT|TARGET_TOO_BROAD|KEEP_REVIEW",
            "relationship_type": "",
            "source_cue": "",
            "target_cue": "",
            "required_entity_anchor": "",
            "required_rule_id": "",
            "allowed_penalties": "",
            "promote_to": "high|medium|low",
            "reviewer_note": "",
        }
    ]


def render_report(summary: dict[str, Any], validation: dict[str, Any], output_root: Path) -> str:
    def table(mapping: dict[str, Any]) -> str:
        return "\n".join(f"| `{key}` | {value} |") if False else "\n".join(f"| `{key}` | {value} |" for key, value in mapping.items()) or "| None | 0 |"

    high = int(summary["primary_links_by_confidence"].get("high", 0))
    primary = int(summary["primary_clean_links"])
    high_pct = (high / primary * 100) if primary else 0.0
    return f"""# Paadal-Pozhippurai v4 Hardened Learned Pattern Report

## Summary

- Output root: `{output_root}`
- Schema version: `{summary['schema_version']}`
- Learned high-confidence examples: `{summary['learned_high_examples']}`
- Full links: `{summary['total_links']}`
- Primary clean linked rows: `{summary['primary_clean_links']}`
- Primary high-confidence rows: `{high}` (`{high_pct:.1f}%`)
- Primary rows promoted to high: `{summary['primary_promoted_to_high']}`
- Full rows promoted to high: `{summary['promoted_to_high']}`
- Low rows promoted to medium: `{summary['low_to_medium']}`
- Manual review required: `{summary['manual_review_required_count']}`
- Empty pozhppurai rows excluded: `{summary['empty_pozhippurai_rows_excluded']}`
- Validation status: `{validation['status']}`

## Learned Pattern Inventory

- Rule patterns: `{summary['learned_rule_patterns']}`
- Anchor patterns: `{summary['learned_anchor_patterns']}`
- Source token patterns: `{summary['learned_source_token_patterns']}`
- Target token patterns: `{summary['learned_target_token_patterns']}`

## Primary Confidence Distribution

| Confidence | Rows |
| --- | ---: |
{table(summary['primary_links_by_confidence'])}

## Full Confidence Distribution

| Confidence | Rows |
| --- | ---: |
{table(summary['links_by_confidence'])}

## Relationship Distribution

| Relationship | Rows |
| --- | ---: |
{table(summary['links_by_relationship_type'])}

## Notes

- This layer uses the current high-confidence rows as local gold-like examples.
- Rows with order-only, ambiguity, broad-target, polysemy, or critical warnings are not promoted to high by this pass.
- This improves the linker conservatively; reaching 85-90% high confidence still requires pattern review and accepted promotion rules.
"""


def write_outputs(
    rows: list[dict[str, Any]],
    primary_rows: list[dict[str, Any]],
    secondary_rows: list[dict[str, Any]],
    summary: dict[str, Any],
    validation: dict[str, Any],
    output_root: Path,
    report_path: Path,
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_hardened_learned_full.jsonl", rows)
    write_tsv(output_root / "paadal_pozhippurai_links_v4_hardened_learned_full.tsv", rows)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_hardened_learned_primary_clean_links.jsonl", primary_rows)
    write_tsv(output_root / "paadal_pozhippurai_links_v4_hardened_learned_primary_clean_links.tsv", primary_rows)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_hardened_learned_primary_clean_links.csv", primary_rows)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_hardened_learned_secondary_no_link.jsonl", secondary_rows)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_hardened_learned_secondary_no_link.csv", secondary_rows)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_hardened_learned_high_confidence.jsonl", [row for row in rows if row.get("confidence") == "high" and not row.get("manual_review_required")])
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_hardened_learned_medium_confidence.jsonl", [row for row in rows if row.get("confidence") == "medium" and not row.get("manual_review_required")])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_hardened_learned_low_confidence_review.csv", [row for row in rows if row.get("confidence") == "low" or row.get("manual_review_required")])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_hardened_learned_no_link_or_unresolved.csv", [row for row in rows if row.get("confidence") == "no_link" or row.get("relationship_type") == "unlinked"])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_hardened_learned_manual_review_pack.csv", build_manual_review_pack(rows))
    candidates = promotion_candidates(primary_rows)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_hardened_learned_promotion_candidates.csv", candidates)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_hardened_learned_pattern_groups.csv", pattern_groups(candidates))
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_hardened_learned_gold_rule_template.csv", gold_rule_template())
    write_iob_v4(output_root / "paadal_pozhippurai_links_v4_hardened_learned_corrected_usable.iob.conll", [row for row in rows if row.get("confidence") in {"high", "medium"} and row.get("target_text")])
    (output_root / "paadal_pozhippurai_links_v4_hardened_learned_summary.json").write_text(
        json.dumps({**summary, "validation": validation}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary, validation, output_root), encoding="utf-8")


def run_learning(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    hardened_root: Path = DEFAULT_HARDENED_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    full_rows = load_jsonl(hardened_root / "paadal_pozhippurai_links_v4_hardened_full.jsonl")
    primary_rows = load_jsonl(hardened_root / "paadal_pozhippurai_links_v4_hardened_primary_clean_links.jsonl")
    secondary_rows = load_jsonl(hardened_root / "paadal_pozhippurai_links_v4_hardened_secondary_no_link.jsonl")
    patterns = learn_patterns(row for row in primary_rows if is_gold_example(row))
    learned_full = apply_learned_patterns(full_rows, patterns)
    learned_primary = apply_learned_patterns(primary_rows, patterns)
    validation = validate_v4_links(table_root, learned_full)
    primary_validation = validate_clean_links(table_root, learned_primary)
    summary = summarize(learned_full, learned_primary, secondary_rows, patterns)
    summary["primary_validation"] = primary_validation
    write_outputs(learned_full, learned_primary, secondary_rows, summary, validation, output_root, report_path)
    return {**summary, "validation": validation, "output_root": str(output_root), "report": str(report_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Learn promotion patterns from v4_hardened high-confidence paadal-pozhppurai links.")
    parser.add_argument("--table-root", "--input-root", dest="table_root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--hardened-root", type=Path, default=DEFAULT_HARDENED_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = run_learning(
        table_root=args.table_root,
        hardened_root=args.hardened_root,
        output_root=args.output_root,
        report_path=args.report,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["validation"]["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
