from enrichment.build_retrieval_ready_corpus import (
    build_lexical_index,
    build_retrieval_ready,
    canonical_id,
    create_chunks,
    create_golden_queries,
    enrich_record,
    normalize_text,
    record_id,
    tamil_tokens,
    validate_outputs,
    verse_id,
)


def sample_record() -> dict:
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
        "thirumurai": "Irandaam Thirumurai",
        "thirumurai_number": 2,
        "author": "Sambandar",
        "hymn_id": "1664",
        "hymn_title": "2.1 திருப்பூந்தராய் - வினா உரை - இந்தளம்",
        "hymn_location": "திருப்பூந்தராய்",
        "hymn_note": "வினா உரை",
        "pann": "இந்தளம்",
        "song_no": "1470",
        "verse_index_in_hymn": 1,
        "verse_text": "செந்நெல்  அம்\r\nகழனி",
        "commentary_available": True,
        "pozhppurai": "பொழிப்புரை: அருள் உரை",
        "kurippurai": "கு-ரை; குறிப்பு உரை",
        "hymn_url": "https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1664",
        "commentary_url": "https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=1470&book_id=110&head_id=60&sub_id=1664",
        "source_parameters": {"subid": "1664", "sub_id": "1664", "song_no": "1470"},
        "text_statistics": {},
        "extraction_metadata": {"extraction_status": "success", "warnings": []},
    }


def test_unicode_and_whitespace_normalization() -> None:
    assert normalize_text(" அம்\u00a0  தமிழ்\r\n\r\n உரை ") == "அம் தமிழ்\nஉரை"


def test_stable_id_generation() -> None:
    assert record_id("1664", "1470") == "thevaram_02_1664_1470"
    assert verse_id("1664", "1470") == "thevaram_02_1664_1470_verse"
    assert canonical_id("1664", "1470") == "tvu_thevaram_irandaam_thirumurai_1664_1470"


def test_tamil_tokenization() -> None:
    assert tamil_tokens("அருள், சிவன்; தமிழ்!") == ["அருள்", "சிவன்", "தமிழ்"]


def test_enrich_record_and_citation() -> None:
    enriched = enrich_record(sample_record())

    assert enriched["record_id"] == "thevaram_02_1664_1470"
    assert enriched["pozhppurai_normalized"] == "அருள் உரை"
    assert enriched["kurippurai_normalized"] == "குறிப்பு உரை"
    assert "TamilVU" in enriched["citation_text"]
    assert enriched["filter_metadata"]["hymn_id"] == "1664"


def test_chunk_creation() -> None:
    enriched = enrich_record(sample_record())
    chunks = create_chunks([enriched])
    chunk_types = {chunk["chunk_type"] for chunk in chunks}

    assert chunk_types == {
        "verse_only",
        "verse_plus_commentary",
        "metadata_context",
        "pozhppurai_only",
        "kurippurai_only",
    }
    assert all(chunk["chunk_id"].startswith(enriched["record_id"]) for chunk in chunks)


def test_lexical_index_creation() -> None:
    enriched = enrich_record(sample_record())
    chunks = create_chunks([enriched])
    index = build_lexical_index([enriched], chunks)

    assert index["song_no_to_record_id"]["1470"] == "thevaram_02_1664_1470"
    assert "1664" in index["hymn_id_to_record_ids"]
    assert "அருள்" in index["term_to_record_ids"]


def test_golden_query_creation() -> None:
    records = [enrich_record(sample_record())]
    chunks = create_chunks(records)
    queries = create_golden_queries(records, chunks, seed=42)

    assert any(query["query_id"] == "exact_song_no_1470" for query in queries)
    assert all("expected_record_ids" in query for query in queries)


def test_validation_checks() -> None:
    source = [sample_record()]
    records = [enrich_record(source[0])]
    chunks = create_chunks(records)
    index = build_lexical_index(records, chunks)
    queries = create_golden_queries(records, chunks, seed=42)

    result = validate_outputs(source, records, chunks, index, queries)

    assert result.ok is False
    assert any("partial_commentary" in error for error in result.errors)


def test_deterministic_build(tmp_path) -> None:
    input_path = tmp_path / "input.jsonl"
    input_path.write_text(__import__("json").dumps(sample_record(), ensure_ascii=False) + "\n", encoding="utf-8")

    first = build_retrieval_ready(input_path, seed=42)
    second = build_retrieval_ready(input_path, seed=42)

    assert first[0] == second[0]
    assert first[1] == second[1]
    assert first[2] == second[2]
    assert first[3] == second[3]
