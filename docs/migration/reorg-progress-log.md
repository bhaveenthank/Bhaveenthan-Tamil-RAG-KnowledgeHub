# Reorganization Progress Log

This log records the monorepo reorganization decisions so future AI and human
contributors can understand what is intentional, what is transitional, and what should
not be re-litigated without new evidence.

## Current Status

- Current phase: **final stabilization**
- Rollback marker: `pre-reorg-2026-06-13`
- Working branch: `codex/reorg-migration`
- Latest verification: `311 passed in 44.24s`
- Boundary status: both transitional and strict boundary checks pass

## Phase Progress Against The Reorg Plan

| Phase | Goal | Status | Notes |
| --- | --- | --- | --- |
| Week 1 / Phase 1 | Baseline current pipeline, mark rollback point, define target package map | Done | Baseline docs, rollback tag, and branch are in place. |
| Week 1 / Phase 2 | Create monorepo structure and shared packages | Done | `projects/*`, `shared/tvu-common`, and `shared/tvu-schemas` exist. |
| Week 2 / Phase 3 | Move code and tests by ownership while preserving compatibility | Done | Project tests are mostly colocated; fixture-heavy integration tests remain workspace-level intentionally. |
| Week 2 / Phase 4 | Clean static cross-project imports and enforce boundaries | Done | `scripts/check-boundaries.py --strict` passes. |
| Week 3 / Phase 5 | Harden contracts between projects | Done | Parser-normalizer and evaluation artifact contracts are documented and tested. |
| Week 3-4 / Phase 6 | Replace compatibility paths with artifact/manifest or CLI contracts | Done | Project-native `tvu-*` commands exist; legacy paths are compatibility only. |
| Week 4 / Phase 7 | Final stabilization, remove safe-to-remove shims, checkpoint commit | Done pending commit | Shims are retained by policy as compatibility; boundaries and command targets are tested. |

## Completed Slices

1. Created rollback marker and migration branch.
2. Split source packages into project-owned directories under `projects/*`.
3. Added legacy `src/<package>` compatibility shims and symlinks.
4. Added `shared/tvu-common` for stable utilities.
5. Added `shared/tvu-schemas` for JSON Schema contracts.
6. Added project `README.md` and `pyproject.toml` files.
7. Moved most tests under project ownership.
8. Added boundary checks, project test runner, and workspace check script.
9. Moved raw snapshot helpers into `tvu-common`.
10. Moved extraction validation under parser ownership.
11. Moved bounded pilot ingestion under parser ownership.
12. Moved cross-stage pilot validation under evaluation ownership.
13. Retired normalizer-to-parser static imports.
14. Added `evaluation.runtime_adapters` to remove static evaluation imports while preserving current behavior.
15. Emptied the boundary allowlist; strict boundaries are now clean.
16. Moved evaluation-owned tests out of retrieval test ownership.
17. Added evaluation result artifact contracts for retrieval benchmark outputs.
18. Extended evaluation result manifests to query-expansion and analytics outputs.
19. Extended evaluation result manifests to comprehensive benchmark and retrieval failure analysis outputs.
20. Taught retrieval failure analysis to consume a retrieval benchmark manifest and verify the benchmark checksum.
21. Taught analytics evaluation to score a versioned analytics observations artifact instead of requiring runtime retrieval calls.
22. Added project-native `tvu-*` console commands at workspace and subproject level.
23. Added `analytics_observations.schema.json` and tested schema/command discoverability.

## Key Decisions

### Keep legacy `src/...` compatibility as a release policy

Decision: preserve legacy import and command paths after migration as compatibility
unless a future release explicitly removes them.

Reason: the repository already has many CLI examples, tests, and user workflows that call
`src/...` directly. Removing them during the structural split would create avoidable
breakage and make it harder to isolate true architecture problems.

Exit criteria: project-native commands, docs, tests, and boundaries must not depend on
legacy paths as the primary interface. This is now satisfied; removing shims is a future
release-management choice, not a reorg blocker.

### Treat parser ingestion as parser-owned

Decision: bounded pilot ingestion moved from `corpus` to parser-side `scraper`.

Reason: those scripts parse source records and emit extracted records. Normalizer should
consume parser artifacts, not call parser internals.

Exit criteria: parser ingestion should publish manifest-backed extracted artifacts.

### Treat cross-stage validation as evaluation-owned

Decision: `validate_pilot_categories` moved to evaluation ownership.

Reason: it compares parser, normalizer, schema, and readiness behavior across stages. It
is not a pure normalizer command.

Exit criteria: replace runtime calls with artifact/manifest inputs.

### Use runtime adapters as compatibility for live benchmark execution

Decision: `evaluation.runtime_adapters` may late-bind existing parser, normalizer,
retrieval, and analytics implementations for commands that intentionally execute live
project behavior.

Reason: this lets static boundaries become clean while preserving current benchmark
behavior and test coverage.

Exit criteria: evaluation commands that can replay artifacts should do so. Commands that
intentionally benchmark the current runtime may keep the adapter as an explicit
compatibility boundary as long as static project imports remain clean.

### Keep root workspace tests intentionally

Decision: some tests remain in root `tests/`.

Reason: they are fixture-heavy or workspace-level integration tests with path assumptions.
Moving them mechanically would add noise and risk without improving package boundaries.

Exit criteria: move them only when a shared repository-root helper or artifact fixture
contract makes ownership obvious.

## AI-First Working Notes

This project is dominantly AI-built and should be optimized for future AI agents as well
as humans.

- Prefer executable checks over prose-only rules.
- Document why a compatibility layer exists before relying on it.
- Keep project ownership explicit in docs, scripts, and tests.
- Preserve source URLs, raw snapshots, Tamil Unicode, hierarchy, and citation paths.
- Do not broaden crawl scope as part of reorganization work.
- Before each slice, read this log plus `docs/migration/reorg-package-map.md` and
  `docs/contracts/artifact-flow.md`.
- After each slice, update this log if ownership, contracts, or intentional debt changes.

## Remaining Compatibility Policy

- `src/...` compatibility shims remain for historical commands and notebooks.
- `evaluation.runtime_adapters` remains for live runtime benchmark execution.
- Root workspace tests remain where fixture ownership is cross-cutting.
- Some historical docs still show legacy commands; `docs/migration/project-native-commands.md`
  is the canonical command surface.
- Artifact manifests are defined generally, but not every historical stage output publishes
  one yet.
  Retrieval benchmark, query-expansion, analytics, comprehensive benchmark, and retrieval
  failure analysis outputs now publish manifests.
  Retrieval failure analysis can now consume the retrieval benchmark manifest as input.
- Analytics evaluation can now consume `analytics-observations-v1` JSON as an artifact
  input, while retaining the runtime adapter path for compatibility.

## Post-Reorg Follow-Ups

1. Commit the completed reorg checkpoint.
2. Add checksum-backed manifests for analytics observations once the retrieval project publishes them.
3. Remove legacy shims only in a planned compatibility-breaking release.
