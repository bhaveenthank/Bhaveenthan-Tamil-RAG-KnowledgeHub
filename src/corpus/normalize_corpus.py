from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

DEFAULT_INPUT = Path("data/processed/enriched/irandaam_thirumurai_enriched.jsonl")
DEFAULT_OUTPUT = Path("data/processed/normalized/thirumurai_02_normalized.jsonl")
DEFAULT_REGISTRY = Path("data/processed/corpus_registry/thirumurai_registry.json")
DEFAULT_MANIFEST = Path("data/processed/normalized/multi_corpus_manifest.json")

SCHEMA_VERSION = "unified-thirumurai-v1"
CORPUS_ID = "thirumurai_02"
CORPUS_CONFIGS = {
    "thirumurai_02": {
        "number": 2,
        "title": "Irandaam Thirumurai",
        "input": DEFAULT_INPUT,
        "output": DEFAULT_OUTPUT,
        "author": "Tirugnanasambandar",
        "nayanmar": "Tirugnanasambandar",
    },
    "thirumurai_04": {
        "number": 4,
        "title": "Naangaam Thirumurai",
        "input": Path("data/processed/pilot/thirumurai_04.jsonl"),
        "output": Path("data/processed/normalized/thirumurai_04_normalized.jsonl"),
        "author": "Tirunavukkarasar",
        "nayanmar": "Tirunavukkarasar",
    },
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(
        json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
        for record in records
    )
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def normalized_author(author: str) -> tuple[str, str]:
    aliases = {
        "Sambandar": ("Tirugnanasambandar", "Tirugnanasambandar"),
        "திருஞானசம்பந்தர்": ("Tirugnanasambandar", "Tirugnanasambandar"),
    }
    return aliases.get(author, (author, author))


def normalize_record(source: dict[str, Any], corpus_id: str = CORPUS_ID) -> dict[str, Any]:
    config = CORPUS_CONFIGS[corpus_id]
    author, nayanmar = normalized_author(str(source.get("author", "")).strip())
    if corpus_id == "thirumurai_04":
        author, nayanmar = config["author"], config["nayanmar"]
    hymn_id = str(source.get("hymn_id", "")).strip()
    song_no = str(source.get("song_no", "")).strip()
    record_id = str(
        source.get("record_id")
        or source.get("canonical_id")
        or f"thevaram_{config['number']:02d}_{hymn_id}_{song_no}"
    ).strip()
    verse_index = source.get("verse_index_in_hymn", "")
    citation = source.get("citation", {})
    canonical_id = str(
        source.get("canonical_id")
        or f"tvu_thevaram_{corpus_id}_{hymn_id}_{song_no}"
    )
    source_record_id = str(
        source.get("source_record_id") or f"tvu:{corpus_id}:{hymn_id}:{song_no}"
    )
    verse_id = str(
        source.get("verse_id") or f"thevaram_{config['number']:02d}_{hymn_id}_{song_no}_verse"
    )
    citation_text = str(
        source.get("citation_text")
        or f"{author}, {config['title']}, {source.get('hymn_title', '')}, பாடல் {song_no}, TamilVU."
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "record_id": record_id,
        "corpus_id": corpus_id,
        "thirumurai_no": config["number"],
        "collection": "Thirumurai",
        "canonical_title": config["title"],
        "author": author,
        "nayanmar": nayanmar,
        "hymn_id": hymn_id,
        "pathigam_id": hymn_id,
        "song_no": song_no,
        "verse_no": str(verse_index),
        "title": str(source.get("hymn_title", "")).strip(),
        "place": str(source.get("hymn_location", "")).strip(),
        "deity": "Siva",
        "verse_text": str(
            source.get("verse_text_normalized") or source.get("verse_text") or ""
        ).strip(),
        "pozhppurai": str(
            source.get("pozhppurai_normalized") or source.get("pozhppurai") or ""
        ).strip(),
        "kurippurai": str(
            source.get("kurippurai_normalized") or source.get("kurippurai") or ""
        ).strip(),
        "source_url": str(
            source.get("hymn_url") or citation.get("hymn_url") or ""
        ).strip(),
        "commentary_url": str(
            source.get("commentary_url") or citation.get("commentary_url") or ""
        ).strip(),
        "metadata": {
            "source": str(source.get("source", "TamilVU")),
            "source_site": str(source.get("source_site", "https://www.tamilvu.org")),
            "source_corpus_version": str(source.get("source_corpus_version", "")),
            "enriched_corpus_version": str(source.get("enriched_corpus_version", "")),
            "source_record_id": source_record_id,
            "canonical_id": canonical_id,
            "verse_id": verse_id,
            "original_author": str(source.get("author", "")),
            "original_collection": str(source.get("collection", "")),
            "work": str(source.get("work", "")),
            "pann": str(source.get("pann", "")),
            "hymn_note": str(source.get("hymn_note", "")),
            "citation_text": citation_text,
            "commentary_available": bool(source.get("commentary_available", False)),
            "extraction_status": str(
                source.get("extraction_metadata", {}).get("extraction_status", "")
            ),
        },
    }


def build_manifest(
    registry: dict[str, Any],
    records: list[dict[str, Any]],
    missing_fields_summary: dict[str, int] | None = None,
    existing_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    corpora = registry.get("corpora", [])
    available = [entry["corpus_id"] for entry in corpora if entry["status"] == "available"]
    counts = dict((existing_manifest or {}).get("per_corpus_record_counts", {}))
    incoming_counts: dict[str, int] = {}
    for record in records:
        incoming_counts[record["corpus_id"]] = incoming_counts.get(record["corpus_id"], 0) + 1
    counts.update(incoming_counts)
    normalized = sorted(counts)
    return {
        "manifest_version": "multi-corpus-readiness-v1",
        "schema_version": SCHEMA_VERSION,
        "total_corpora_registered": len(corpora),
        "available_corpora": available,
        "normalized_corpora": normalized,
        "total_normalized_records": sum(counts.values()),
        "per_corpus_record_counts": dict(sorted(counts.items())),
        "validation_summary": dict((existing_manifest or {}).get("validation_summary", {})),
        "missing_fields_summary": missing_fields_summary or {},
        "readiness_status": (
            "READY_FOR_CONTROLLED_EXPANSION"
            if len(corpora) == 12 and bool(counts)
            else "NOT_READY"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Normalize the existing Irandaam Thirumurai enriched corpus."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--corpus-id", choices=sorted(CORPUS_CONFIGS), default=CORPUS_ID)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args(argv)

    config = CORPUS_CONFIGS[args.corpus_id]
    input_path = args.input if args.input != DEFAULT_INPUT or args.corpus_id == CORPUS_ID else config["input"]
    output_path = args.output if args.output != DEFAULT_OUTPUT or args.corpus_id == CORPUS_ID else config["output"]
    source_records = load_jsonl(input_path)
    records = [normalize_record(record, args.corpus_id) for record in source_records]
    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    existing_manifest = (
        json.loads(args.manifest.read_text(encoding="utf-8")) if args.manifest.exists() else {}
    )
    existing_counts = dict(existing_manifest.get("per_corpus_record_counts", {}))
    if not existing_counts:
        for known_id, known_config in CORPUS_CONFIGS.items():
            if known_config["output"].exists():
                existing_counts[known_id] = sum(
                    1
                    for line in known_config["output"].read_text(encoding="utf-8").splitlines()
                    if line.strip()
                )
    existing_counts[args.corpus_id] = 0
    existing_manifest["per_corpus_record_counts"] = existing_counts

    write_jsonl(output_path, records)
    write_json(args.manifest, build_manifest(registry, records, existing_manifest=existing_manifest))

    print(f"Source records: {len(source_records)}")
    print(f"Normalized records: {len(records)}")
    print(f"Corpus: {args.corpus_id}")
    print(f"Output: {output_path}")
    print(f"Manifest: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
