# Reorganization Package Map

The repository is being reorganized as a contract-first monorepo with independent
project packages and shared contract packages.

## Current Phase

The migration is now in **final stabilization**. Static project boundaries are clean,
project-native commands are defined, and compatibility paths are documented as legacy
support rather than the primary interface.

The chronological progress and rationale are tracked in
`docs/migration/reorg-progress-log.md`.

## Shared Packages

- `shared/tvu-common`: stable utilities only.
- `shared/tvu-schemas`: JSON Schema contracts and schema loading helpers.

Shared packages must not depend on project packages.

## Project Packages

| Project | Source Packages | Responsibility |
| --- | --- | --- |
| `projects/crawler` | `inspector`, `tvu_scraper` | URL classification, inspection, safe fetch, raw snapshots |
| `projects/parser` | `scraper`, `parsers`, `validation` | DOM/source extraction, bounded pilot ingestion, and extraction QA |
| `projects/normalizer` | `corpus` | normalized corpus records, schema validation, readiness audits over parser artifacts |
| `projects/knowledge` | `knowledge` | registries, span annotations, extraction candidates |
| `projects/retrieval` | `enrichment`, `retrieval`, `embeddings`, `vector_index`, `rag`, `analytics` | chunks, indexes, embeddings, RAG context, occurrence/analytics |
| `projects/evaluation` | `evaluation` | benchmarks, failure analysis, capability reports |
| `projects/app` | none yet | future user-facing app |

## Transitional Compatibility

The legacy `src/<package>` directories now contain path-extension shims. They allow
existing imports such as `from scraper.irandaam_thirumurai_builder import ...` to keep
working while the physical implementation lives under `projects/*/src`.

This compatibility layer is retained by policy for historical commands and notebooks.
The canonical command surface is the project-native `tvu-*` command set documented in
`docs/migration/project-native-commands.md`.

Legacy `src/corpus/pilot_ingest_*.py` commands remain as compatibility links, but the
owned implementation is now parser-side. `src/corpus/validate_pilot_categories.py`
is also a compatibility link to evaluation because it compares parser, normalizer, and
schema behavior across stages.

## Test Ownership

Most low-risk tests now live beside their owning project under `projects/*/tests`.
Fixture-heavy and repo-root integration tests remain under the workspace-level `tests/`
directory until they are updated to use a shared repository-root helper instead of
deriving paths from `Path(__file__)`.

Evaluation benchmark and report tests live under `projects/evaluation/tests`; retrieval
tests under `projects/retrieval/tests` should cover retrieval engines, indexes, and
query expansion behavior rather than evaluation reporting.

## Boundary Checks

Use `python3 scripts/check-boundaries.py` to prevent new unexpected cross-project imports.
The transitional allowlist is currently empty, so default and strict mode should both
pass. Use `python3 scripts/check-boundaries.py --strict` in CI-style checks to make that
expectation explicit.

Evaluation/orchestration modules use runtime adapters only where a command intentionally
executes live project behavior. Replay-style paths should prefer artifact/manifest inputs,
such as retrieval failure analysis consuming retrieval benchmark manifests and analytics
evaluation consuming `analytics-observations-v1`.

Use `python3 scripts/run-project-tests.py PROJECT` for a project-owned test slice, where
`PROJECT` is one of `crawler`, `parser`, `normalizer`, `knowledge`, `retrieval`,
`evaluation`, `shared`, `workspace`, or `all`.
