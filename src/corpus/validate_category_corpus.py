from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from corpus.pilot_ingest_category import DEFAULT_PLAN, load_json, load_jsonl
from corpus.normalize_category_corpus import default_normalized_path

REQUIRED_FIELDS = {
    "schema_version": str,
    "record_id": str,
    "record_type": str,
    "category_id": str,
    "book_id": str,
    "work_id": str,
    "language": str,
    "content_text": str,
    "source_url": str,
    "source_metadata": dict,
    "parser_family": str,
}


def valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_records(records: list[dict[str, Any]], category_id: str) -> dict[str, Any]:
    missing: Counter[str] = Counter()
    invalid_types: Counter[str] = Counter()
    malformed_urls = 0
    category_mismatches = 0
    ids: Counter[str] = Counter()
    dictionary_missing: Counter[str] = Counter()
    sangam_missing: Counter[str] = Counter()
    grammar_missing: Counter[str] = Counter()
    prose_missing: Counter[str] = Counter()
    nondeterministic_ids = 0

    for record in records:
        for field, expected_type in REQUIRED_FIELDS.items():
            if field not in record:
                missing[field] += 1
            elif not isinstance(record[field], expected_type):
                invalid_types[field] += 1
            elif isinstance(record[field], str) and not record[field].strip():
                missing[field] += 1
        if not str(record.get("content_text") or record.get("verse_text") or "").strip():
            missing["content_text_or_verse_text"] += 1
        if record.get("category_id") != category_id:
            category_mismatches += 1
        if isinstance(record.get("source_url"), str) and not valid_url(record["source_url"]):
            malformed_urls += 1
        record_id = str(record.get("record_id") or "")
        if record_id:
            ids[record_id] += 1
        if category_id == "dictionaries":
            for field in ("entry_headword", "definition", "source_url"):
                if not str(record.get(field) or "").strip():
                    dictionary_missing[field] += 1
            if record_id and not record_id.startswith("tvu_dictionaries_"):
                nondeterministic_ids += 1
        if category_id == "sangam_literature":
            for field in (
                "verse_text",
                "verse_no",
                "poem_no",
                "thinai",
                "author",
                "source_url",
            ):
                if not str(record.get(field) or "").strip():
                    sangam_missing[field] += 1
            if record_id and not record_id.startswith("tvu_sangam_literature_"):
                nondeterministic_ids += 1
        if category_id == "grammar":
            for field in (
                "rule_no",
                "rule_text",
                "source_url",
                "parser_family",
                "record_type",
            ):
                if not str(record.get(field) or "").strip():
                    grammar_missing[field] += 1
            if record_id and not record_id.startswith("tvu_grammar_"):
                nondeterministic_ids += 1
        if category_id == "twentieth_century_prose":
            for field in (
                "category_id",
                "parser_family",
                "record_type",
                "content_text",
                "source_url",
            ):
                if not str(record.get(field) or "").strip():
                    prose_missing[field] += 1
            if record.get("parser_family") != "prose_parser":
                prose_missing["parser_family"] += 1
            if record.get("record_type") != "prose_section":
                prose_missing["record_type"] += 1
            if record_id and not record_id.startswith(
                "tvu_twentieth_century_prose_"
            ):
                nondeterministic_ids += 1

    duplicates = sorted(record_id for record_id, count in ids.items() if count > 1)
    error_count = (
        sum(missing.values())
        + sum(invalid_types.values())
        + sum(dictionary_missing.values())
        + sum(sangam_missing.values())
        + sum(grammar_missing.values())
        + sum(prose_missing.values())
        + malformed_urls
        + category_mismatches
        + nondeterministic_ids
        + len(duplicates)
    )
    return {
        "category_id": category_id,
        "record_count": len(records),
        "status": "VALID" if records and error_count == 0 else "INVALID",
        "error_count": error_count if records else error_count + 1,
        "missing_fields": dict(sorted(missing.items())),
        "invalid_field_types": dict(sorted(invalid_types.items())),
        "malformed_source_urls": malformed_urls,
        "category_mismatches": category_mismatches,
        "duplicate_record_ids": duplicates,
        "dictionary_missing_fields": dict(sorted(dictionary_missing.items())),
        "sangam_missing_fields": dict(sorted(sangam_missing.items())),
        "grammar_missing_fields": dict(sorted(grammar_missing.items())),
        "prose_missing_fields": dict(sorted(prose_missing.items())),
        "nondeterministic_ids": nondeterministic_ids,
        "source_url_coverage": (
            sum(bool(record.get("source_url")) for record in records) / len(records)
            if records
            else 0.0
        ),
    }


