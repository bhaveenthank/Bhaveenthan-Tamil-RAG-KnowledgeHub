# Artifact Flow Contract

Stages communicate through versioned artifacts and manifests, not through internal
implementation imports.

```text
RawSnapshot
  -> ExtractedRecord
  -> NormalizedRecord
  -> AnnotationRecord
  -> RetrievalChunk
  -> EmbeddingRecord / IndexRecord
  -> EvaluationResult
  -> App Result
```

## Artifact Manifest

Each published artifact directory should contain a `manifest.json` matching
`shared/tvu-schemas/schemas/artifact_manifest.schema.json`.

Required manifest concepts:

- `artifact_id`
- `artifact_type`
- `schema_version`
- `producer`
- `record_count`
- `source_artifacts`
- `checksums`
- `warnings`
- `created_at`

## Dependency Rule

Projects may depend on:

- `shared/tvu-common`
- `shared/tvu-schemas`
- published artifacts from earlier stages

Projects should not import another project's internal implementation as a long-term
contract. Transitional imports are allowed only while this migration is in progress.

The parser-to-normalizer handoff is now a JSONL artifact boundary: parser-owned pilot
ingestion writes `data/processed/pilot_categories/<category_id>/records.jsonl`, and
normalizer-owned commands read those records through shared artifact helpers.

## Current Enforcement

`scripts/check-boundaries.py` enforces this rule. New cross-project imports fail unless
they are explicitly recorded as current migration debt in the script's transitional
allowlist, which is currently empty.

Evaluation/orchestration still has runtime adapter calls into parser, normalizer,
retrieval, and analytics code for compatibility. Those should eventually become CLI or
artifact-manifest based checks.

This contract exists partly to keep AI-assisted work grounded: new stages should add or
reuse schemas and manifests before depending on another project's implementation details.

Retrieval benchmark, query-expansion, analytics, comprehensive benchmark, and retrieval
failure-analysis outputs now publish adjacent manifests by default. These manifests use
`artifact_type=evaluation_result`, record output checksums, reference source artifacts,
and are the first step toward replacing evaluation runtime adapters with artifact inputs.

Retrieval failure analysis can now consume a retrieval benchmark manifest with
`--benchmark-manifest`; it resolves the benchmark JSON from `outputs.results` and checks
the recorded checksum before analysis.

Analytics evaluation can now consume precomputed analytics observations with
`--observations`. This lets retrieval/analytics code produce observations and lets
evaluation score them without importing retrieval internals. The current observations
artifact is defined by
`shared/tvu-schemas/schemas/analytics_observations.schema.json`; the shape is:

```json
{
  "schema_version": "analytics-observations-v1",
  "producer": "retrieval.analytics",
  "observations": [
    {
      "case_id": "analytics_author_moon",
      "observed": {
        "intent": "group_by_author",
        "term": "சந்திரன்",
        "expanded": true,
        "group_by": "author",
        "total_occurrences": 686,
        "top_results": [{"group_key": "Tirugnanasambandar"}],
        "matched_terms": ["சந்திரன்", "நிலா"],
        "evidence_samples": [{"record_id": "example"}]
      }
    }
  ]
}
```

The evaluator requires every benchmark `case_id` to be present in the observations
artifact. The next hardening step is to publish this observations artifact with a
checksum-backed manifest from the retrieval/analytics project.
