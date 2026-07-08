from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

DEFAULT_QA_CSV = Path("data/processed/thevaram_pozhippurai_links/qa_review_pack/paadal_pozhippurai_link_qa_samples.csv")
DEFAULT_V2_LINKS = Path("data/processed/thevaram_pozhippurai_links_v2/paadal_pozhippurai_links.jsonl")
DEFAULT_REPORT = Path("reports/thevaram-pozhppurai-link-phase3-review-summary.md")

DECISIONS = {
    "ACCEPT",
    "WRONG_TARGET",
    "PARTIAL_MATCH",
    "WRONG_RELATION_TYPE",
    "NEEDS_SPLIT",
    "NO_LINK_POSSIBLE",
}
RELATIONSHIPS = {
    "explains_line",
    "explains_phrase",
    "glosses_word",
    "interprets_image",
    "theological_explanation",
    "describes_entity",
}
UPDATED_CONFIDENCE = {"HIGH", "MEDIUM", "LOW", "NO_LINK"}


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def key_for(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("paadal_id", "")),
        str(row.get("source_line_no", "")),
        clean_text(str(row.get("source_text", ""))),
    )


def clean_text(text: str) -> str:
    return " ".join(text.replace("\n", " ").split())


def text_overlap(a: str, b: str) -> float:
    a_chars = {char for char in a if not char.isspace()}
    b_chars = {char for char in b if not char.isspace()}
    if not a_chars or not b_chars:
        return 0.0
    return len(a_chars & b_chars) / len(a_chars | b_chars)


def float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def source_is_short(source: str) -> bool:
    return len(clean_text(source).strip(" ,;.!?-—:")) <= 16


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def infer_relationship(source: str, target: str, current: str) -> str:
    source_clean = clean_text(source)
    target_clean = clean_text(target)
    joined = f"{source_clean} {target_clean}"

    theology_terms = (
        "அருள்",
        "அருளுக",
        "போக்கியருளுக",
        "தேவர் உலகில்",
        "உலகில் உயர்வோடு",
        "வாழ்வர்",
        "வினை",
        "பாவ",
        "முத்தி",
        "நோய்",
        "இடுக்கண்",
        "துன்ப",
        "உய்வர்",
        "வேண்ட",
        "வழிபட",
        "அடியார்",
        "திருவருள்",
        "அறியமுடியாத",
    )
    place_or_deity_terms = (
        "சிவபெருமான்",
        "சிவபிரான்",
        "பெருமான்",
        "நாதன்",
        "அடிகளார்",
        "அடிகள்",
        "உறைபவர்",
        "உறையும்",
        "எழுந்தருளிய",
        "இடம்",
        "திரு",
        "பிரான்",
        "உமையம்மை",
        "தேவி",
    )
    imagery_terms = (
        "பிறை",
        "மதி",
        "விடை",
        "பாம்பு",
        "கொன்றை",
        "சடை",
        "கங்கை",
        "மழு",
        "மான்",
        "சாம்பல்",
        "பொடி",
        "சூடி",
        "ஏறி",
        "தோடு",
        "செவி",
        "புலி",
        "மணி",
        "மலர்",
        "வெண்மை",
    )

    if contains_any(joined, theology_terms):
        return "theological_explanation"
    if contains_any(joined, imagery_terms) and not contains_any(target_clean, ("உறைபவர்", "இடம்", "நாதன்")):
        return "interprets_image"
    if contains_any(target_clean, place_or_deity_terms):
        return "describes_entity"
    if source_is_short(source_clean) and len(target_clean) <= 40:
        return "glosses_word"
    if len(source_clean) >= 60 and len(target_clean) >= 120:
        return "explains_line"
    return current if current in RELATIONSHIPS else "explains_phrase"


