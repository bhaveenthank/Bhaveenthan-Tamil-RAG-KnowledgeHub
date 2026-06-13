from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from vector_index.build_faiss_index import METADATA_NAME, NUMPY_ARRAY_NAME, faiss_available, load_jsonl

DEFAULT_EMBEDDING_MANIFEST = Path("data/processed/embeddings/embedding_manifest.json")
DEFAULT_VECTOR_MANIFEST = Path("data/processed/vector_index/irandaam_thirumurai/vector_index_manifest.json")
DEFAULT_CACHE_DIR = Path("data/processed/embeddings/hf_cache")


@dataclass(slots=True)
class SemanticResult:
    rank: int
    similarity_score: float
    retrieval_mode: str
    chunk_id: str
    parent_record_id: str
    record_id: str
    chunk_type: str
    citation_text: str
    source_urls: dict[str, str]
    deterministic_rank_key: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "score": self.similarity_score,
            "similarity_score": self.similarity_score,
            "retrieval_mode": self.retrieval_mode,
            "chunk_id": self.chunk_id,
            "parent_record_id": self.parent_record_id,
            "record_id": self.record_id,
            "chunk_type": self.chunk_type,
            "citation_text": self.citation_text,
            "source_urls": self.source_urls,
            "deterministic_rank_key": self.deterministic_rank_key,
        }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector)
    if norm == 0:
        raise ValueError("query embedding has zero norm")
    return (vector / norm).astype(np.float32)


def passes_filters(metadata: dict[str, Any], filters: dict[str, Any]) -> bool:
    values = metadata.get("filter_metadata", {})
    for key, value in (filters or {}).items():
        if str(values.get(key)) != str(value):
            return False
    return True


class QueryEmbeddingModel:
    def __init__(self, model_name: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> None:
        os.environ.setdefault("HF_HOME", str(cache_dir.resolve()))
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Install `python3 -m pip install -e '.[embeddings]'`."
            ) from exc
        self.model_name = model_name
        self._model = SentenceTransformer(model_name, cache_folder=str(cache_dir))

    def encode_query(self, query_text: str) -> np.ndarray:
        vector = self._model.encode(
            [query_text],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]
        return normalize_vector(np.asarray(vector, dtype=np.float32))


class SemanticRetriever:
    def __init__(
        self,
        embedding_manifest_path: Path = DEFAULT_EMBEDDING_MANIFEST,
        vector_manifest_path: Path = DEFAULT_VECTOR_MANIFEST,
        cache_dir: Path = DEFAULT_CACHE_DIR,
        model: QueryEmbeddingModel | None = None,
    ) -> None:
        if not vector_manifest_path.exists():
            raise FileNotFoundError(f"vector index manifest not found: {vector_manifest_path}")
        self.embedding_manifest = load_json(embedding_manifest_path)
        self.vector_manifest = load_json(vector_manifest_path)
        self.index_type = self.vector_manifest["index_type"]
        self.dimension = int(self.vector_manifest["embedding_dimension"])
        output_dir = Path(self.vector_manifest["output_dir"])
        self.metadata = load_jsonl(output_dir / METADATA_NAME)
        self.matrix = np.load(output_dir / NUMPY_ARRAY_NAME)
        if self.matrix.shape != (len(self.metadata), self.dimension):
            raise ValueError(f"vector matrix and metadata mismatch: {self.matrix.shape} vs {len(self.metadata)}")
        self.model = model or QueryEmbeddingModel(self.embedding_manifest["embedding_model"], cache_dir=cache_dir)
        self._faiss_index = None
        if self.index_type == "faiss" and faiss_available():
            import faiss

            self._faiss_index = faiss.read_index(self.vector_manifest["faiss_index_path"])

    def search(self, query_text: str, filters: dict[str, Any] | None = None, top_k: int = 10) -> list[dict[str, Any]]:
        query_vector = self.model.encode_query(query_text)
        if query_vector.shape[0] != self.dimension:
            raise ValueError(f"query embedding dimension {query_vector.shape[0]} does not match index dimension {self.dimension}")
        candidates = self._search_candidates(query_vector, top_k=max(top_k * 20, top_k), filters=filters or {})
        candidates.sort(key=lambda item: (-item[0], item[1]["deterministic_rank_key"], item[1]["chunk_id"]))
        return [
            SemanticResult(
                rank=rank,
                similarity_score=round(float(score), 8),
                retrieval_mode="semantic",
                chunk_id=metadata["chunk_id"],
                parent_record_id=metadata["parent_record_id"],
                record_id=metadata["parent_record_id"],
                chunk_type=metadata["chunk_type"],
                citation_text=metadata["citation_text"],
                source_urls=metadata.get("source_urls", {}),
                deterministic_rank_key=metadata["deterministic_rank_key"],
            ).to_dict()
            for rank, (score, metadata) in enumerate(candidates[:top_k], start=1)
        ]

    def _search_candidates(
        self,
        query_vector: np.ndarray,
        top_k: int,
        filters: dict[str, Any],
    ) -> list[tuple[float, dict[str, Any]]]:
        if self._faiss_index is not None and not filters:
            scores, positions = self._faiss_index.search(query_vector.reshape(1, -1), min(top_k, len(self.metadata)))
            return [
                (float(score), self.metadata[int(position)])
                for score, position in zip(scores[0], positions[0])
                if int(position) >= 0
            ]

        scores = self.matrix @ query_vector
        candidates = []
        for position, score in enumerate(scores):
            metadata = self.metadata[position]
            if passes_filters(metadata, filters):
                candidates.append((float(score), metadata))
        return candidates


def parse_filter(values: list[str]) -> dict[str, str]:
    filters = {}
    for value in values:
        if "=" in value:
            key, raw = value.split("=", 1)
            filters[key] = raw
    return filters


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run local semantic retrieval over TamilVU vector index")
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--filter", action="append", default=[])
    args = parser.parse_args(argv)
    retriever = SemanticRetriever()
    results = retriever.search(args.query, filters=parse_filter(args.filter), top_k=args.top_k)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
