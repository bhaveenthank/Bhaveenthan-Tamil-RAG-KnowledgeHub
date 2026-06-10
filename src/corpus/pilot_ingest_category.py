from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from parsers.base_parser import ParseContext, parser_for_family

DEFAULT_PLAN = Path("data/processed/corpus_registry/pilot_category_plan.json")
DEFAULT_REGISTRY = Path("data/processed/corpus_registry/website_category_registry.json")
MAX_PILOT_BOOKS = 1
MAX_PILOT_RECORDS = 10


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
        if len(records) >= limit:
            break
    return records


def load_fixture_sources(base_dir: Path, metadata_path: Path, limit: int) -> list[dict[str, Any]]:
    metadata = load_json(metadata_path)
    fixtures = metadata.get("fixtures", [])
    if len(fixtures) > 3:
        raise ValueError("pilot fixture manifest exceeds the three-page limit")
    sources: list[dict[str, Any]] = []
    for fixture in fixtures[:limit]:
        fixture_path = base_dir / fixture["fixture_path"]
        sources.append(
            {
                **fixture,
                "source_work": metadata.get("source_work", ""),
                "html_content": fixture_path.read_text(encoding="utf-8"),
            }
        )
    return sources


def jsonl_text(records: Iterable[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        for record in records
    )


def write_once(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") == content:
            return "reused"
        raise FileExistsError(f"refusing to overwrite existing pilot artifact: {path}")
    path.write_text(content, encoding="utf-8")
    return "created"


def find_pilot(plan: dict[str, Any], category_id: str) -> dict[str, Any]:
    for pilot in plan.get("pilots", []):
        if pilot.get("category_id") == category_id:
            return pilot
    raise ValueError(f"category is not in the controlled pilot plan: {category_id}")


def validate_plan_entry(
    pilot: dict[str, Any],
    categories: dict[str, dict[str, Any]],
    max_books: int,
    max_records: int,
) -> None:
    category_id = pilot["category_id"]
    if category_id not in categories:
        raise ValueError(f"pilot category is absent from website registry: {category_id}")
    if pilot["parser_family"] != categories[category_id]["parser_family"]:
        raise ValueError(f"parser family mismatch for category: {category_id}")
    if not 1 <= max_books <= min(MAX_PILOT_BOOKS, int(pilot["max_books"])):
        raise ValueError("controlled pilot permits exactly one book")
    if not 1 <= max_records <= min(MAX_PILOT_RECORDS, int(pilot["max_records"])):
        raise ValueError("controlled pilot permits between 1 and 10 records")


def dry_run_summary(pilot: dict[str, Any], max_books: int, max_records: int) -> dict[str, Any]:
    return {
        "action": "dry_run",
        "category_id": pilot["category_id"],
        "parser_family": pilot["parser_family"],
        "source_mode": pilot.get("source_mode", "pending_inspection"),
        "max_books": max_books,
        "max_records": max_records,
        "network_requests": 0,
        "writes": 0,
        "ready": bool(pilot.get("source_path")),
    }


def ingest_category(
    category_id: str,
    *,
    max_books: int = 1,
    max_records: int = 10,
    dry_run: bool = False,
    base_dir: Path = Path("."),
    plan_path: Path = DEFAULT_PLAN,
    registry_path: Path = DEFAULT_REGISTRY,
) -> dict[str, Any]:
    plan = load_json(base_dir / plan_path)
    registry = load_json(base_dir / registry_path)
    categories = {
        category["category_id"]: category for category in registry.get("categories", [])
    }
    pilot = find_pilot(plan, category_id)
    validate_plan_entry(pilot, categories, max_books, max_records)
    if dry_run:
        return dry_run_summary(pilot, max_books, max_records)

    source_path_value = pilot.get("source_path")
    if not source_path_value:
        raise ValueError(
            f"{category_id} has no inspected local source; run --dry-run until a source is approved"
        )
    source_path = base_dir / source_path_value
    if not source_path.is_file():
        raise FileNotFoundError(f"approved local source is missing: {source_path}")

    if pilot.get("source_mode") == "fixture_html":
        source_records = load_fixture_sources(base_dir, source_path, max_records)
    else:
        source_records = load_jsonl(source_path, max_records)
    if not source_records:
        raise ValueError(f"approved local source contains no records: {source_path}")

    context = ParseContext(
        category_id=category_id,
        category_tamil=pilot["category_tamil"],
        parser_family=pilot["parser_family"],
        book_id=pilot.get("book_id", f"{category_id}_pilot_book"),
        work_id=pilot.get("work_id", f"{category_id}_pilot_work"),
        pilot_id=pilot["pilot_id"],
    )
    parser = parser_for_family(context.parser_family)
    parsed_records = [
        record
        for source in source_records
        for record in parser.parse(source, context)
    ][:max_records]

    raw_dir = base_dir / "data/raw/pilot_categories" / category_id
    processed_dir = base_dir / "data/processed/pilot_categories" / category_id
    raw_status = write_once(raw_dir / "source_records.jsonl", jsonl_text(source_records))
    output_status = write_once(processed_dir / "records.jsonl", jsonl_text(parsed_records))
    manifest = {
        "pilot_id": pilot["pilot_id"],
        "category_id": category_id,
        "category_tamil": pilot["category_tamil"],
        "parser_family": context.parser_family,
        "source_mode": pilot["source_mode"],
        "source_path": str(source_path_value),
        "book_count": 1,
        "fixture_page_count": len(source_records),
        "record_count": len(parsed_records),
        "max_books": max_books,
        "max_records": max_records,
        "network_requests": 0,
        "raw_output": str(raw_dir / "source_records.jsonl"),
        "processed_output": str(processed_dir / "records.jsonl"),
    }
    manifest_status = write_once(
        processed_dir / "ingestion_manifest.json",
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    return {
        **manifest,
        "write_status": {
            "raw": raw_status,
            "processed": output_status,
            "manifest": manifest_status,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run one bounded, local-source multi-category pilot ingestion."
    )
    parser.add_argument("--category-id", required=True)
    parser.add_argument("--max-books", type=int, default=1)
    parser.add_argument("--max-records", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        summary = ingest_category(
            args.category_id,
            max_books=args.max_books,
            max_records=args.max_records,
            dry_run=args.dry_run,
            base_dir=args.base_dir,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
