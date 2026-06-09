from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

DEFAULT_INPUT = Path("data/releases/irandaam-thirumurai-v1/irandaam_thirumurai.jsonl")
DEFAULT_ENRICHED = Path("data/processed/enriched/irandaam_thirumurai_enriched.jsonl")
DEFAULT_CHUNKS = Path("data/processed/chunks/irandaam_thirumurai_chunks.jsonl")
DEFAULT_LEXICAL_INDEX = Path("data/processed/indexes/irandaam_thirumurai_lexical_index.json")
DEFAULT_GOLDEN = Path("data/processed/eval/golden_queries.jsonl")
DEFAULT_REPORT = Path("reports/retrieval-readiness-report.md")

SCHEMA_VERSION = "retrieval-ready-irandaam-thirumurai-v1.1"
SOURCE_CORPUS_VERSION = "irandaam-thirumurai-v1"
ENRICHED_CORPUS_VERSION = "irandaam-thirumurai-v1.1"
TAMIL_RE = re.compile(r"[\u0B80-\u0BFF]")
TOKEN_SPLIT_RE = re.compile(r"[^\w\u0B80-\u0BFF]+", re.UNICODE)


@dataclass(slots=True)
class ValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.split("\n"):
        normalized = " ".join(line.replace("\xa0", " ").split())
        if normalized:
            lines.append(normalized)
    return "\n".join(lines).strip()


def normalize_inline(text: str) -> str:
    return " ".join(normalize_text(text).split())


def normalize_label_text(text: str) -> str:
    text = normalize_text(text)
    text = re.sub(r"(பொழிப்புரை|பொ-ரை)\s*[:;]\s*", "", text)
    text = re.sub(r"(குறிப்புரை|கு-ரை)\s*[:;]\s*", "", text)
    return normalize_text(text)


def record_id(hymn_id: str, song_no: str) -> str:
    return f"thevaram_02_{hymn_id}_{song_no}"


def verse_id(hymn_id: str, song_no: str) -> str:
    return f"{record_id(hymn_id, song_no)}_verse"


def canonical_id(hymn_id: str, song_no: str) -> str:
    return f"tvu_thevaram_irandaam_thirumurai_{hymn_id}_{song_no}"


def tamil_tokens(text: str) -> list[str]:
    tokens = []
    for raw in TOKEN_SPLIT_RE.split(normalize_inline(text).lower()):
        token = raw.strip("_")
        if token:
            tokens.append(token)
    return tokens


def unique_terms(tokens: list[str]) -> list[str]:
    return sorted(set(tokens))


def keyword_candidates(tokens: list[str], limit: int = 30) -> list[str]:
    counts = Counter(token for token in tokens if len(token) > 1)
    return [term for term, _count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:limit]]


def token_estimate(text: str) -> int:
    return max(1, len(tamil_tokens(text)))


def source_record_id(record: dict) -> str:
    return f"tvu:{record['hymn_id']}:{record['song_no']}"


def citation(record: dict) -> dict:
    return {
        "source_name": "TamilVU",
        "collection": record["collection"],
        "thirumurai": record["thirumurai"],
        "author": record["author"],
        "hymn_title": record["hymn_title"],
        "hymn_id": record["hymn_id"],
        "song_no": record["song_no"],
        "hymn_url": record["hymn_url"],
        "commentary_url": record["commentary_url"],
        "citation_string": f"திருஞானசம்பந்தர், இரண்டாம் திருமுறை, {record['hymn_title']}, பாடல் {record['song_no']}, TamilVU.",
    }


def filter_metadata(record: dict) -> dict:
    metadata = record.get("extraction_metadata", {})
    return {
        "source": record["source"],
        "collection": record["collection"],
        "work": record["work"],
        "thirumurai": record["thirumurai"],
        "thirumurai_number": record["thirumurai_number"],
        "author": record["author"],
        "hymn_id": record["hymn_id"],
        "hymn_title": record["hymn_title"],
        "hymn_location": record["hymn_location"],
        "hymn_note": record["hymn_note"],
        "pann": record["pann"],
        "song_no": record["song_no"],
        "commentary_available": record["commentary_available"],
        "extraction_status": metadata.get("extraction_status", ""),
    }


