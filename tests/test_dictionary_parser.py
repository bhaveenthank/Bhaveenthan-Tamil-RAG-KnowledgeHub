import hashlib
import json
from pathlib import Path

from corpus.normalize_category_corpus import normalize_record
from corpus.validate_category_corpus import validate_records
from parsers.base_parser import ParseContext
from parsers.dictionary_parser import DictionaryParser


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/dictionary"


def context() -> ParseContext:
    return ParseContext(
        category_id="dictionaries",
        category_tamil="அகராதிகள்",
        parser_family="dictionary_parser",
        book_id="tamil_tamil_agaramuthali",
        work_id="m_shanmugampillai_tamil_agaramuthali",
        pilot_id="pilot_005",
    )


def source(page: str, url: str, page_type: str) -> dict:
    return {
        "fixture_path": f"tests/fixtures/dictionary/{page}",
        "page_type": page_type,
        "source_url": url,
        "source_work": "Tamil - Tamil Agaramuthali by M. Shanmugampillai",
        "html_content": (FIXTURES / page).read_text(encoding="utf-8"),
    }


def parsed_entry() -> dict:
    records = DictionaryParser().parse(
        source(
            "03_single_entry.html",
            "https://www.tamilvu.org/slet/pmdictionary/ldttamls.jsp?x=1&y=1",
            "dictionary_entry",
        ),
        context(),
    )
    return records[0]


def test_navigation_fixtures_do_not_create_entries() -> None:
    parser = DictionaryParser()
    assert parser.parse(
        source(
            "01_work_index.html",
            "https://www.tamilvu.org/ta/library-ldttam-html-ldttamin-159450",
            "work_index",
        ),
        context(),
    ) == []
    assert parser.parse(
        source(
            "02_alphabet_navigation.html",
            "https://www.tamilvu.org/ta/library-ldttam-html-ldttamas-159443",
            "alphabet_navigation",
        ),
        context(),
    ) == []


def test_fixture_parsing_and_schema_mapping() -> None:
    record = parsed_entry()

    assert record["record_type"] == "dictionary_entry"
    assert record["entry_headword"] == "அ"
    assert record["definition"].startswith("தமிழ் எழுத்துகளுள் முதல் உயிர் எழுத்து")
    assert record["content_text"] == record["definition"]
    assert record["part_of_speech"] == ""
    assert record["source_metadata"]["part_of_speech_source"] == "not_provided"
    assert record["source_metadata"]["source_record_id"] == "dictionary_entry:1:அ"
    assert record["parser_family"] == "dictionary_parser"


def test_dictionary_output_is_deterministic() -> None:
    assert parsed_entry() == parsed_entry()
    assert parsed_entry()["record_id"].startswith("tvu_dictionaries_")


def test_dictionary_normalization_and_validation() -> None:
    normalized = normalize_record(parsed_entry())
    result = validate_records([normalized], "dictionaries")

    assert normalized["schema_version"] == "website-corpus-v2"
    assert normalized["entry_headword"] == "அ"
    assert normalized["definition"] == normalized["content_text"]
    assert result["status"] == "VALID"
    assert result["dictionary_missing_fields"] == {}
    assert result["duplicate_record_ids"] == []


def test_dictionary_validation_catches_required_fields() -> None:
    record = normalize_record(parsed_entry())
    record["entry_headword"] = ""
    record["definition"] = ""

    result = validate_records([record], "dictionaries")

    assert result["status"] == "INVALID"
    assert result["dictionary_missing_fields"] == {
        "definition": 1,
        "entry_headword": 1,
    }


def test_fixture_manifest_is_exactly_three_pages() -> None:
    metadata = json.loads((FIXTURES / "source_metadata.json").read_text(encoding="utf-8"))

    assert metadata["fixture_limit"] == 3
    assert len(metadata["fixtures"]) == 3
    assert {item["page_type"] for item in metadata["fixtures"]} == {
        "work_index",
        "alphabet_navigation",
        "dictionary_entry",
    }


def test_frozen_thirumurai_corpus_is_unchanged() -> None:
    release = ROOT / "data/releases/irandaam-thirumurai-v1"
    expected = {}
    for line in (release / "corpus_checksum.sha256").read_text(encoding="utf-8").splitlines():
        digest, filename = line.split(maxsplit=1)
        expected[filename] = digest

    corpus = release / "irandaam_thirumurai.jsonl"
    assert hashlib.sha256(corpus.read_bytes()).hexdigest() == expected[corpus.name]
