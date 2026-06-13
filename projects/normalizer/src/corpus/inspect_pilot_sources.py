from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_PLAN = Path("data/processed/corpus_registry/pilot_category_plan.json")
DEFAULT_FIXTURE_PLAN = Path(
    "data/processed/corpus_registry/pilot_fixture_plan.json"
)
DEFAULT_FIXTURE_ROOT = Path("tests/fixtures/pilot_categories")
DEFAULT_REPORT = Path("reports/pilot-source-inspection-report.md")

INSPECTION_PROFILES: dict[str, dict[str, Any]] = {
    "grammar": {
        "fixture_type": "html",
        "risk_level": "medium",
        "expected_source_structure": (
            "Book/chapter headings with numbered sutra or rule text, explanation, "
            "examples, exceptions, and possible commentary."
        ),
        "fixture_focus": [
            "navigation or contents page",
            "single rule with explanation",
            "rule with examples or commentary",
        ],
        "notes": (
            "Rule boundaries and explanation labels must be confirmed from source HTML."
        ),
        "priority_rank": 2,
    },
    "sangam_literature": {
        "fixture_type": "html",
        "risk_level": "high",
        "expected_source_structure": (
            "Anthology/work hierarchy with poem number, poet, thinai/thurai metadata, "
            "verse lines, colophon, and optional commentary."
        ),
        "fixture_focus": [
            "anthology or poem navigation",
            "poem with literary metadata",
            "poem with commentary or colophon",
        ],
        "notes": (
            "Poem boundaries and source-provided literary metadata must not be flattened."
        ),
        "priority_rank": 3,
    },
    "twentieth_century_prose": {
        "fixture_type": "text",
        "risk_level": "high",
        "expected_source_structure": (
            "Book, chapter, section, paragraph, page, footnote, and author or edition "
            "metadata in typed HTML or document-oriented pages."
        ),
        "fixture_focus": [
            "book or chapter contents",
            "prose section with paragraphs",
            "section with page markers or footnotes",
        ],
        "notes": (
            "Rights and public-domain status must be confirmed before any source capture."
        ),
        "priority_rank": 4,
    },
    "dictionaries": {
        "fixture_type": "dictionary_entry",
        "risk_level": "medium",
        "expected_source_structure": (
            "Headword navigation with one or more senses, grammatical labels, examples, "
            "etymology, and cross-references."
        ),
        "fixture_focus": [
            "headword index or navigation",
            "single-sense entry",
            "multi-sense entry with cross-reference",
        ],
        "notes": (
            "A bounded dictionary entry is the simplest new structured-text parser pilot."
        ),
        "priority_rank": 1,
    },
    "encyclopedias": {
        "fixture_type": "mixed",
        "risk_level": "high",
        "expected_source_structure": (
            "Headword article with sections, references, author/editor metadata, "
            "cross-links, tables, and possible images."
        ),
        "fixture_focus": [
            "article index or navigation",
            "plain text article",
            "article with references, table, or media",
        ],
        "notes": (
            "The current dictionary-parser assignment may need a dedicated encyclopedia "
            "adapter after fixtures expose mixed article and media structure."
        ),
        "priority_rank": 5,
    },
}


