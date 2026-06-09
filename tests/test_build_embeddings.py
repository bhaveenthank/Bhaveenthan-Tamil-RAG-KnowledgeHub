import json

import pytest

from embeddings.build_embeddings import (
    ALL_CHUNK_TYPES,
    DEFAULT_CHUNK_TYPES,
    build_embeddings,
    embedding_record,
    parse_chunk_types,
    selected_chunks,
    sha256_text,
)


class FakeEmbeddingModel:
    model_name = "fake-local-model"

    def encode(self, texts: list[str], batch_size: int) -> list[list[float]]:
        return [[float(len(text)), float(index), float(batch_size)] for index, text in enumerate(texts)]


def sample_chunk(chunk_type: str = "verse_plus_commentary", suffix: str = "a") -> dict:
    return {
        "chunk_id": f"thevaram_02_1664_1470_{chunk_type}_{suffix}",
        "parent_record_id": "thevaram_02_1664_1470",
        "chunk_type": chunk_type,
        "chunk_text": "செந்நெல் அம் கழனி",
        "chunk_text_normalized": "செந்நெல் அம் கழனி",
        "source_urls": {
            "hymn_url": "https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1664",
            "commentary_url": "https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=1470&book_id=110&head_id=60&sub_id=1664",
        },
        "filter_metadata": {"hymn_id": "1664", "song_no": "1470"},
        "citation": {"citation_string": "TamilVU citation"},
        "deterministic_rank_key": f"1664:1470:{chunk_type}:{suffix}",
    }


def write_jsonl(path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def read_jsonl(path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_parse_chunk_types_default() -> None:
    assert parse_chunk_types([]) == DEFAULT_CHUNK_TYPES


def test_parse_chunk_types_all() -> None:
    assert parse_chunk_types([], include_all=True) == ALL_CHUNK_TYPES


def test_parse_chunk_types_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        parse_chunk_types(["verse_plus_commentary,unknown"])


def test_selected_chunks_filters_type_and_empty_text() -> None:
    chunks = [
        sample_chunk("verse_plus_commentary", "b"),
        sample_chunk("verse_only", "a"),
        {**sample_chunk("verse_plus_commentary", "c"), "chunk_text_normalized": "", "chunk_text": ""},
    ]

    selected = selected_chunks(chunks, ("verse_plus_commentary",))

    assert [chunk["chunk_id"] for chunk in selected] == ["thevaram_02_1664_1470_verse_plus_commentary_b"]


def test_embedding_record_preserves_ids_and_metadata() -> None:
    chunk = sample_chunk()
    record = embedding_record(chunk, [0.1, 0.2, 0.3], "fake-local-model")

    assert record["chunk_id"] == chunk["chunk_id"]
    assert record["parent_record_id"] == chunk["parent_record_id"]
    assert record["source_urls"] == chunk["source_urls"]
    assert record["embedding_dimension"] == 3
    assert record["chunk_text_sha256"] == sha256_text(chunk["chunk_text_normalized"])


def test_build_embeddings_writes_jsonl_and_manifest(tmp_path) -> None:
    input_path = tmp_path / "chunks.jsonl"
    output_path = tmp_path / "embeddings.jsonl"
    manifest_path = tmp_path / "manifest.json"
    chunks = [sample_chunk("metadata_context", "a"), sample_chunk("verse_plus_commentary", "b")]
    write_jsonl(input_path, chunks)

    result = build_embeddings(
        input_path=input_path,
        output_path=output_path,
        manifest_path=manifest_path,
        model=FakeEmbeddingModel(),
        chunk_types=("verse_plus_commentary",),
        batch_size=8,
    )

    records = read_jsonl(output_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert result.embedded_count == 1
    assert result.skipped_count == 1
    assert result.vector_dimension == 3
    assert records[0]["chunk_type"] == "verse_plus_commentary"
    assert records[0]["embedding"] == [17.0, 0.0, 8.0]
    assert manifest["embedded_count"] == 1
    assert manifest["vector_database_created"] is False
    assert manifest["paid_api_used"] is False


def test_build_embeddings_is_deterministic(tmp_path) -> None:
    input_path = tmp_path / "chunks.jsonl"
    first_output = tmp_path / "first.jsonl"
    first_manifest = tmp_path / "first_manifest.json"
    second_output = tmp_path / "second.jsonl"
    second_manifest = tmp_path / "second_manifest.json"
    write_jsonl(input_path, [sample_chunk("verse_plus_commentary", "b"), sample_chunk("verse_plus_commentary", "a")])

    build_embeddings(
        input_path=input_path,
        output_path=first_output,
        manifest_path=first_manifest,
        model=FakeEmbeddingModel(),
        chunk_types=("verse_plus_commentary",),
        batch_size=4,
    )
    build_embeddings(
        input_path=input_path,
        output_path=second_output,
        manifest_path=second_manifest,
        model=FakeEmbeddingModel(),
        chunk_types=("verse_plus_commentary",),
        batch_size=4,
    )

    assert first_output.read_text(encoding="utf-8") == second_output.read_text(encoding="utf-8")
    assert json.loads(first_manifest.read_text(encoding="utf-8"))["build_fingerprint"] == json.loads(
        second_manifest.read_text(encoding="utf-8")
    )["build_fingerprint"]
