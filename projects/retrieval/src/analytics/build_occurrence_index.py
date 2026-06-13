from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from retrieval.query_expander import QueryExpander, ordered_unique

DEFAULT_INPUT_DIRS = (
    Path("data/processed/normalized"),
    Path("data/processed/normalized_categories"),
)
DEFAULT_OUTPUT = Path("data/processed/analytics/occurrence_index.jsonl")
DEFAULT_MANIFEST = Path("data/processed/analytics/occurrence_index_manifest.json")
DEFAULT_REPORT = Path("reports/occurrence-search-report.md")
SEARCH_FIELDS = (
    "verse_text",
    "commentary_text",
    "pozhppurai",
    "kurippurai",
    "content_text",
    "definition",
    "rule_text",
    "explanation_text",
    "title",
    "author",
)


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(unicodedata.normalize("NFC", str(value)).split())


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def source_paths(input_dirs: tuple[Path, ...] = DEFAULT_INPUT_DIRS) -> list[Path]:
    paths: list[Path] = []
    for directory in input_dirs:
        if directory.exists():
            paths.extend(sorted(directory.glob("*.jsonl")))
    return paths


def infer_corpus_id(path: Path, record: dict[str, Any]) -> str:
    if record.get("corpus_id"):
        return str(record["corpus_id"])
    if path.parent.name == "normalized_categories":
        return str(record.get("category_id") or path.stem.replace("_normalized", ""))
    return path.stem.replace("_normalized", "")


def work_label(record: dict[str, Any]) -> str:
    metadata = record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}
    source_metadata = record.get("source_metadata", {}) if isinstance(record.get("source_metadata"), dict) else {}
    return str(
        record.get("work_id")
        or metadata.get("work")
        or source_metadata.get("source_work")
        or record.get("collection")
        or record.get("canonical_title")
        or record.get("title")
        or ""
    )


def source_label(record: dict[str, Any]) -> str:
    metadata = record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}
    source_metadata = record.get("source_metadata", {}) if isinstance(record.get("source_metadata"), dict) else {}
    return str(
        metadata.get("source")
        or source_metadata.get("source")
        or source_metadata.get("source_work")
        or "TamilVU"
    )