def deterministic_rank_key(record: dict, chunk_type: str | None = None) -> str:
    base = f"{int(record['hymn_id']):04d}:{int(record['song_no']):04d}"
    return f"{base}:{chunk_type}" if chunk_type else base


def enrich_record(record: dict) -> dict:
    hymn_id = str(record["hymn_id"])
    song_no = str(record["song_no"])
    rid = record_id(hymn_id, song_no)

    verse = normalize_label_text(record.get("verse_text", ""))
    pozh = normalize_label_text(record.get("pozhppurai", ""))
    kuri = normalize_label_text(record.get("kurippurai", ""))
    commentary_parts = [part for part in [pozh, kuri] if part]
    combined_commentary = "\n\n".join(commentary_parts)
    metadata_text = normalize_inline(
        " ".join(
            [
                record["collection"],
                record["work"],
                record["thirumurai"],
                record["author"],
                record["hymn_title"],
                record["hymn_location"],
                record.get("hymn_note", ""),
                record.get("pann", ""),
                song_no,
            ]
        )
    )
    full_text = normalize_text("\n\n".join(part for part in [metadata_text, verse, combined_commentary] if part))
    tokens = tamil_tokens(" ".join([full_text, metadata_text]))
    normalized_terms = unique_terms(tokens)

    enriched = dict(record)
    enriched.update(
        {
            "schema_version": SCHEMA_VERSION,
            "source_corpus_version": SOURCE_CORPUS_VERSION,
            "enriched_corpus_version": ENRICHED_CORPUS_VERSION,
            "record_id": rid,
            "source_record_id": source_record_id(record),
            "verse_id": verse_id(hymn_id, song_no),
            "canonical_id": canonical_id(hymn_id, song_no),
            "verse_text_normalized": verse,
            "pozhppurai_normalized": pozh,
            "kurippurai_normalized": kuri,
            "combined_commentary": combined_commentary,
            "full_text_for_search": full_text,
            "metadata_text_for_search": metadata_text,
            "search_text": full_text,
            "search_text_normalized": normalize_inline(full_text),
            "metadata_text": metadata_text,
            "citation_text": citation(record)["citation_string"],
            "citation": citation(record),
            "filter_metadata": filter_metadata(record),
            "tamil_tokens": tokens,
            "normalized_tokens": tokens,
            "unique_terms": normalized_terms,
            "keyword_candidates": keyword_candidates(tokens),
            "deterministic_rank_key": deterministic_rank_key(record),
        }
    )
    return enriched


def chunk_text_for_type(record: dict, chunk_type: str) -> str:
    if chunk_type == "verse_only":
        return record["verse_text_normalized"]
    if chunk_type == "pozhppurai_only":
        return record["pozhppurai_normalized"]
    if chunk_type == "kurippurai_only":
        return record["kurippurai_normalized"]
    if chunk_type == "verse_plus_commentary":
        return "\n\n".join(
            part
            for part in [
                record["verse_text_normalized"],
                record["pozhppurai_normalized"],
                record["kurippurai_normalized"],
            ]
            if part
        )
    if chunk_type == "metadata_context":
        return record["metadata_text"]
    raise ValueError(f"unknown chunk type: {chunk_type}")


