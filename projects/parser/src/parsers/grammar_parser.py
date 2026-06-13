from __future__ import annotations

import re
from typing import Any, Mapping
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .base_parser import BaseParser, ParseContext, normalized_text


class GrammarParser(BaseParser):
    parser_family = "grammar_parser"
    record_type = "grammar_rule"

    RULE_NO_PATTERN = re.compile(r"^(\d+)\.?$")
    URI_PATTERN = re.compile(r"['\"]([^'\"]*l0900uri\.jsp\?[^'\"]+)['\"]")

    def parse_html(
        self, html: str, source: Mapping[str, Any], context: ParseContext
    ) -> list[dict[str, Any]]:
        soup = BeautifulSoup(html, "lxml")
        source_url = str(source.get("source_url") or "")
        subid = parse_qs(urlparse(source_url).query).get("subid", [""])[0]
        records: list[dict[str, Any]] = []
        for row in soup.find_all("tr"):
            cells = row.find_all("td", recursive=False)
            if len(cells) < 2:
                continue
            match = self.RULE_NO_PATTERN.match(
                normalized_text(cells[0].get_text(" ", strip=True))
            )
            rule_cell = cells[1]
            if not match or "poem" not in (rule_cell.get("class") or []):
                continue
            rule_no = match.group(1)
            rule_lines = [
                normalized_text(part)
                for part in rule_cell.get_text("\n", strip=True).splitlines()
                if normalized_text(part)
            ]
            rule_text = "\n".join(rule_lines)
            if not rule_text:
                continue
            urai_link = row.find(
                "a", string=lambda value: normalized_text(value) == "உரை"
            )
            commentary_url = ""
            if urai_link:
                target = self.URI_PATTERN.search(str(urai_link.get("onclick") or ""))
                if target:
                    commentary_url = urljoin(source_url, target.group(1))
            structured = {
                "record_id": f"nannul:{rule_no}",
                "record_type": self.record_type,
                "title": f"நன்னூல் நூற்பா {rule_no}",
                "author": "பவணந்தி முனிவர்",
                "genre": "இலக்கணம்",
                "section_id": normalized_text(source.get("section_title")),
                "chapter_id": normalized_text(source.get("chapter_title")),
                "rule_no": rule_no,
                "rule_text": rule_text,
                "explanation_text": "",
                "content_text": rule_text,
                "commentary_url": commentary_url,
                "source_url": source_url,
                "source_record_id": f"nannul:{rule_no}",
                "source_metadata": {
                    "fixture_path": source.get("fixture_path", ""),
                    "fixture_page_type": source.get("page_type", ""),
                    "original_sha256": source.get("original_sha256", ""),
                    "source_work": source.get("source_work", ""),
                    "source_subid": subid,
                    "subsection_title": source.get("subsection_title", ""),
                    "explanation_source": "not_collected_in_three_page_pilot",
                    "citation_text": f"நன்னூல், எழுத்து இயல், நூற்பா {rule_no}",
                },
            }
            record = super().parse(structured, context)[0]
            for field in ("rule_no", "rule_text", "explanation_text"):
                record[field] = normalized_text(structured[field])
            records.append(record)
        return records

    def parse(
        self, source: Mapping[str, Any], context: ParseContext
    ) -> list[dict[str, Any]]:
        html = source.get("html_content")
        if html:
            return self.parse_html(str(html), source, context)
        record = super().parse(source, context)[0]
        record["rule_no"] = normalized_text(source.get("rule_no"))
        record["rule_text"] = normalized_text(
            source.get("rule_text") or source.get("content_text")
        )
        record["explanation_text"] = normalized_text(source.get("explanation_text"))
        return [record]