def gold_correction(row: dict[str, str]) -> dict[str, str] | None:
    source = clean_text(row.get("source_text", ""))
    target = clean_text(row.get("target_text", ""))

    if "தோடு உடைய செவியன்" in source and "விடை ஏறி" in source and "வெண்மதி" in source:
        return {
            "manual_decision": "NEEDS_SPLIT",
            "correct_relationship_type": "interprets_image",
            "correct_target_text_or_note": (
                "Split into: தோடு உடைய செவியன் ↔ தோடணிந்த திருச்செவியை உடைய; "
                "விடை ஏறி ↔ விடை மீது ஏறி; தூ வெண்மதி சூடி ↔ ஒப்பற்ற தூய வெண்மையான பிறையை முடிமிசைச் சூடி"
            ),
            "v2_rule_suggestion": "For compound iconographic lines, split source phrases before assigning one target span.",
            "reviewer_notes": "One paadal line contains three iconographic descriptions; the single row is too broad for one primary link.",
            "updated_confidence": "MEDIUM",
        }
    if "புக்கிட்டு" in source:
        return {
            "manual_decision": "WRONG_TARGET" if "தேடப் புகுந்து" not in target else "ACCEPT",
            "correct_relationship_type": "explains_phrase",
            "correct_target_text_or_note": "தேடப் புகுந்து",
            "v2_rule_suggestion": "Prefer direct lexical/phrase paraphrase for புக்கிட்டு.",
            "reviewer_notes": "Direct phrase-level explanation from the gold correction examples.",
            "updated_confidence": "HIGH",
        }
    if source.strip(" !,.;") == "புண்ணியனே":
        return {
            "manual_decision": "WRONG_TARGET" if "புண்ணியனே" not in target else "ACCEPT",
            "correct_relationship_type": "glosses_word",
            "correct_target_text_or_note": "புண்ணியனே",
            "v2_rule_suggestion": "Short repeated vocative terms should prefer exact gloss spans over nearby broader commentary.",
            "reviewer_notes": "Direct word-level gloss from the gold correction examples.",
            "updated_confidence": "HIGH",
        }
    if "ஒத்து அமைந்த உம்பர்வானில்" in source:
        return {
            "manual_decision": "ACCEPT" if "தேவர் உலகில் உயர்வோடு ஓங்கி வாழ்வர்" in target else "PARTIAL_MATCH",
            "correct_relationship_type": "theological_explanation",
            "correct_target_text_or_note": "அமைந்த ஒப்புடையவர் என்று கூறத் தேவர் உலகில் உயர்வோடு ஓங்கி வாழ்வர்",
            "v2_rule_suggestion": "Classify devotional result/worldly-spiritual elevation as theological_explanation.",
            "reviewer_notes": "Explains spiritual/religious result of hymn devotion.",
            "updated_confidence": "HIGH",
        }
    if "பரக்கும் மிழலையீர்" in source and "கரக்கை தவிர்மினே" in source:
        return {
            "manual_decision": "NEEDS_SPLIT",
            "correct_relationship_type": "theological_explanation",
            "correct_target_text_or_note": (
                "பரக்கும் மிழலையீர் ↔ எங்கும் பரவிய புகழ் உடைய திருவீழிமிழலையில் உறைபவரே; "
                "கரக்கை தவிர்மினே ↔ எமக்கு அளிக்கும் காசில் உள்ள குறையைப் போக்கியருளுக"
            ),
            "v2_rule_suggestion": "Split vocative deity/place description from prayer/request spans.",
            "reviewer_notes": "Contains a describes_entity sub-link and a theological prayer/request sub-link.",
            "updated_confidence": "HIGH",
        }
    if "கரக்கை தவிர்மினே" in source:
        return {
            "manual_decision": "ACCEPT" if "குறையைப் போக்கியருளுக" in target else "WRONG_TARGET",
            "correct_relationship_type": "theological_explanation",
            "correct_target_text_or_note": "எமக்கு அளிக்கும் காசில் உள்ள குறையைப் போக்கியருளுக",
            "v2_rule_suggestion": "Treat divine request/removal language as theological_explanation.",
            "reviewer_notes": "Prayer/request for divine removal of defect. Secondary: explains_phrase.",
            "updated_confidence": "HIGH",
        }
    if "செந்நெல் அம் கழனிப் பழனத்து" in source:
        return {
            "manual_decision": "ACCEPT" if target == "செந்நெல் விளையும் அழகிய வயல்களை உடைய சோலைகளின்" else "PARTIAL_MATCH",
            "correct_relationship_type": "explains_phrase",
            "correct_target_text_or_note": "செந்நெல் விளையும் அழகிய வயல்களை உடைய சோலைகளின்",
            "v2_rule_suggestion": "Trim landscape phrase explanations to the direct phrase span when possible.",
            "reviewer_notes": "Explains the landscape phrase.",
            "updated_confidence": "HIGH",
        }
    if "கண் புகார்" in source and "பிணி அறியார்" in source and "கற்றாரும் கேட்டாரும்" in source:
        return {
            "manual_decision": "NEEDS_SPLIT",
            "correct_relationship_type": "explains_phrase",
            "correct_target_text_or_note": (
                "கண் புகார்; பிணி அறியார் ↔ இடுக்கண் அடையார். நோய் உறார்; "
                "கற்றாரும் கேட்டாரும் ↔ அவன் புகழைக் கற்றவரும் கேட்டவரும்"
            ),
            "v2_rule_suggestion": "Split result phrases from participant phrases instead of linking the whole line to one target.",
            "reviewer_notes": "The row combines two phrase-level explanations; secondary theological context may apply.",
            "updated_confidence": "MEDIUM",
        }
    if "கற்றாரும் கேட்டாரும்" in source:
        return {
            "manual_decision": "ACCEPT" if "கற்றவரும் கேட்டவரும்" in target else "WRONG_TARGET",
            "correct_relationship_type": "explains_phrase",
            "correct_target_text_or_note": "அவன் புகழைக் கற்றவரும் கேட்டவரும்",
            "v2_rule_suggestion": "Prefer phrase expansion for கற்றாரும் கேட்டாரும்.",
            "reviewer_notes": "Phrase expansion. Secondary theological context if linked to devotional merit/result.",
            "updated_confidence": "HIGH",
        }
    if "விடையேறியோர்" in source or ("விடை" in source and "ஏற" in source and "உமையம்மை" in target):
        return {
            "manual_decision": "ACCEPT" if "விடை" in target else "PARTIAL_MATCH",
            "correct_relationship_type": "describes_entity",
            "correct_target_text_or_note": "உமையம்மையை இடப்பாகத்தே உடையவனாய், விடை மீது ஏறி",
            "v2_rule_suggestion": "Bull-riding plus Parvati-left-half descriptions should primarily describe Siva's iconographic entity form.",
            "reviewer_notes": "Describes Siva through Parvati-on-left-half and bull-riding iconography. Secondary: interprets_image.",
            "updated_confidence": "HIGH",
        }
    return None


