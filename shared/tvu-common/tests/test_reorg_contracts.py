from __future__ import annotations

import json
from pathlib import Path

from tvu_common.manifests import ArtifactManifest
from tvu_common.unicode import normalize_tamil_text, tamil_ratio
from tvu_schemas import schema_path


def test_shared_unicode_helpers_preserve_tamil_text() -> None:
    text = "  தமிழ்\u00a0மொழி  \n\n இலக்கியம் "

    assert normalize_tamil_text(text) == "தமிழ் மொழி\nஇலக்கியம்"
    assert tamil_ratio("தமிழ் ABC") > 0


def test_artifact_manifest_contains_required_contract_fields() -> None:
    manifest = ArtifactManifest(
        artifact_id="tamilvu-test-v1",
        artifact_type="normalized",
        schema_version="website-corpus-v2",
        producer="test",
        record_count=3,
    ).to_dict()
    schema = json.loads(schema_path("artifact_manifest.schema.json").read_text(encoding="utf-8"))

    missing = [field for field in schema["required"] if field not in manifest]

    assert missing == []


def test_schema_registry_exposes_expected_schemas() -> None:
    expected = [
        "raw_snapshot.schema.json",
        "extracted_record.schema.json",
        "normalized_record.schema.json",
        "annotation_record.schema.json",
        "retrieval_chunk.schema.json",
        "embedding_record.schema.json",
        "artifact_manifest.schema.json",
        "evaluation_result.schema.json",
        "analytics_observations.schema.json",
    ]

    for name in expected:
        assert Path(schema_path(name)).is_file()
