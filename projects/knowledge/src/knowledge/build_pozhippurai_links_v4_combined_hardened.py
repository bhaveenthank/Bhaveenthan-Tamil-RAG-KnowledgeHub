from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from knowledge.build_pozhippurai_links_v4 import validate_clean_links, validate_v4_links, write_iob_v4
from knowledge.build_pozhippurai_links_v4_hardened import load_hardening_pack
from knowledge.fix_ambiguous_pozhippurai_spans import (
    ambiguous_count,
    apply_ambiguity_fix,
)
from knowledge.fix_missing_anchor_links import (
    apply_missing_anchor_fix,
    load_anchor_rules,
    missing_anchor_count,
)
from knowledge.fix_pozhippurai_broad_targets import (
    broad_count,
    fix_rows,
)
from knowledge.learn_pozhippurai_high_confidence_patterns import load_jsonl
from knowledge.link_thevaram_pozhippurai import DEFAULT_TABLE_ROOT, read_jsonl
from knowledge.link_thevaram_pozhippurai_v3 import build_manual_review_pack, write_csv_file, write_jsonl, write_tsv

SCHEMA_VERSION = "thevaram-pozhppurai-paadallink-v4-combined-hardened"
DEFAULT_BASE_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_hardened_learned")
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram_pozhippurai_links/v4_combined_hardened")
DEFAULT_REPORT = DEFAULT_OUTPUT_ROOT / "paadal_pozhippurai_links_v4_combined_hardened_report.md"


def confidence_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get("confidence", "")) for row in rows).items()))


def stable_identity(row: dict[str, Any]) -> str:
    return str(row.get("base_link_id") or row.get("link_id") or "")


def baseline_counts(base_root: Path, paadal_by_id: dict[str, str]) -> dict[str, Any]:
    full = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_full.jsonl")
    primary = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_primary_clean_links.jsonl")
    return {
        "total_links": len(full),
        "primary_links": len(primary),
        "full_confidence": confidence_counts(full),
        "primary_confidence": confidence_counts(primary),
        "full_broad_target_count": broad_count(full, paadal_by_id),
        "primary_broad_target_count": broad_count(primary, paadal_by_id),
        "full_missing_anchor_count": missing_anchor_count(full),
        "primary_missing_anchor_count": missing_anchor_count(primary),
        "full_ambiguous_span_count": ambiguous_count(full),
        "primary_ambiguous_span_count": ambiguous_count(primary),
        "manual_review_required_count": sum(bool(row.get("manual_review_required")) for row in full),
        "relationship_type_counts": dict(sorted(Counter(row.get("relationship_type", "") for row in full).items())),
    }