def render_dictionary_report(result: dict[str, Any]) -> str:
    missing_rows = "\n".join(
        f"| `{field}` | {count} |"
        for field, count in result["dictionary_missing_fields"].items()
    ) or "| None | 0 |"
    return f"""# Dictionary Pilot Validation Report

## Summary

- Records validated: `{result['record_count']}`
- Status: `{result['status']}`
- Validation errors: `{result['error_count']}`
- Source URL coverage: `{result['source_url_coverage']:.1%}`
- Duplicate record IDs: `{len(result['duplicate_record_ids'])}`
- Non-deterministic IDs: `{result['nondeterministic_ids']}`
- Malformed source URLs: `{result['malformed_source_urls']}`

## Dictionary Fields

| Missing Field | Count |
| --- | ---: |
{missing_rows}

`part_of_speech` is optional because the selected source table does not label it
explicitly. The parser leaves it empty and records `part_of_speech_source=not_provided`
instead of inferring a grammatical category.

## Decision

The dictionary pilot is `{'PILOT_VERIFIED' if result['status'] == 'VALID' else 'REPAIR_REQUIRED'}`.
This decision applies only to the three-page fixture set and does not authorize category
scraping.
"""


def render_dictionary_readiness(result: dict[str, Any]) -> str:
    ready = result["status"] == "VALID"
    return f"""# Dictionary Pilot Readiness Report

## Assessment

| Dimension | Result | Evidence |
| --- | --- | --- |
| Parser quality | `{'READY' if ready else 'REPAIR'}` | Two-column TamilVU entry table mapped without inferred fields |
| Normalization quality | `{'READY' if ready else 'REPAIR'}` | Unified schema v2 dictionary record with deterministic identity |
| Metadata quality | `{'READY' if ready else 'REPAIR'}` | Exact source URL, fixture path, work title, and source checksum retained |
| Synonym readiness | `FOUNDATIONAL` | Semicolon-delimited meanings remain source text; sense splitting is deferred |
| Literary-analysis contribution | `FOUNDATIONAL` | Headword definitions can later support lexical explanation and synonym authority |

## Limits

- Evidence covers exactly three pages and one dictionary entry.
- Part of speech is absent from the source response and is not inferred.
- Individual senses, examples, etymologies, and cross-references are not yet structurally split.
- No claim is made about all entries or other TamilVU dictionaries and nigandus.

## Recommendation

`{'PILOT_VERIFIED' if ready else 'REPAIR_REQUIRED'}` for the bounded
M. Shanmugampillai Tamil-Tamil Agaramuthali fixture set. Before expansion, sample
multi-row and structurally unusual entry pages under a separately approved phase.
"""


def render_sangam_report(result: dict[str, Any]) -> str:
    missing_rows = "\n".join(
        f"| `{field}` | {count} |"
        for field, count in result["sangam_missing_fields"].items()
    ) or "| None | 0 |"
    return f"""# Sangam Literature Pilot Validation Report

## Summary

- Work: `நற்றிணை`
- Fixture pages: `3`
- Poems validated: `{result['record_count']}`
- Status: `{result['status']}`
- Validation errors: `{result['error_count']}`
- Source URL coverage: `{result['source_url_coverage']:.1%}`
- Duplicate record IDs: `{len(result['duplicate_record_ids'])}`
- Non-deterministic IDs: `{result['nondeterministic_ids']}`

## Required Sangam Fields

| Missing Field | Count |
| --- | ---: |
{missing_rows}

The source explicitly labels poem number and thinai. Poet and situation are split from the
source colophon at its final separator. `thurai` stores the source situation text; it is
not normalized to a controlled literary taxonomy in this pilot.

## Decision

The Natrinai pilot is `{'PILOT_VERIFIED' if result['status'] == 'VALID' else 'REPAIR_REQUIRED'}`.
This decision covers three allowlisted fixture pages and three poems only. It does not
authorize downloading the remaining poem groups or commentary pages.
"""