def create_chunk(record: dict, chunk_type: str) -> dict:
    text = normalize_text(chunk_text_for_type(record, chunk_type))
    tokens = tamil_tokens(" ".join([text, record["metadata_text"]]))
    return {
        "chunk_id": f"{record['record_id']}_{chunk_type}",
        "parent_record_id": record["record_id"],
        "chunk_type": chunk_type,
        "chunk_text": text,
        "chunk_text_normalized": normalize_inline(text),
        "token_estimate": token_estimate(text),
        "char_count": len(text),
        "language": record["language"],
        "citation": record["citation"],
        "filter_metadata": record["filter_metadata"],
        "source_urls": {
            "hymn_url": record["hymn_url"],
            "commentary_url": record["commentary_url"],
        },
        "deterministic_rank_key": deterministic_rank_key(record, chunk_type),
        "tamil_tokens": tokens,
        "normalized_tokens": tokens,
        "unique_terms": unique_terms(tokens),
        "keyword_candidates": keyword_candidates(tokens),
    }


def create_chunks(enriched_records: list[dict]) -> list[dict]:
    chunks = []
    for record in enriched_records:
        for chunk_type in ["verse_only", "verse_plus_commentary", "metadata_context"]:
            chunks.append(create_chunk(record, chunk_type))
        if record["pozhppurai_normalized"]:
            chunks.append(create_chunk(record, "pozhppurai_only"))
        if record["kurippurai_normalized"]:
            chunks.append(create_chunk(record, "kurippurai_only"))
    return sorted(chunks, key=lambda chunk: chunk["deterministic_rank_key"])


def add_index_value(index: dict[str, list[str]], key: str, value: str) -> None:
    if key:
        index.setdefault(key, []).append(value)


def finalize_index_lists(index: dict[str, list[str]]) -> dict[str, list[str]]:
    return {key: sorted(set(values)) for key, values in sorted(index.items())}


def build_lexical_index(enriched_records: list[dict], chunks: list[dict]) -> dict:
    term_to_record_ids: dict[str, list[str]] = {}
    term_to_chunk_ids: dict[str, list[str]] = {}
    hymn_id_to_record_ids: dict[str, list[str]] = {}
    song_no_to_record_id: dict[str, str] = {}
    author_to_record_ids: dict[str, list[str]] = {}
    pann_to_record_ids: dict[str, list[str]] = {}
    hymn_title_terms_to_record_ids: dict[str, list[str]] = {}
    missing_commentary = []
    partial_commentary = []

    for record in enriched_records:
        rid = record["record_id"]
        for term in record["unique_terms"]:
            add_index_value(term_to_record_ids, term, rid)
        add_index_value(hymn_id_to_record_ids, record["hymn_id"], rid)
        song_no_to_record_id[record["song_no"]] = rid
        add_index_value(author_to_record_ids, record["author"], rid)
        add_index_value(pann_to_record_ids, record.get("pann", ""), rid)
        for term in unique_terms(tamil_tokens(record["hymn_title"])):
            add_index_value(hymn_title_terms_to_record_ids, term, rid)
        if not record["pozhppurai_normalized"] or not record["kurippurai_normalized"]:
            missing_commentary.append(rid)
        if record["filter_metadata"]["extraction_status"] == "partial_commentary":
            partial_commentary.append(rid)

    for chunk in chunks:
        for term in chunk["unique_terms"]:
            add_index_value(term_to_chunk_ids, term, chunk["chunk_id"])

    return {
        "schema_version": SCHEMA_VERSION,
        "record_count": len(enriched_records),
        "chunk_count": len(chunks),
        "term_to_record_ids": finalize_index_lists(term_to_record_ids),
        "term_to_chunk_ids": finalize_index_lists(term_to_chunk_ids),
        "hymn_id_to_record_ids": finalize_index_lists(hymn_id_to_record_ids),
        "song_no_to_record_id": dict(sorted(song_no_to_record_id.items(), key=lambda item: int(item[0]))),
        "author_to_record_ids": finalize_index_lists(author_to_record_ids),
        "pann_to_record_ids": finalize_index_lists(pann_to_record_ids),
        "hymn_title_terms_to_record_ids": finalize_index_lists(hymn_title_terms_to_record_ids),
        "missing_commentary_record_ids": sorted(set(missing_commentary)),
        "partial_commentary_record_ids": sorted(set(partial_commentary)),
    }


