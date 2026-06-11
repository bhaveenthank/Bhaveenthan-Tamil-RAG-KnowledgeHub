import hashlib
import json
from pathlib import Path

from corpus.normalize_category_corpus import normalize_record
from corpus.validate_category_corpus import validate_records
from parsers.base_parser import ParseContext
from parsers.grammar_parser import GrammarParser


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/grammar"


def context() -> ParseContext:
    return ParseContext(
        category_id="grammar",
        category_tamil="இலக்கணம்",
        parser_family="grammar_parser",
        book_id="nannul",
        work_id="nannul_kaandigai_urai",
        pilot_id="pilot_001",
    )


def fixture_source(page_type: str) -> dict:
    metadata = json.loads((FIXTURES / "source_metadata.json").read_text(encoding="utf-8"))
    item = next(entry for entry in metadata["fixtures"] if entry["page_type"] == page_type)
    return {
        **item,
        "source_work": metadata["source_work"],
        "html_content": (ROOT / item["fixture_path"]).read_text(encoding="utf-8"),
    }


def parsed_rules() -> list[dict]:
    return GrammarParser().parse(fixture_source("grammar_rules"), context())


def test_navigation_fixtures_do_not_create_rules() -> None:
    parser = GrammarParser()

    assert parser.parse(fixture_source("work_index"), context()) == []
    assert parser.parse(fixture_source("grammar_navigation"), context()) == []


def test_nannul_fixture_parsing() -> None:
    records = parsed_rules()

    assert len(records) == 2
    first = records[0]
    assert first["record_type"] == "grammar_rule"
    assert first["rule_no"] == "56"
    assert first["chapter_id"] == "எழுத்ததிகாரம்"
    assert first["section_id"] == "எழுத்தியல்"
    assert len(first["rule_text"].splitlines()) == 2
    assert first["explanation_text"] == ""
    assert first["commentary_url"].endswith("song_no=56&book_id=6&head_id=10")
    assert first["source_metadata"]["source_subid"] == "212"


def test_grammar_output_is_deterministic_and_unique() -> None:
    first = parsed_rules()
    second = parsed_rules()

    assert first == second
    assert len({record["record_id"] for record in first}) == 2
    assert all(record["record_id"].startswith("tvu_grammar_") for record in first)


def test_grammar_normalization_and_validation() -> None:
    normalized = [normalize_record(record) for record in parsed_rules()]
    result = validate_records(normalized, "grammar")

    assert all(record["schema_version"] == "website-corpus-v2" for record in normalized)
    assert all(record["content_text"] == record["rule_text"] for record in normalized)
    assert result["status"] == "VALID"
    assert result["grammar_missing_fields"] == {}
    assert result["duplicate_record_ids"] == []
    assert result["source_url_coverage"] == 1.0


def test_grammar_validation_catches_required_fields() -> None:
    record = normalize_record(parsed_rules()[0])
    record["rule_no"] = ""
    record["rule_text"] = ""
    record["content_text"] = ""

    result = validate_records([record], "grammar")

    assert result["status"] == "INVALID"
    assert result["grammar_missing_fields"] == {"rule_no": 1, "rule_text": 1}


def test_fixture_manifest_is_exactly_three_pages() -> None:
    metadata = json.loads((FIXTURES / "source_metadata.json").read_text(encoding="utf-8"))

    assert metadata["fixture_limit"] == 3
    assert len(metadata["fixtures"]) == 3
    assert {item["page_type"] for item in metadata["fixtures"]} == {
        "work_index",
        "grammar_navigation",
        "grammar_rules",
    }


def test_grammar_parser_has_no_network_or_llm_path() -> None:
    script = (ROOT / "src/parsers/grammar_parser.py").read_text(encoding="utf-8")

    for forbidden in (
        "import requests",
        "from requests",
        "urlopen",
        "openai",
        "anthropic",
        "google.cloud",
    ):
        assert forbidden not in script


def test_existing_pilot_and_frozen_artifacts_remain_unchanged() -> None:
    plan = json.loads(
        (ROOT / "data/processed/corpus_registry/pilot_category_plan.json").read_text(
            encoding="utf-8"
        )
    )
    statuses = {
        pilot["category_id"]: pilot["status"] for pilot in plan["pilots"]
    }
    assert statuses["saivam"] == "local_seed_ready"
    assert statuses["sangam_literature"] == "pilot_verified"
    assert statuses["dictionaries"] == "pilot_verified"

    release = ROOT / "data/releases/irandaam-thirumurai-v1"
    expected = {}
    for line in (release / "corpus_checksum.sha256").read_text(encoding="utf-8").splitlines():
        digest, filename = line.split(maxsplit=1)
        expected[filename] = digest
    corpus = release / "irandaam_thirumurai.jsonl"
    assert hashlib.sha256(corpus.read_bytes()).hexdigest() == expected[corpus.name]