def render_sangam_readiness(result: dict[str, Any]) -> str:
    ready = result["status"] == "VALID"
    return f"""# Sangam Literature Pilot Readiness Report

## Pilot Result

- Fixtures collected: `3`
- Records parsed: `{result['record_count']}`
- Records normalized: `{result['record_count']}`
- Validation errors: `{result['error_count']}`
- Source URL coverage: `{result['source_url_coverage']:.1%}`
- Missing required Sangam metadata: `{sum(result['sangam_missing_fields'].values())}`

## Assessment

| Dimension | Result | Evidence |
| --- | --- | --- |
| Parser quality | `{'READY' if ready else 'REPAIR'}` | Three poem boundaries parsed from one bounded Natrinai page excerpt |
| Normalization quality | `{'READY' if ready else 'REPAIR'}` | Unified schema v2 preserves verse lines, poem identity, thinai, poet, and colophon |
| Metadata quality | `{'READY' if ready else 'REPAIR'}` | Exact source URL, commentary URL, fixture checksum, work, and subid retained |
| Citation readiness | `{'READY' if ready else 'REPAIR'}` | Work title and poem number provide stable source-unit citations |
| Literary-analysis contribution | `HIGH` | Adds poet, thinai, situation, and anthology comparison beyond devotional verse |

## Comparison With Saivam

Both pilots preserve ordered Tamil verse, deterministic identity, exact source URLs, and
commentary links through `verse_parser`. Saivam retains hymn, sacred-place, pann, and
commentary fields; Sangam retains anthology poem number, thinai, source situation, poet,
and colophon. The clean validation of both shapes shows that `verse_parser` generalizes
beyond Thirumurai while keeping tradition-specific fields distinct.

## Missing Metadata Findings

No required field is missing in the three parsed poems. The source does not expose places
or normalized themes as dedicated fields, and the pilot does not infer them. Commentary
text is also absent because only the commentary URLs were retained; those pages were
outside the three-request fixture scope.

## Limits

- Evidence covers exactly three source pages and poems 1-3 from Natrinai.
- The original content endpoint groups ten poems; the committed fixture is a bounded excerpt.
- Commentary URLs are preserved but commentary pages were not fetched.
- `thurai` is source colophon prose, not a normalized scholarly classification.
- The parser is not yet proven against missing-poet, variant-colophon, or damaged poem pages.

## Recommendation

`{'PILOT_VERIFIED' if ready else 'REPAIR_REQUIRED'}` for the bounded Natrinai fixture set.
Before expansion, sample structurally unusual poems under a separately approved phase.
"""


def render_grammar_report(result: dict[str, Any]) -> str:
    missing_rows = "\n".join(
        f"| `{field}` | {count} |"
        for field, count in result["grammar_missing_fields"].items()
    ) or "| None | 0 |"
    return f"""# Grammar Pilot Validation Report

## Summary

- Work: `நன்னூல் - காண்டிகையுரை`
- Fixture pages: `3`
- Rules validated: `{result['record_count']}`
- Status: `{result['status']}`
- Validation errors: `{result['error_count']}`
- Source URL coverage: `{result['source_url_coverage']:.1%}`
- Duplicate record IDs: `{len(result['duplicate_record_ids'])}`
- Non-deterministic IDs: `{result['nondeterministic_ids']}`

## Required Grammar Fields

| Missing Field | Count |
| --- | ---: |
{missing_rows}

Rule number, rule text, chapter, section, source URL, and commentary URL are retained.
`explanation_text` is optional in this pilot because commentary pages would have exceeded
the approved three-page fixture limit.

## Decision

The Nannul grammar pilot is
`{'PILOT_VERIFIED' if result['status'] == 'VALID' else 'REPAIR_REQUIRED'}`.
This decision covers the wrapper, navigation, and one two-rule content page only. It does
not authorize downloading other Nannul sections or commentary pages.
"""


