import json

import numpy as np
import pytest

from vector_index.build_faiss_index import (
    build_vector_index,
    normalized_matrix,
    validate_embedding_records,
)


def embedding_record(chunk_id: str = "c1", parent_record_id: str = "r1", embedding=None) -> dict:
    embedding = embedding if embedding is not None else [3.0, 4.0]
    return {
        "chunk_id": chunk_id,
        "parent_record_id": parent_record_id,
        "chunk_type": "verse_plus_commentary",
        "citation": {"citation_string": "TamilVU citation"},
        "source_urls": {"hymn_url": "https://www.tamilvu.org/", "commentary_url": "https://www.tamilvu.org/urai"},
        "filter_metadata": {"hymn_id": "1664"},
        "deterministic_rank_key": chunk_id,
        "embedding_model": "fake-model",
        "embedding_dimension": len(embedding),
        "chunk_text_sha256": "abc",
        "embedding": embedding,
    }


def write_jsonl(path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_dimension_validation_accepts_consistent_records() -> None:
    assert validate_embedding_records([embedding_record(), embedding_record("c2", "r2")]) == 2


def test_dimension_validation_rejects_mismatch() -> None:
    with pytest.raises(ValueError):
        validate_embedding_records([{**embedding_record(), "embedding_dimension": 3}])


def test_normalized_matrix() -> None:
    matrix = normalized_matrix([embedding_record()], 2)

    assert matrix.shape == (1, 2)
    assert np.isclose(np.linalg.norm(matrix[0]), 1.0)


def test_index_artifact_creation(tmp_path) -> None:
    embeddings_path = tmp_path / "embeddings.jsonl"
    output_dir = tmp_path / "index"
    manifest_path = output_dir / "vector_index_manifest.json"
    write_jsonl(embeddings_path, [embedding_record("c2", "r2"), embedding_record("c1", "r1")])

    result = build_vector_index(embeddings_path=embeddings_path, output_dir=output_dir, manifest_path=manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    metadata_lines = (output_dir / "metadata.jsonl").read_text(encoding="utf-8").splitlines()

    assert result.vector_count == 2
    assert result.embedding_dimension == 2
    assert result.index_type in {"faiss", "numpy"}
    assert (output_dir / "embeddings.npy").exists()
    assert len(metadata_lines) == 2
    assert manifest["managed_vector_database"] is False
    assert manifest["vectors_normalized_for_cosine"] is True

