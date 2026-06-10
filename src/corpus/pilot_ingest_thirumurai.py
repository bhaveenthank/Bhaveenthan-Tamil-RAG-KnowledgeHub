from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qsl, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from inspector.site_inspector import fetch_html, save_snapshot, snapshot_filename
from scraper.irandaam_thirumurai_builder import split_hymn_title, text_statistics
from scraper.pilot_hymn_scraper import COMMENTARY_URL_RE, normalize_text

PILOT_CONFIGS = {
    4: {
        "corpus_id": "thirumurai_04",
        "canonical_title": "Naangaam Thirumurai",
        "title": "Naangaam Thirumurai",
        "author": "Tirunavukkarasar (Appar)",
        "nayanmar": "Tirunavukkarasar",
        "left_frame_url": "https://www.tamilvu.org/slet/l4140/l4140lft.jsp",
        "hymn_path_fragment": "l4130son.jsp",
        "commentary_path_fragment": "l4140uri.jsp",
        "pilot_hymn_limit": 5,
    }
}
SECTION_LABEL_RE = re.compile(
    r"(?m)^\s*(?:\d+\.\s*)?(பொழிப்புரை|பொ-ரை|குறிப்புரை|கு-ரை|பொருள்|விளக்கம்|குறிப்பு)\s*(?::|;|\s*$)"
)


@dataclass(slots=True)
class PilotHymn:
    hymn_id: str
    title: str
    url: str
    place: str
    note: str
    pann: str


def query_params(url: str) -> dict[str, str]:
    return dict(parse_qsl(urlparse(url).query, keep_blank_values=True))


def snapshot(url: str, directory: Path, timeout: int, resume: bool) -> str:
    path = directory / snapshot_filename(url)
    if resume and path.exists():
        return path.read_text(encoding="utf-8")
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            html = fetch_html(url, timeout=timeout)
            save_snapshot(url, html, directory)
            return html
        except Exception as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(attempt * 2)
    raise RuntimeError(f"failed after 3 attempts: {last_error}")


def extract_hymn_links(config: dict, html: str) -> list[PilotHymn]:
    soup = BeautifulSoup(html, "lxml")
    links: list[PilotHymn] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if config["hymn_path_fragment"] not in href:
            continue
        url = urljoin(config["left_frame_url"], href)
        hymn_id = query_params(url).get("subid", "")
        if not hymn_id or url in seen:
            continue
        seen.add(url)
        title = normalize_text(anchor.get_text(" ", strip=True))
        place, note, pann = split_hymn_title(title)
        links.append(PilotHymn(hymn_id, title, url, place, note, pann))
    return links


def commentary_url(source_url: str, outer_row: Tag) -> str:
    anchor = outer_row.find("a", onclick=True)
    if not anchor:
        return ""
    match = COMMENTARY_URL_RE.search(anchor.get("onclick", ""))
    return urljoin(source_url, match.group(1)) if match else ""


def parse_pilot_hymn(source_url: str, html: str) -> tuple[str, list[dict]]:
    soup = BeautifulSoup(html, "lxml")
    heading = soup.select_one("td.subhead")
    title = normalize_text(heading.get_text(" ", strip=True)) if heading else ""
    verses: list[dict] = []
    for number_cell in soup.select("td.pno"):
        row = number_cell.find_parent("tr")
        cells = row.find_all("td", recursive=False) if row else []
        if len(cells) < 2:
            continue
        song_no = normalize_text(number_cell.get_text(" ", strip=True)).rstrip(".")
        if not song_no.isdigit():
            continue
        verse_lines = [
            normalize_text(line)
            for line in cells[1].get_text("\n", strip=True).splitlines()
            if normalize_text(line)
        ]
        outer_poem = number_cell.find_parent("td", class_="poem")
        outer_row = outer_poem.find_parent("tr") if outer_poem else None
        uri = commentary_url(source_url, outer_row) if outer_row else ""
        if not uri:
            continue
        params = query_params(uri)
        if song_no and verse_lines:
            verses.append(
                {
                    "song_no": params.get("song_no", song_no),
                    "verse_text": "\n".join(verse_lines),
                    "commentary_url": uri,
                    "source_parameters": params,
                }
            )
    return title, verses


