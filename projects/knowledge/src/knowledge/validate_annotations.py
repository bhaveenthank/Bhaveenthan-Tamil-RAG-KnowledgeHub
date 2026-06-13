from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_ANNOTATION_DIR = Path("data/knowledge/annotations")
DEFAULT_OUTPUT = DEFAULT_ANNOTATION_DIR / "annotation_validation.json"
DEFAULT_REPORT = Path("reports/annotation-fixture-report.md")

ANNOTATION_FILES = [
    "entities_gold.json",
    "deities_gold.json",
    "authors_gold.json",
    "motifs_gold.json",
    "epithets_gold.json",
    "similes_gold.json",
    "metaphors_gold.json",
    "relationships_gold.json",
]

SPAN_TYPES = {
    "entity",
    "deity",
    "author",
    "place",
    "work",
    "motif",
    "theme",
    "epithet",
    "simile",
    "metaphor",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def validate_span(record: dict[str, Any], annotation: dict[str, Any]) -> list[str]:
    errors = []
    text = record.get("text", "")
    start = annotation.get("start")
    end = annotation.get("end")
    ann_text = annotation.get("text")
    if not isinstance(start, int) or not isinstance(end, int):
        return ["span annotation must include integer start and end"]
    if start < 0 or end <= start or end > len(text):
        errors.append("annotation span is out of range")
    elif text[start:end] != ann_text:
        errors.append("annotation text does not match record span")
    for field in ("annotation_id", "type", "label", "text", "review_status"):
        if not annotation.get(field):
            errors.append(f"missing annotation field: {field}")
    return errors


def validate_relationship(annotation: dict[str, Any], annotation_ids: set[str]) -> list[str]:
    errors = []
    for field in ("annotation_id", "type", "source", "target", "relationship_type", "review_status"):
        if not annotation.get(field):
            errors.append(f"missing relationship field: {field}")
    if annotation.get("source") and annotation["source"] not in annotation_ids:
        errors.append("relationship source does not reference an annotation in the same record")
    if annotation.get("target") and annotation["target"] not in annotation_ids:
        errors.append("relationship target does not reference an annotation in the same record")
    return errors


def validate_annotation_file(path: Path) -> dict[str, Any]:
    errors: list[str] = []
    payload = load_json(path)
    records = payload.get("records", []) if isinstance(payload.get("records"), list) else []
    type_counts: dict[str, int] = {}
    annotation_count = 0
    if not path.exists():
        errors.append("annotation file is missing")
    if payload.get("schema_version") != "annotation-gold-v1":
        errors.append("schema_version must be annotation-gold-v1")
    if payload.get("status") != "manual_gold_seed":
        errors.append("status must be manual_gold_seed")
    if payload.get("automatic_extraction_performed") is not False:
        errors.append("automatic_extraction_performed must be false")
    if not records:
        errors.append("records must not be empty")
    record_ids = set()
    for record in records:
        record_id = record.get("record_id")
        if not record_id:
            errors.append("record_id is required")
        elif record_id in record_ids:
            errors.append(f"duplicate record_id: {record_id}")
        record_ids.add(record_id)
        if not record.get("text"):
            errors.append(f"{record_id}: text is required")
        if not isinstance(record.get("annotations"), list) or not record["annotations"]:
            errors.append(f"{record_id}: annotations must be a non-empty list")
            continue
        annotation_ids = {
            annotation.get("annotation_id")
            for annotation in record["annotations"]
            if annotation.get("annotation_id")
        }
        if len(annotation_ids) != len(record["annotations"]):
            errors.append(f"{record_id}: duplicate or missing annotation_id")
        for annotation in record["annotations"]:
            annotation_count += 1
            ann_type = annotation.get("type")
            type_counts[ann_type] = type_counts.get(ann_type, 0) + 1
            if ann_type == "relationship":
                errors.extend(
                    f"{record_id}:{annotation.get('annotation_id')}: {error}"
                    for error in validate_relationship(annotation, annotation_ids)
                )
            elif ann_type in SPAN_TYPES:
                errors.extend(
                    f"{record_id}:{annotation.get('annotation_id')}: {error}"
                    for error in validate_span(record, annotation)
                )
            else:
                errors.append(f"{record_id}:{annotation.get('annotation_id')}: invalid type {ann_type}")
    return {
        "file": str(path),
        "annotation_set": payload.get("annotation_set", path.stem),
        "record_count": len(records),
        "annotation_count": annotation_count,
        "type_counts": type_counts,
        "errors": errors,
    }


def validate_annotations(annotation_dir: Path = DEFAULT_ANNOTATION_DIR) -> dict[str, Any]:
    results = [
        validate_annotation_file(annotation_dir / file_name)
        for file_name in ANNOTATION_FILES
    ]
    errors = [error for result in results for error in result["errors"]]
    type_counts: dict[str, int] = {}
    for result in results:
        for ann_type, count in result["type_counts"].items():
            type_counts[ann_type] = type_counts.get(ann_type, 0) + count
    return {
        "schema_version": "annotation-validation-v1",
        "annotation_file_count": len(results),
        "record_count": sum(result["record_count"] for result in results),
        "annotation_count": sum(result["annotation_count"] for result in results),
        "type_counts": dict(sorted(type_counts.items())),
        "files": results,
        "valid": not errors,
        "errors": errors,
        "automatic_extraction_performed": False,
        "scraping_performed": False,
        "llm_calls": 0,
    }


def render_report(validation: dict[str, Any]) -> str:
    file_rows = "\n".join(
        f"| `{Path(result['file']).name}` | {result['record_count']} | "
        f"{result['annotation_count']} | {len(result['errors'])} |"
        for result in validation["files"]
    )
    type_rows = "\n".join(
        f"| `{ann_type}` | {count} |"
        for ann_type, count in validation["type_counts"].items()
    )
    return f"""# Annotation Fixture Report

## Summary

- Annotation files: `{validation['annotation_file_count']}`
- Records: `{validation['record_count']}`
- Annotations: `{validation['annotation_count']}`
- Validation: `{'VALID' if validation['valid'] else 'INVALID'}`
- Automatic extraction performed: `{str(validation['automatic_extraction_performed']).lower()}`
- Scraping performed: `{str(validation['scraping_performed']).lower()}`
- LLM calls: `{validation['llm_calls']}`

## Counts By File

| File | Records | Annotations | Errors |
| --- | ---: | ---: | ---: |
{file_rows}

## Counts By Annotation Type

| Type | Count |
| --- | ---: |
{type_rows}

## Coverage

The fixtures cover entity, deity, author, motif, epithet, simile, metaphor, and
relationship examples. Place and work appear inside entity and relationship fixtures.

## Limitations

- The fixture set is intentionally small.
- It is manually curated and not a corpus-wide annotation release.
- It has no inter-annotator agreement measurement yet.
- Metaphor and relationship examples are seed examples for schema testing.

## Future Expansion Recommendations

Add positive, negative, and ambiguous examples for each extraction target before building
automatic extractors.
"""


def write_outputs(
    validation: dict[str, Any],
    *,
    output_path: Path = DEFAULT_OUTPUT,
    report_path: Path = DEFAULT_REPORT,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(validation), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate manual gold annotation fixtures.")
    parser.add_argument("--annotation-dir", type=Path, default=DEFAULT_ANNOTATION_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    validation = validate_annotations(args.annotation_dir)
    write_outputs(validation, output_path=args.output, report_path=args.report)
    print(json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if validation["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