def load_plan(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def is_verified(pilot: dict[str, Any]) -> bool:
    return pilot.get("status") in {"local_seed_ready", "verified", "pilot_verified"}


def remaining_pilots(plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        pilot
        for pilot in plan.get("pilots", [])
        if not is_verified(pilot)
    ]


def build_fixture_plan(plan: dict[str, Any]) -> dict[str, Any]:
    fixtures = []
    for pilot in remaining_pilots(plan):
        category_id = pilot["category_id"]
        if category_id not in INSPECTION_PROFILES:
            raise ValueError(f"missing inspection profile for pilot: {category_id}")
        profile = INSPECTION_PROFILES[category_id]
        fixtures.append(
            {
                "category_id": category_id,
                "category_tamil": pilot["category_tamil"],
                "parser_family": pilot["parser_family"],
                "fixture_needed": True,
                "fixture_type": profile["fixture_type"],
                "target_fixture_count": 3,
                "risk_level": profile["risk_level"],
                "source_inspection_status": "metadata_only_unconfirmed",
                "expected_source_structure": profile["expected_source_structure"],
                "fixture_focus": profile["fixture_focus"],
                "notes": profile["notes"],
                "recommended_order": profile["priority_rank"],
            }
        )
    return {
        "fixture_plan_version": "pilot-fixture-plan-v1",
        "source_basis": "pilot registry metadata; no live source fetch",
        "network_access": False,
        "verified_categories": [
            pilot["category_id"]
            for pilot in plan.get("pilots", [])
            if is_verified(pilot)
        ],
        "remaining_category_count": len(fixtures),
        "fixtures": sorted(fixtures, key=lambda item: item["recommended_order"]),
    }


def fixture_readme(item: dict[str, Any]) -> str:
    focus = "\n".join(f"{index}. {value}" for index, value in enumerate(item["fixture_focus"], 1))
    return f"""# {item['category_tamil']} Pilot Fixtures

- Category ID: `{item['category_id']}`
- Parser family: `{item['parser_family']}`
- Planned fixture type: `{item['fixture_type']}`
- Target fixture count: `{item['target_fixture_count']}`
- Risk level: `{item['risk_level']}`
- Source status: `{item['source_inspection_status']}`

## Expected Structure

{item['expected_source_structure']}

## Required Fixture Coverage

{focus}

## Collection Rule

Add only a tiny, allowlisted, source-attributed fixture after source inspection is
explicitly approved. Do not place full books, full category exports, credentials,
copyright-restricted bulk text, or generated corpus outputs in this directory.

## Notes

{item['notes']}
"""


def render_report(fixture_plan: dict[str, Any]) -> str:
    rows = []
    for item in fixture_plan["fixtures"]:
        rows.append(
            f"| {item['recommended_order']} | {item['category_tamil']} "
            f"| `{item['parser_family']}` | `{item['fixture_type']}` "
            f"| {item['target_fixture_count']} | {item['risk_level']} "
            f"| {item['expected_source_structure']} | {item['notes']} |"
        )
    dictionary_verified = "dictionaries" in fixture_plan["verified_categories"]
    recommendation = (
        """Develop `grammar_parser` next using a tiny grammar fixture set. Dictionary
entry parsing is now pilot-verified, so grammar provides the simplest new hierarchy:
rule, explanation, example, exception, and commentary. Follow with the Sangam
`verse_parser` variant."""
        if dictionary_verified
        else """Develop `dictionary_parser` next using the `dictionaries` category. A small
headword entry is likely to provide the clearest new structured-text boundary after the
proven verse parser. Follow with `grammar_parser`, then the Sangam `verse_parser` variant."""
    )
    recommended_order = (
        """1. Grammar: rule, explanation, and example boundaries.
2. Sangam literature: poem hierarchy and literary metadata.
3. Twentieth-century prose: chapter/paragraph extraction after rights review.
4. Encyclopedias: mixed article/media structure after simpler dictionary evidence."""
        if dictionary_verified
        else """1. Dictionaries: bounded headword and sense structures.
2. Grammar: rule, explanation, and example boundaries.
3. Sangam literature: poem hierarchy and literary metadata.
4. Twentieth-century prose: chapter/paragraph extraction after rights review.
5. Encyclopedias: mixed article/media structure after simpler dictionary evidence."""
    )
    return f"""# Pilot Source Inspection Report

## Scope

This is a metadata-only source inspection and fixture plan. It reads the controlled pilot
registry and does not fetch TamilVU pages, traverse links, ingest records, or write raw
source content.

## Status

- Already verified: `{", ".join(fixture_plan['verified_categories'])}`
- Remaining pilot categories: `{fixture_plan['remaining_category_count']}`
- Planned fixtures per category: `3`
- Network requests: `0`
- Source-specific structures: `unconfirmed until allowlisted fixture collection`

## Remaining Categories

| Order | Category | Parser Family | Fixture Type | Count | Risk | Expected Source Structure | Inspection Note |
| ---: | --- | --- | --- | ---: | --- | --- | --- |
{chr(10).join(rows)}

## Parser Development Recommendation

{recommendation}

The highest-risk parser application is `dictionary_parser` for encyclopedias because
articles may contain sections, references, tables, cross-links, and media that exceed a
simple headword/sense model. Treat it as a separate adapter decision after fixtures.

## Recommended Order

{recommended_order}

Image, manuscript, OCR, PDF-heavy, mixed-site, and full-category work remains deferred.
"""


def inspect_sources(
    *,
    base_dir: Path = Path("."),
    plan_path: Path = DEFAULT_PLAN,
    fixture_plan_path: Path = DEFAULT_FIXTURE_PLAN,
    fixture_root: Path = DEFAULT_FIXTURE_ROOT,
    report_path: Path = DEFAULT_REPORT,
    dry_run: bool = False,
) -> dict[str, Any]:
    plan = load_plan(base_dir / plan_path)
    fixture_plan = build_fixture_plan(plan)
    summary = {
        "action": "dry_run" if dry_run else "write_plan",
        "verified_categories": fixture_plan["verified_categories"],
        "remaining_categories": [
            item["category_id"] for item in fixture_plan["fixtures"]
        ],
        "fixture_directories": len(fixture_plan["fixtures"]),
        "target_fixture_count": sum(
            item["target_fixture_count"] for item in fixture_plan["fixtures"]
        ),
        "network_requests": 0,
        "writes": 0 if dry_run else 2 + len(fixture_plan["fixtures"]),
    }
    if dry_run:
        return summary

    output_plan = base_dir / fixture_plan_path
    output_plan.parent.mkdir(parents=True, exist_ok=True)
    output_plan.write_text(
        json.dumps(fixture_plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for item in fixture_plan["fixtures"]:
        directory = base_dir / fixture_root / item["category_id"]
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "README.md").write_text(fixture_readme(item), encoding="utf-8")
    report = base_dir / report_path
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(render_report(fixture_plan), encoding="utf-8")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Plan tiny local fixtures for unverified pilot categories."
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        summary = inspect_sources(base_dir=args.base_dir, dry_run=args.dry_run)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
