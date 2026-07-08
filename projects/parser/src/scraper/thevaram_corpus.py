from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qsl, urljoin, urlparse

from bs4 import BeautifulSoup, Tag

if __package__ in {None, ""}:
    for parent in Path(__file__).resolve().parents:
        shared_src = parent / "shared/tvu-common/src"
        legacy_src = parent / "src"
        if shared_src.is_dir() and legacy_src.is_dir():
            sys.path.insert(0, str(shared_src))
            sys.path.insert(0, str(legacy_src))
            break
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scraper.pilot_hymn_scraper import COMMENTARY_URL_RE, normalize_text, split_commentary_text
from tvu_common.checksums import sha256_text
from tvu_common.snapshot import USER_AGENT, save_snapshot, snapshot_filename

TAMILVU_HOST = "www.tamilvu.org"
SCHEMA_VERSION = "thevaram-relational-v1"
DEFAULT_BASE_DIR = Path(".")
DEFAULT_OUTPUT_ROOT = Path("data/processed/thevaram")
DEFAULT_RAW_ROOT = Path("data/raw/corpus/thevaram")
DEFAULT_REPORT = Path("reports/thevaram-1-8-ingestion-report.md")


@dataclass(frozen=True, slots=True)
class FetchAttempt:
    name: str
    url: str
    args: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ThirumuraiConfig:
    thirumurai_no: int
    corpus_id: str
    title: str
    author: str
    nayanmar: str
    left_frame_url: str
    hymn_path_fragments: tuple[str, ...]
    verified_navigation: bool = True
    work_id: str = "thevaram"
    work_title: str = "தேவாரம்"


THIRUMURAI_CONFIGS: dict[int, ThirumuraiConfig] = {
    1: ThirumuraiConfig(
        1,
        "thirumurai_01",
        "Mudhalaam Thirumurai",
        "Tirugnanasambandar",
        "Tirugnanasambandar",
        "https://www.tamilvu.org/slet/l4110/l4110lft.jsp",
        ("l4110son.jsp",),
    ),
    2: ThirumuraiConfig(
        2,
        "thirumurai_02",
        "Irandaam Thirumurai",
        "Tirugnanasambandar",
        "Tirugnanasambandar",
        "https://www.tamilvu.org/slet/l4120/l4120lft.jsp",
        ("l4120son.jsp",),
    ),
    3: ThirumuraiConfig(
        3,
        "thirumurai_03",
        "Moondraam Thirumurai",
        "Tirugnanasambandar",
        "Tirugnanasambandar",
        "https://www.tamilvu.org/slet/l4130/l4130lft.jsp",
        ("l4130son.jsp",),
    ),
    4: ThirumuraiConfig(
        4,
        "thirumurai_04",
        "Naangaam Thirumurai",
        "Tirunavukkarasar (Appar)",
        "Tirunavukkarasar",
        "https://www.tamilvu.org/slet/l4140/l4140lft.jsp",
        ("l4130son.jsp",),
    ),
    5: ThirumuraiConfig(
        5,
        "thirumurai_05",
        "Aindhaam Thirumurai",
        "Tirunavukkarasar (Appar)",
        "Tirunavukkarasar",
        "https://www.tamilvu.org/slet/l4150/l4150lft.jsp",
        ("l4150son.jsp",),
    ),
    6: ThirumuraiConfig(
        6,
        "thirumurai_06",
        "Aaraam Thirumurai",
        "Tirunavukkarasar (Appar)",
        "Tirunavukkarasar",
        "https://www.tamilvu.org/slet/l4160/l4160lft.jsp",
        ("l4160son.jsp",),
    ),
    7: ThirumuraiConfig(
        7,
        "thirumurai_07",
        "Ezhaam Thirumurai",
        "Sundarar",
        "Sundarar",
        "https://www.tamilvu.org/slet/l4170/l4170lft.jsp",
        ("l4170son.jsp",),
    ),
    8: ThirumuraiConfig(
        8,
        "thirumurai_08",
        "Ettaam Thirumurai",
        "Manikkavasagar",
        "Manikkavasagar",
        "https://www.tamilvu.org/slet/l4180/l4180lft.jsp",
        ("l4180son.jsp",),
        work_id="tiruvacakam_tirukkovaiyar",
        work_title="திருவாசகம் / திருக்கோவையார்",
    ),
}