def ids_for_term(records: list[dict], term: str, field: str | None = None) -> list[str]:
    output = []
    for record in records:
        haystack = record[field] if field else record["search_text_normalized"]
        if term in tamil_tokens(haystack):
            output.append(record["record_id"])
    return sorted(set(output))


def chunk_ids_for_records(chunks: list[dict], record_ids: list[str], chunk_type: str | None = None) -> list[str]:
    ids = set(record_ids)
    return sorted(
        chunk["chunk_id"]
        for chunk in chunks
        if chunk["parent_record_id"] in ids and (chunk_type is None or chunk["chunk_type"] == chunk_type)
    )


def make_query(query_id: str, text: str, query_type: str, expected_records: list[str], chunks: list[dict], filters: dict | None = None, notes: str = "", chunk_type: str | None = None) -> dict:
    return {
        "query_id": query_id,
        "query_text": text,
        "query_type": query_type,
        "expected_record_ids": sorted(set(expected_records)),
        "expected_chunk_ids": chunk_ids_for_records(chunks, expected_records, chunk_type=chunk_type) if expected_records else [],
        "required_filters": filters or {},
        "expected_min_results": min(1, len(expected_records)),
        "notes": notes,
    }


def create_golden_queries(records: list[dict], chunks: list[dict], seed: int) -> list[dict]:
    by_hymn = defaultdict(list)
    for record in records:
        by_hymn[record["hymn_id"]].append(record)
    all_ids = [record["record_id"] for record in records]
    first = records[0]
    queries = [
        make_query("exact_song_no_1470", "find song_no 1470", "exact_lookup", [r["record_id"] for r in records if r["song_no"] == "1470"], chunks, {"song_no": "1470"}),
        make_query("exact_hymn_id_1664", "find hymn_id 1664", "exact_lookup", [r["record_id"] for r in records if r["hymn_id"] == "1664"], chunks, {"hymn_id": "1664"}),
        make_query("known_hymn_title_thiruppoontharai", "திருப்பூந்தராய்", "exact_title", [r["record_id"] for r in records if "திருப்பூந்தராய்" in r["hymn_title"]], chunks),
        make_query("metadata_author_sambandar", "all records by Sambandar", "metadata", all_ids, chunks, {"author": "Sambandar"}),
        make_query("metadata_irandaam_thirumurai", "all records in Irandaam Thirumurai", "metadata", all_ids, chunks, {"thirumurai": "Irandaam Thirumurai"}),
        make_query("metadata_pann_indhalam", "all records with pann = இந்தளம்", "metadata", [r["record_id"] for r in records if r.get("pann") == "இந்தளம்"], chunks, {"pann": "இந்தளம்"}),
        make_query("keyword_arul", "records containing அருள்", "keyword", ids_for_term(records, "அருள்"), chunks),
        make_query("keyword_sivan", "records containing சிவன்", "keyword", ids_for_term(records, "சிவன்"), chunks),
        make_query("keyword_sivaperuman", "records containing சிவபெருமான்", "keyword", ids_for_term(records, "சிவபெருமான்"), chunks),
        make_query("keyword_thiruppoontharai", "records containing திருப்பூந்தராய்", "keyword", ids_for_term(records, "திருப்பூந்தராய்"), chunks),
        make_query("commentary_with_pozhppurai", "records with pozhppurai", "commentary", [r["record_id"] for r in records if r["pozhppurai_normalized"]], chunks, chunk_type="pozhppurai_only"),
        make_query("commentary_with_kurippurai", "records with kurippurai", "commentary", [r["record_id"] for r in records if r["kurippurai_normalized"]], chunks, chunk_type="kurippurai_only"),
        make_query("commentary_partial", "records with partial_commentary", "commentary", [r["record_id"] for r in records if r["filter_metadata"]["extraction_status"] == "partial_commentary"], chunks, {"extraction_status": "partial_commentary"}),
        make_query("commentary_missing_pozhppurai", "records missing pozhppurai", "commentary", [r["record_id"] for r in records if not r["pozhppurai_normalized"]], chunks),
        make_query("commentary_missing_kurippurai", "records missing kurippurai", "commentary", [r["record_id"] for r in records if not r["kurippurai_normalized"]], chunks),
        make_query("mixed_author_arul", "Sambandar அருள்", "mixed", ids_for_term(records, "அருள்"), chunks, {"author": "Sambandar"}),
        make_query("mixed_title_commentary", f"{first['hymn_title']} அருள்", "mixed", [r["record_id"] for r in by_hymn[first["hymn_id"]] if "அருள்" in r["search_text_normalized"]], chunks, {"hymn_id": first["hymn_id"]}),
        make_query("mixed_thirumurai_song", "Irandaam Thirumurai song_no 1470", "mixed", [r["record_id"] for r in records if r["song_no"] == "1470"], chunks, {"thirumurai": "Irandaam Thirumurai", "song_no": "1470"}),
    ]

    for index, hymn_id in enumerate(["1702", "1711", "1748", "1785"], start=1):
        queries.append(make_query(f"sample_hymn_{hymn_id}", f"find hymn_id {hymn_id}", "exact_lookup", [r["record_id"] for r in records if r["hymn_id"] == hymn_id], chunks, {"hymn_id": hymn_id}, notes="sampled spread query"))

    high_value_terms = ["மதி", "கங்கை", "வேதம்", "பாம்பு", "கோயில்", "மலர்", "வினை", "மறை", "புகலி", "திருவடி", "சடை", "விடை"]
    for term in high_value_terms:
        expected = ids_for_term(records, term)
        if expected:
            queries.append(make_query(f"keyword_{hashlib.sha1(term.encode()).hexdigest()[:8]}", f"records containing {term}", "keyword", expected, chunks))

    rng = random_sample_records(records, seed, 8)
    for record in rng:
        queries.append(make_query(f"deterministic_record_{record['record_id']}", f"{record['hymn_title']} பாடல் {record['song_no']}", "manual_spot_check", [record["record_id"]], chunks, {"hymn_id": record["hymn_id"], "song_no": record["song_no"]}))

    return queries[:50]


