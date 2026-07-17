from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from knowledge.build_pozhippurai_links_v4 import validate_clean_links, validate_v4_links, write_iob_v4
from knowledge.learn_pozhippurai_high_confidence_patterns import (
    apply_learned_patterns,
    gold_rule_template,
    is_gold_example,
    learn_patterns,
    pattern_groups,
    promotion_candidates,
)
from knowledge.link_thevaram_pozhippurai import DEFAULT_TABLE_ROOT
from knowledge.link_thevaram_pozhippurai_v3 import build_manual_review_pack, write_csv_file, write_jsonl, write_tsv

SCHEMA_VERSION = "thevaram-pozhppurai-paadallink-v4-combined-learned"
DEFAULT_COMBINED_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_combined_hardened")
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_combined_learned")
DEFAULT_REPORT = DEFAULT_OUTPUT_ROOT / "paadal_pozhippurai_links_v4_combined_learned_report.md"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def stable_identity(row: dict[str, Any]) -> str:
    return str(row.get("base_link_id") or row.get("link_id") or "")


def identity_set(row: dict[str, Any]) -> set[str]:
    return {str(value) for value in (row.get("link_id"), row.get("base_link_id")) if value not in {None, ""}}


def confidence_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("confidence", "")) for row in rows).items()))


def stamp_schema(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stamped = []
    for row in rows:
        item = dict(row)
        item["schema_version"] = SCHEMA_VERSION
        item["combined_learned_base_schema_version"] = row.get("schema_version", "")
        stamped.append(item)
    return stamped


def summarize(
    *,
    learned_full: list[dict[str, Any]],
    learned_primary: list[dict[str, Any]],
    secondary: list[dict[str, Any]],
    baseline_full: list[dict[str, Any]],
    baseline_primary: list[dict[str, Any]],
    patterns: Any,
    validation: dict[str, Any],
    primary_validation: dict[str, Any],
    prior_high_identity_sets: list[set[str]],
) -> dict[str, Any]:
    high_after_ids = set().union(*(identity_set(row) for row in learned_primary if row.get("confidence") == "high"))
    lost_prior_high_sets = [ids for ids in prior_high_identity_sets if ids.isdisjoint(high_after_ids)]
    lost_prior_high = sorted(next(iter(ids)) for ids in lost_prior_high_sets if ids)
    baseline_primary_conf = confidence_counts(baseline_primary)
    learned_primary_conf = confidence_counts(learned_primary)
    baseline_full_conf = confidence_counts(baseline_full)
    learned_full_conf = confidence_counts(learned_full)
    baseline_high = int(baseline_primary_conf.get("high", 0))
    new_high = int(learned_primary_conf.get("high", 0))
    accepted = (
        new_high >= baseline_high
        and not lost_prior_high
        and validation.get("status") == "VALID"
        and primary_validation.get("status") == "VALID"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "run_status": "accepted" if accepted else "rejected_acceptance_rule_failed",
        "accepted": accepted,
        "baseline_total_links": len(baseline_full),
        "total_links": len(learned_full),
        "baseline_primary_clean_links": len(baseline_primary),
        "primary_clean_links": len(learned_primary),
        "baseline_full_confidence": baseline_full_conf,
        "full_confidence": learned_full_conf,
        "baseline_primary_confidence": baseline_primary_conf,
        "primary_confidence": learned_primary_conf,
        "primary_high_confidence_gained": max(0, new_high - baseline_high),
        "primary_high_confidence_lost": max(0, baseline_high - new_high),
        "prior_high_primary_links_checked": len(prior_high_identity_sets),
        "prior_high_primary_links_lost": len(lost_prior_high),
        "lost_prior_high_link_ids_sample": lost_prior_high[:25],
        "combined_primary_high_rows_available": baseline_high,
        "learned_high_examples_used": patterns.high_example_count,
        "high_rows_excluded_from_gold_examples": baseline_high - patterns.high_example_count,
        "learned_rule_patterns": len(patterns.rule_counts),
        "learned_anchor_patterns": len(patterns.anchor_counts),
        "learned_source_token_patterns": len(patterns.source_token_counts),
        "learned_target_token_patterns": len(patterns.target_token_counts),
        "full_promoted_to_high": sum(1 for row in learned_full if row.get("confidence") == "high" and row.get("previous_confidence") != "high"),
        "primary_promoted_to_high": sum(1 for row in learned_primary if row.get("confidence") == "high" and row.get("previous_confidence") != "high"),
        "full_low_to_medium": sum(1 for row in learned_full if row.get("confidence") == "medium" and row.get("previous_confidence") == "low"),
        "primary_low_to_medium": sum(1 for row in learned_primary if row.get("confidence") == "medium" and row.get("previous_confidence") == "low"),
        "baseline_manual_review_required_count": sum(bool(row.get("manual_review_required")) for row in baseline_full),
        "manual_review_required_count": sum(bool(row.get("manual_review_required")) for row in learned_full),
        "secondary_no_link_rows": len(secondary),
        "links_by_relationship_type": dict(sorted(Counter(str(row.get("relationship_type", "")) for row in learned_full).items())),
        "validation": validation,
        "primary_validation": primary_validation,
    }


def render_report(summary: dict[str, Any], output_root: Path) -> str:
    def table(mapping: dict[str, Any]) -> str:
        return "\n".join(f"| `{key}` | {value} |" for key, value in mapping.items()) or "| None | 0 |"

    primary = int(summary["primary_clean_links"])
    high = int(summary["primary_confidence"].get("high", 0))
    high_pct = high / primary * 100 if primary else 0.0
    baseline_high = int(summary["baseline_primary_confidence"].get("high", 0))
    baseline_pct = baseline_high / primary * 100 if primary else 0.0
    return f"""# Paadal-Pozhippurai v4 Combined Learned Pattern Report

## Acceptance

- Run status: `{summary['run_status']}`
- Accepted: `{str(summary['accepted']).lower()}`
- Output root: `{output_root}`
- Schema version: `{summary['schema_version']}`
- Validation status: `{summary['validation']['status']}`
- Primary validation status: `{summary['primary_validation']['status']}`

## Learning Source

- Combined primary high rows available: `{summary['combined_primary_high_rows_available']}`
- Clean high examples used as gold-like patterns: `{summary['learned_high_examples_used']}`
- High rows excluded from learning: `{summary['high_rows_excluded_from_gold_examples']}`
- Learned rule patterns: `{summary['learned_rule_patterns']}`
- Learned anchor patterns: `{summary['learned_anchor_patterns']}`
- Learned source token patterns: `{summary['learned_source_token_patterns']}`
- Learned target token patterns: `{summary['learned_target_token_patterns']}`

## Confidence Movement

- Baseline primary high confidence: `{baseline_high}` (`{baseline_pct:.1f}%`)
- New primary high confidence: `{high}` (`{high_pct:.1f}%`)
- Primary high confidence gained: `{summary['primary_high_confidence_gained']}`
- Prior high primary links lost: `{summary['prior_high_primary_links_lost']}`
- Primary promoted to high: `{summary['primary_promoted_to_high']}`
- Primary low to medium: `{summary['primary_low_to_medium']}`
- Full promoted to high: `{summary['full_promoted_to_high']}`
- Full low to medium: `{summary['full_low_to_medium']}`
- Manual review required before: `{summary['baseline_manual_review_required_count']}`
- Manual review required after: `{summary['manual_review_required_count']}`

## Primary Confidence Distribution

| Confidence | Rows |
| --- | ---: |
{table(summary['primary_confidence'])}

## Full Confidence Distribution

| Confidence | Rows |
| --- | ---: |
{table(summary['full_confidence'])}

## Relationship Distribution

| Relationship | Rows |
| --- | ---: |
{table(summary['links_by_relationship_type'])}

## Notes

- This pass learns only from the combined hardened high-confidence primary rows.
- It does not overwrite `v4_combined_hardened`; it writes a new `v4_combined_learned` output.
- These are model/rule-confidence promotions, not final scholarly gold annotations.
"""


def write_outputs(
    *,
    output_root: Path,
    report_path: Path,
    learned_full: list[dict[str, Any]],
    learned_primary: list[dict[str, Any]],
    secondary: list[dict[str, Any]],
    summary: dict[str, Any],
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_combined_learned_full.jsonl", learned_full)
    write_tsv(output_root / "paadal_pozhippurai_links_v4_combined_learned_full.tsv", learned_full)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_combined_learned_primary_clean_links.jsonl", learned_primary)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_learned_primary_clean_links.csv", learned_primary)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_combined_learned_high_confidence.jsonl", [row for row in learned_full if row.get("confidence") == "high" and not row.get("manual_review_required")])
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_combined_learned_medium_confidence.jsonl", [row for row in learned_full if row.get("confidence") == "medium" and not row.get("manual_review_required")])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_learned_low_confidence_review.csv", [row for row in learned_full if row.get("confidence") == "low" or row.get("manual_review_required")])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_learned_no_link_or_unresolved.csv", [row for row in learned_full if row.get("confidence") == "no_link" or row.get("relationship_type") == "unlinked"])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_learned_manual_review_pack.csv", build_manual_review_pack(learned_full))
    candidates = promotion_candidates(learned_primary)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_learned_promotion_candidates.csv", candidates)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_learned_pattern_groups.csv", pattern_groups(candidates))
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_learned_gold_rule_template.csv", gold_rule_template())
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_combined_learned_secondary_no_link.jsonl", secondary)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_learned_secondary_no_link.csv", secondary)
    write_iob_v4(output_root / "paadal_pozhippurai_links_v4_combined_learned_corrected_usable.iob.conll", [row for row in learned_full if row.get("confidence") in {"high", "medium"} and row.get("target_text")])
    (output_root / "paadal_pozhippurai_links_v4_combined_learned_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report = render_report(summary, output_root)
    report_path.write_text(report, encoding="utf-8")
    (output_root / "baseline_vs_combined_learned_report.md").write_text(report, encoding="utf-8")


def run_learning(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    combined_root: Path = DEFAULT_COMBINED_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    full = load_jsonl(combined_root / "paadal_pozhippurai_links_v4_combined_hardened_full.jsonl")
    primary = load_jsonl(combined_root / "paadal_pozhippurai_links_v4_combined_hardened_primary_clean_links.jsonl")
    secondary = load_jsonl(combined_root / "paadal_pozhippurai_links_v4_combined_hardened_secondary_no_link.jsonl")
    prior_high_identity_sets = [identity_set(row) for row in primary if row.get("confidence") == "high"]
    patterns = learn_patterns(row for row in primary if bool(is_gold_example(row)))
    learned_full = stamp_schema(apply_learned_patterns(full, patterns))
    learned_primary = stamp_schema(apply_learned_patterns(primary, patterns))
    validation = validate_v4_links(table_root, learned_full)
    primary_validation = validate_clean_links(table_root, learned_primary)
    summary = summarize(
        learned_full=learned_full,
        learned_primary=learned_primary,
        secondary=secondary,
        baseline_full=full,
        baseline_primary=primary,
        patterns=patterns,
        validation=validation,
        primary_validation=primary_validation,
        prior_high_identity_sets=prior_high_identity_sets,
    )
    write_outputs(
        output_root=output_root,
        report_path=report_path,
        learned_full=learned_full,
        learned_primary=learned_primary,
        secondary=secondary,
        summary=summary,
    )
    return {**summary, "output_root": str(output_root), "report": str(report_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Learn from v4_combined_hardened high-confidence links and recalibrate low/medium rows.")
    parser.add_argument("--table-root", "--input-root", dest="table_root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--combined-root", type=Path, default=DEFAULT_COMBINED_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = run_learning(table_root=args.table_root, combined_root=args.combined_root, output_root=args.output_root, report_path=args.report)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
