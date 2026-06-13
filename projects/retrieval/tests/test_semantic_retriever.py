import json

import numpy as np
import pytest

from retrieval.semantic_retriever import SemanticRetriever
from vector_index.build_faiss_index import build_vector_index


class FakeQueryModel:
    model_name = "fake-model"

    def __init__(self, vector: list[float] | None = None) -> None:
        self.vector = np.asarray(vector or [1.0, 0.0], dtype=np.float32)

    def encode_query(self, query_text: str) -> np.ndarray:
        return self.vector / np.linalg.norm(self.vector)


def embedding_record(chunk_id: str, parent_record_id: str, key: str, vector: list[float]) -> dict:
    return {
        "chunk_id": chunk_id,
        "parent_record_id": parent_record_id,
        "chunk_type": "verse_plus_commentary",
        "citation": {"citation_string": f"Citation {chunk_id}"},
        "source_urls": {"hymn_url": "https://www.tamilvu.org/", "commentary_url": "https://www.tamilvu.org/urai"},
        "filter_metadata": {"hymn_id": parent_record_id},
        "deterministic_rank_key": key,
        "embedding_model": "fake-model",
        "embedding_dimension": len(vector),
        "chunk_text_sha256": chunk_id,
        "embedding": vector,
    }


def write_json(path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def create_semantic_fixture(tmp_path):
    embeddings_path = tmp_path / "embeddings.jsonl"
    vector_dir = tmp_path / "vector_index"
    vector_manifest = vector_dir / "vector_index_manifest.json"
    embedding_manifest = tmp_path / "embedding_manifest.json"
    write_jsonl(
        embeddings_path,
        [
            embedding_record("c2", "r2", "002", [0.0, 1.0]),
            embedding_record("c1", "r1", "001", [1.0, 0.0]),
            embedding_record("c3", "r3", "003", [1.0, 0.0]),
        ],
    )
    build_vector_index(embeddings_path=embeddings_path, output_dir=vector_dir, manifest_path=vector_manifest)
    write_json(embedding_manifest, {"embedding_model": "fake-model"})
    return embedding_manifest, vector_manifest


def test_semantic_top_k_result_format(tmp_path) -> None:
    embedding_manifest, vector_manifest = create_semantic_fixture(tmp_path)
    retriever = SemanticRetriever(
        embedding_manifest_path=embedding_manifest,
        vector_manifest_path=vector_manifest,
        model=FakeQueryModel([1.0, 0.0]),
    )

    results = retriever.search("அருள்", top_k=2)

    assert len(results) == 2
    assert results[0]["retrieval_mode"] == "semantic"
    assert results[0]["chunk_id"] == "c1"
    assert results[0]["parent_record_id"] == "r1"
    assert results[0]["record_id"] == "r1"
    assert "citation_text" in results[0]


def test_semantic_deterministic_tie_breaking(tmp_path) -> None:
    embedding_manifest, vector_manifest = create_semantic_fixture(tmp_path)
    retriever = SemanticRetriever(
        embedding_manifest_path=embedding_manifest,
        vector_manifest_path=vector_manifest,
        model=FakeQueryModel([1.0, 0.0]),
    )

    first = retriever.search("query", top_k=3)
    second = retriever.search("query", top_k=3)

    assert first == second
    assert [result["chunk_id"] for result in first[:2]] == ["c1", "c3"]


def test_semantic_retriever_missing_index(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        SemanticRetriever(
            embedding_manifest_path=tmp_path / "embedding_manifest.json",
            vector_manifest_path=tmp_path / "missing_manifest.json",
            model=FakeQueryModel(),
        )

