from __future__ import annotations

import re
from typing import Any, Mapping
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .base_parser import BaseParser, ParseContext, normalized_text


class VerseParser(BaseParser):
    parser_family = "verse_parser"
    record_type = "verse"

    HEADING_PATTERN = re.compile(r"^(\d+)\s*\.\s*(.+)$")

    @staticmethod
    def split_colophon(value: str) -> tuple[str, str]:
        colophon = normalized_text(value)
        for separator in (".-", ".–", " - ", "–"):
            if separator in colophon:
                situation, author = colophon.rsplit(separator, 1)
                return normalized_text(situation), normalized_text(author)
        return colophon, ""

    def parse_html(
        self, html: str, source: Mapping[str, Any], context: ParseContext
    ) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        records: list[dict[str, Any]] = []
        source_url = str(source.get("source_url") or "")
        source_subid = parse_qs(urlparse(source_url).query).get("subid", [""])[0]
        for heading in soup.select("div.subhead"):
            match = self.HEADING_PATTERN.match(normalized_text(heading.get_text(" ", strip=True)))
            if not match:
                continue
            poem_no, thinai = match.groups()
            heading_table = heading.find_parent("table")
            verse_table = heading_table.find_next_sibling("table") if heading_table else None
            if verse_table is None:
                continue
            lines = [
                normalized_text(div.get_text(" ", strip=True))
                for div in verse_table.select("div.poem")
                if normalized_text(div.get_text(" ", strip=True))
            ]
            verse_text = "\n".join(lines)
            if not verse_text:
                continue
            urai_link = verse_table.find(
                "a", string=lambda value: normalized_text(value) == "உரை"
            )
            commentary_url = (
                urljoin(source_url, urai_link.get("href", ""))
                if urai_link
                else ""
            )
            footer = verse_table.find_next_sibling("div", class_="footer")
            colophon_table = footer.find_next_sibling("table") if footer else None
            colophon_div = (
                colophon_table.select_one("div.poem") if colophon_table else None
            )
            colophon = normalized_text(
                colophon_div.get_text(" ", strip=True) if colophon_div else ""
            )
            thurai, author = self.split_colophon(colophon)
            structured = {
                "record_id": f"natrinai:{poem_no}",
                "record_type": self.record_type,
                "title": f"நற்றிணை {poem_no}. {thinai}",
                "author": author,
                "genre": "சங்க இலக்கியம்",
                "verse_no": poem_no,
                "poem_no": poem_no,
                "song_no": poem_no,
                "thinai": normalized_text(thinai),
                "thurai": thurai,
                "colophon": colophon,
                "verse_text": verse_text,
                "content_text": verse_text,
                "source_url": source_url,
                "commentary_url": commentary_url,
                "source_record_id": f"natrinai:{poem_no}",
                "source_metadata": {
                    "fixture_path": source.get("fixture_path", ""),
                    "fixture_page_type": source.get("page_type", ""),
                    "original_sha256": source.get("original_sha256", ""),
                    "source_work": source.get("source_work", ""),
                    "source_subid": source_subid,
                    "citation_text": f"நற்றிணை {poem_no}",
                },
            }
            record = super().parse(structured, context)[0]
            for field in ("poem_no", "thinai", "thurai", "colophon"):
                record[field] = normalized_text(structured[field])
            records.append(record)
        return records

    def parse(
        self, source: Mapping[str, Any], context: ParseContext
    ) -> list[dict[str, Any]]:
        html = source.get("html_content")
        if html:
            return self.parse_html(str(html), source, context)
        return super().parse(source, context)