@dataclass(slots=True)
class PaadalThogupu:
    thogupu_id: str
    thirumurai_no: int
    ordinal: int
    title: str
    paadapatta_thalam: str
    title_note: str
    pann: str
    source_url: str
    source_subid: str


@dataclass(slots=True)
class Paadal:
    paadal_id: str
    thogupu_id: str
    thirumurai_no: int
    global_song_no: str
    source_song_no: str
    local_song_no: str
    verse_index_in_thogupu: int
    paadal_text: str
    tokenized_paadal: list[str]
    source_url: str
    commentary_url: str
    source_parameters: dict[str, str]


@dataclass(slots=True)
class Commentary:
    commentary_id: str
    paadal_id: str
    kurippurai: str
    pozhppurai: str
    extraction_status: str
    warnings: list[str]


@dataclass(slots=True)
class TextSpan:
    span_id: str
    parent_id: str
    field_name: str
    span_type: str
    start_char: int
    end_char: int
    text: str
    metadata: dict[str, str]


def parse_range(value: str) -> list[int]:
    selected: list[int] = []
    for part in value.split(","):
        item = part.strip()
        if not item:
            continue
        if "-" in item:
            start, end = item.split("-", 1)
            selected.extend(range(int(start), int(end) + 1))
        else:
            selected.append(int(item))
    unknown = [item for item in selected if item not in THIRUMURAI_CONFIGS]
    if unknown:
        raise ValueError(f"unsupported thirumurai numbers: {unknown}")
    return sorted(dict.fromkeys(selected))


def query_params(url: str) -> dict[str, str]:
    return dict(parse_qsl(urlparse(url).query, keep_blank_values=True))


def internal_tamilvu_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc in {"", TAMILVU_HOST}


def split_title(title: str) -> tuple[str, str, str]:
    parts = [part.strip() for part in re.split(r"\s+-\s+", title) if part.strip()]
    if len(parts) >= 3:
        return parts[0], " - ".join(parts[1:-1]), parts[-1]
    if len(parts) == 2:
        return parts[0], "", parts[1]
    return title.strip(), "", ""


def tokenize_tamil_text(text: str) -> list[str]:
    return [token for token in re.split(r"[\s,.;:!?()\[\]{}\"'“”‘’\-]+", text) if token]


def stable_id(*parts: object) -> str:
    raw = "|".join(str(part) for part in parts)
    return sha256_text(raw)[:16]


def fetch_or_read(
    session,
    url: str,
    raw_dir: Path,
    timeout: int,
    resume: bool,
    retries: int = 0,
    fetch_missing: bool = True,
) -> str:
    path = raw_dir / snapshot_filename(url)
    if resume and path.exists():
        return path.read_text(encoding="utf-8")
    if not fetch_missing:
        raise FileNotFoundError(f"missing cached raw snapshot: {url}")
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            result = subprocess.run(
                [
                    "curl",
                    "--fail",
                    "--location",
                    "--silent",
                    "--show-error",
                    "--connect-timeout",
                    str(min(10, timeout)),
                    "--max-time",
                    str(timeout),
                    "--user-agent",
                    USER_AGENT,
                    url,
                ],
                check=True,
                capture_output=True,
                timeout=timeout + 1,
            )
            html = result.stdout.decode("utf-8", errors="replace")
            if not html.strip():
                raise ValueError(f"empty response body: {url}")
            save_snapshot(url, html, raw_dir)
            return html
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.decode("utf-8", errors="replace").strip()
            last_error = RuntimeError(message or f"curl failed with exit code {exc.returncode}: {url}")
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1 + attempt)
    assert last_error is not None
    raise last_error


