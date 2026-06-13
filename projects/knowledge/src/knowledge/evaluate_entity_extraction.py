from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from knowledge.entity_extractor import build_entity_terms, extract_entities

DEFAULT_GOLD_PATH = Path("data/knowledge/annotations/entities_gold.json")
DEFAULT_OUTPUT = Path("data/processed/eval/entity_extraction_results.json")
DEFAULT_REPORT = Path("reports/entity-extraction-report.md")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def expected_entities(gold: dict[str, Any]) -> list[dict[str, Any]]:
    expected = []
    for record in gold.get("records", []):
        for annotation in record.get("annotations", []):
            if annotation.get("type") == "entity":
                expected.append(
                    {
                        "record_id": record["record_id"],
                        "label": annotation["label"],
                        "text": annotation["text"],
                        "start": annotation["start"],
                        "end": annotation["end"],
                    }
                )
    return expected


def score_key(item: dict[str, Any]) -> tuple[str, str, str, int, int]:
    return (
        item["record_id"],
        item["label"],
        item["text"],
        int(item["start"]),
        int(item["end"]),
    )


def evaluate_entity_extraction(gold_path: Path = DEFAULT_GOLD_PATH) -> dict[str, Any]:
    gold = load_json(gold_path)
    terms = build_entity_terms()
    extracted_records = []
    flat_extracted = []
    for record in gold.get("records", []):
        extracted = extract_entities(record["text"], terms)
        with_record_id = [
            {
                "record_id": record["record_id"],
                "label": item["label"],
                "text": item["text"],
                "start": item["start"],
                "end": item["end"],
                "canonical_id": item["canonical_id"],
                "canonical_name": item["canonical_name"],
                "match_source": item["match_source"],
            }
            for item in extracted
        ]
        flat_extracted.extend(with_record_id)
        extracted_records.append(
            {
                "record_id": record["record_id"],
                "text": record["text"],
                "expected": [
                    {
                        "label": annotation["label"],
                        "text": annotation["text"],
                        "start": annotation["start"],
                        "end": annotation["end"],
                    }
                    for annotation in record.get("annotations", [])
                    if annotation.get("type") == "entity"
                ],
                "extracted": with_record_id,
            }
        )
    expected = expected_entities(gold)
    expected_set = {score_key(item) for item in expected}
    extracted_set = {score_key(item) for item in flat_extracted}
    true_positive_keys = expected_set & extracted_set
    false_positive_keys = extracted_set - expected_set
    false_negative_keys = expected_set - extracted_set
    precision = (
        len(true_positive_keys) / len(extracted_set)
        if extracted_set
        else 0.0
    )
    recall = (
        len(true_positive_keys) / len(expected_set)
        if expected_set
        else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    errors = {
        "false_positives": [
            item for item in flat_extracted if score_key(item) in false_positive_keys
        ],
        "false_negatives": [
            item for item in expected if score_key(item) in false_negative_keys
        ],
    }
    return {
        "evaluation_version": "entity-extraction-pilot-v1",
        "gold_path": str(gold_path),
        "supported_entity_types": ["deity", "author", "place", "work"],
        "expected_count": len(expected_set),
        "extracted_count": len(extracted_set),
        "true_positive_count": len(true_positive_keys),
        "false_positive_count": len(false_positive_keys),
        "false_negative_count": len(false_negative_keys),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "exact_match": round(recall, 4),
        "records": extracted_records,
        "expected_entities": expected,
        "extracted_entities": flat_extracted,
        "errors": errors,
        "entity_extraction_pilot_performed": True,
        "corpus_wide_extraction_performed": False,
        "scraping_performed": False,
        "llm_calls": 0,
    }


def render_report(results: dict[str, Any]) -> str:
    false_negative_rows = "\n".join(
        f"| `{item['record_id']}` | `{item['label']}` | {item['text']} | "
        f"{item['start']}-{item['end']} |"
        for item in results["errors"]["false_negatives"]
    ) or "| none | none | none | none |"
    false_positive_rows = "\n".join(
        f"| `{item['record_id']}` | `{item['label']}` | {item['text']} | "
        f"{item['start']}-{item['end']} |"
        for item in results["errors"]["false_positives"]
    ) or "| none | none | none | none |"
    return f"""# Entity Extraction Report

## Summary

- Supported entity types: `{', '.join(results['supported_entity_types'])}`
- Expected entities: `{results['expected_count']}`
- Extracted entities: `{results['extracted_count']}`
- True positives: `{results['true_positive_count']}`
- False positives: `{results['false_positive_count']}`
- False negatives: `{results['false_negative_count']}`
- Precision: `{results['precision']:.4f}`
- Recall: `{results['recall']:.4f}`
- F1: `{results['f1']:.4f}`
- Exact match: `{results['exact_match']:.4f}`
- Entity extraction pilot performed: `{str(results['entity_extraction_pilot_performed']).lower()}`
- Corpus-wide extraction performed: `{str(results['corpus_wide_extraction_performed']).lower()}`
- Scraping performed: `{str(results['scraping_performed']).lower()}`
- LLM calls: `{results['llm_calls']}`

## Error Analysis

### False Negatives

| Record | Label | Text | Span |
| --- | --- | --- | --- |
{false_negative_rows}

### False Positives

| Record | Label | Text | Span |
| --- | --- | --- | --- |
{false_positive_rows}

## Future Improvements

- Add missing deity authority seeds after human review.
- Add more negative and ambiguous examples before broad extraction.
- Add spelling and orthographic variant handling only after fixture coverage improves.
"""


def write_outputs(
    results: dict[str, Any],
    *,
    output_path: Path = DEFAULT_OUTPUT,
    report_path: Path = DEFAULT_REPORT,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(results), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate deterministic entity extraction.")
    parser.add_argument("--gold", type=Path, default=DEFAULT_GOLD_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args(argv)
    results = evaluate_entity_extraction(args.gold)
    write_outputs(results, output_path=args.output, report_path=args.report)
    print(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
