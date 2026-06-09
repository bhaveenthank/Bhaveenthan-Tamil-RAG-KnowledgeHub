import json

from corpus.normalize_corpus import build_manifest, normalize_record, write_jsonl
from corpus.validate_corpus import validate_records


def source_record() -> dict:
    return {
        "record_id": "thevaram_02_1664_1470",
        "canonical_id": "canonical-1470",
        "source_record_id": "tvu:1664:1470",
        "verse_id": "verse-1470",
        "source": "TamilVU",
        "source_site": "https://www.tamilvu.org",
        "source_corpus_version": "irandaam-thirumurai-v1",
        "enriched_corpus_version": "irandaam-thirumurai-v1.1",
        "author": "Sambandar",
        "collection": "Thevaram",
        "work": "Panniru Thirumurai",
        "hymn_id": "1664",
        "song_no": "1470",
        "verse_index_in_hymn": 1,
        "hymn_title": "திருப்பூந்தராய்",
        "hymn_location": "திருப்பூந்தராய்",
        "hymn_note": "வினா உரை",
        "pann": "இந்தளம்",
        "verse_text_normalized": "தமிழ் பாடல்",
        "pozhppurai_normalized": "பொழிப்புரை",
        "kurippurai_normalized": "குறிப்புரை",
        "hymn_url": "https://www.tamilvu.org/hymn",
        "commentary_url": "https://www.tamilvu.org/commentary",
        "citation_text": "citation",
        "commentary_available": True,
        "extraction_metadata": {"extraction_status": "success"},
    }


def registry() -> dict:
    path = "data/processed/corpus_registry/thirumurai_registry.json"
    return json.loads(open(path, encoding="utf-8").read())


def test_registry_has_all_twelve_thirumurai() -> None:
    entries = registry()["corpora"]

    assert len(entries) == 12
    assert [entry["thirumurai_no"] for entry in entries] == list(range(1, 13))
    assert len({entry["corpus_id"] for entry in entries}) == 12


def test_irandaam_thirumurai_is_available() -> None:
    entry = next(
        entry for entry in registry()["corpora"] if entry["corpus_id"] == "thirumurai_02"
    )

    assert entry["status"] == "available"
    assert entry["source_type"] == "local"


def test_normalized_schema_contains_required_fields() -> None:
    normalized = normalize_record(source_record())
    result = validate_records([normalized])

    assert result["status"] == "VALID"
    assert normalized["record_id"] == "thevaram_02_1664_1470"
    assert normalized["corpus_id"] == "thirumurai_02"
    assert normalized["thirumurai_no"] == 2
    assert normalized["metadata"]["canonical_id"] == "canonical-1470"


def test_validator_detects_missing_required_fields() -> None:
    normalized = normalize_record(source_record())
    normalized["author"] = ""
    del normalized["verse_text"]

    result = validate_records([normalized])

    assert result["status"] == "INVALID"
    assert result["missing_fields"]["author"] == 1
    assert result["missing_fields"]["verse_text"] == 1


def test_validator_detects_duplicate_record_ids() -> None:
    normalized = normalize_record(source_record())

    result = validate_records([normalized, dict(normalized)])

    assert result["status"] == "INVALID"
    assert result["duplicate_record_ids"] == ["thevaram_02_1664_1470"]


def test_validator_detects_invalid_thirumurai_number() -> None:
    normalized = normalize_record(source_record())
    normalized["thirumurai_no"] = 13

    result = validate_records([normalized])

    assert result["status"] == "INVALID"
    assert result["invalid_thirumurai_no"] == 1


def test_normalization_output_is_deterministic(tmp_path) -> None:
    records = [normalize_record(source_record())]
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"

    write_jsonl(first, records)
    write_jsonl(second, records)

    assert first.read_bytes() == second.read_bytes()


def test_manifest_generation() -> None:
    records = [normalize_record(source_record())]
    manifest = build_manifest(registry(), records, {})

    assert manifest["total_corpora_registered"] == 12
    assert manifest["available_corpora"] == ["thirumurai_02"]
    assert manifest["normalized_corpora"] == ["thirumurai_02"]
    assert manifest["total_normalized_records"] == 1
    assert manifest["readiness_status"] == "READY_FOR_CONTROLLED_EXPANSION"
