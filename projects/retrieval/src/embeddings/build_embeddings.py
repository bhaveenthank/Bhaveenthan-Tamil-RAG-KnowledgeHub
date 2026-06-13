from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

DEFAULT_INPUT = Path("data/processed/chunks/irandaam_thirumurai_chunks.jsonl")
DEFAULT_OUTPUT = Path("data/processed/embeddings/irandaam_thirumurai_embeddings.jsonl")
DEFAULT_MANIFEST = Path("data/processed/embeddings/embedding_manifest.json")
DEFAULT_CACHE_DIR = Path("data/processed/embeddings/hf_cache")
DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_CHUNK_TYPES = ("verse_plus_commentary",)
ALL_CHUNK_TYPES = (
    "verse_only",
    "pozhppurai_only",
    "kurippurai_only",
    "verse_plus_commentary",
    "metadata_context",
)
SCHEMA_VERSION = "tvu-local-embeddings-v1"
SOURCE_CHUNKS_VERSION = "irandaam-thirumurai-v1.1"


class EmbeddingModel(Protocol):
    model_name: str

    def encode(self, texts: list[str], batch_size: int) -> list[list[float]]:
        ...


@dataclass(slots=True)
class EmbeddingBuildResult:
    embedded_count: int
    skipped_count: int
    vector_dimension: int
    chunk_type_counts: dict[str, int]
    output_path: Path
    manifest_path: Path


class SentenceTransformerEmbeddingModel:
    def __init__(self, model_name: str, cache_dir: Path = DEFAULT_CACHE_DIR) -> None:
        os.environ.setdefault("HF_HOME", str(cache_dir.resolve()))
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Install the local embedding extras with "
                "`python3 -m pip install -e '.[embeddings]'` before generating embeddings."
            ) from exc

        self.model_name = model_name
        self._model = SentenceTransformer(model_name, cache_folder=str(cache_dir))

    def encode(self, texts: list[str], batch_size: int) -> list[list[float]]:
        vectors = self._model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [[float(value) for value in vector] for vector in vectors]


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_chunk_types(values: list[str], include_all: bool = False) -> tuple[str, ...]:
    if include_all:
        return ALL_CHUNK_TYPES
    if not values:
        return DEFAULT_CHUNK_TYPES
    parsed = []
    for value in values:
        for chunk_type in value.split(","):
            chunk_type = chunk_type.strip()
            if chunk_type:
                parsed.append(chunk_type)
    invalid = sorted(set(parsed) - set(ALL_CHUNK_TYPES))
    if invalid:
        raise ValueError(f"unsupported chunk type(s): {', '.join(invalid)}")
    return tuple(dict.fromkeys(parsed))


def selected_chunks(chunks: list[dict], chunk_types: tuple[str, ...]) -> list[dict]:
    selected = [
        chunk
        for chunk in chunks
        if chunk.get("chunk_type") in chunk_types and str(chunk.get("chunk_text_normalized") or chunk.get("chunk_text") or "").strip()
    ]
    return sorted(selected, key=lambda chunk: (chunk["deterministic_rank_key"], chunk["chunk_id"]))


def embedding_record(chunk: dict, vector: list[float], model_name: str) -> dict:
    text = str(chunk.get("chunk_text_normalized") or chunk.get("chunk_text") or "")
    return {
        "schema_version": SCHEMA_VERSION,
        "source_chunks_version": SOURCE_CHUNKS_VERSION,
        "embedding_model": model_name,
        "embedding_dimension": len(vector),
        "chunk_id": chunk["chunk_id"],
        "parent_record_id": chunk["parent_record_id"],
        "chunk_type": chunk["chunk_type"],
        "chunk_text_sha256": sha256_text(text),
        "source_urls": chunk.get("source_urls", {}),
        "filter_metadata": chunk.get("filter_metadata", {}),
        "citation": chunk.get("citation", {}),
        "deterministic_rank_key": chunk["deterministic_rank_key"],
        "embedding": vector,
    }