def classify_non_gold(
    row: dict[str, str],
    v2_match: dict[str, Any] | None,
    *,
    prefer_v2_target: bool,
) -> dict[str, str]:
    source = clean_text(row.get("source_text", ""))
    target = clean_text(row.get("target_text", ""))
    current_relationship = row.get("relationship_type_v1", "")
    current_confidence = row.get("confidence_v1", "")
    score = float_value(row.get("score_v1"))
    token_score = float_value(row.get("token_score"))
    char_score = float_value(row.get("char_score"))
    entity_score = float_value(row.get("entity_score"))
    containment_score = float_value(row.get("containment_score"))
    diagnostic = row.get("diagnostic_category", "")
    link_status = row.get("link_status_v1", "")

    if link_status == "no_pozhippurai" or current_confidence == "none" or not target:
        return {
            "manual_decision": "NO_LINK_POSSIBLE",
            "correct_relationship_type": "",
            "correct_target_text_or_note": "No pozhppurai target span is available in the current corpus row.",
            "v2_rule_suggestion": "Keep as explicit no-link coverage until commentary text is available.",
            "reviewer_notes": "No target span exists to validate.",
            "updated_confidence": "NO_LINK",
        }

    v2_target = clean_text(str(v2_match.get("target_text", ""))) if v2_match else ""
    v2_confidence = str(v2_match.get("confidence", "")) if v2_match else ""
    v2_score = float_value(v2_match.get("score")) if v2_match else 0.0
    replacement_available = bool(prefer_v2_target and v2_target and v2_target != target)
    relation = infer_relationship(source, v2_target or target, current_relationship)

    if replacement_available:
        overlap = text_overlap(target, v2_target)
        decision = "PARTIAL_MATCH" if overlap >= 0.35 or target in v2_target or v2_target in target else "WRONG_TARGET"
        updated = "MEDIUM" if v2_confidence in {"high", "medium"} or v2_score >= 0.32 else "LOW"
        if decision == "WRONG_TARGET" and updated == "MEDIUM":
            updated = "LOW"
        return {
            "manual_decision": decision,
            "correct_relationship_type": relation,
            "correct_target_text_or_note": v2_target,
            "v2_rule_suggestion": "Use the v2 multi-segment target window when it gives a fuller or better-aligned explanation.",
            "reviewer_notes": (
                "Older target differs from the stronger v2 candidate. "
                f"Target character-overlap={overlap:.2f}; v2 confidence={v2_confidence or 'unknown'}."
            ),
            "updated_confidence": updated,
        }

    if diagnostic in {"missing_pozhippurai"}:
        return {
            "manual_decision": "NO_LINK_POSSIBLE",
            "correct_relationship_type": "",
            "correct_target_text_or_note": "No pozhppurai target span is available.",
            "v2_rule_suggestion": "Keep missing commentary as no-link rather than forcing an alignment.",
            "reviewer_notes": row.get("problem_reason", "Missing target span."),
            "updated_confidence": "NO_LINK",
        }

    if diagnostic in {"ambiguous_multiple_targets"}:
        return {
            "manual_decision": "PARTIAL_MATCH",
            "correct_relationship_type": relation,
            "correct_target_text_or_note": target,
            "v2_rule_suggestion": "Add a human-reviewed ambiguity rule or split the target when several nearby spans score similarly.",
            "reviewer_notes": row.get("problem_reason", "Multiple plausible target spans; keep only after human spot-check."),
            "updated_confidence": "MEDIUM" if score >= 0.28 else "LOW",
        }

    weak_evidence = (
        diagnostic in {"low_lexical_overlap", "no_shared_entity_anchor", "order_only_weak_match", "weak_similarity"}
        or (token_score == 0 and entity_score == 0 and char_score < 0.08 and containment_score == 0)
    )
    if weak_evidence:
        decision = "PARTIAL_MATCH" if score >= 0.24 or char_score >= 0.12 or token_score > 0 else "WRONG_TARGET"
        return {
            "manual_decision": decision,
            "correct_relationship_type": relation,
            "correct_target_text_or_note": target if decision == "PARTIAL_MATCH" else "No stronger target identified automatically; needs human correction.",
            "v2_rule_suggestion": "Do not promote weak order-only matches without lexical, containment, or entity support.",
            "reviewer_notes": row.get("problem_reason", "Weak evidence for this alignment."),
            "updated_confidence": "LOW",
        }

    if relation != current_relationship and current_relationship in RELATIONSHIPS:
        return {
            "manual_decision": "WRONG_RELATION_TYPE",
            "correct_relationship_type": relation,
            "correct_target_text_or_note": target,
            "v2_rule_suggestion": "Update relation type using the Phase 3 relationship definitions.",
            "reviewer_notes": f"Source and target are usable, but relation is better classified as {relation}.",
            "updated_confidence": "MEDIUM" if current_confidence != "high" else "HIGH",
        }

    updated_confidence = "HIGH" if current_confidence == "high" or diagnostic == "strong_link" else "MEDIUM"
    if current_confidence == "low":
        updated_confidence = "LOW"
    return {
        "manual_decision": "ACCEPT",
        "correct_relationship_type": relation,
        "correct_target_text_or_note": target,
        "v2_rule_suggestion": "Keep this alignment; no correction required in this review pass.",
        "reviewer_notes": "Candidate span and relation are acceptable under the Phase 3 rubric.",
        "updated_confidence": updated_confidence,
    }


