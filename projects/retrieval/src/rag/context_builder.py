from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from retrieval.hybrid_retriever import HybridRetriever
from retrieval.query_expander import QueryExpander

DEFAULT_ENRICHED = Path("data/processed/enriched/irandaam_thirumurai_enriched.jsonl")
DEFAULT_TOP_K = 5
DEFAULT_MAX_CONTEXT_CHARS = 100_000
CONTENT_FIELDS = ("verse_text", "pozhppurai", "kurippurai", "metadata_context")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def expand_matched_modes(modes: list[str]) -> list[str]:
    expanded: set[str] = set()
    for mode in modes:
        if mode == "both":
            expanded.update({"lexical", "semantic"})
        elif mode:
            expanded.add(mode)
    return [mode for mode in ("lexical", "semantic") if mode in expanded]


def source_urls(record: dict[str, Any], result: dict[str, Any]) -> list[str]:
    urls = [
        record.get("hymn_url", ""),
        record.get("commentary_url", ""),
        *(result.get("source_urls", {}) or {}).values(),
    ]
    return list(dict.fromkeys(url for url in urls if url))


def trim_content(content: dict[str, str], remaining_chars: int) -> tuple[dict[str, str], int, bool]:
    trimmed: dict[str, str] = {}
    used = 0
    was_truncated = False
    for field in CONTENT_FIELDS:
        value = content.get(field, "")
        available = max(0, remaining_chars - used)
        if len(value) <= available:
            trimmed[field] = value
            used += len(value)
        elif available > 0:
            if available <= 3:
                trimmed[field] = "." * available
            else:
                suffix = "..."
                keep = available - len(suffix)
                trimmed[field] = value[:keep].rstrip() + suffix
            used += len(trimmed[field])
            was_truncated = True
        else:
            trimmed[field] = ""
            if value:
                was_truncated = True
    return trimmed, used, was_truncated


def context_from_result(
    result: dict[str, Any],
    record: dict[str, Any],
    context_index: int,
    remaining_chars: int,
) -> tuple[dict[str, Any], int]:
    citation = record.get("citation", {})
    content = {
        "verse_text": record.get("verse_text_normalized", record.get("verse_text", "")),
        "pozhppurai": record.get("pozhppurai_normalized", record.get("pozhppurai", "")),
        "kurippurai": record.get("kurippurai_normalized", record.get("kurippurai", "")),
        "metadata_context": record.get("metadata_text", ""),
    }
    content, used_chars, truncated = trim_content(content, remaining_chars)
    context = {
        "context_id": f"ctx_{context_index:03d}",
        "rank": result["rank"],
        "parent_record_id": result.get("parent_record_id") or result["record_id"],
        "chunk_id": result["chunk_id"],
        "chunk_type": result.get("chunk_type", ""),
        "matched_modes": expand_matched_modes(result.get("matched_modes", [])),
        "hybrid_score": result.get("hybrid_score", result.get("score", 0.0)),
        "retrieval": {
            "lexical_score": result.get("lexical_score", 0.0),
            "semantic_score": result.get("semantic_score", 0.0),
            "normalized_lexical_score": result.get("normalized_lexical_score", 0.0),
            "normalized_semantic_score": result.get("normalized_semantic_score", 0.0),
            "matched_fields": result.get("matched_fields", []),
            "exact_match_boost": result.get("exact_match_boost", 0.0),
            "metadata_filter_boost": result.get("metadata_filter_boost", 0.0),
        },
        "citation": {
            "source_name": citation.get("source_name", record.get("source", "TamilVU")),
            "source_title": citation.get("hymn_title", record.get("hymn_title", "")),
            "citation_text": citation.get("citation_string", result.get("citation_text", "")),
            "author": citation.get("author", record.get("author", "")),
            "collection": citation.get("collection", record.get("collection", "")),
            "thirumurai": citation.get("thirumurai", record.get("thirumurai", "")),
            "song_no": str(citation.get("song_no", record.get("song_no", ""))),
            "hymn_id": str(citation.get("hymn_id", record.get("hymn_id", ""))),
            "source_urls": source_urls(record, result),
        },
        "content": content,
        "content_char_count": used_chars,
        "content_truncated": truncated,
        "deterministic_rank_key": result.get(
            "deterministic_rank_key",
            record.get("deterministic_rank_key", ""),
        ),
    }
    return context, used_chars


