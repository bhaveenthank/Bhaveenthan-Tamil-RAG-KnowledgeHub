from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ParseContext:
    category_id: str
    category_tamil: str
    parser_family: str
    book_id: str
    work_id: str
    pilot_id: str


def normalized_text(value: Any) -> str:
    return unicodedata.normalize("NFC", str(value or "")).strip()


def deterministic_record_id(context: ParseContext, source: Mapping[str, Any]) -> str:
    native_id = normalized_text(
        source.get("record_id")
        or source.get("source_record_id")
        or source.get("song_no")
        or source.get("entry_headword")
    )
    source_url = normalized_text(source.get("source_url") or source.get("hymn_url"))
    content = normalized_text(
        source.get("content_text")
        or source.get("verse_text")
        or source.get("definition")
        or source.get("title")
    )
    identity = json.dumps(
        [context.category_id, context.book_id, context.work_id, native_id, source_url, content],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]
    return f"tvu_{context.category_id}_{digest}"


class BaseParser:
    parser_family = "base_parser"
    record_type = "prose_section"

    def parse(self, source: Mapping[str, Any], context: ParseContext) -> list[dict[str, Any]]:
        """Map one inspected source unit to schema v2.

        TODO: parser-family modules should replace this conservative mapping only
        after category-specific HTML fixtures and hierarchy rules are approved.
        """
        verse_text = normalized_text(source.get("verse_text"))
        content_text = normalized_text(
            source.get("content_text")
            or verse_text
            or source.get("definition")
            or source.get("title")
        )
        commentary_text = normalized_text(
            source.get("commentary_text")
            or " ".join(
                part
                for part in (
                    normalized_text(source.get("pozhppurai")),
                    normalized_text(source.get("kurippurai")),
                )
                if part
            )
        )
        source_metadata = dict(source.get("source_metadata") or source.get("metadata") or {})
        source_metadata.update(
            {
                "parser_family": context.parser_family,
                "pilot_id": context.pilot_id,
                "pilot_scope": True,
                "source_record_id": normalized_text(source.get("record_id")),
            }
        )
        record = {
            "schema_version": "website-corpus-v2",
            "record_id": deterministic_record_id(context, source),
            "record_type": normalized_text(source.get("record_type")) or self.record_type,
            "category_id": context.category_id,
            "collection_id": normalized_text(source.get("collection_id") or source.get("collection")),
            "book_id": context.book_id,
            "work_id": context.work_id,
            "corpus_id": normalized_text(source.get("corpus_id")),
            "title": normalized_text(source.get("title") or source.get("canonical_title")),
            "author": normalized_text(source.get("author")),
            "language": normalized_text(source.get("language")) or "ta",
            "genre": normalized_text(source.get("genre")),
            "period": normalized_text(source.get("period")),
            "section_id": normalized_text(source.get("section_id")),
            "chapter_id": normalized_text(source.get("chapter_id")),
            "page_no": normalized_text(source.get("page_no")),
            "content_text": content_text,
            "commentary_text": commentary_text,
            "source_url": normalized_text(source.get("source_url") or source.get("hymn_url")),
            "commentary_url": normalized_text(source.get("commentary_url")),
            "image_url": normalized_text(source.get("image_url")),
            "pdf_url": normalized_text(source.get("pdf_url")),
            "source_metadata": source_metadata,
            "parser_family": context.parser_family,
        }
        for field in (
            "hymn_id",
            "pathigam_id",
            "song_no",
            "verse_no",
            "verse_text",
            "pozhppurai",
            "kurippurai",
            "entry_headword",
        ):
            if field in source:
                record[field] = normalized_text(source.get(field))
        return [record]


def parser_for_family(parser_family: str) -> BaseParser:
    from .dictionary_parser import DictionaryParser
    from .external_link_registry import ExternalLinkRegistryParser
    from .grammar_parser import GrammarParser
    from .image_metadata_parser import ImageMetadataParser
    from .mixed_parser import MixedParser
    from .prose_parser import ProseParser
    from .table_parser import TableParser
    from .verse_parser import VerseParser

    parsers = {
        parser.parser_family: parser
        for parser in (
            VerseParser(),
            ProseParser(),
            GrammarParser(),
            DictionaryParser(),
            TableParser(),
            ImageMetadataParser(),
            MixedParser(),
            ExternalLinkRegistryParser(),
        )
    }
    if parser_family not in parsers:
        raise ValueError(f"unsupported parser family: {parser_family}")
    return parsers[parser_family]