def build_manifest(
    *,
    input_path: Path,
    output_path: Path,
    model_name: str,
    chunk_types: tuple[str, ...],
    all_chunk_count: int,
    selected_count: int,
    embedded_records: list[dict],
    skipped_count: int,
) -> dict:
    type_counts = Counter(record["chunk_type"] for record in embedded_records)
    vector_dimension = embedded_records[0]["embedding_dimension"] if embedded_records else 0
    build_fingerprint = sha256_text(
        json.dumps(
            {
                "input_sha256": sha256_file(input_path),
                "model_name": model_name,
                "chunk_types": chunk_types,
                "schema_version": SCHEMA_VERSION,
                "record_count": len(embedded_records),
                "vector_dimension": vector_dimension,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return {
        "artifact_type": "local_embedding_manifest",
        "schema_version": SCHEMA_VERSION,
        "source_chunks_version": SOURCE_CHUNKS_VERSION,
        "source_chunks_path": str(input_path),
        "source_chunks_sha256": sha256_file(input_path),
        "output_path": str(output_path),
        "embedding_model": model_name,
        "embedding_backend": "sentence-transformers",
        "embedding_normalized": True,
        "chunk_types_requested": list(chunk_types),
        "all_input_chunk_count": all_chunk_count,
        "selected_chunk_count": selected_count,
        "embedded_count": len(embedded_records),
        "skipped_count": skipped_count,
        "embedding_dimension": vector_dimension,
        "chunk_type_counts": dict(sorted(type_counts.items())),
        "build_fingerprint": build_fingerprint,
        "id_policy": "chunk_id and parent_record_id are copied from retrieval-ready chunks; no random IDs are generated.",
        "cloud_services_used": False,
        "paid_api_used": False,
        "vector_database_created": False,
    }


def build_embeddings(
    *,
    input_path: Path = DEFAULT_INPUT,
    output_path: Path = DEFAULT_OUTPUT,
    manifest_path: Path = DEFAULT_MANIFEST,
    model: EmbeddingModel,
    chunk_types: tuple[str, ...] = DEFAULT_CHUNK_TYPES,
    batch_size: int = 32,
) -> EmbeddingBuildResult:
    chunks = load_jsonl(input_path)
    selected = selected_chunks(chunks, chunk_types)
    texts = [str(chunk.get("chunk_text_normalized") or chunk.get("chunk_text") or "") for chunk in selected]
    vectors = model.encode(texts, batch_size=batch_size) if texts else []
    if len(vectors) != len(selected):
        raise ValueError(f"model returned {len(vectors)} vectors for {len(selected)} chunks")

    records = [embedding_record(chunk, vector, model.model_name) for chunk, vector in zip(selected, vectors)]
    vector_dimensions = {record["embedding_dimension"] for record in records}
    if len(vector_dimensions) > 1:
        raise ValueError(f"embedding dimension mismatch: {sorted(vector_dimensions)}")

    write_jsonl(records, output_path)
    manifest = build_manifest(
        input_path=input_path,
        output_path=output_path,
        model_name=model.model_name,
        chunk_types=chunk_types,
        all_chunk_count=len(chunks),
        selected_count=len(selected),
        embedded_records=records,
        skipped_count=len(chunks) - len(selected),
    )
    write_json(manifest, manifest_path)

    return EmbeddingBuildResult(
        embedded_count=len(records),
        skipped_count=len(chunks) - len(selected),
        vector_dimension=next(iter(vector_dimensions), 0),
        chunk_type_counts=manifest["chunk_type_counts"],
        output_path=output_path,
        manifest_path=manifest_path,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build local sentence-transformer embeddings for TamilVU chunks")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--chunk-type", action="append", default=[])
    parser.add_argument("--all-chunk-types", action="store_true")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args(argv)

    try:
        chunk_types = parse_chunk_types(args.chunk_type, include_all=args.all_chunk_types)
        model = SentenceTransformerEmbeddingModel(args.model, cache_dir=args.cache_dir)
        result = build_embeddings(
            input_path=args.input,
            output_path=args.output,
            manifest_path=args.manifest,
            model=model,
            chunk_types=chunk_types,
            batch_size=args.batch_size,
        )
    except Exception as exc:
        print(f"Embedding build failed: {exc}", file=sys.stderr)
        return 1

    print(
        "Embedding build complete: "
        f"embedded={result.embedded_count} skipped={result.skipped_count} "
        f"dimension={result.vector_dimension} output={result.output_path} manifest={result.manifest_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