def random_sample_records(records: list[dict], seed: int, count: int) -> list[dict]:
    import random

    rng = random.Random(seed)
    return sorted(rng.sample(records, min(count, len(records))), key=lambda r: (int(r["hymn_id"]), int(r["song_no"])))


def validate_outputs(source_records: list[dict], enriched: list[dict], chunks: list[dict], index: dict, queries: list[dict]) -> ValidationResult:
    errors = []
    warnings = []
    record_ids = [r["record_id"] for r in enriched]
    chunk_ids = [c["chunk_id"] for c in chunks]
    source_song = sorted(r["song_no"] for r in source_records)
    enriched_song = sorted(r["song_no"] for r in enriched)
    chunks_by_record = defaultdict(list)
    for chunk in chunks:
        chunks_by_record[chunk["parent_record_id"]].append(chunk)

    checks = [
        (len(enriched) == len(source_records), "enriched record count differs from source"),
        (len(record_ids) == len(set(record_ids)), "record_id values are not unique"),
        (source_song == enriched_song, "source song_no set/order changed"),
        (len(chunk_ids) == len(set(chunk_ids)), "chunk_id values are not unique"),
    ]
    for ok, message in checks:
        if not ok:
            errors.append(message)

    for record in enriched:
        rid = record["record_id"]
        types = {chunk["chunk_type"] for chunk in chunks_by_record[rid]}
        if "verse_only" not in types:
            errors.append(f"{rid} missing verse_only chunk")
        if "verse_plus_commentary" not in types:
            errors.append(f"{rid} missing verse_plus_commentary chunk")
        if record["pozhppurai_normalized"] and "pozhppurai_only" not in types:
            errors.append(f"{rid} missing pozhppurai_only chunk")
        if not record["pozhppurai_normalized"] and "pozhppurai_only" in types:
            errors.append(f"{rid} has pozhppurai_only chunk without pozhppurai")
        if record["kurippurai_normalized"] and "kurippurai_only" not in types:
            errors.append(f"{rid} missing kurippurai_only chunk")
        if not record["kurippurai_normalized"] and "kurippurai_only" in types:
            errors.append(f"{rid} has kurippurai_only chunk without kurippurai")
        if not record.get("citation") or not record.get("citation_text"):
            errors.append(f"{rid} missing citation")
        for key, value in record.items():
            if value is None:
                errors.append(f"{rid} has null field {key}")

    for chunk in chunks:
        if not chunk.get("citation"):
            errors.append(f"{chunk['chunk_id']} missing citation")
        for key, value in chunk.items():
            if value is None:
                errors.append(f"{chunk['chunk_id']} has null field {key}")

    if "அருள்" not in index["term_to_record_ids"]:
        errors.append("lexical index missing known term அருள்")
    if "1470" not in index["song_no_to_record_id"]:
        errors.append("song_no lookup missing 1470")
    if "1664" not in index["hymn_id_to_record_ids"]:
        errors.append("hymn_id lookup missing 1664")
    if len(index["partial_commentary_record_ids"]) != 7:
        errors.append("partial_commentary lookup does not contain 7 records")
    for query in queries:
        if len(query["expected_record_ids"]) < query["expected_min_results"]:
            errors.append(f"golden query {query['query_id']} has insufficient expected records")
    if len(queries) < 30:
        warnings.append("golden query set has fewer than 30 queries")

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings)