def build_index_rows(paths: list[Path]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    record_ids: set[str] = set()
    source_files: list[dict[str, Any]] = []

    for path in paths:
        records = load_jsonl(path)
        source_files.append({"path": str(path), "record_count": len(records)})
        for record in records:
            record_id = str(record.get("record_id", ""))
            if not record_id:
                continue
            record_ids.add(record_id)
            corpus_id = infer_corpus_id(path, record)
            category_id = str(record.get("category_id") or corpus_id)
            record_type = str(record.get("record_type") or record.get("schema_version") or "corpus_record")
            source_metadata = record.get("source_metadata", {}) if isinstance(record.get("source_metadata"), dict) else {}
            metadata = record.get("metadata", {}) if isinstance(record.get("metadata"), dict) else {}
            source_url = str(record.get("source_url") or record.get("hymn_url") or "")
            commentary_url = str(record.get("commentary_url") or "")
            if not commentary_url:
                commentary_url = str(metadata.get("commentary_url") or "")
            for field_name in SEARCH_FIELDS:
                text = normalize_text(record.get(field_name, ""))
                if not text:
                    continue
                index_id = hashlib.sha256(f"{record_id}:{field_name}".encode("utf-8")).hexdigest()[:20]
                rows.append(
                    {
                        "index_id": f"occ_{index_id}",
                        "corpus_id": corpus_id,
                        "category_id": category_id,
                        "record_id": record_id,
                        "record_type": record_type,
                        "field_name": field_name,
                        "text": text,
                        "text_length": len(text),
                        "author": str(record.get("author") or ""),
                        "work": work_label(record),
                        "source": source_label(record),
                        "title": str(record.get("title") or record.get("canonical_title") or ""),
                        "source_url": source_url,
                        "commentary_url": commentary_url,
                        "source_metadata": {
                            "source_file": str(path),
                            "source_record_id": str(
                                source_metadata.get("source_record_id")
                                or metadata.get("source_record_id")
                                or ""
                            ),
                            "citation_text": str(
                                source_metadata.get("citation_text")
                                or metadata.get("citation_text")
                                or ""
                            ),
                        },
                    }
                )

    rows.sort(key=lambda row: (row["corpus_id"], row["record_id"], SEARCH_FIELDS.index(row["field_name"])))
    field_counts = Counter(row["field_name"] for row in rows)
    corpus_counts = Counter(row["corpus_id"] for row in rows)
    manifest = {
        "manifest_version": "occurrence-index-v1",
        "source": "local_normalized_corpora",
        "source_files": source_files,
        "indexed_records": len(record_ids),
        "indexed_field_entries": len(rows),
        "indexed_fields": sorted(field_counts),
        "field_entry_counts": dict(sorted(field_counts.items())),
        "corpus_entry_counts": dict(sorted(corpus_counts.items())),
        "scraping_performed": False,
        "llm_calls": 0,
    }
    manifest["example_searches"] = example_search_counts(rows)
    return rows, manifest


def example_search_counts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    expander = QueryExpander()
    examples = []
    for term in ("சந்திரன்", "சிவன்", "அப்பர்", "உவமை"):
        expansion = expander.expand(term)
        terms = ordered_unique(expansion["expanded_terms"] or [term])
        count = 0
        for row in rows:
            text = row["text"]
            for matched_term in terms:
                start = text.find(matched_term)
                while start != -1:
                    count += 1
                    start = text.find(matched_term, start + 1)
        examples.append(
            {
                "term": term,
                "expand_query": True,
                "matched_terms": terms,
                "occurrence_count": count,
            }
        )
    return examples


def write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def render_report(manifest: dict[str, Any]) -> str:
    field_rows = "\n".join(
        f"| `{field}` | {count} |" for field, count in manifest["field_entry_counts"].items()
    )
    corpus_rows = "\n".join(
        f"| `{corpus}` | {count} |" for corpus, count in manifest["corpus_entry_counts"].items()
    )
    example_rows = "\n".join(
        f"| `{item['term']}` | `{', '.join(item['matched_terms'])}` | {item['occurrence_count']} |"
        for item in manifest.get("example_searches", [])
    )
    return f"""# Occurrence Search Report

## Summary

- Indexed records: `{manifest['indexed_records']}`
- Indexed field entries: `{manifest['indexed_field_entries']}`
- Indexed fields: `{', '.join(manifest['indexed_fields'])}`
- Scraping performed: `{str(manifest['scraping_performed']).lower()}`
- LLM calls: `{manifest['llm_calls']}`

## Corpus Coverage

| Corpus | Indexed field entries |
| --- | ---: |
{corpus_rows}

## Field Coverage

| Field | Indexed entries |
| --- | ---: |
{field_rows}

## Example Searches

```bash
python3 src/analytics/search_occurrences.py --term "சந்திரன்"
python3 src/analytics/search_occurrences.py --term "சந்திரன்" --expand-query
```

Expanded search uses the curated query expander. For `சந்திரன்`, it searches the canonical
term plus reviewed synonym and variant forms from `data/knowledge/synonyms.json`.

| Query | Expanded terms | Occurrences |
| --- | --- | ---: |
{example_rows}

## Limitations

- Matching is literal substring matching; inflection, sandhi, and morphology are not yet handled.
- This layer returns evidence occurrences only. It does not aggregate counts into literary claims.
- Source text quality is limited to the currently normalized local corpora and pilot fixtures.
- Motif and literary-device terms are search cues, not automatic annotations.

## Recommendation

Use this occurrence index as the foundation for Phase 25 aggregation and statistics.
Aggregation should consume these evidence rows rather than re-reading source corpora.
"""


def build_occurrence_index(
    output: Path = DEFAULT_OUTPUT,
    manifest_path: Path = DEFAULT_MANIFEST,
    report_path: Path = DEFAULT_REPORT,
    input_dirs: tuple[Path, ...] = DEFAULT_INPUT_DIRS,
) -> dict[str, Any]:
    rows, manifest = build_index_rows(source_paths(input_dirs))
    write_jsonl(rows, output)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(manifest), encoding="utf-8")
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a local corpus-wide occurrence evidence index")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_occurrence_index(args.output, args.manifest, args.report)
    print(
        "Occurrence index built: "
        f"records={manifest['indexed_records']} fields={manifest['indexed_field_entries']} "
        f"output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
