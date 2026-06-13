from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(slots=True)
class ArtifactManifest:
    artifact_id: str
    artifact_type: str
    schema_version: str
    producer: str
    record_count: int
    source_artifacts: list[str] = field(default_factory=list)
    checksums: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "schema_version": self.schema_version,
            "producer": self.producer,
            "record_count": self.record_count,
            "source_artifacts": self.source_artifacts,
            "checksums": self.checksums,
            "warnings": self.warnings,
            "created_at": self.created_at,
        }
