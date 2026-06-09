from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

DEFAULT_EMBEDDINGS = Path("data/processed/embeddings/irandaam_thirumurai_embeddings.jsonl")
DEFAULT_OUTPUT_DIR = Path("data/processed/vector_index/irandaam_thirumurai")
DEFAULT_MANIFEST = DEFAULT_OUTPUT_DIR / "vector_index_manifest.json"
NUMPY_ARRAY_NAME = "embeddings.npy"
METADATA_NAME = "metadata.jsonl"
FAISS_INDEX_NAME = "index.faiss"
SCHEMA_VERSION = "tvu-local-vector-index-v1"


@dataclass(slots=True)
class VectorIndexBuildResult:
    index_type: str
    vector_count: int
    embedding_dimension: int
    output_dir: Path
    manifest_path: Path


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def faiss_available() -> bool:
    try:
        import faiss  # noqa: F401
    except ImportError:
        return False
    return True


def validate_embedding_records(records: list[dict[str, Any]]) -> int:
    if not records:
        raise ValueError("embedding file contains no records")
    missing_ids = [index for index, record in enumerate(records, start=1) if not record.get("chunk_id") or not record.get("parent_record_id")]
    if missing_ids:
        raise ValueError(f"embedding records missing chunk_id or parent_record_id at rows: {missing_ids[:10]}")
    dimensions = {int(record.get("embedding_dimension", 0)) for record in records}
    actual_dimensions = {len(record.get("embedding", [])) for record in records}
    if len(dimensions) != 1 or len(actual_dimensions) != 1 or dimensions != actual_dimensions:
        raise ValueError(
            f"embedding dimension mismatch: declared={sorted(dimensions)} actual={sorted(actual_dimensions)}"
        )
    if next(iter(dimensions)) <= 0:
        raise ValueError("embedding dimension must be positive")
    duplicate_chunks = [chunk_id for chunk_id, count in Counter(record["chunk_id"] for record in records).items() if count > 1]
    if duplicate_chunks:
        raise ValueError(f"duplicate chunk_id values: {duplicate_chunks[:10]}")
    return next(iter(dimensions))


def normalized_matrix(records: list[dict[str, Any]], dimension: int) -> np.ndarray:
    matrix = np.asarray([record["embedding"] for record in records], dtype=np.float32)
    if matrix.shape != (len(records), dimension):
        raise ValueError(f"unexpected embedding matrix shape: {matrix.shape}")
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    if np.any(norms == 0):
        raise ValueError("zero-length embedding vector detected")
    return matrix / norms


def metadata_record(record: dict[str, Any], position: int) -> dict[str, Any]:
    citation = record.get("citation", {})
    return {
        "position": position,
        "chunk_id": record["chunk_id"],
        "parent_record_id": record["parent_record_id"],
        "record_id": record["parent_record_id"],
        "chunk_type": record["chunk_type"],
        "citation_text": citation.get("citation_string", ""),
        "citation": citation,
        "source_urls": record.get("source_urls", {}),
        "filter_metadata": record.get("filter_metadata", {}),
        "deterministic_rank_key": record["deterministic_rank_key"],
        "embedding_model": record.get("embedding_model", ""),
        "embedding_dimension": record.get("embedding_dimension", 0),
        "chunk_text_sha256": record.get("chunk_text_sha256", ""),
    }


def build_manifest(
    *,
    embeddings_path: Path,
    output_dir: Path,
    records: list[dict[str, Any]],
    dimension: int,
    index_type: str,
    faiss_index_path: Path | None,
) -> dict[str, Any]:
    model_names = sorted({record.get("embedding_model", "") for record in records})
    chunk_type_counts = Counter(record["chunk_type"] for record in records)
    return {
        "artifact_type": "local_vector_index",
        "schema_version": SCHEMA_VERSION,
        "index_type": index_type,
        "vector_count": len(records),
        "embedding_dimension": dimension,
        "embedding_models": model_names,
        "embedding_source_path": str(embeddings_path),
        "embedding_source_sha256": sha256_file(embeddings_path),
        "output_dir": str(output_dir),
        "numpy_array_path": str(output_dir / NUMPY_ARRAY_NAME),
        "metadata_path": str(output_dir / METADATA_NAME),
        "faiss_index_path": str(faiss_index_path) if faiss_index_path else "",
        "chunk_type_counts": dict(sorted(chunk_type_counts.items())),
        "vectors_normalized_for_cosine": True,
        "similarity": "cosine",
        "tie_break": "similarity desc, deterministic_rank_key asc, chunk_id asc",
        "managed_vector_database": False,
        "cloud_services_used": False,
    }


def build_vector_index(
    embeddings_path: Path = DEFAULT_EMBEDDINGS,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    manifest_path: Path = DEFAULT_MANIFEST,
) -> VectorIndexBuildResult:
    records = load_jsonl(embeddings_path)
    records = sorted(records, key=lambda record: (record["deterministic_rank_key"], record["chunk_id"]))
    dimension = validate_embedding_records(records)
    matrix = normalized_matrix(records, dimension)
    metadata = [metadata_record(record, position) for position, record in enumerate(records)]

    output_dir.mkdir(parents=True, exist_ok=True)
    np.save(output_dir / NUMPY_ARRAY_NAME, matrix)
    write_jsonl(metadata, output_dir / METADATA_NAME)

    index_type = "numpy"
    faiss_index_path = None
    if faiss_available():
        import faiss

        index = faiss.IndexFlatIP(dimension)
        index.add(matrix)
        faiss_index_path = output_dir / FAISS_INDEX_NAME
        faiss.write_index(index, str(faiss_index_path))
        index_type = "faiss"

    manifest = build_manifest(
        embeddings_path=embeddings_path,
        output_dir=output_dir,
        records=records,
        dimension=dimension,
        index_type=index_type,
        faiss_index_path=faiss_index_path,
    )
    write_json(manifest, manifest_path)

    return VectorIndexBuildResult(
        index_type=index_type,
        vector_count=len(records),
        embedding_dimension=dimension,
        output_dir=output_dir,
        manifest_path=manifest_path,
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a local FAISS or NumPy vector index from TamilVU embeddings")
    parser.add_argument("--embeddings", type=Path, default=DEFAULT_EMBEDDINGS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = build_vector_index(
            embeddings_path=args.embeddings,
            output_dir=args.output_dir,
            manifest_path=args.manifest,
        )
    except Exception as exc:
        print(f"Vector index build failed: {exc}", file=sys.stderr)
        return 1
    print(
        "Vector index build complete: "
        f"type={result.index_type} vectors={result.vector_count} dimension={result.embedding_dimension} "
        f"output={result.output_dir} manifest={result.manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

