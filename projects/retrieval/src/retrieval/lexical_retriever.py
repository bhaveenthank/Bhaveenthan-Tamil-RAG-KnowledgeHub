from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from enrichment.build_retrieval_ready_corpus import tamil_tokens

DEFAULT_ENRICHED = Path("data/processed/enriched/irandaam_thirumurai_enriched.jsonl")
DEFAULT_CHUNKS = Path("data/processed/chunks/irandaam_thirumurai_chunks.jsonl")
DEFAULT_INDEX = Path("data/processed/indexes/irandaam_thirumurai_lexical_index.json")

SUPPORTED_FILTERS = {
    "author",
    "thirumurai_number",
    "hymn_id",
    "song_no",
    "pann",
    "extraction_status",
    "commentary_available",
}


@dataclass(slots=True)
class RetrievalResult:
    rank: int
    score: int
    retrieval_mode: str
    record_id: str
    chunk_id: str | None
    chunk_type: str | None
    matched_fields: list[str]
    citation_text: str
    source_urls: dict[str, str]
    deterministic_rank_key: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "score": self.score,
            "retrieval_mode": self.retrieval_mode,
            "record_id": self.record_id,
            "chunk_id": self.chunk_id,
            "chunk_type": self.chunk_type,
            "matched_fields": self.matched_fields,
            "citation_text": self.citation_text,
            "source_urls": self.source_urls,
            "deterministic_rank_key": self.deterministic_rank_key,
        }


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalize_query_value(value: Any) -> Any:
    if isinstance(value, str):
        lowered = value.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return value


