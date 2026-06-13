from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from retrieval.lexical_retriever import LexicalRetriever
from retrieval.semantic_retriever import SemanticRetriever

DEFAULT_LEXICAL_WEIGHT = 0.65
DEFAULT_SEMANTIC_WEIGHT = 0.35
DEFAULT_CANDIDATE_MULTIPLIER = 10

EXACT_MATCH_FIELDS = {
    "exact_chunk_id",
    "exact_record_id",
    "exact_song_no",
    "exact_hymn_id",
    "exact_hymn_title",
}
TEXT_MATCH_FIELDS = {
    "verse_text_normalized",
    "pozhppurai_normalized",
    "kurippurai_normalized",
}


@dataclass(slots=True)
class HybridCandidate:
    record_id: str
    chunk_id: str
    chunk_type: str
    citation_text: str
    source_urls: dict[str, str]
    deterministic_rank_key: str
    lexical_score: float = 0.0
    semantic_score: float = 0.0
    normalized_lexical_score: float = 0.0
    normalized_semantic_score: float = 0.0
    matched_fields: set[str] = field(default_factory=set)
    matched_modes: set[str] = field(default_factory=set)


@dataclass(slots=True)
class HybridResult:
    rank: int
    score: float
    retrieval_mode: str
    record_id: str
    parent_record_id: str
    chunk_id: str
    chunk_type: str
    matched_modes: list[str]
    matched_fields: list[str]
    lexical_score: float
    semantic_score: float
    normalized_lexical_score: float
    normalized_semantic_score: float
    exact_match_boost: float
    metadata_filter_boost: float
    citation_text: str
    source_urls: dict[str, str]
    deterministic_rank_key: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "score": self.score,
            "hybrid_score": self.score,
            "retrieval_mode": self.retrieval_mode,
            "record_id": self.record_id,
            "parent_record_id": self.parent_record_id,
            "chunk_id": self.chunk_id,
            "chunk_type": self.chunk_type,
            "matched_modes": self.matched_modes,
            "matched_fields": self.matched_fields,
            "lexical_score": self.lexical_score,
            "semantic_score": self.semantic_score,
            "normalized_lexical_score": self.normalized_lexical_score,
            "normalized_semantic_score": self.normalized_semantic_score,
            "exact_match_boost": self.exact_match_boost,
            "metadata_filter_boost": self.metadata_filter_boost,
            "citation_text": self.citation_text,
            "source_urls": self.source_urls,
            "deterministic_rank_key": self.deterministic_rank_key,
        }


def normalize_scores(results: list[dict], score_key: str = "score") -> dict[str, float]:
    max_score = max((float(result.get(score_key, 0.0)) for result in results), default=0.0)
    if max_score <= 0:
        return {result["record_id"]: 0.0 for result in results}
    return {result["record_id"]: float(result.get(score_key, 0.0)) / max_score for result in results}


def exact_match_boost(query_text: str, filters: dict[str, Any], candidate: HybridCandidate) -> float:
    boost = 0.0
    if candidate.matched_fields & EXACT_MATCH_FIELDS:
        boost += 0.25
    if filters.get("song_no") and str(filters["song_no"]) in candidate.record_id:
        boost += 0.20
    if filters.get("hymn_id") and str(filters["hymn_id"]) in candidate.record_id:
        boost += 0.15
    if candidate.record_id and candidate.record_id in query_text:
        boost += 0.25
    if candidate.chunk_id and candidate.chunk_id in query_text:
        boost += 0.25
    for field in sorted(candidate.matched_fields & TEXT_MATCH_FIELDS):
        boost += 0.05
    return boost


def metadata_filter_boost(filters: dict[str, Any], candidate: HybridCandidate) -> float:
    if not filters:
        return 0.0
    metadata_hits = [field for field in candidate.matched_fields if field.startswith("metadata_filter:")]
    return min(0.20, 0.05 * (len(metadata_hits) or len(filters)))


def hybrid_score(
    candidate: HybridCandidate,
    query_text: str,
    filters: dict[str, Any],
    lexical_weight: float = DEFAULT_LEXICAL_WEIGHT,
    semantic_weight: float = DEFAULT_SEMANTIC_WEIGHT,
) -> tuple[float, float, float]:
    exact_boost = exact_match_boost(query_text, filters, candidate)
    metadata_boost = metadata_filter_boost(filters, candidate)
    score = (
        lexical_weight * candidate.normalized_lexical_score
        + semantic_weight * candidate.normalized_semantic_score
        + exact_boost
        + metadata_boost
    )
    return score, exact_boost, metadata_boost


