from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tvu_common.checksums import sha256_file
from tvu_common.manifests import ArtifactManifest

EVALUATION_SCHEMA_VERSION = "evaluation-result-v1"


def write_evaluation_manifest(
    *,
    evaluation_type: str,
    producer: str,
    record_count: int,
    outputs: dict[str, Path],
    manifest_path: Path | None = None,
    source_artifacts: list[str] | None = None,
    modes: list[str] | None = None,
    metrics: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
) -> Path:
    checksums = {
        name: sha256_file(path)
        for name, path in outputs.items()
        if path.is_file()
    }
    primary_output = outputs.get("results") or next(iter(outputs.values()))
    manifest = ArtifactManifest(
        artifact_id=primary_output.stem,
        artifact_type="evaluation_result",
        schema_version=EVALUATION_SCHEMA_VERSION,
        producer=producer,
        record_count=record_count,
        source_artifacts=source_artifacts or [],
        checksums=checksums,
        warnings=warnings or [],
    ).to_dict()
    manifest["evaluation_type"] = evaluation_type
    manifest["modes"] = modes or []
    manifest["outputs"] = {name: str(path) for name, path in outputs.items()}
    if metrics is not None:
        manifest["metrics"] = metrics
    manifest_path = manifest_path or primary_output.with_suffix(".manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def load_evaluation_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("artifact_type") != "evaluation_result":
        raise ValueError(f"not an evaluation result manifest: {path}")
    return manifest


def resolve_manifest_output(manifest_path: Path, manifest: dict[str, Any], output_name: str) -> Path:
    outputs = manifest.get("outputs") or {}
    value = outputs.get(output_name)
    if not value:
        raise ValueError(f"manifest has no output named {output_name!r}: {manifest_path}")
    path = Path(value)
    if path.is_absolute() or path.exists():
        return path
    return manifest_path.parent / path


def verify_manifest_output_checksum(
    manifest_path: Path,
    manifest: dict[str, Any],
    output_name: str,
    path: Path,
) -> None:
    expected = (manifest.get("checksums") or {}).get(output_name)
    if not expected:
        return
    observed = sha256_file(path)
    if observed != expected:
        raise ValueError(
            f"checksum mismatch for {output_name!r} in {manifest_path}: "
            f"expected {expected}, observed {observed}"
        )