def split_pilot_commentary(html: str) -> tuple[str, str, str, list[str]]:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = "\n".join(
        normalize_text(line)
        for line in soup.get_text("\n", strip=True).splitlines()
        if normalize_text(line)
    )
    if "Try error :java.lang.NullPointerException" in text:
        return "", "", "source_error", ["source_null_pointer_error"]
    matches = list(SECTION_LABEL_RE.finditer(text))
    sections: dict[str, list[str]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sections.setdefault(match.group(1), []).append(normalize_text(text[match.end():end]))
    pozh = " ".join(sections.get("பொழிப்புரை", []) + sections.get("பொ-ரை", [])).strip()
    notes = []
    for label in ("குறிப்புரை", "கு-ரை", "பொருள்", "விளக்கம்", "குறிப்பு"):
        notes.extend(sections.get(label, []))
    kuri = "\n\n".join(part for part in notes if part).strip()
    warnings = []
    if not pozh:
        warnings.append("missing_pozhppurai")
    if not kuri:
        warnings.append("missing_kurippurai")
    status = "success" if pozh and kuri else "partial_commentary"
    return pozh, kuri, status, warnings


def build_record(config: dict, hymn: PilotHymn, title: str, verse: dict, index: int, commentary: tuple) -> dict:
    pozh, kuri, status, warnings = commentary
    return {
        "record_type": "verse_with_commentary",
        "source": "TamilVU",
        "source_site": "https://www.tamilvu.org",
        "language": "ta",
        "domain": "Tamil literature",
        "genre": "Devotional poetry",
        "religious_tradition": "Saivam",
        "collection": "Thevaram",
        "work": "Panniru Thirumurai",
        "thirumurai": config["title"],
        "thirumurai_number": 4,
        "author": config["author"],
        "nayanmar": config["nayanmar"],
        "hymn_id": hymn.hymn_id,
        "hymn_title": title or hymn.title,
        "hymn_location": hymn.place,
        "hymn_note": hymn.note,
        "pann": hymn.pann,
        "song_no": verse["song_no"],
        "verse_index_in_hymn": index,
        "verse_text": verse["verse_text"],
        "commentary_available": bool(verse["commentary_url"]),
        "pozhppurai": pozh,
        "kurippurai": kuri,
        "hymn_url": hymn.url,
        "commentary_url": verse["commentary_url"],
        "source_parameters": verse["source_parameters"],
        "text_statistics": text_statistics(verse["verse_text"], pozh, kuri),
        "extraction_metadata": {
            "extractor": "pilot_ingest_thirumurai",
            "extractor_version": "0.1",
            "fetched_at": datetime.now(UTC).isoformat(),
            "extraction_status": status,
            "warnings": warnings,
            "pilot_scope": True,
        },
    }


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def ingest(thirumurai_no: int, delay: float, timeout: int, resume: bool, base_dir: Path) -> tuple[list[dict], dict]:
    if thirumurai_no not in PILOT_CONFIGS:
        raise ValueError("controlled pilot supports only thirumurai_no=4")
    config = PILOT_CONFIGS[thirumurai_no]
    raw_root = base_dir / "data/raw/pilot" / config["corpus_id"]
    processed = base_dir / "data/processed/pilot" / f"{config['corpus_id']}.jsonl"
    nav_html = snapshot(config["left_frame_url"], raw_root / "navigation", timeout, resume)
    discovered = extract_hymn_links(config, nav_html)
    selected = discovered[: config["pilot_hymn_limit"]]
    records: list[dict] = []
    failures: list[dict] = []
    for hymn_index, hymn in enumerate(selected):
        if hymn_index and delay:
            time.sleep(delay)
        try:
            html = snapshot(hymn.url, raw_root / "hymns", timeout, resume)
            title, verses = parse_pilot_hymn(hymn.url, html)
            if not verses:
                raise ValueError("no verses parsed")
            for verse_index, verse in enumerate(verses, start=1):
                if delay:
                    time.sleep(delay)
                if verse["commentary_url"]:
                    uri_html = snapshot(
                        verse["commentary_url"], raw_root / "commentary", timeout, resume
                    )
                    commentary = split_pilot_commentary(uri_html)
                else:
                    commentary = ("", "", "missing_commentary_url", ["missing_commentary_url"])
                records.append(build_record(config, hymn, title, verse, verse_index, commentary))
        except Exception as exc:
            failures.append({"hymn_id": hymn.hymn_id, "url": hymn.url, "error": str(exc)})
    write_jsonl(processed, records)
    summary = {
        "corpus_id": config["corpus_id"],
        "thirumurai_no": thirumurai_no,
        "hymns_discovered": len(discovered),
        "pilot_hymns_selected": len(selected),
        "records_ingested": len(records),
        "failures": failures,
        "output": str(processed),
    }
    (processed.parent / f"{config['corpus_id']}_ingestion_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return records, summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run one bounded multi-Thirumurai pilot ingestion.")
    parser.add_argument("--thirumurai-no", type=int, required=True)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--base-dir", type=Path, default=Path("."))
    args = parser.parse_args(argv)
    try:
        records, summary = ingest(
            args.thirumurai_no, args.delay, args.timeout, args.resume, args.base_dir
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Hymns discovered: {summary['hymns_discovered']}")
    print(f"Pilot hymns selected: {summary['pilot_hymns_selected']}")
    print(f"Records ingested: {len(records)}")
    print(f"Failures: {len(summary['failures'])}")
    print(f"Output: {summary['output']}")
    return 0 if not summary["failures"] and records else 2


if __name__ == "__main__":
    raise SystemExit(main())
