from knowledge.build_saanrugraph_high_confidence_rag_pack import (
    RELATION_TO_CAPABILITY,
    build_capabilities,
    build_chunk_text,
    build_questions,
    build_rag_corpus,
    evidence_path,
)


def row(link_id: str, relation: str) -> dict:
    capability = RELATION_TO_CAPABILITY[relation]
    return {
        "link_id": link_id,
        "paadal_id": "thirumurai_01_paadal_1",
        "commentary_id": "thirumurai_01_paadal_1_commentary",
        "thirumurai_no": "1",
        "pathigam_id": "thirumurai_01_thogupu_1",
        "hymn_id": "thirumurai_01_thogupu_1",
        "relationship_type": relation,
        "capability_id": capability["capability_id"],
        "capability_name": capability["capability_name"],
        "question_type": capability["question_type"],
        "source_text": "விடை ஏறி",
        "target_text": "விடை மீது ஏறி",
        "source_start_char": "0",
        "source_end_char": "8",
        "target_start_char": "10",
        "target_end_char": "22",
        "full_paadal_text": "விடை ஏறி",
        "full_pozhippurai": "விடை மீது ஏறி",
        "source_url": "https://example.test/paadal",
        "commentary_url": "https://example.test/commentary",
        "evidence_path": "path",
        "global_song_no": "1",
        "confidence": "high",
        "score": "0.99",
    }


def test_evidence_path_contains_offsets() -> None:
    path = evidence_path(row("x", "interprets_image"))
    assert "Thirumurai 1" in path
    assert "source[0:8]" in path
    assert "pozhippurai[10:22]" in path


def test_capabilities_cover_all_relation_types() -> None:
    rows = [row(str(index), relation) for index, relation in enumerate(RELATION_TO_CAPABILITY, start=1)]
    capabilities = build_capabilities(rows)
    assert len(capabilities) == len(RELATION_TO_CAPABILITY)
    assert all(item["can_support_rag_now"] is False for item in capabilities)


def test_questions_are_balanced_by_relation() -> None:
    rows = []
    for relation in RELATION_TO_CAPABILITY:
        rows.extend(row(f"{relation}_{index}", relation) for index in range(3))
    questions = build_questions(rows, per_capability=2)
    assert len(questions) == len(RELATION_TO_CAPABILITY) * 2
    assert all(question["question_tamil"] for question in questions)
    assert all(question["gold_answer_outline"] for question in questions)


def test_chunk_text_contains_phase4_sections() -> None:
    chunk = build_chunk_text(row("x", "interprets_image"))
    assert "Paadal span:" in chunk
    assert "Pozhippurai explanation:" in chunk
    assert "Full Paadal:" in chunk
    assert "Evidence path:" in chunk


def test_rag_corpus_record_is_ready_to_index() -> None:
    rows = [row("x", "interprets_image")]
    corpus = build_rag_corpus(rows)
    assert len(corpus) == 1
    record = corpus[0]
    assert record["link_id"] == "x"
    assert record["chunk_type"] == "high_confidence_paadal_pozhippurai_evidence_path"
    assert record["chunk_text"]
    assert record["retrieval_fields"]["paadal_span"] == "விடை ஏறி"
    assert record["citation"]["commentary_url"] == "https://example.test/commentary"