def render_grammar_readiness(result: dict[str, Any]) -> str:
    ready = result["status"] == "VALID"
    return f"""# Grammar Pilot Readiness Report

## Pilot Result

- Fixtures collected: `3`
- Records parsed: `{result['record_count']}`
- Records normalized: `{result['record_count']}`
- Validation errors: `{result['error_count']}`
- Source URL coverage: `{result['source_url_coverage']:.1%}`
- Missing required grammar metadata: `{sum(result['grammar_missing_fields'].values())}`

## Assessment

| Dimension | Result | Evidence |
| --- | --- | --- |
| Parser quality | `{'READY' if ready else 'REPAIR'}` | Two numbered Nannul rules parsed with preserved line breaks |
| Normalization quality | `{'READY' if ready else 'REPAIR'}` | Unified schema v2 retains rule, chapter, section, and source identity |
| Metadata quality | `{'READY' if ready else 'REPAIR'}` | Exact rule page, commentary URL, fixture checksum, work, and subid retained |
| Citation readiness | `{'READY' if ready else 'REPAIR'}` | Work, subsection, and rule number form stable citations |
| Linguistic-analysis contribution | `FOUNDATIONAL` | Adds explicit grammatical rules and classifications beyond literary and lexical records |

## Comparison With Existing Pilots

Verse records center on ordered poetic lines and literary hierarchy. Dictionary records
center on headwords and definitions. Grammar records center on a numbered rule within a
chapter and section, with explanation kept separate. The common envelope supports all
three shapes without reusing verse or dictionary fields incorrectly.

## Missing Metadata Findings

No required grammar field is missing. `explanation_text` is empty because the source places
commentary behind separate `உரை` endpoints and the approved fixture budget was exhausted.
The exact commentary URLs are retained for a later, separately approved inspection.

## Risks Before Expansion

- Other Nannul sections may contain different rule or commentary layouts.
- Examples, exceptions, commentator identity, and cross-rule references are not yet parsed.
- Tolkappiyam and other grammar works may use deeper chapter/commentary hierarchy.
- The parser must not treat metrical rule text as ordinary literary verse.

## Recommendation

`{'PILOT_VERIFIED' if ready else 'REPAIR_REQUIRED'}` for the bounded Nannul fixture set.
Before broader grammar ingestion, inspect structurally different rules and one commentary
endpoint under a new allowlisted phase.
"""


def render_prose_report(result: dict[str, Any]) -> str:
    missing_rows = "\n".join(
        f"| `{field}` | {count} |"
        for field, count in result["prose_missing_fields"].items()
    ) or "| None | 0 |"
    return f"""# Prose Pilot Validation Report

## Summary

- Work: `பாரதியார் கட்டுரைகள்`
- Fixture pages: `3`
- Paragraph sections validated: `{result['record_count']}`
- Status: `{result['status']}`
- Validation errors: `{result['error_count']}`
- Source URL coverage: `{result['source_url_coverage']:.1%}`
- Duplicate record IDs: `{len(result['duplicate_record_ids'])}`
- Non-deterministic IDs: `{result['nondeterministic_ids']}`

## Required Prose Fields

| Missing Field | Count |
| --- | ---: |
{missing_rows}

## Rights Boundary

TamilVU policy requires permission before reproducing site data and excludes third-party
copyright from that permission. Committed fixtures therefore preserve inspected structure,
URLs, and hashes while using a compact rights-safe test passage rather than copied TamilVU
essay text. This validates parser behavior, not permission for prose ingestion.

## Decision

The prose parser is `{'PILOT_VERIFIED' if result['status'] == 'VALID' else 'REPAIR_REQUIRED'}`
for the bounded structural fixture. Full source ingestion remains rights-gated.
"""