def stamp_schema(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stamped = []
    for row in rows:
        item = dict(row)
        item["schema_version"] = SCHEMA_VERSION
        item["combined_base_schema_version"] = row.get("schema_version", "")
        item["combined_hardening_layers"] = [
            "broad_target_minimal_span",
            "missing_anchor_resolver",
            "ambiguous_span_global_assignment",
        ]
        stamped.append(item)
    return stamped


def apply_combined(
    rows: list[dict[str, Any]],
    *,
    table_root: Path,
    paadal_by_id: dict[str, str],
    hardening_pack: Any,
    anchor_rules: Any,
) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    broad_rows, broad_changes = fix_rows(rows, paadal_by_id, hardening_pack)
    missing_rows, missing_changes = apply_missing_anchor_fix(broad_rows, anchor_rules)
    ambiguous_rows, ambiguity_changes = apply_ambiguity_fix(missing_rows, table_root, hardening_pack)
    return stamp_schema(ambiguous_rows), {
        "broad_changes": broad_changes,
        "missing_changes": missing_changes,
        "ambiguity_changes": ambiguity_changes,
    }


def summarize(
    *,
    full: list[dict[str, Any]],
    primary: list[dict[str, Any]],
    changes: dict[str, list[dict[str, Any]]],
    baseline: dict[str, Any],
    paadal_by_id: dict[str, str],
    validation: dict[str, Any],
    primary_validation: dict[str, Any],
    prior_high_ids: set[str],
) -> dict[str, Any]:
    primary_conf = Counter(str(row.get("confidence", "")) for row in primary)
    high_before = int(baseline.get("primary_confidence", {}).get("high", 0))
    high_after = primary_conf.get("high", 0)
    current_high_ids = {stable_identity(row) for row in primary if row.get("confidence") == "high"}
    lost_high_ids = sorted(prior_high_ids - current_high_ids)
    broad_after = broad_count(primary, paadal_by_id)
    missing_after = missing_anchor_count(primary)
    ambiguous_after = ambiguous_count(primary)
    accepted = (
        broad_after < int(baseline.get("primary_broad_target_count", 0))
        and missing_after < int(baseline.get("primary_missing_anchor_count", 0))
        and ambiguous_after < int(baseline.get("primary_ambiguous_span_count", 0))
        and high_after >= high_before
        and not lost_high_ids
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
        "full_confidence": confidence_counts(full),
        "primary_confidence": dict(sorted(primary_conf.items())),
        "full_broad_target_count": broad_count(full, paadal_by_id),
        "primary_broad_target_count": broad_after,
        "broad_target_rows_resolved": int(baseline.get("primary_broad_target_count", 0)) - broad_after,
        "full_missing_anchor_count": missing_anchor_count(full),
        "primary_missing_anchor_count": missing_after,
        "missing_anchor_rows_resolved": int(baseline.get("primary_missing_anchor_count", 0)) - missing_after,
        "full_ambiguous_span_count": ambiguous_count(full),
        "primary_ambiguous_span_count": ambiguous_after,
        "ambiguous_rows_resolved": int(baseline.get("primary_ambiguous_span_count", 0)) - ambiguous_after,
        "high_confidence_gained": max(0, high_after - high_before),
        "high_confidence_lost": max(0, high_before - high_after),
        "prior_high_primary_links_checked": len(prior_high_ids),
        "prior_high_primary_links_lost": len(lost_high_ids),
        "lost_prior_high_link_ids_sample": lost_high_ids[:25],
        "target_shrink_applied_count": len(changes["broad_changes"]),
        "missing_anchor_change_rows": len(changes["missing_changes"]),
        "ambiguity_change_rows": len(changes["ambiguity_changes"]),
        "medium_upgraded_to_high_total": max(0, high_after - high_before),
        "low_or_medium_changed_total": sum(
            1
            for row in primary
            if row.get("previous_confidence")
            and row.get("previous_confidence") != row.get("confidence")
        ),
        "manual_review_required_count": sum(bool(row.get("manual_review_required")) for row in full),
        "relationship_type_counts": dict(sorted(Counter(row.get("relationship_type", "") for row in full).items())),
        "validation": validation,
        "primary_validation": primary_validation,
    }


def render_report(summary: dict[str, Any], output_root: Path) -> str:
    def table(mapping: dict[str, Any]) -> str:
        return "\n".join(f"| `{key}` | {value} |" for key, value in mapping.items()) or "| None | 0 |"

    baseline = summary["baseline"]
    return f"""# Paadal-Pozhippurai v4 Combined Hardened Report

## Acceptance

- Run status: `{summary['run_status']}`
- Accepted: `{str(summary['accepted']).lower()}`
- Output root: `{output_root}`
- Schema version: `{summary['schema_version']}`

## Baseline Versus Combined

- Baseline total links: `{baseline['total_links']}`
- Combined total links: `{summary['total_links']}`
- Baseline primary high confidence: `{baseline['primary_confidence'].get('high', 0)}`
- Combined primary high confidence: `{summary['primary_confidence'].get('high', 0)}`
- High confidence gained: `{summary['high_confidence_gained']}`
- Prior high primary links lost: `{summary['prior_high_primary_links_lost']}`

## Blocker Counts

| Issue | Baseline Primary | Combined Primary | Resolved |
| --- | ---: | ---: | ---: |
| `broad_target` | {baseline['primary_broad_target_count']} | {summary['primary_broad_target_count']} | {summary['broad_target_rows_resolved']} |
| `missing_anchor` | {baseline['primary_missing_anchor_count']} | {summary['primary_missing_anchor_count']} | {summary['missing_anchor_rows_resolved']} |
| `ambiguous_span` | {baseline['primary_ambiguous_span_count']} | {summary['primary_ambiguous_span_count']} | {summary['ambiguous_rows_resolved']} |

## Change Counts

- Target shrink applied rows: `{summary['target_shrink_applied_count']}`
- Missing-anchor change rows: `{summary['missing_anchor_change_rows']}`
- Ambiguity change rows: `{summary['ambiguity_change_rows']}`
- Manual review required: `{summary['manual_review_required_count']}`
- Validation status: `{summary['validation']['status']}`
- Primary validation status: `{summary['primary_validation']['status']}`

## Combined Confidence Distribution

| Confidence | Rows |
| --- | ---: |
{table(summary['full_confidence'])}

## Primary Confidence Distribution

| Confidence | Rows |
| --- | ---: |
{table(summary['primary_confidence'])}

## Relationship Distribution

| Relationship | Rows |
| --- | ---: |
{table(summary['relationship_type_counts'])}

## Notes

- This is the first cumulative table applying the accepted broad-target, missing-anchor, and ambiguous-span fixes together.
- It still does not claim final scholarly gold accuracy.
- Remaining low/medium rows should be handled with targeted manual review and additional accepted rules.
"""


def write_outputs(
    output_root: Path,
    full: list[dict[str, Any]],
    primary: list[dict[str, Any]],
    secondary: list[dict[str, Any]],
    changes: dict[str, list[dict[str, Any]]],
    summary: dict[str, Any],
    report_path: Path,
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_combined_hardened_full.jsonl", full)
    write_tsv(output_root / "paadal_pozhippurai_links_v4_combined_hardened_full.tsv", full)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_combined_hardened_primary_clean_links.jsonl", primary)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_hardened_primary_clean_links.csv", primary)
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_combined_hardened_high_confidence.jsonl", [row for row in full if row.get("confidence") == "high" and not row.get("manual_review_required")])
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_combined_hardened_medium_confidence.jsonl", [row for row in full if row.get("confidence") == "medium" and not row.get("manual_review_required")])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_hardened_low_review.csv", [row for row in full if row.get("confidence") == "low" or row.get("manual_review_required")])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_hardened_no_link_or_unresolved.csv", [row for row in full if row.get("confidence") == "no_link" or row.get("relationship_type") == "unlinked"])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_hardened_broad_target_changes.csv", changes["broad_changes"])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_hardened_missing_anchor_changes.csv", changes["missing_changes"])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_hardened_ambiguity_changes.csv", changes["ambiguity_changes"])
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_hardened_manual_review_pack.csv", build_manual_review_pack(full))
    write_jsonl(output_root / "paadal_pozhippurai_links_v4_combined_hardened_secondary_no_link.jsonl", secondary)
    write_csv_file(output_root / "paadal_pozhippurai_links_v4_combined_hardened_secondary_no_link.csv", secondary)
    write_iob_v4(output_root / "paadal_pozhippurai_links_v4_combined_hardened_corrected_usable.iob.conll", [row for row in full if row.get("confidence") in {"high", "medium"} and row.get("target_text")])
    (output_root / "paadal_pozhippurai_links_v4_combined_hardened_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report = render_report(summary, output_root)
    report_path.write_text(report, encoding="utf-8")
    (output_root / "baseline_vs_combined_hardened_report.md").write_text(report, encoding="utf-8")


def run_combined(
    *,
    table_root: Path = DEFAULT_TABLE_ROOT,
    base_root: Path = DEFAULT_BASE_ROOT,
    output_root: Path = DEFAULT_OUTPUT_ROOT,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    paadal_by_id = {str(row.get("paadal_id", "")): str(row.get("paadal_text", "")) for row in read_jsonl(table_root / "paadalgal.jsonl")}
    hardening_pack = load_hardening_pack()
    anchor_rules, _ontology = load_anchor_rules()
    full = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_full.jsonl")
    primary = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_primary_clean_links.jsonl")
    secondary = load_jsonl(base_root / "paadal_pozhippurai_links_v4_hardened_learned_secondary_no_link.jsonl")
    baseline = baseline_counts(base_root, paadal_by_id)
    prior_high_ids = {stable_identity(row) for row in primary if row.get("confidence") == "high"}

    combined_full, full_changes = apply_combined(full, table_root=table_root, paadal_by_id=paadal_by_id, hardening_pack=hardening_pack, anchor_rules=anchor_rules)
    combined_primary, primary_changes = apply_combined(primary, table_root=table_root, paadal_by_id=paadal_by_id, hardening_pack=hardening_pack, anchor_rules=anchor_rules)
    validation = validate_v4_links(table_root, combined_full)
    primary_validation = validate_clean_links(table_root, combined_primary)
    summary = summarize(
        full=combined_full,
        primary=combined_primary,
        changes=primary_changes,
        baseline=baseline,
        paadal_by_id=paadal_by_id,
        validation=validation,
        primary_validation=primary_validation,
        prior_high_ids=prior_high_ids,
    )
    write_outputs(output_root, combined_full, combined_primary, secondary, primary_changes, summary, report_path)
    return {**summary, "output_root": str(output_root), "report": str(report_path)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build cumulative v4 combined hardened paadal-pozhppurai links.")
    parser.add_argument("--table-root", "--input-root", dest="table_root", type=Path, default=DEFAULT_TABLE_ROOT)
    parser.add_argument("--base-root", type=Path, default=DEFAULT_BASE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    summary = run_combined(table_root=args.table_root, base_root=args.base_root, output_root=args.output_root, report_path=args.report)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