def summarize_counts(enriched: list[dict], chunks: list[dict], index: dict, queries: list[dict], validation: ValidationResult) -> dict:
    return {
        "enriched_records": len(enriched),
        "chunks": len(chunks),
        "chunk_counts_by_type": dict(sorted(Counter(chunk["chunk_type"] for chunk in chunks).items())),
        "lexical_record_terms": len(index["term_to_record_ids"]),
        "lexical_chunk_terms": len(index["term_to_chunk_ids"]),
        "golden_queries": len(queries),
        "partial_commentary_records": len(index["partial_commentary_record_ids"]),
        "validation_ok": validation.ok,
    }


def render_report(summary: dict, validation: ValidationResult, paths: dict[str, Path]) -> str:
    recommendation = "RETRIEVAL_READY" if validation.ok else "RETRIEVAL_REPAIR_REQUIRED"
    lines = [
        "# Retrieval Readiness Report",
        "",
        "## Input Corpus Summary",
        "",
        f"- Source corpus: `{SOURCE_CORPUS_VERSION}`",
        f"- Input: `{paths['input']}`",
        "",
        "## Enriched Corpus Summary",
        "",
        f"- Enriched records: `{summary['enriched_records']}`",
        f"- Enriched version: `{ENRICHED_CORPUS_VERSION}`",
        f"- Schema version: `{SCHEMA_VERSION}`",
        "",
        "## Normalization Summary",
        "",
        "- Unicode normalized with NFC.",
        "- Repeated whitespace and blank lines collapsed conservatively.",
        "- Tamil words, punctuation meaning, and line-level verse content are preserved.",
        "- Commentary labels are removed only when they appear as extracted prose labels.",
        "",
        "## Chunk Counts",
        "",
    ]
    for chunk_type, count in summary["chunk_counts_by_type"].items():
        lines.append(f"- `{chunk_type}`: `{count}`")
    lines.extend(
        [
            "",
            "## Lexical Index Statistics",
            "",
            f"- Record terms: `{summary['lexical_record_terms']}`",
            f"- Chunk terms: `{summary['lexical_chunk_terms']}`",
            f"- Partial commentary record IDs: `{summary['partial_commentary_records']}`",
            "",
            "## Golden Query Statistics",
            "",
            f"- Golden queries: `{summary['golden_queries']}`",
            "",
            "## Validation Results",
            "",
            f"- Validation OK: `{validation.ok}`",
        ]
    )
    if validation.errors:
        lines.extend(["", "### Errors", ""])
        lines.extend(f"- {error}" for error in validation.errors)
    if validation.warnings:
        lines.extend(["", "### Warnings", ""])
        lines.extend(f"- {warning}" for warning in validation.warnings)
    lines.extend(
        [
            "",
            "## Missing/Partial Commentary Handling",
            "",
            "- Missing commentary fields are preserved as empty normalized strings.",
            "- `partial_commentary` records are indexed in `partial_commentary_record_ids`.",
            "- No missing commentary prose is fabricated.",
            "",
            "## Deterministic Retrieval Design",
            "",
            "Rule-based retrieval order:",
            "",
            "1. Apply metadata filters first.",
            "2. Exact `song_no` or `hymn_id` match.",
            "3. Exact title/hymn term match.",
            "4. Exact keyword match in verse.",
            "5. Exact keyword match in `pozhppurai`.",
            "6. Exact keyword match in `kurippurai`.",
            "7. Combined `search_text` match.",
            "8. Semantic/vector search later only if lexical retrieval is insufficient.",
            "9. Fixed reranking order: exact identifier, exact title, exact verse, exact commentary, combined text, semantic score later.",
            "10. Return fixed top-k with stable tie-breaking using `deterministic_rank_key`.",
            "",
            "## Files Generated",
            "",
        ]
    )
    for label, path in paths.items():
        if label != "input":
            lines.append(f"- `{label}`: `{path}`")
    lines.extend(["", "## Readiness Recommendation", "", f"`{recommendation}`"])
    return "\n".join(lines)