def review_rows(
    rows: list[dict[str, str]],
    *,
    v2_links: list[dict[str, Any]],
    prefer_v2_target: bool,
) -> list[dict[str, str]]:
    v2_by_key = {key_for(row): row for row in v2_links}
    reviewed: list[dict[str, str]] = []
    for row in rows:
        updated = dict(row)
        v2_match = v2_by_key.get(key_for(row))
        correction = gold_correction(row) or classify_non_gold(
            row,
            v2_match,
            prefer_v2_target=prefer_v2_target,
        )
        updated.update(correction)
        if "updated_confidence" not in updated:
            updated["updated_confidence"] = correction["updated_confidence"]
        reviewed.append(updated)
    return reviewed


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("No rows to write")
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    required_tail = [
        "manual_decision",
        "correct_relationship_type",
        "correct_target_text_or_note",
        "v2_rule_suggestion",
        "reviewer_notes",
        "updated_confidence",
    ]
    fieldnames = [field for field in fieldnames if field not in required_tail] + required_tail
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def validate_rows(rows: list[dict[str, str]]) -> dict[str, Any]:
    errors: list[str] = []
    for index, row in enumerate(rows, start=2):
        if row.get("manual_decision") not in DECISIONS:
            errors.append(f"line {index}: invalid manual_decision {row.get('manual_decision')!r}")
        relationship = row.get("correct_relationship_type", "")
        if relationship and relationship not in RELATIONSHIPS:
            errors.append(f"line {index}: invalid correct_relationship_type {relationship!r}")
        if row.get("updated_confidence") not in UPDATED_CONFIDENCE:
            errors.append(f"line {index}: invalid updated_confidence {row.get('updated_confidence')!r}")
        if not row.get("link_id"):
            errors.append(f"line {index}: missing stable link_id")
    return {
        "status": "VALID" if not errors else "INVALID",
        "errors": errors[:20],
        "error_count": len(errors),
    }