def render_prose_readiness(result: dict[str, Any]) -> str:
    ready = result["status"] == "VALID"
    return f"""# Prose Pilot Readiness Report

## Pilot Result

- Fixtures collected: `3`
- Paragraph sections parsed: `{result['record_count']}`
- Records normalized: `{result['record_count']}`
- Validation errors: `{result['error_count']}`
- Source URL coverage: `{result['source_url_coverage']:.1%}`

## Assessment

| Dimension | Result | Evidence |
| --- | --- | --- |
| Parser quality | `{'READY' if ready else 'REPAIR'}` | Explicit prose-section and paragraph boundaries produce deterministic records |
| Normalization quality | `{'READY' if ready else 'REPAIR'}` | Schema v2 preserves work, chapter, section, title, author, and paragraph text |
| Metadata quality | `{'READY' if ready else 'REPAIR'}` | Source URL, link ID, inspection hash, fixture status, and rights status are retained |
| Citation readiness | `{'READY' if ready else 'REPAIR'}` | Work, section title, paragraph index, and exact source page identify each record |
| Literary-analysis contribution | `HIGH` | Adds narrative and explanatory prose for style, theme, author, and cross-genre comparison |

## Comparison With Existing Pilots

Verse records preserve line order and poetic hierarchy; dictionary records center on
headword meaning; grammar records center on numbered rules. Prose records instead preserve
ordered paragraphs within a titled section. The common envelope supports all four shapes
without coercing prose into verse lines or dictionary definitions.

## Limits

- Three inspected pages exposed a wrapper, contents page, and another iframe wrapper.
- The third wrapper referenced a legacy endpoint outside the approved request budget.
- The committed content is structural and rights-safe, not a copy of TamilVU prose.
- Page markers, footnotes, edition details, and multi-chapter transitions remain unproven.
- Large-scale prose ingestion requires written permission and edition-level rights review.

## Recommendation

`{'PILOT_VERIFIED' if ready else 'REPAIR_REQUIRED'}` for parser and schema behavior.
Keep corpus ingestion blocked until TamilVU and any third-party edition permissions are
documented.
"""


def render_validation_report(result: dict[str, Any]) -> str:
    missing_rows = "\n".join(
        f"| `{field}` | {count} |"
        for field, count in result["missing_fields"].items()
    ) or "| None | 0 |"
    return f"""# Multi-Category Pilot Validation Report

## Verified Sample

- Category: `{result['category_id']}`
- Records: `{result['record_count']}`
- Status: `{result['status']}`
- Validation errors: `{result['error_count']}`
- Source URL coverage: `{result['source_url_coverage']:.1%}`
- Duplicate record IDs: `{len(result['duplicate_record_ids'])}`
- Malformed source URLs: `{result['malformed_source_urls']}`
- Category mismatches: `{result['category_mismatches']}`

## Missing Fields

| Field | Count |
| --- | ---: |
{missing_rows}

## Safety Result

The verified sample used an existing local, validated corpus artifact. Network requests,
website discovery, full-category scraping, LLM calls, and mutation of frozen corpora were
all outside this run.
"""


def render_comparison_report(
    plan: dict[str, Any], verified: dict[str, Any] | None = None
) -> str:
    rows = []
    for pilot in plan.get("pilots", []):
        is_verified = verified and pilot["category_id"] == verified["category_id"]
        prior_verified = pilot.get("status") in {
            "local_seed_ready",
            "verified",
            "pilot_verified",
        }
        prior_records = pilot.get("verified_record_count")
        if pilot["category_id"] == "saivam" and prior_records is None:
            prior_records = 10
        content_labels = {
            "dictionaries": "Validated dictionary entry",
            "grammar": "Validated grammar rules",
            "sangam_literature": "Validated Sangam verses",
            "saivam": "Validated verse/commentary seed",
            "twentieth_century_prose": "Validated structural prose paragraphs",
        }
        verified_content = content_labels.get(
            pilot["category_id"], "Validated bounded pilot"
        )
        verified_risk = (
            "Existing validated corpus seed"
            if pilot["category_id"] == "saivam"
            else "Three-page fixture evidence only"
        )
        rows.append(
            "| {category} | `{family}` | {records} | {missing} | {coverage} | {content} | {risk} | {suitability} |".format(
                category=pilot["category_tamil"],
                family=pilot["parser_family"],
                records=(
                    verified["record_count"]
                    if is_verified
                    else prior_records if prior_verified else 0
                ),
                missing=(
                    sum(verified["missing_fields"].values())
                    if is_verified
                    else 0 if prior_verified else "Not tested"
                ),
                coverage=(
                    f"{verified['source_url_coverage']:.1%}"
                    if is_verified
                    else "100.0%" if prior_verified else "Not tested"
                ),
                content=(
                    verified_content
                    if is_verified
                    else "Validated prior pilot" if prior_verified else "Pending inspected sample"
                ),
                risk=(
                    verified_risk
                    if is_verified
                    else "Bounded pilot evidence only" if prior_verified else "HTML hierarchy unknown"
                ),
                suitability=(
                    "Framework verified"
                    if is_verified or prior_verified
                    else "Source inspection required"
                ),
            )
        )
    return """# Multi-Category Pilot Comparison Report

This table compares only bounded pilot readiness. A planned row does not imply that source
content has been fetched or approved.

| Category | Parser Family | Records | Missing Fields | URL Coverage | Content Type | Extraction Risks | Next Expansion |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
{rows}

## Finding

The shared contract works for bounded Saivam, Sangam, dictionary, grammar, and structural
prose evidence. Encyclopedia ingestion still requires source inspection and local fixtures.
Permissioned source-text fixtures remain required before prose corpus expansion.
""".format(rows="\n".join(rows))