def validate_context_package(package: dict[str, Any], retrieval_succeeded: bool = True) -> list[str]:
    errors: list[str] = []
    contexts = package.get("contexts", [])
    if retrieval_succeeded and not contexts:
        errors.append("retrieval succeeded but context package is empty")
    if package.get("context_count") != len(contexts):
        errors.append("context_count does not match contexts")

    expected_ids = [f"ctx_{index:03d}" for index in range(1, len(contexts) + 1)]
    actual_ids = [context.get("context_id") for context in contexts]
    if actual_ids != expected_ids:
        errors.append("context IDs are not deterministic")

    seen_records: set[str] = set()
    seen_chunks: set[str] = set()
    for context in contexts:
        parent_record_id = context.get("parent_record_id")
        chunk_id = context.get("chunk_id")
        citation = context.get("citation", {})
        if not parent_record_id:
            errors.append(f"{context.get('context_id')}: missing parent_record_id")
        if not chunk_id:
            errors.append(f"{context.get('context_id')}: missing chunk_id")
        if not citation.get("citation_text") or not citation.get("source_title"):
            errors.append(f"{context.get('context_id')}: incomplete citation")
        if parent_record_id in seen_records:
            errors.append(f"{context.get('context_id')}: duplicate parent_record_id")
        if chunk_id in seen_chunks:
            errors.append(f"{context.get('context_id')}: duplicate chunk_id")
        seen_records.add(parent_record_id)
        seen_chunks.add(chunk_id)
    return errors


class ContextBuilder:
    def __init__(
        self,
        retriever: HybridRetriever | None = None,
        enriched_path: Path = DEFAULT_ENRICHED,
        query_expander: QueryExpander | None = None,
    ) -> None:
        self.retriever = retriever or HybridRetriever()
        self.query_expander = query_expander
        records = load_jsonl(enriched_path)
        self.records_by_id = {record["record_id"]: record for record in records}

    def build(
        self,
        query: str,
        top_k: int = DEFAULT_TOP_K,
        filters: dict[str, Any] | None = None,
        max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
        expand_query: bool = False,
    ) -> dict[str, Any]:
        expansion = None
        retrieval_query = query
        if expand_query:
            expansion = (self.query_expander or QueryExpander()).expand(query)
            retrieval_query = expansion["expanded_query_text"]
        results = self.retriever.search(
            retrieval_query,
            filters=filters or {},
            top_k=max(top_k * 3, top_k),
        )
        contexts: list[dict[str, Any]] = []
        seen_records: set[str] = set()
        seen_chunks: set[str] = set()
        used_chars = 0

        for result in results:
            parent_record_id = result.get("parent_record_id") or result.get("record_id")
            chunk_id = result.get("chunk_id")
            if not parent_record_id or not chunk_id:
                continue
            if parent_record_id in seen_records or chunk_id in seen_chunks:
                continue
            record = self.records_by_id.get(parent_record_id)
            if not record:
                continue
            remaining_chars = max_context_chars - used_chars
            if remaining_chars <= 0:
                break
            context, context_chars = context_from_result(
                result,
                record,
                context_index=len(contexts) + 1,
                remaining_chars=remaining_chars,
            )
            contexts.append(context)
            seen_records.add(parent_record_id)
            seen_chunks.add(chunk_id)
            used_chars += context_chars
            if len(contexts) >= top_k:
                break

        package = {
            "query": query,
            "retrieval_mode": "hybrid",
            "context_count": len(contexts),
            "contexts": contexts,
            "context_limits": {
                "top_k": top_k,
                "max_context_chars": max_context_chars,
                "used_context_chars": used_chars,
                "estimated_tokens": max(1, (used_chars + 3) // 4) if used_chars else 0,
                "truncated_contexts": sum(context["content_truncated"] for context in contexts),
            },
            "validation": {
                "status": "valid",
                "errors": [],
            },
        }
        if expansion is not None:
            package["query_expansion"] = expansion
            package["retrieval_query"] = retrieval_query
        errors = validate_context_package(package, retrieval_succeeded=bool(results))
        package["validation"] = {
            "status": "valid" if not errors else "invalid",
            "errors": errors,
        }
        if errors:
            raise ValueError("invalid context package: " + "; ".join(errors))
        return package
