import hashlib
import json
from pathlib import Path

from corpus.normalize_category_corpus import normalize_record
from corpus.validate_category_corpus import validate_records
from parsers.base_parser import ParseContext
from parsers.verse_parser import VerseParser


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/sangam_literature"


def context() -> ParseContext:
    return ParseContext(
        category_id="sangam_literature",
        category_tamil="சங்க இலக்கியம்",
        parser_family="verse_parser",
        book_id="ettuthokai",
        work_id="natrinai",
        pilot_id="pilot_002",
    )


def fixture_source(page_type: str) -> dict:
    metadata = json.loads((FIXTURES / "source_metadata.json").read_text(encoding="utf-8"))
    item = next(entry for entry in metadata["fixtures"] if entry["page_type"] == page_type)
    return {
        **item,
        "source_work": metadata["source_work"],
        "html_content": (ROOT / item["fixture_path"]).read_text(encoding="utf-8"),
    }


def parsed_poems() -> list[dict]:
    return VerseParser().parse(fixture_source("poem_group"), context())


def test_navigation_fixtures_do_not_create_poems() -> None:
    parser = VerseParser()

    assert parser.parse(fixture_source("work_index"), context()) == []
    assert parser.parse(fixture_source("poem_navigation"), context()) == []


def test_natrinai_fixture_parsing() -> None:
    records = parsed_poems()

    assert len(records) == 3
    first = records[0]
    assert first["record_type"] == "verse"
    assert first["poem_no"] == first["verse_no"] == first["song_no"] == "1"
    assert first["thinai"] == "குறிஞ்சி"
    assert first["author"] == "கபிலர்"
    assert first["thurai"] == "பிரிவு உணர்த்திய தோழிக்குத் தலைவி சொல்லியது"
    assert len(first["verse_text"].splitlines()) == 9
    assert first["commentary_url"].endswith("book_id=21&song_no=1")
    assert first["source_metadata"]["source_subid"] == "3362"


def test_sangam_output_is_deterministic_and_unique() -> None:
    first = parsed_poems()
    second = parsed_poems()

    assert first == second
    assert len({record["record_id"] for record in first}) == 3
    assert all(
        record["record_id"].startswith("tvu_sangam_literature_")
        for record in first
    )


def test_sangam_normalization_and_validation() -> None:
    normalized = [normalize_record(record) for record in parsed_poems()]
    result = validate_records(normalized, "sangam_literature")

    assert all(record["schema_version"] == "website-corpus-v2" for record in normalized)
    assert all(record["content_text"] == record["verse_text"] for record in normalized)
    assert result["status"] == "VALID"
    assert result["sangam_missing_fields"] == {}
    assert result["source_url_coverage"] == 1.0


def test_sangam_validation_catches_literary_identity_gaps() -> None:
    record = normalize_record(parsed_poems()[0])
    record["thinai"] = ""
    record["author"] = ""

    result = validate_records([record], "sangam_literature")

    assert result["status"] == "INVALID"
    assert result["sangam_missing_fields"] == {"author": 1, "thinai": 1}


def test_fixture_manifest_is_exactly_three_pages() -> None:
    metadata = json.loads((FIXTURES / "source_metadata.json").read_text(encoding="utf-8"))

    assert metadata["fixture_limit"] == 3
    assert len(metadata["fixtures"]) == 3
    assert {item["page_type"] for item in metadata["fixtures"]} == {
        "work_index",
        "poem_navigation",
        "poem_group",
    }


def test_sangam_parser_has_no_network_or_llm_path() -> None:
    script = (ROOT / "src/parsers/verse_parser.py").read_text(encoding="utf-8")

    for forbidden in (
        "import requests",
        "from requests",
        "urlopen",
        "openai",
        "anthropic",
        "google.cloud",
    ):
        assert forbidden not in script


def test_frozen_corpora_are_unchanged() -> None:
    release = ROOT / "data/releases/irandaam-thirumurai-v1"
    expected = {}
    for line in (release / "corpus_checksum.sha256").read_text(encoding="utf-8").splitlines():
        digest, filename = line.split(maxsplit=1)
        expected[filename] = digest
    corpus = release / "irandaam_thirumurai.jsonl"
    assert hashlib.sha256(corpus.read_bytes()).hexdigest() == expected[corpus.name]

    fourth = ROOT / "data/processed/normalized/thirumurai_04_normalized.jsonl"
    assert (
        hashlib.sha256(fourth.read_bytes()).hexdigest()
        == "0c1090fa310e323041ca2435942f8124a69b8d78ff8d3f3fcb697cd96b60a0d7"
    )