def render_report(
    rows: list[dict[str, str]],
    validation: dict[str, Any],
    output_csv: Path,
    *,
    prefer_v2_target: bool,
) -> str:
    decisions = Counter(row["manual_decision"] for row in rows)
    relationships = Counter(row["correct_relationship_type"] or "unlinked" for row in rows)
    confidence = Counter(row["updated_confidence"] for row in rows)
    thirumurai = Counter(str(row.get("thirumurai_no", "")) for row in rows)
    target_strategy = (
        "Used the stronger v2 multi-segment candidate as the correction target for older v1 QA rows."
        if prefer_v2_target
        else "Reviewed the candidate target already present in the QA CSV without replacing it from another pack."
    )

    def table(counter: Counter[str]) -> str:
        return "\n".join(f"| `{key}` | {counter[key]} |" for key in sorted(counter)) or "| None | 0 |"

    return f"""# Thevaram Phase 3 Paadal-Pozhippurai QA Review Summary

## Scope

- Reviewed CSV: `{output_csv}`
- Rows reviewed: `{len(rows)}`
- Validation status: `{validation["status"]}`
- Validation errors: `{validation["error_count"]}`

This is a machine-assisted Phase 3 correction pass. It keeps every stable `link_id`,
fills the requested review columns, applies the provided gold correction examples, and
flags rows that still need human judgement.

## Manual Decisions

| Decision | Rows |
| --- | ---: |
{table(decisions)}

## Correct Relationship Types

| Relationship | Rows |
| --- | ---: |
{table(relationships)}

## Updated Confidence

| Confidence | Rows |
| --- | ---: |
{table(confidence)}

## Thirumurai Coverage

| Thirumurai | Rows |
| --- | ---: |
{table(thirumurai)}

## How The Review Was Done

- Applied the Phase 3 gold examples exactly where their source phrases appeared.
- {target_strategy}
- Classified weak links by evidence type: missing pozhppurai, ambiguous target, low lexical overlap, no shared entity anchor, or order-only matching.
- Preserved the original source span, target span evidence, and stable `link_id`.

## What Still Needs Human Review

- `WRONG_TARGET`: replace with the correct visible pozhppurai span where possible.
- `PARTIAL_MATCH`: decide whether to trim, expand, or accept the span.
- `NEEDS_SPLIT`: split one broad row into multiple source-target pairs before treating it as gold.
- `LOW` confidence rows: use for model guidance only after spot-checking.
"""


def review_file(
    *,
    qa_csv: Path,
    v2_links_path: Path,
    output_csv: Path,
    report_path: Path,
    prefer_v2_target: bool,
) -> dict[str, Any]:
    rows = read_csv(qa_csv)
    v2_links = read_jsonl(v2_links_path)
    reviewed = review_rows(rows, v2_links=v2_links, prefer_v2_target=prefer_v2_target)
    validation = validate_rows(reviewed)
    write_csv(output_csv, reviewed)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        render_report(reviewed, validation, output_csv, prefer_v2_target=prefer_v2_target),
        encoding="utf-8",
    )
    return {
        "input_csv": str(qa_csv),
        "output_csv": str(output_csv),
        "report": str(report_path),
        "rows": len(reviewed),
        "manual_decisions": dict(sorted(Counter(row["manual_decision"] for row in reviewed).items())),
        "updated_confidence": dict(sorted(Counter(row["updated_confidence"] for row in reviewed).items())),
        "validation": validation,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fill Phase 3 review columns for a Thevaram paadal-pozhppurai QA CSV.")
    parser.add_argument("--qa-csv", type=Path, default=DEFAULT_QA_CSV)
    parser.add_argument("--v2-links", type=Path, default=DEFAULT_V2_LINKS)
    parser.add_argument("--output-csv", type=Path)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--prefer-v2-target", action="store_true")
    args = parser.parse_args(argv)

    output_csv = args.output_csv or args.qa_csv
    summary = review_file(
        qa_csv=args.qa_csv,
        v2_links_path=args.v2_links,
        output_csv=output_csv,
        report_path=args.report,
        prefer_v2_target=args.prefer_v2_target,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if summary["validation"]["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
