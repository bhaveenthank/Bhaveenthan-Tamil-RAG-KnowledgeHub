# ADR-002: AI-First Reorganization And Contract Hardening

## Status

Accepted.

## Context

The TamilVU corpus project is an AI-first codebase: most scaffolding, tests,
architecture notes, and migration work are produced with AI assistance. That makes drift a
first-order risk. Future agents need a short path to understand current phase, project
ownership, compatibility layers, and what must not be changed casually.

The repository was originally a single Python package layout. It is being reorganized into
independent projects that interact through code, schemas, and data artifacts.

## Decision

Use a contract-first monorepo with:

- `projects/*` for owned implementation packages.
- `shared/tvu-common` for stable utilities.
- `shared/tvu-schemas` for artifact schemas.
- `src/*` as legacy compatibility shims.
- boundary checks that fail static cross-project imports.
- project-native `tvu-*` console commands as the canonical command surface.
- migration logs and ADRs as required grounding context for future AI work.

The reorganization is in **final stabilization**. Static boundaries are clean, runtime
compatibility is explicit, and replay-style evaluation paths should prefer
artifact/manifest contracts.

## Consequences

Positive:

- Future AI agents can inspect ownership and constraints quickly.
- Static project boundaries are enforceable.
- Legacy commands keep working after migration as compatibility.
- Project-native commands are available from the workspace and owning subprojects.
- Reorg progress can be audited without reconstructing chat history.

Tradeoffs:

- Compatibility shims add indirection.
- Runtime adapters remain for commands that intentionally execute live project behavior.
- Documentation must be maintained after each slice, or the AI-first benefit erodes.

## Guardrails

- Do not remove compatibility shims except in a planned compatibility-breaking release.
- Do not add a cross-project import without recording it in `scripts/check-boundaries.py`
  with a removal plan.
- Do not broaden crawling during reorg work.
- Treat raw snapshots, provenance, Tamil Unicode fidelity, and literary hierarchy as
  non-negotiable contracts.
