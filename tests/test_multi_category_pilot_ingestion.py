import hashlib
import json
from pathlib import Path

import pytest

from corpus.normalize_category_corpus import normalize_category
from corpus.pilot_ingest_category import ingest_category
from corpus.validate_category_corpus import validate_records


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "data/processed/corpus_registry/pilot_category_plan.json"
REGISTRY = ROOT / "data/processed/corpus_registry/website_category_registry.json"


def seed_workspace(tmp_path: Path) -> None:
    registry_dir = tmp_path / "data/processed/corpus_registry"
    registry_dir.mkdir(parents=True)
    (registry_dir / "pilot_category_plan.json").write_text(
        PLAN.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (registry_dir / "website_category_registry.json").write_text(
        REGISTRY.read_text(encoding="utf-8"), encoding="utf-8"
    )
    seed = tmp_path / "data/processed/normalized/thirumurai_04_normalized.jsonl"
    seed.parent.mkdir(parents=True)
    source = {
        "record_id": "thevaram_04_1912_1",
        "corpus_id": "thirumurai_04",
        "collection": "Thirumurai",
        "canonical_title": "Naangaam Thirumurai",
        "author": "Tirunavukkarasar",
        "hymn_id": "1912",
        "pathigam_id": "1912",
        "song_no": "1",
        "verse_no": "1",
        "title": "திருஅதிகைவீரட்டானம்",
        "verse_text": "தமிழ் பாடல் வரி",
        "pozhppurai": "பொழிப்பு",
        "kurippurai": "குறிப்பு",
        "source_url": "https://www.tamilvu.org/slet/example?subid=1912",
        "commentary_url": "https://www.tamilvu.org/slet/commentary?song_no=1",
        "metadata": {"source": "TamilVU"},
    }
    seed.write_text(json.dumps(source, ensure_ascii=False) + "\n", encoding="utf-8")


def test_pilot_plan_contains_six_valid_categories() -> None:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    category_ids = {item["category_id"] for item in registry["categories"]}

    assert len(plan["pilots"]) == 6
    assert all(pilot["category_id"] in category_ids for pilot in plan["pilots"])
    assert all(pilot["max_books"] == 1 for pilot in plan["pilots"])
    assert all(pilot["max_records"] == 10 for pilot in plan["pilots"])
    assert plan["network_access"] is False


def test_dry_run_writes_nothing(tmp_path) -> None:
    seed_workspace(tmp_path)
    summary = ingest_category("grammar", dry_run=True, base_dir=tmp_path)

    assert summary["network_requests"] == 0
    assert summary["writes"] == 0
    assert not (tmp_path / "data/raw/pilot_categories").exists()
    assert not (tmp_path / "data/processed/pilot_categories").exists()


def test_pending_category_cannot_ingest_without_inspection(tmp_path) -> None:
    seed_workspace(tmp_path)

    with pytest.raises(ValueError, match="no inspected local source"):
        ingest_category("grammar", base_dir=tmp_path)


def test_bounded_ingestion_normalization_and_validation(tmp_path) -> None:
    seed_workspace(tmp_path)
    summary = ingest_category("saivam", max_records=1, base_dir=tmp_path)
    records, output, _ = normalize_category("saivam", base_dir=tmp_path)
    result = validate_records(records, "saivam")

    assert summary["record_count"] == 1
    assert summary["network_requests"] == 0
    assert output.name == "saivam_normalized.jsonl"
    assert records[0]["schema_version"] == "website-corpus-v2"
    assert records[0]["book_id"] == "panniru_thirumurai"
    assert records[0]["verse_text"] == "தமிழ் பாடல் வரி"
    assert result["status"] == "VALID"
    assert result["source_url_coverage"] == 1.0


def test_write_once_prevents_changed_output_overwrite(tmp_path) -> None:
    seed_workspace(tmp_path)
    ingest_category("saivam", max_records=1, base_dir=tmp_path)

    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        ingest_category("saivam", max_records=2, base_dir=tmp_path)


def test_validator_catches_missing_required_fields() -> None:
    result = validate_records(
        [
            {
                "schema_version": "website-corpus-v2",
                "record_id": "r1",
                "record_type": "verse",
                "category_id": "saivam",
                "book_id": "",
                "work_id": "work",
                "language": "ta",
                "content_text": "",
                "source_url": "",
                "source_metadata": {},
                "parser_family": "verse_parser",
            }
        ],
        "saivam",
    )

    assert result["status"] == "INVALID"
    assert result["missing_fields"]["book_id"] == 1
    assert result["missing_fields"]["content_text_or_verse_text"] == 1


def test_full_scope_and_frozen_artifacts_are_unchanged() -> None:
    corpus = ROOT / "data/releases/irandaam-thirumurai-v1/irandaam_thirumurai.jsonl"
    checksums = ROOT / "data/releases/irandaam-thirumurai-v1/corpus_checksum.sha256"
    expected = {
        filename: digest
        for digest, filename in (
            line.split(maxsplit=1)
            for line in checksums.read_text(encoding="utf-8").splitlines()
        )
    }
    script = (ROOT / "src/corpus/pilot_ingest_category.py").read_text(encoding="utf-8")

    assert hashlib.sha256(corpus.read_bytes()).hexdigest() == expected[corpus.name]
    assert "import requests" not in script
    assert "from requests" not in script
    assert "import httpx" not in script
    assert "from httpx" not in script
    assert "MAX_PILOT_RECORDS = 10" in script
    assert "MAX_PILOT_BOOKS = 1" in script