def validate_category(
    category_id: str,
    *,
    base_dir: Path = Path("."),
    input_path: Path | None = None,
    report_path: Path | None = None,
) -> dict[str, Any]:
    source = input_path or default_normalized_path(base_dir, category_id)
    records = load_jsonl(source, 10)
    result = validate_records(records, category_id)
    report = report_path or base_dir / (
        "reports/dictionary-pilot-validation-report.md"
        if category_id == "dictionaries"
        else "reports/sangam-pilot-validation-report.md"
        if category_id == "sangam_literature"
        else "reports/grammar-pilot-validation-report.md"
        if category_id == "grammar"
        else "reports/prose-pilot-validation-report.md"
        if category_id == "twentieth_century_prose"
        else "reports/multi-category-pilot-validation-report.md"
    )
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        render_dictionary_report(result)
        if category_id == "dictionaries"
        else render_sangam_report(result)
        if category_id == "sangam_literature"
        else render_grammar_report(result)
        if category_id == "grammar"
        else render_prose_report(result)
        if category_id == "twentieth_century_prose"
        else render_validation_report(result),
        encoding="utf-8",
    )
    plan = load_json(base_dir / DEFAULT_PLAN)
    if category_id in {
        "dictionaries",
        "sangam_literature",
        "grammar",
        "twentieth_century_prose",
    } and result["status"] == "VALID":
        for pilot in plan.get("pilots", []):
            if pilot.get("category_id") == category_id:
                pilot["status"] = "pilot_verified"
                pilot["validation_status"] = "VALID"
                pilot["verified_record_count"] = result["record_count"]
        (base_dir / DEFAULT_PLAN).write_text(
            json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if category_id == "dictionaries":
            readiness = base_dir / "reports/dictionary-pilot-readiness-report.md"
            readiness.write_text(render_dictionary_readiness(result), encoding="utf-8")
        elif category_id == "sangam_literature":
            readiness = base_dir / "reports/sangam-pilot-readiness-report.md"
            readiness.write_text(render_sangam_readiness(result), encoding="utf-8")
        elif category_id == "grammar":
            readiness = base_dir / "reports/grammar-pilot-readiness-report.md"
            readiness.write_text(render_grammar_readiness(result), encoding="utf-8")
        else:
            readiness = base_dir / "reports/prose-pilot-readiness-report.md"
            readiness.write_text(render_prose_readiness(result), encoding="utf-8")
    comparison = base_dir / "reports/multi-category-pilot-comparison-report.md"
    comparison.write_text(render_comparison_report(plan, result), encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate one normalized category pilot.")
    parser.add_argument("--category-id", required=True)
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    parser.add_argument("--input", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = validate_category(
            args.category_id,
            base_dir=args.base_dir,
            input_path=args.input,
            report_path=args.report,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