class LexicalRetriever:
    def __init__(
        self,
        enriched_path: Path = DEFAULT_ENRICHED,
        chunks_path: Path = DEFAULT_CHUNKS,
        index_path: Path = DEFAULT_INDEX,
    ) -> None:
        self.records = load_jsonl(enriched_path)
        self.chunks = load_jsonl(chunks_path)
        self.index = json.loads(index_path.read_text(encoding="utf-8"))
        self.records_by_id = {record["record_id"]: record for record in self.records}
        self.chunks_by_id = {chunk["chunk_id"]: chunk for chunk in self.chunks}
        self.chunks_by_record: dict[str, list[dict]] = {}
        for chunk in self.chunks:
            self.chunks_by_record.setdefault(chunk["parent_record_id"], []).append(chunk)

    def search(self, query_text: str, filters: dict[str, Any] | None = None, top_k: int = 10) -> list[dict]:
        filters = {key: normalize_query_value(value) for key, value in (filters or {}).items() if key in SUPPORTED_FILTERS}
        candidates = self._candidate_chunks(query_text, filters)
        scored = []
        for chunk in candidates:
            record = self.records_by_id[chunk["parent_record_id"]]
            score, matched = self._score(query_text, filters, record, chunk)
            if score > 0:
                scored.append((score, matched, record, chunk))
        scored.sort(key=lambda item: (-item[0], item[3]["deterministic_rank_key"], item[3]["chunk_id"]))
        results = []
        for rank, (score, matched, record, chunk) in enumerate(scored[:top_k], start=1):
            results.append(
                RetrievalResult(
                    rank=rank,
                    score=score,
                    retrieval_mode="lexical",
                    record_id=record["record_id"],
                    chunk_id=chunk["chunk_id"],
                    chunk_type=chunk["chunk_type"],
                    matched_fields=matched,
                    citation_text=record["citation_text"],
                    source_urls={
                        "hymn_url": record["hymn_url"],
                        "commentary_url": record["commentary_url"],
                    },
                    deterministic_rank_key=chunk["deterministic_rank_key"],
                ).to_dict()
            )
        return results

    def _candidate_chunks(self, query_text: str, filters: dict[str, Any]) -> list[dict]:
        record_ids: set[str] = set()
        if filters.get("song_no"):
            rid = self.index["song_no_to_record_id"].get(str(filters["song_no"]))
            if rid:
                record_ids.add(rid)
        if filters.get("hymn_id"):
            record_ids.update(self.index["hymn_id_to_record_ids"].get(str(filters["hymn_id"]), []))
        if filters.get("author"):
            record_ids.update(self.index["author_to_record_ids"].get(str(filters["author"]), []))
        if filters.get("pann"):
            record_ids.update(self.index["pann_to_record_ids"].get(str(filters["pann"]), []))
        record_id_match = self._extract_record_id(query_text)
        chunk_id_match = self._extract_chunk_id(query_text)
        if record_id_match and record_id_match in self.records_by_id:
            record_ids.add(record_id_match)
        if chunk_id_match and chunk_id_match in self.chunks_by_id:
            record_ids.add(self.chunks_by_id[chunk_id_match]["parent_record_id"])
        for token in tamil_tokens(query_text):
            record_ids.update(self.index["term_to_record_ids"].get(token, []))
        record_ids.update(self._commentary_availability_record_ids(query_text))
        if not record_ids:
            record_ids = {record["record_id"] for record in self.records}
        return [chunk for chunk in self.chunks if chunk["parent_record_id"] in record_ids and self._passes_filters(self.records_by_id[chunk["parent_record_id"]], filters)]

    def _passes_filters(self, record: dict, filters: dict[str, Any]) -> bool:
        metadata = record["filter_metadata"]
        for key, value in filters.items():
            if str(metadata.get(key)) != str(value):
                return False
        return True

    def _score(self, query_text: str, filters: dict[str, Any], record: dict, chunk: dict) -> tuple[int, list[str]]:
        matched: list[str] = []
        score = 0
        query = query_text.strip()
        query_tokens = tamil_tokens(query_text)
        record_id_match = self._extract_record_id(query_text)
        chunk_id_match = self._extract_chunk_id(query_text)

        if chunk_id_match and chunk_id_match == chunk["chunk_id"]:
            score += 10000
            matched.append("exact_chunk_id")
        if record_id_match and record_id_match == record["record_id"]:
            score += 9500
            matched.append("exact_record_id")
        if filters.get("song_no") and str(filters["song_no"]) == record["song_no"]:
            score += 9000
            matched.append("exact_song_no")
        if filters.get("hymn_id") and str(filters["hymn_id"]) == record["hymn_id"]:
            score += 8500
            matched.append("exact_hymn_id")
        metadata_filter_hits = [key for key, value in filters.items() if str(record["filter_metadata"].get(key)) == str(value)]
        if metadata_filter_hits:
            score += 200 * len(metadata_filter_hits)
            matched.extend(f"metadata_filter:{key}" for key in metadata_filter_hits)
        if query and query in record["hymn_title"]:
            score += 8000
            matched.append("exact_hymn_title")
        if self._matches_commentary_availability(query_text, record):
            score += 7500
            matched.append("commentary_availability")

        field_scores = [
            ("verse_text_normalized", 700),
            ("pozhppurai_normalized", 600),
            ("kurippurai_normalized", 500),
            ("search_text_normalized", 400),
            ("metadata_text", 300),
        ]
        for field, weight in field_scores:
            field_tokens = set(tamil_tokens(record.get(field, "")))
            hits = sorted(set(query_tokens) & field_tokens)
            if hits:
                score += weight * len(hits)
                matched.append(field)
        if query_tokens and set(query_tokens) & set(chunk.get("unique_terms", [])):
            score += 100
            matched.append("chunk_text")
        return score, sorted(set(matched))

    def _commentary_availability_record_ids(self, query_text: str) -> set[str]:
        query = query_text.lower()
        ids: set[str] = set()
        if "with pozhppurai" in query:
            ids.update(record["record_id"] for record in self.records if record["pozhppurai_normalized"])
        if "with kurippurai" in query:
            ids.update(record["record_id"] for record in self.records if record["kurippurai_normalized"])
        if "missing pozhppurai" in query:
            ids.update(record["record_id"] for record in self.records if not record["pozhppurai_normalized"])
        if "missing kurippurai" in query:
            ids.update(record["record_id"] for record in self.records if not record["kurippurai_normalized"])
        if "partial_commentary" in query:
            ids.update(self.index["partial_commentary_record_ids"])
        return ids

    def _matches_commentary_availability(self, query_text: str, record: dict) -> bool:
        query = query_text.lower()
        return (
            ("with pozhppurai" in query and bool(record["pozhppurai_normalized"]))
            or ("with kurippurai" in query and bool(record["kurippurai_normalized"]))
            or ("missing pozhppurai" in query and not record["pozhppurai_normalized"])
            or ("missing kurippurai" in query and not record["kurippurai_normalized"])
            or ("partial_commentary" in query and record["filter_metadata"]["extraction_status"] == "partial_commentary")
        )

    def _extract_record_id(self, query_text: str) -> str | None:
        match = re.search(r"thevaram_02_\d+_\d+(?!_)", query_text)
        return match.group(0) if match else None

    def _extract_chunk_id(self, query_text: str) -> str | None:
        match = re.search(r"thevaram_02_\d+_\d+_[a-z_]+", query_text)
        return match.group(0) if match else None


def parse_filter(values: list[str]) -> dict[str, str]:
    filters = {}
    for value in values:
        if "=" not in value:
            continue
        key, raw = value.split("=", 1)
        filters[key] = raw
    return filters


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic lexical retrieval")
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--filter", action="append", default=[])
    parser.add_argument("--top-k", type=int, default=10)
    args = parser.parse_args(argv)
    retriever = LexicalRetriever()
    results = retriever.search(args.query, filters=parse_filter(args.filter), top_k=args.top_k)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
