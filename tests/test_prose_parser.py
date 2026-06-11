import hashlib
import json
from pathlib import Path

from corpus.normalize_category_corpus import normalize_record
from corpus.validate_category_corpus import validate_records
from parsers.base_parser import ParseContext
from parsers.prose_parser import ProseParser


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/prose"


def context() -> ParseContext:
    return ParseContext(
        category_id="twentieth_century_prose",
        category_tamil="இருபதாம் நூற்றாண்டு இலக்கியங்கள் உரைநடைகள்",
        parser_family="prose_parser",
        book_id="bharathiyar_katturaigal",
        work_id="bharathiyar_katturaigal_poompuhar",
        pilot_id="pilot_004",
    )


def fixture_source(page_type: str) -> dict:
    metadata = json.loads((FIXTURES / "source_metadata.json").read_text(encoding="utf-8"))
    item = next(entry for entry in metadata["fixtures"] if entry["page_type"] == page_type)
    return {
        **item,
        "source_work": metadata["source_work"],
        "html_content": (ROOT / item["fixture_path"]).read_text(encoding="utf-8"),
    }


def parsed_sections() -> list[dict]:
    return ProseParser().parse(fixture_source("prose_section"), context())


def test_navigation_fixtures_do_not_create_prose_records() -> None:
    parser = ProseParser()

    assert parser.parse(fixture_source("work_index"), context()) == []
    assert parser.parse(fixture_source("prose_contents"), context()) == []


def test_prose_fixture_parsing_and_metadata() -> None:
    records = parsed_sections()

    assert len(records) == 2
    first = records[0]
    assert first["record_type"] == "prose_section"
    assert first["title"] == "யாரைத் தொழுவது?"
    assert first["author"] == "சுப்பிரமணிய பாரதி"
    assert first["chapter_id"] == "bharathiyar_katturaigal_religion"
    assert first["section_id"] == "118166:p001"
    assert first["source_url"].endswith("linkid=118166")
    assert first["source_metadata"]["paragraph_index"] == 1
    assert first["source_metadata"]["rights_status"] == "no_tamilvu_essay_text_reproduced"


def test_prose_output_is_deterministic_and_unique() -> None:
    first = parsed_sections()
    second = parsed_sections()

    assert first == second
    assert len({record["record_id"] for record in first}) == 2
    assert all(
        record["record_id"].startswith("tvu_twentieth_century_prose_")
        for record in first
    )


def test_prose_normalization_and_validation() -> None:
    normalized = [normalize_record(record) for record in parsed_sections()]
    result = validate_records(normalized, "twentieth_century_prose")

    assert all(record["schema_version"] == "website-corpus-v2" for record in normalized)
    assert all(record["record_type"] == "prose_section" for record in normalized)
    assert result["status"] == "VALID"
    assert result["prose_missing_fields"] == {}
    assert result["duplicate_record_ids"] == []
    assert result["source_url_coverage"] == 1.0


def test_prose_validation_catches_required_fields_and_duplicates() -> None:
    record = normalize_record(parsed_sections()[0])
    record["content_text"] = ""
    duplicate = dict(record)

    result = validate_records([record, duplicate], "twentieth_century_prose")

    assert result["status"] == "INVALID"
    assert result["prose_missing_fields"]["content_text"] == 2
    assert result["duplicate_record_ids"] == [record["record_id"]]


def test_fixture_manifest_is_exactly_three_rights_safe_pages() -> None:
    metadata = json.loads((FIXTURES / "source_metadata.json").read_text(encoding="utf-8"))

    assert metadata["fixture_limit"] == 3
    assert len(metadata["fixtures"]) == 3
    assert {item["page_type"] for item in metadata["fixtures"]} == {
        "work_index",
        "prose_contents",
        "prose_section",
    }
    assert all("rights_status" in item for item in metadata["fixtures"])
    assert metadata["fixtures"][-1]["fixture_content_status"].startswith("synthetic")


def test_prose_parser_has_no_network_or_llm_path() -> None:
    script = (ROOT / "src/parsers/prose_parser.py").read_text(encoding="utf-8")

    for forbidden in (
        "import requests",
        "from requests",
        "urlopen",
        "openai",
        "anthropic",
        "google.cloud",
    ):
        assert forbidden not in script


def test_existing_pilots_and_frozen_artifacts_remain_unchanged() -> None:
    plan = json.loads(
        (ROOT / "data/processed/corpus_registry/pilot_category_plan.json").read_text(
            encoding="utf-8"
        )
    )
    statuses = {pilot["category_id"]: pilot["status"] for pilot in plan["pilots"]}
    assert statuses["saivam"] == "local_seed_ready"
    assert statuses["sangam_literature"] == "pilot_verified"
    assert statuses["dictionaries"] == "pilot_verified"
    assert statuses["grammar"] == "pilot_verified"

    release = ROOT / "data/releases/irandaam-thirumurai-v1"
    expected = {}
    for line in (release / "corpus_checksum.sha256").read_text(encoding="utf-8").splitlines():
        digest, filename = line.split(maxsplit=1)
        expected[filename] = digest
    corpus = release / "irandaam_thirumurai.jsonl"
    assert hashlib.sha256(corpus.read_bytes()).hexdigest() == expected[corpus.name]