def slet_referer(url: str) -> str:
    parsed = urlparse(url)
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "slet":
        module = parts[1]
        return f"https://{TAMILVU_HOST}/slet/{module}/{module}lft.jsp"
    return f"https://{TAMILVU_HOST}/"


def http_variant(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme == "https" and parsed.netloc == TAMILVU_HOST:
        return parsed._replace(scheme="http").geturl()
    return url


def fetch_attempts(url: str) -> list[FetchAttempt]:
    referer = slet_referer(url)
    browser_ua = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
    return [
        FetchAttempt("default", url),
        FetchAttempt(
            "browser_headers",
            url,
            (
                "--http1.1",
                "--compressed",
                "--user-agent",
                browser_ua,
                "--referer",
                referer,
                "--header",
                "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "--header",
                "Connection: close",
            ),
        ),
        FetchAttempt("ipv4_http10", url, ("--ipv4", "--http1.0", "--user-agent", browser_ua)),
        FetchAttempt("tls12", url, ("--tlsv1.2", "--user-agent", browser_ua)),
        FetchAttempt("plain_http", http_variant(url), ("--user-agent", browser_ua)),
    ]


def fetch_with_attempt(
    attempt: FetchAttempt,
    *,
    logical_url: str,
    raw_dir: Path,
    timeout: int,
) -> str:
    result = subprocess.run(
        [
            "curl",
            "--fail",
            "--location",
            "--silent",
            "--show-error",
            "--connect-timeout",
            str(min(8, timeout)),
            "--max-time",
            str(timeout),
            *attempt.args,
            attempt.url,
        ],
        check=True,
        capture_output=True,
        timeout=timeout + 1,
    )
    html = result.stdout.decode("utf-8", errors="replace")
    if not html.strip():
        raise ValueError(f"empty response body: {attempt.url}")
    save_snapshot(logical_url, html, raw_dir)
    return html


def fetch_or_read_with_fallbacks(url: str, raw_dir: Path, timeout: int, resume: bool) -> dict[str, str]:
    path = raw_dir / snapshot_filename(url)
    if resume and path.exists():
        return {"status": "cached", "method": "cached", "url": url, "path": str(path)}

    errors: list[str] = []
    for attempt in fetch_attempts(url):
        try:
            fetch_with_attempt(attempt, logical_url=url, raw_dir=raw_dir, timeout=timeout)
            return {
                "status": "fetched",
                "method": attempt.name,
                "url": url,
                "fetched_from": attempt.url,
                "path": str(path),
            }
        except subprocess.CalledProcessError as exc:
            message = exc.stderr.decode("utf-8", errors="replace").strip()
            errors.append(f"{attempt.name}: {message or f'curl exited {exc.returncode}'}")
        except Exception as exc:
            errors.append(f"{attempt.name}: {exc}")
    raise RuntimeError("; ".join(errors))


def should_delay(url: str, raw_dir: Path, resume: bool) -> bool:
    return not (resume and (raw_dir / snapshot_filename(url)).exists())


def extract_frame_sources(source_url: str, html: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    return [urljoin(source_url, tag["src"]) for tag in soup.find_all("frame", src=True)]


def extract_thogupu_links(config: ThirumuraiConfig, source_url: str, html: str) -> list[PaadalThogupu]:
    soup = BeautifulSoup(html, "lxml")
    frame_sources = extract_frame_sources(source_url, html)
    if frame_sources:
        return []
    links: list[PaadalThogupu] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        absolute = urljoin(source_url, href)
        if not any(fragment in absolute for fragment in config.hymn_path_fragments):
            continue
        params = query_params(absolute)
        subid = params.get("subid", "")
        if not subid or absolute in seen:
            continue
        seen.add(absolute)
        title = normalize_text(anchor.get_text(" ", strip=True))
        thalam, note, pann = split_title(title)
        links.append(
            PaadalThogupu(
                thogupu_id=f"{config.corpus_id}_thogupu_{subid}",
                thirumurai_no=config.thirumurai_no,
                ordinal=len(links) + 1,
                title=title,
                paadapatta_thalam=thalam,
                title_note=note,
                pann=pann,
                source_url=absolute,
                source_subid=subid,
            )
        )
    return links


def commentary_url(source_url: str, row: Tag) -> str:
    anchor = row.find("a", string=lambda value: value and "உரை" in value)
    if not anchor:
        anchor = row.find("a", onclick=True)
    if not anchor:
        return ""
    match = COMMENTARY_URL_RE.search(anchor.get("onclick", ""))
    return urljoin(source_url, match.group(1)) if match else ""


def next_commentary_url(source_url: str, poem_cell: Tag, outer_row: Tag | None) -> str:
    if outer_row:
        uri = commentary_url(source_url, outer_row)
        if uri:
            return uri
    for anchor in poem_cell.find_all_next("a", onclick=True):
        if "உரை" not in anchor.get_text(" ", strip=True):
            continue
        match = COMMENTARY_URL_RE.search(anchor.get("onclick", ""))
        if match:
            return urljoin(source_url, match.group(1))
    return ""


def poem_text_source(poem_cell: Tag) -> Tag:
    inner_row = poem_cell.find("tr")
    if inner_row:
        cells = inner_row.find_all("td", recursive=False)
        if len(cells) >= 2 and not cells[1].find("table", class_="tamil"):
            return cells[1]
    tamil_table = poem_cell.find("table", class_="tamil")
    if tamil_table:
        return tamil_table
    nested_poem = poem_cell.find("td", class_="poem")
    if nested_poem:
        return nested_poem
    return poem_cell


def visible_song_number(poem_cell: Tag, outer_row: Tag | None, text_source: Tag) -> str:
    inner_row = poem_cell.find("tr")
    if inner_row:
        cells = inner_row.find_all("td", recursive=False)
        if len(cells) >= 2:
            value = normalize_text(cells[0].get_text(" ", strip=True)).rstrip(".")
            if value:
                return value
    if outer_row:
        cells = outer_row.find_all("td", recursive=False)
        if poem_cell in cells:
            poem_index = cells.index(poem_cell)
            number_cell = next(
                (
                    cell
                    for cell in reversed(cells[:poem_index])
                    if "pno" in (cell.get("class") or [])
                ),
                None,
            )
            if number_cell is not None:
                value = normalize_text(number_cell.get_text(" ", strip=True)).rstrip(".")
                if value:
                    return value
    match = re.search(r"பாடல்\s+எண்\s*:?\s*(\d+)", poem_cell.get_text(" ", strip=True))
    if match:
        return match.group(1)
    local_number = poem_cell.find("td", class_="pn")
    if local_number:
        return normalize_text(local_number.get_text(" ", strip=True)).rstrip(".")
    nested_number = poem_cell.find("td", class_="pno", string=lambda value: value and value.strip().isdigit())
    if nested_number:
        return normalize_text(nested_number.get_text(" ", strip=True)).rstrip(".")
    return normalize_text(text_source.get_text(" ", strip=True)).split(" ", 1)[0].rstrip(".")


def parse_paadal_page(config: ThirumuraiConfig, thogupu: PaadalThogupu, html: str) -> list[Paadal]:
    soup = BeautifulSoup(html, "lxml")
    paadalgal: list[Paadal] = []
    seen_paadal_ids: set[str] = set()
    for poem_cell in soup.find_all("td", class_="poem"):
        if poem_cell.find_parent("td", class_="poem"):
            continue
        outer_row = poem_cell.find_parent("tr")
        text_source = poem_text_source(poem_cell)
        visible_no = visible_song_number(poem_cell, outer_row, text_source)
        text = "\n".join(
            normalize_text(line)
            for line in text_source.get_text("\n", strip=True).splitlines()
            if normalize_text(line)
        )
        if not visible_no or not text:
            continue
        uri = next_commentary_url(thogupu.source_url, poem_cell, outer_row)
        params = query_params(uri)
        source_song_no = params.get("song_no", visible_no)
        global_no = source_song_no
        base_paadal_id = f"{config.corpus_id}_paadal_{global_no}"
        paadal_id = base_paadal_id
        if paadal_id in seen_paadal_ids:
            global_no = f"{source_song_no}_{thogupu.source_subid}_{len(paadalgal) + 1}"
            paadal_id = f"{config.corpus_id}_paadal_{global_no}"
        seen_paadal_ids.add(paadal_id)
        paadalgal.append(
            Paadal(
                paadal_id=paadal_id,
                thogupu_id=thogupu.thogupu_id,
                thirumurai_no=config.thirumurai_no,
                global_song_no=global_no,
                source_song_no=source_song_no,
                local_song_no=visible_no,
                verse_index_in_thogupu=len(paadalgal) + 1,
                paadal_text=text,
                tokenized_paadal=tokenize_tamil_text(text),
                source_url=thogupu.source_url,
                commentary_url=uri,
                source_parameters=params,
            )
        )
    return paadalgal


def line_spans(parent_id: str, field_name: str, span_type: str, text: str) -> list[TextSpan]:
    spans: list[TextSpan] = []
    cursor = 0
    for line_no, line in enumerate(text.splitlines(), start=1):
        start = text.find(line, cursor)
        if start < 0:
            continue
        end = start + len(line)
        cursor = end
        if line.strip():
            spans.append(
                TextSpan(
                    span_id=f"{parent_id}_{field_name}_{line_no}",
                    parent_id=parent_id,
                    field_name=field_name,
                    span_type=span_type,
                    start_char=start,
                    end_char=end,
                    text=line,
                    metadata={"line_no": str(line_no)},
                )
            )
    return spans


def commentary_spans(commentary: Commentary) -> list[TextSpan]:
    spans: list[TextSpan] = []
    for field_name, span_type, text in (
        ("kurippurai", "commentary_kurippurai", commentary.kurippurai),
        ("pozhppurai", "commentary_pozhppurai", commentary.pozhppurai),
    ):
        if text:
            spans.extend(line_spans(commentary.paadal_id, field_name, span_type, text))
    return spans


def write_jsonl(path: Path, rows: Iterable[object]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            payload = asdict(row) if hasattr(row, "__dataclass_fields__") else row
            payload["schema_version"] = SCHEMA_VERSION
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def write_table_outputs(output_root: Path, rows: dict[str, list[object]]) -> dict[str, int]:
    counts = {}
    for name, items in rows.items():
        counts[name] = write_jsonl(output_root / f"{name}.jsonl", items)
    return counts


def failure_raw_dir(base_dir: Path, failure: dict[str, str]) -> Path:
    kind = "commentary" if "paadal_id" in failure else "paadal_thogupugal"
    return base_dir / DEFAULT_RAW_ROOT / failure["corpus_id"] / kind


def selected_failure(failure: dict[str, str], corpus_filter: set[str], kind_filter: str) -> bool:
    if corpus_filter and failure["corpus_id"] not in corpus_filter:
        return False
    kind = "commentary" if "paadal_id" in failure else "thogupu"
    return kind_filter == "all" or kind_filter == kind


def fetch_missing_failures(
    *,
    base_dir: Path,
    timeout: int,
    delay: float,
    corpus_filter: set[str],
    kind_filter: str,
    limit: int | None,
    offset: int,
    progress_every: int,
) -> dict[str, object]:
    import requests

    summary_path = base_dir / DEFAULT_OUTPUT_ROOT / "ingestion_summary.json"
    source_summary = json.loads(summary_path.read_text(encoding="utf-8"))
    source_failures = [
        failure
        for failure in source_summary["failures"]
        if selected_failure(failure, corpus_filter, kind_filter)
    ]
    selected = source_failures[offset:]
    if limit is not None:
        selected = selected[:limit]

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
    fetched: list[dict[str, str]] = []
    skipped_cached: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for index, failure in enumerate(selected, start=1):
        url = failure["url"]
        if url in seen_urls:
            continue
        seen_urls.add(url)
        raw_dir = failure_raw_dir(base_dir, failure)
        path = raw_dir / snapshot_filename(url)
        if path.exists():
            skipped_cached.append(failure)
            continue
        if progress_every and (index == 1 or index % progress_every == 0):
            print(f"[fetch-failures] {index}/{len(selected)} {failure['corpus_id']} {url}", flush=True)
        if delay and fetched:
            time.sleep(delay)
        try:
            result = fetch_or_read_with_fallbacks(url, raw_dir, timeout, resume=True)
            fetched_item = dict(failure)
            fetched_item.update(result)
            fetched.append(fetched_item)
        except Exception as exc:
            failed = dict(failure)
            failed["error"] = str(exc)
            failures.append(failed)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "source_summary": str(summary_path),
        "selected": len(selected),
        "fetched": len(fetched),
        "skipped_cached": len(skipped_cached),
        "failures": failures,
    }
    fetch_summary_path = base_dir / DEFAULT_OUTPUT_ROOT / "failure_fetch_summary.json"
    fetch_summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def scrape_configs(
    configs: list[ThirumuraiConfig],
    *,
    base_dir: Path,
    delay: float,
    timeout: int,
    resume: bool,
    dry_run: bool,
    fetch_missing: bool,
    limit_thogupugal: int | None,
    limit_paadalgal_per_thogupu: int | None,
    progress_every: int,
) -> dict[str, object]:
    import requests

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Connection": "close",
        }
    )
    raw_root = base_dir / DEFAULT_RAW_ROOT
    output_root = base_dir / DEFAULT_OUTPUT_ROOT
    tables: dict[str, list[object]] = {
        "thirumurai_books": [],
        "paadal_thogupugal": [],
        "paadalgal": [],
        "commentaries": [],
        "text_spans": [],
    }
    failures: list[dict[str, str]] = []

    for config in configs:
        tables["thirumurai_books"].append(
            {
                "thirumurai_no": config.thirumurai_no,
                "corpus_id": config.corpus_id,
                "title": config.title,
                "work_id": config.work_id,
                "work_title": config.work_title,
                "author": config.author,
                "nayanmar": config.nayanmar,
                "source_url": config.left_frame_url,
                "verified_navigation": config.verified_navigation,
            }
        )
        try:
            nav_html = fetch_or_read(
                session,
                config.left_frame_url,
                raw_root / config.corpus_id / "navigation",
                timeout,
                resume,
                fetch_missing=fetch_missing,
            )
            frames = extract_frame_sources(config.left_frame_url, nav_html)
            if frames:
                nav_url = frames[0]
                nav_html = fetch_or_read(
                    session,
                    nav_url,
                    raw_root / config.corpus_id / "navigation",
                    timeout,
                    resume,
                    fetch_missing=fetch_missing,
                )
            thogupugal = extract_thogupu_links(config, config.left_frame_url, nav_html)
            selected = thogupugal[:limit_thogupugal] if limit_thogupugal else thogupugal
            tables["paadal_thogupugal"].extend(selected)
            if dry_run:
                continue
            for thogupu_index, thogupu in enumerate(selected):
                hymn_raw_dir = raw_root / config.corpus_id / "paadal_thogupugal"
                if thogupu_index and delay and should_delay(thogupu.source_url, hymn_raw_dir, resume):
                    time.sleep(delay)
                if progress_every and thogupu_index % progress_every == 0:
                    print(
                        f"[{config.corpus_id}] thogupu {thogupu_index + 1}/{len(selected)} "
                        f"{thogupu.source_subid}",
                        flush=True,
                    )
                try:
                    hymn_html = fetch_or_read(
                        session,
                        thogupu.source_url,
                        hymn_raw_dir,
                        timeout,
                        resume,
                        fetch_missing=fetch_missing,
                    )
                    paadalgal = parse_paadal_page(config, thogupu, hymn_html)
                    if limit_paadalgal_per_thogupu:
                        paadalgal = paadalgal[:limit_paadalgal_per_thogupu]
                    tables["paadalgal"].extend(paadalgal)
                    for paadal in paadalgal:
                        tables["text_spans"].extend(
                            line_spans(paadal.paadal_id, "paadal_text", "paadal_line", paadal.paadal_text)
                        )
                        commentary_raw_dir = raw_root / config.corpus_id / "commentary"
                        if delay and paadal.commentary_url and should_delay(paadal.commentary_url, commentary_raw_dir, resume):
                            time.sleep(delay)
                        if not paadal.commentary_url:
                            commentary = Commentary(
                                f"{paadal.paadal_id}_commentary",
                                paadal.paadal_id,
                                "",
                                "",
                                "missing_commentary_url",
                                ["missing_commentary_url"],
                            )
                        else:
                            try:
                                commentary_html = fetch_or_read(
                                    session,
                                    paadal.commentary_url,
                                    commentary_raw_dir,
                                    timeout,
                                    resume,
                                    fetch_missing=fetch_missing,
                                )
                                parts = split_commentary_text(commentary_html)
                                commentary = Commentary(
                                    f"{paadal.paadal_id}_commentary",
                                    paadal.paadal_id,
                                    parts.kurippurai,
                                    parts.pozhppurai,
                                    parts.extraction_status,
                                    parts.warnings,
                                )
                            except Exception as exc:
                                failures.append(
                                    {
                                        "corpus_id": config.corpus_id,
                                        "thogupu_id": thogupu.thogupu_id,
                                        "paadal_id": paadal.paadal_id,
                                        "url": paadal.commentary_url,
                                        "error": str(exc),
                                    }
                                )
                                commentary = Commentary(
                                    f"{paadal.paadal_id}_commentary",
                                    paadal.paadal_id,
                                    "",
                                    "",
                                    "commentary_fetch_failed",
                                    [str(exc)],
                                )
                        tables["commentaries"].append(commentary)
                        tables["text_spans"].extend(commentary_spans(commentary))
                except Exception as exc:
                    failures.append(
                        {
                            "corpus_id": config.corpus_id,
                            "thogupu_id": thogupu.thogupu_id,
                            "url": thogupu.source_url,
                            "error": str(exc),
                        }
                    )
        except Exception as exc:
            failures.append(
                {
                    "corpus_id": config.corpus_id,
                    "thogupu_id": "",
                    "url": config.left_frame_url,
                    "error": str(exc),
                }
            )

    counts = write_table_outputs(output_root, tables)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "dry_run": dry_run,
        "counts": counts,
        "failures": failures,
        "output_root": str(output_root),
    }
    (output_root / "ingestion_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return summary


def render_report(summary: dict[str, object]) -> str:
    counts = summary["counts"]
    failures = summary["failures"]
    return "\n".join(
        [
            "# Thevaram 1-8 Ingestion Report",
            "",
            f"- Schema version: `{summary['schema_version']}`",
            f"- Dry run: `{summary['dry_run']}`",
            f"- Output root: `{summary['output_root']}`",
            "",
            "## Table Counts",
            "",
            *(f"- `{name}`: `{count}`" for name, count in counts.items()),
            "",
            "## Failures",
            "",
            *(f"- `{item['corpus_id']}` `{item['url']}`: {item['error']}" for item in failures),
            "" if failures else "- None",
            "",
        ]
    )


def compact_summary(summary: dict[str, object]) -> dict[str, object]:
    failure_counts: dict[str, int] = {}
    failure_kinds: dict[str, int] = {}
    for failure in summary["failures"]:
        corpus_id = failure["corpus_id"]
        failure_counts[corpus_id] = failure_counts.get(corpus_id, 0) + 1
        kind = "commentary" if "paadal_id" in failure else "thogupu"
        failure_kinds[kind] = failure_kinds.get(kind, 0) + 1
    return {
        "schema_version": summary["schema_version"],
        "dry_run": summary["dry_run"],
        "counts": summary["counts"],
        "failure_count": len(summary["failures"]),
        "failure_counts": dict(sorted(failure_counts.items())),
        "failure_kinds": dict(sorted(failure_kinds.items())),
        "output_root": summary["output_root"],
    }


def parse_corpus_filter(value: str) -> set[str]:
    selected: set[str] = set()
    for part in value.split(","):
        item = part.strip()
        if not item:
            continue
        if item.isdigit():
            selected.add(f"thirumurai_{int(item):02d}")
        else:
            selected.add(item)
    return selected


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build normalized Thevaram/Thirumurai 1-8 tables.")
    parser.add_argument("--thirumurai", default="1-8", help="Comma/range list, e.g. 1-4,8")
    parser.add_argument("--base-dir", type=Path, default=DEFAULT_BASE_DIR)
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--execute", action="store_true", help="Fetch hymn and commentary pages.")
    parser.add_argument("--offline", action="store_true", help="Only read cached raw snapshots; never fetch missing pages.")
    parser.add_argument("--limit-thogupugal", type=int)
    parser.add_argument("--limit-paadalgal-per-thogupu", type=int)
    parser.add_argument("--progress-every", type=int, default=25)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--compact-summary", action="store_true")
    parser.add_argument("--fetch-failures", action="store_true", help="Fetch only URLs currently listed as failures.")
    parser.add_argument("--failure-corpus", default="", help="Comma list like 1,2 or thirumurai_05.")
    parser.add_argument("--failure-kind", choices=["all", "thogupu", "commentary"], default="all")
    parser.add_argument("--failure-limit", type=int)
    parser.add_argument("--failure-offset", type=int, default=0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.fetch_failures:
        summary = fetch_missing_failures(
            base_dir=args.base_dir,
            timeout=args.timeout,
            delay=args.delay,
            corpus_filter=parse_corpus_filter(args.failure_corpus),
            kind_filter=args.failure_kind,
            limit=args.failure_limit,
            offset=args.failure_offset,
            progress_every=args.progress_every,
        )
        payload = {
            "schema_version": summary["schema_version"],
            "selected": summary["selected"],
            "fetched": summary["fetched"],
            "skipped_cached": summary["skipped_cached"],
            "failure_count": len(summary["failures"]),
        }
        print(json.dumps(payload if args.compact_summary else summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 2 if summary["failures"] else 0

    configs = [THIRUMURAI_CONFIGS[number] for number in parse_range(args.thirumurai)]
    summary = scrape_configs(
        configs,
        base_dir=args.base_dir,
        delay=args.delay,
        timeout=args.timeout,
        resume=args.resume,
        dry_run=not args.execute,
        fetch_missing=not args.offline,
        limit_thogupugal=args.limit_thogupugal,
        limit_paadalgal_per_thogupu=args.limit_paadalgal_per_thogupu,
        progress_every=args.progress_every,
    )
    report_path = args.report if args.report.is_absolute() else args.base_dir / args.report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_report(summary), encoding="utf-8")
    payload = compact_summary(summary) if args.compact_summary else summary
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if summary["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
