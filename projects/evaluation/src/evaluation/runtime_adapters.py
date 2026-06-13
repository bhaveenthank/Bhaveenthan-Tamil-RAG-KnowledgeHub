from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

DEFAULT_LEXICAL_WEIGHT = 0.65
DEFAULT_SEMANTIC_WEIGHT = 0.35
DEFAULT_VECTOR_MANIFEST = Path(
    "data/processed/vector_index/irandaam_thirumurai/vector_index_manifest.json"
)


def _attr(module_name: str, attr_name: str) -> Any:
    return getattr(import_module(module_name), attr_name)


class LexicalRetriever:
    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        return _attr("retrieval.lexical_retriever", "LexicalRetriever")(*args, **kwargs)


class SemanticRetriever:
    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        return _attr("retrieval.semantic_retriever", "SemanticRetriever")(*args, **kwargs)


class HybridRetriever:
    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        return _attr("retrieval.hybrid_retriever", "HybridRetriever")(*args, **kwargs)


class QueryExpander:
    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        return _attr("retrieval.query_expander", "QueryExpander")(*args, **kwargs)


class ParseContext:
    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        return _attr("parsers.base_parser", "ParseContext")(*args, **kwargs)


class DictionaryParser:
    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        return _attr("parsers.dictionary_parser", "DictionaryParser")(*args, **kwargs)


class GrammarParser:
    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        return _attr("parsers.grammar_parser", "GrammarParser")(*args, **kwargs)


class ProseParser:
    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        return _attr("parsers.prose_parser", "ProseParser")(*args, **kwargs)


class VerseParser:
    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        return _attr("parsers.verse_parser", "VerseParser")(*args, **kwargs)


def parser_for_family(parser_family: str) -> Any:
    return _attr("parsers.base_parser", "parser_for_family")(parser_family)


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    return _attr("corpus.normalize_category_corpus", "normalize_record")(record)


def validate_records(records: list[dict[str, Any]], category_id: str) -> dict[str, Any]:
    return _attr("corpus.validate_category_corpus", "validate_records")(records, category_id)


def required_fields() -> dict[str, type]:
    return _attr("corpus.validate_category_corpus", "REQUIRED_FIELDS")


def retrieve_analytical(query: str, top_n: int = 10) -> dict[str, Any]:
    return _attr("analytics.analytical_retriever", "retrieve_analytical")(query, top_n=top_n)


def analyze_term(
    term: str,
    *,
    expand_query: bool = False,
    group_by: str = "category",
    top_n: int = 10,
) -> dict[str, Any]:
    return _attr("analytics.analyze_term", "analyze_term")(
        term,
        expand_query=expand_query,
        group_by=group_by,
        top_n=top_n,
    )


def search_occurrences(
    term: str,
    *,
    expand_query: bool = False,
    limit: int = 10,
) -> dict[str, Any]:
    return _attr("analytics.search_occurrences", "search_occurrences")(
        term,
        expand_query=expand_query,
        limit=limit,
    )
