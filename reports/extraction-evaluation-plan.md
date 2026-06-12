# Extraction Evaluation Plan

## Purpose

This plan maps future extraction phases to the manual gold annotation fixtures created in
Phase 30.

## Phase Map

| Phase | Focus | Gold Fixtures |
| --- | --- | --- |
| Phase 31 | Entity Extraction Pilot | `entities_gold.json` |
| Phase 32 | Deity & Author Extraction | `deities_gold.json`, `authors_gold.json` |
| Phase 33 | Motif & Theme Extraction | `motifs_gold.json` plus future theme examples |
| Phase 34 | Epithet Extraction | `epithets_gold.json` |
| Phase 35 | Simile & Metaphor Detection | `similes_gold.json`, `metaphors_gold.json` |
| Phase 36 | Relationship Extraction | `relationships_gold.json` |
| Phase 37 | Knowledge Re-Benchmark | All accepted extraction outputs plus the 100-question benchmark |

## Evaluation Metrics

- precision
- recall
- F1
- span accuracy
- normalized-label accuracy
- relationship endpoint accuracy
- false-positive analysis
- false-negative analysis

## Quality Gate

No extractor output should be promoted into curated registries until it passes fixture
evaluation and source traceability checks.
