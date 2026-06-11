from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from .base_parser import BaseParser, ParseContext, normalized_text


class ProseParser(BaseParser):
    parser_family = "prose_parser"
    record_type = "prose_section"

    def parse_html(
        self, html: str, source: Mapping[str, Any], context: ParseContext
    ) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        source_url = normalized_text(source.get("source_url"))
        link_id = parse_qs(urlparse(source_url).query).get("linkid", [""])[0]
        records: list[dict[str, Any]] = []
        for container in soup.select("[data-prose-section], .prose-section"):
            title_node = container.select_one(
                "[data-section-title], .section-title, h1, h2, h3"
            )
            title = normalized_text(
                title_node.get_text(" ", strip=True) if title_node else source.get("title")
            )
            section_id = normalized_text(
                container.get("data-section-id")
                or source.get("section_id")
                or link_id
            )
            paragraphs = [
                normalized_text(node.get_text(" ", strip=True))
                for node in container.select("p[data-prose-paragraph], p.prose-paragraph")
            ]
            paragraphs = [paragraph for paragraph in paragraphs if paragraph]
            for paragraph_index, content_text in enumerate(paragraphs, start=1):
                paragraph_id = f"{section_id}:p{paragraph_index:03d}"
                structured = {
                    "record_id": paragraph_id,
                    "record_type": self.record_type,
                    "title": title,
                    "author": source.get("author", ""),
                    "genre": source.get("genre", "உரைநடை"),
                    "period": source.get("period", "இருபதாம் நூற்றாண்டு"),
                    "chapter_id": source.get("chapter_id", ""),
                    "section_id": paragraph_id,
                    "content_text": content_text,
                    "source_url": source_url,
                    "source_record_id": paragraph_id,
                    "source_metadata": {
                        "fixture_path": source.get("fixture_path", ""),
                        "fixture_page_type": source.get("page_type", ""),
                        "original_sha256": source.get("original_sha256", ""),
                        "source_work": source.get("source_work", ""),
                        "source_link_id": link_id,
                        "section_source_id": section_id,
                        "paragraph_index": paragraph_index,
                        "fixture_content_status": source.get(
                            "fixture_content_status", ""
                        ),
                        "rights_status": source.get("rights_status", ""),
                        "citation_text": f"{source.get('source_work', '')}, {title}, பத்தி {paragraph_index}",
                    },
                }
                records.append(super().parse(structured, context)[0])
        return records

    def parse(
        self, source: Mapping[str, Any], context: ParseContext
    ) -> list[dict[str, Any]]:
        html = source.get("html_content")
        if html:
            return self.parse_html(str(html), source, context)
        return super().parse(source, context)