def build_retrieval_ready(input_path: Path, seed: int) -> tuple[list[dict], list[dict], dict, list[dict], ValidationResult, dict]:
    source_records = sorted(load_jsonl(input_path), key=lambda r: (int(r["hymn_id"]), int(r["song_no"])))
    enriched = [enrich_record(record) for record in source_records]
    chunks = create_chunks(enriched)
    index = build_lexical_index(enriched, chunks)
    queries = create_golden_queries(enriched, chunks, seed)
    validation = validate_outputs(source_records, enriched, chunks, index, queries)
    summary = summarize_counts(enriched, chunks, index, queries, validation)
    return enriched, chunks, index, queries, validation, summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build retrieval-ready derived corpus artifacts from frozen Irandaam Thirumurai v1")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-enriched", type=Path, default=DEFAULT_ENRICHED)
    parser.add_argument("--output-chunks", type=Path, default=DEFAULT_CHUNKS)
    parser.add_argument("--output-lexical-index", type=Path, default=DEFAULT_LEXICAL_INDEX)
    parser.add_argument("--output-golden-queries", type=Path, default=DEFAULT_GOLDEN)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--deterministic-seed", type=int, default=42)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    enriched, chunks, index, queries, validation, summary = build_retrieval_ready(args.input, args.deterministic_seed)
    write_jsonl(enriched, args.output_enriched)
    write_jsonl(chunks, args.output_chunks)
    write_json(index, args.output_lexical_index)
    write_jsonl(queries, args.output_golden_queries)
    paths = {
        "input": args.input,
        "enriched": args.output_enriched,
        "chunks": args.output_chunks,
        "lexical_index": args.output_lexical_index,
        "golden_queries": args.output_golden_queries,
        "report": args.report,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(summary, validation, paths), encoding="utf-8")
    print(f"Enriched records: {summary['enriched_records']}")
    print(f"Chunks: {summary['chunks']}")
    print(f"Golden queries: {summary['golden_queries']}")
    print(f"Validation OK: {validation.ok}")
    print(f"Recommendation: {'RETRIEVAL_READY' if validation.ok else 'RETRIEVAL_REPAIR_REQUIRED'}")
    return 0 if validation.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
