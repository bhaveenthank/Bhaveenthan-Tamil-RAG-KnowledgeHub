from retrieval.lexical_retriever import LexicalRetriever


def test_exact_song_no_lookup() -> None:
    results = LexicalRetriever().search("find song_no 1470", filters={"song_no": "1470"}, top_k=3)

    assert results
    assert results[0]["record_id"] == "thevaram_02_1664_1470"
    assert "exact_song_no" in results[0]["matched_fields"]


def test_exact_hymn_id_lookup() -> None:
    results = LexicalRetriever().search("find hymn_id 1664", filters={"hymn_id": "1664"}, top_k=10)

    assert {result["record_id"] for result in results} <= {
        f"thevaram_02_1664_{song_no}" for song_no in range(1470, 1480)
    }
    assert all("exact_hymn_id" in result["matched_fields"] for result in results)


def test_metadata_filter() -> None:
    results = LexicalRetriever().search("records", filters={"pann": "இந்தளம்"}, top_k=10)

    assert results
    assert all(result["record_id"].startswith("thevaram_02_") for result in results)


def test_keyword_retrieval() -> None:
    results = LexicalRetriever().search("அருள்", top_k=10)

    assert results
    assert any("pozhppurai_normalized" in result["matched_fields"] or "kurippurai_normalized" in result["matched_fields"] for result in results)


def test_deterministic_ranking() -> None:
    retriever = LexicalRetriever()

    first = retriever.search("அருள்", top_k=10)
    second = retriever.search("அருள்", top_k=10)

    assert first == second


def test_top_k_behavior() -> None:
    results = LexicalRetriever().search("அருள்", top_k=5)

    assert len(results) == 5


def test_citation_fields_exist() -> None:
    result = LexicalRetriever().search("find song_no 1470", filters={"song_no": "1470"}, top_k=1)[0]

    assert "TamilVU" in result["citation_text"]
    assert result["source_urls"]["hymn_url"].startswith("https://www.tamilvu.org/")
    assert result["source_urls"]["commentary_url"].startswith("https://www.tamilvu.org/")


def test_exact_record_and_chunk_lookup() -> None:
    retriever = LexicalRetriever()
    record_results = retriever.search("thevaram_02_1664_1470", top_k=1)
    chunk_results = retriever.search("thevaram_02_1664_1470_verse_only", top_k=1)

    assert record_results[0]["record_id"] == "thevaram_02_1664_1470"
    assert chunk_results[0]["chunk_id"] == "thevaram_02_1664_1470_verse_only"
