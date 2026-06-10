import hashlib
import json
from pathlib import Path


REGISTRY_PATH = Path("data/processed/corpus_registry/website_category_registry.json")
THIRUMURAI_REGISTRY_PATH = Path(
    "data/processed/corpus_registry/thirumurai_registry.json"
)
EXPECTED_TAMIL_CATEGORIES = {
    "சொல்லடைவு",
    "தமிழ் எண் சுவடி",
    "இலக்கணம்",
    "சங்க இலக்கியம்",
    "பதினெண் கீழ்க்கணக்கு",
    "காப்பியங்கள்",
    "சமய இலக்கியங்கள்",
    "சைவம்",
    "வைணவம்",
    "கிறித்துவம்",
    "இசுலாம்",
    "சிற்றிலக்கியங்கள்",
    "நெறி நூல்கள்",
    "சித்தர் இலக்கியம்",
    "இருபதாம் நூற்றாண்டு இலக்கியங்கள் கவிதைகள்",
    "இருபதாம் நூற்றாண்டு இலக்கியங்கள் உரைநடைகள்",
    "நாட்டுப்புற இலக்கியங்கள்",
    "சிறுவர் இலக்கியங்கள்",
    "ரோமன் வடிவம்",
    "அகராதிகள்",
    "நிகண்டுகள்",
    "பிற மொழியில் தமிழ் நூல்கள்",
    "கலைக்களஞ்சியங்கள்",
    "கலைச்சொல் தொகுப்புகள்",
    "சுவடிக்காட்சியகம்",
    "பண்பாட்டுக் காட்சியகம்",
    "நாட்டுடைமை நூல்கள்",
    "நாட்டுடைமையாக்கப்பட்ட தமிழறிஞர்களின் நூல்கள் உருப்பட வடிவில்",
    "நாட்டுடைமையாக்கப்பட்ட தமிழறிஞர்களின் நூல்கள் தட்டச்சு வடிவில்",
    "உருப்பட நூல்கள்",
    "தமிழக வரலாறு, கலைப் பண்பாடு, இலக்கியம் தொடர்பான நூல்கள்",
    "பிற நூலக இணையத் தளங்கள்",
}
VALID_PARSER_FAMILIES = {
    "verse_parser",
    "prose_parser",
    "grammar_parser",
    "dictionary_parser",
    "table_parser",
    "image_metadata_parser",
    "mixed_parser",
    "external_link_registry",
}
VALID_PRIORITIES = {"pilot", "high", "medium", "low", "defer"}
VALID_STATUSES = {"planned", "pilot_candidate", "deferred"}


def website_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def thirumurai_registry() -> dict:
    return json.loads(THIRUMURAI_REGISTRY_PATH.read_text(encoding="utf-8"))


def test_website_category_registry_exists_and_is_complete() -> None:
    categories = website_registry()["categories"]

    assert REGISTRY_PATH.exists()
    assert len(categories) == 32
    assert {category["category_tamil"] for category in categories} == EXPECTED_TAMIL_CATEGORIES


def test_category_ids_are_deterministic_and_unique() -> None:
    categories = website_registry()["categories"]
    ids = [category["category_id"] for category in categories]

    assert len(ids) == len(set(ids))
    assert all(identifier == identifier.lower() for identifier in ids)
    assert all(identifier.replace("_", "").isalnum() for identifier in ids)


def test_parser_families_priorities_and_statuses_are_valid() -> None:
    categories = website_registry()["categories"]

    assert {category["parser_family"] for category in categories} == VALID_PARSER_FAMILIES
    assert all(category["priority"] in VALID_PRIORITIES for category in categories)
    assert all(category["status"] in VALID_STATUSES for category in categories)


def test_schema_v2_and_architecture_documents_exist() -> None:
    required = [
        Path("docs/website-wide-corpus-architecture.md"),
        Path("docs/book-registry-schema.md"),
        Path("docs/unified-corpus-schema-v2.md"),
        Path("docs/adr/ADR-001-website-wide-corpus-scope.md"),
        Path("reports/parser-strategy-matrix.md"),
        Path("reports/website-corpus-expansion-plan.md"),
    ]

    assert all(path.exists() and path.stat().st_size > 100 for path in required)
    schema = Path("docs/unified-corpus-schema-v2.md").read_text(encoding="utf-8")
    for record_type in (
        "verse",
        "hymn",
        "prose_section",
        "grammar_rule",
        "dictionary_entry",
        "encyclopedia_entry",
        "manuscript_image",
        "external_reference",
    ):
        assert f"`{record_type}`" in schema


def test_existing_thirumurai_registry_statuses_are_preserved() -> None:
    entries = {
        entry["corpus_id"]: entry for entry in thirumurai_registry()["corpora"]
    }

    assert entries["thirumurai_02"]["status"] == "available"
    assert entries["thirumurai_04"]["status"] == "available"
    assert entries["thirumurai_04"]["verification_status"] == "pilot_verified"
    assert all(entry["collection_family"] == "thirumurai" for entry in entries.values())


def test_frozen_corpus_checksum_is_unchanged() -> None:
    release = Path("data/releases/irandaam-thirumurai-v1")
    expected = {}
    for line in (release / "corpus_checksum.sha256").read_text(encoding="utf-8").splitlines():
        digest, filename = line.split(maxsplit=1)
        expected[filename] = digest

    corpus_path = release / "irandaam_thirumurai.jsonl"
    actual = hashlib.sha256(corpus_path.read_bytes()).hexdigest()

    assert actual == expected["irandaam_thirumurai.jsonl"]


def test_architecture_phase_contains_no_new_scraper_command() -> None:
    architecture = Path("docs/website-wide-corpus-architecture.md").read_text(
        encoding="utf-8"
    )
    plan = Path("reports/website-corpus-expansion-plan.md").read_text(encoding="utf-8")

    assert "not a crawl frontier" in architecture
    assert "No website-wide scrape" in Path(
        "docs/adr/ADR-001-website-wide-corpus-scope.md"
    ).read_text(encoding="utf-8")
    assert "allowlisted books" in plan