class HybridRetriever:
    def __init__(
        self,
        lexical_retriever: LexicalRetriever | None = None,
        semantic_retriever: SemanticRetriever | None = None,
        lexical_weight: float = DEFAULT_LEXICAL_WEIGHT,
        semantic_weight: float = DEFAULT_SEMANTIC_WEIGHT,
    ) -> None:
        if lexical_weight < 0 or semantic_weight < 0:
            raise ValueError("hybrid weights must be non-negative")
        if lexical_weight == 0 and semantic_weight == 0:
            raise ValueError("at least one hybrid weight must be positive")
        self.lexical_retriever = lexical_retriever or LexicalRetriever()
        self.semantic_retriever = semantic_retriever or SemanticRetriever()
        self.lexical_weight = lexical_weight
        self.semantic_weight = semantic_weight

    def search(self, query_text: str, filters: dict[str, Any] | None = None, top_k: int = 10) -> list[dict[str, Any]]:
        filters = filters or {}
        candidate_k = max(top_k * DEFAULT_CANDIDATE_MULTIPLIER, top_k)
        lexical_results = self.lexical_retriever.search(query_text, filters=filters, top_k=candidate_k)
        semantic_results = self.semantic_retriever.search(query_text, filters=filters, top_k=candidate_k)
        candidates = merge_candidates(lexical_results, semantic_results)
        lexical_norm = normalize_scores(lexical_results)
        semantic_norm = normalize_scores(semantic_results)

        scored = []
        for candidate in candidates.values():
            candidate.normalized_lexical_score = lexical_norm.get(candidate.record_id, 0.0)
            candidate.normalized_semantic_score = semantic_norm.get(candidate.record_id, 0.0)
            score, exact_boost, metadata_boost = hybrid_score(
                candidate,
                query_text=query_text,
                filters=filters,
                lexical_weight=self.lexical_weight,
                semantic_weight=self.semantic_weight,
            )
            scored.append((score, exact_boost, metadata_boost, candidate))
        scored.sort(key=lambda item: (-item[0], item[3].deterministic_rank_key, item[3].record_id, item[3].chunk_id))

        return [
            HybridResult(
                rank=rank,
                score=round(float(score), 8),
                retrieval_mode="hybrid",
                record_id=candidate.record_id,
                parent_record_id=candidate.record_id,
                chunk_id=candidate.chunk_id,
                chunk_type=candidate.chunk_type,
                matched_modes=matched_modes_label(candidate),
                matched_fields=sorted(candidate.matched_fields),
                lexical_score=candidate.lexical_score,
                semantic_score=candidate.semantic_score,
                normalized_lexical_score=round(candidate.normalized_lexical_score, 8),
                normalized_semantic_score=round(candidate.normalized_semantic_score, 8),
                exact_match_boost=round(exact_boost, 8),
                metadata_filter_boost=round(metadata_boost, 8),
                citation_text=candidate.citation_text,
                source_urls=candidate.source_urls,
                deterministic_rank_key=candidate.deterministic_rank_key,
            ).to_dict()
            for rank, (score, exact_boost, metadata_boost, candidate) in enumerate(scored[:top_k], start=1)
        ]


def matched_modes_label(candidate: HybridCandidate) -> list[str]:
    if candidate.matched_modes == {"lexical", "semantic"}:
        return ["both"]
    return sorted(candidate.matched_modes)


def candidate_from_result(result: dict, mode: str) -> HybridCandidate:
    record_id = result.get("record_id") or result.get("parent_record_id")
    return HybridCandidate(
        record_id=record_id,
        chunk_id=result.get("chunk_id") or "",
        chunk_type=result.get("chunk_type") or "",
        citation_text=result.get("citation_text") or "",
        source_urls=result.get("source_urls") or {},
        deterministic_rank_key=result.get("deterministic_rank_key") or record_id,
        lexical_score=float(result.get("score", 0.0)) if mode == "lexical" else 0.0,
        semantic_score=float(result.get("similarity_score", result.get("score", 0.0))) if mode == "semantic" else 0.0,
        matched_fields=set(result.get("matched_fields", [])),
        matched_modes={mode},
    )


def merge_candidates(lexical_results: list[dict], semantic_results: list[dict]) -> dict[str, HybridCandidate]:
    candidates: dict[str, HybridCandidate] = {}
    for mode, results in [("lexical", lexical_results), ("semantic", semantic_results)]:
        for result in results:
            record_id = result.get("record_id") or result.get("parent_record_id")
            if record_id not in candidates:
                candidates[record_id] = candidate_from_result(result, mode)
                continue
            candidate = candidates[record_id]
            candidate.matched_modes.add(mode)
            candidate.matched_fields.update(result.get("matched_fields", []))
            if mode == "lexical":
                candidate.lexical_score = max(candidate.lexical_score, float(result.get("score", 0.0)))
            else:
                candidate.semantic_score = max(candidate.semantic_score, float(result.get("similarity_score", result.get("score", 0.0))))
            if mode == "lexical" and result.get("chunk_id"):
                candidate.chunk_id = result["chunk_id"]
                candidate.chunk_type = result.get("chunk_type") or candidate.chunk_type
            if not candidate.citation_text:
                candidate.citation_text = result.get("citation_text") or ""
            if not candidate.source_urls:
                candidate.source_urls = result.get("source_urls") or {}
            candidate.deterministic_rank_key = min(candidate.deterministic_rank_key, result.get("deterministic_rank_key", candidate.deterministic_rank_key))
    return candidates


def parse_filter(values: list[str]) -> dict[str, str]:
    filters = {}
    for value in values:
        if "=" in value:
            key, raw = value.split("=", 1)
            filters[key] = raw
    return filters


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic hybrid retrieval")
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--filter", action="append", default=[])
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--lexical-weight", type=float, default=DEFAULT_LEXICAL_WEIGHT)
    parser.add_argument("--semantic-weight", type=float, default=DEFAULT_SEMANTIC_WEIGHT)
    args = parser.parse_args(argv)
    retriever = HybridRetriever(lexical_weight=args.lexical_weight, semantic_weight=args.semantic_weight)
    results = retriever.search(args.query, filters=parse_filter(args.filter), top_k=args.top_k)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
