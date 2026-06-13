from __future__ import annotations

from typing import Any, Mapping

from bs4 import BeautifulSoup

from .base_parser import BaseParser, ParseContext, normalized_text


class DictionaryParser(BaseParser):
    parser_family = "dictionary_parser"
    record_type = "dictionary_entry"

    HEADWORD_LABELS = {"சொல்", "தலைச்சொல்", "headword"}
    DEFINITION_LABELS = {"அருஞ்சொற்பொருள்", "பொருள்", "definition"}
    POS_LABELS = {"சொல்வகை", "இலக்கணக்குறிப்பு", "part of speech", "pos"}

    @staticmethod
    def _column(headers: list[str], labels: set[str]) -> int | None:
        for index, header in enumerate(headers):
            if header.casefold() in {label.casefold() for label in labels}:
                return index
        return None

    def parse_html(
        self, html: str, source: Mapping[str, Any], context: ParseContext
    ) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        records: list[dict[str, Any]] = []
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            if not rows:
                continue
            headers = [
                normalized_text(cell.get_text(" ", strip=True))
                for cell in rows[0].find_all(["th", "td"])
            ]
            headword_index = self._column(headers, self.HEADWORD_LABELS)
            definition_index = self._column(headers, self.DEFINITION_LABELS)
            pos_index = self._column(headers, self.POS_LABELS)
            if headword_index is None or definition_index is None:
                continue
            for row_index, row in enumerate(rows[1:], start=1):
                cells = [
                    normalized_text(cell.get_text(" ", strip=True))
                    for cell in row.find_all(["th", "td"])
                ]
                if max(headword_index, definition_index) >= len(cells):
                    continue
                headword = cells[headword_index]
                definition = cells[definition_index]
                if not headword or not definition:
                    continue
                part_of_speech = (
                    cells[pos_index] if pos_index is not None and pos_index < len(cells) else ""
                )
                structured = {
                    "record_id": f"{source.get('page_type', 'entry')}:{row_index}:{headword}",
                    "record_type": self.record_type,
                    "entry_headword": headword,
                    "definition": definition,
                    "part_of_speech": part_of_speech,
                    "content_text": definition,
                    "title": headword,
                    "source_url": source.get("source_url", ""),
                    "source_record_id": f"{source.get('page_type', 'entry')}:{row_index}:{headword}",
                    "source_metadata": {
                        "fixture_path": source.get("fixture_path", ""),
                        "fixture_page_type": source.get("page_type", ""),
                        "original_sha256": source.get("original_sha256", ""),
                        "source_work": source.get("source_work", ""),
                        "part_of_speech_source": (
                            "explicit" if part_of_speech else "not_provided"
                        ),
                    },
                }
                record = super().parse(structured, context)[0]
                record["entry_headword"] = headword
                record["definition"] = definition
                record["part_of_speech"] = part_of_speech
                records.append(record)
        return records

    def parse(
        self, source: Mapping[str, Any], context: ParseContext
    ) -> list[dict[str, Any]]:
        html = source.get("html_content")
        if html:
            return self.parse_html(str(html), source, context)
        record = super().parse(source, context)[0]
        record["definition"] = normalized_text(
            source.get("definition") or source.get("content_text")
        )
        record["part_of_speech"] = normalized_text(source.get("part_of_speech"))
        return [record]
