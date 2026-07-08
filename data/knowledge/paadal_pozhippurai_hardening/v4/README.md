# Paadal–Pozhippurai Linker v4 Hardening Research Pack

## Purpose

This pack is designed to fix six major linker weaknesses:

1. `low_surface_vocab_gap`
2. `low_order_only_support`
3. `low_missing_entity_anchor`
4. `low_ambiguous_multiple_targets`
5. `accepted_high_ready` / medium-confidence strengthening
6. `empty_pozhippurai_secondary`

The uploaded CSV contained **150 review samples**.

## Uploaded sample profile

```json
{
  "uploaded_sample_count": 150,
  "hardening_category_counts": {
    "low_ambiguous_multiple_targets": 25,
    "low_missing_entity_anchor": 25,
    "low_order_only_support": 25,
    "low_surface_vocab_gap": 25,
    "low_weak_similarity": 25,
    "medium_review_sample": 25
  },
  "relationship_type_counts": {
    "interprets_image": 29,
    "explains_line": 2,
    "explains_phrase": 44,
    "theological_explanation": 20,
    "describes_entity": 45,
    "glosses_word": 10
  },
  "confidence_counts": {
    "low": 125,
    "medium": 25
  }
}
```

## Core idea

The linker should not depend only on direct surface vocabulary or poem/commentary order.

The v4 hardened score should combine:

- surface token overlap
- Tamil morphology-aware normalization
- semantic lexicon overlap
- entity anchors
- ontology relation cues
- relationship-type cue scoring
- global sequence alignment
- previous/next neighbour evidence
- reverse-order alignment
- target granularity penalty
- gold-pattern similarity

## Most important created files

| File | Purpose |
|---|---|
| `01_surface_vocab_gap_semantic_lexicon.csv/jsonl` | Tamil synonym/semantic lexicon examples for low surface overlap |
| `01_morphology_aware_matching_rules.csv` | Tamil suffix, compound, sandhi, and verb normalization rules |
| `01_ontology_relation_cues.csv` | Subject-relation-object cues for Siva imagery, worship, grace, myth events |
| `02_order_only_support_alignment_algorithms.json` | DP/Viterbi, reverse-order, and neighbour algorithms |
| `03_entity_annotation_hierarchy_expansion.csv/jsonl` | Deeper entity hierarchy for deity, thalam, object, body part, myth events |
| `04_ambiguous_multiple_targets_resolution_config.json` | Global assignment and ambiguity-margin handling |
| `05_scoring_feature_spec.json` | Stronger scoring model with weights, penalties, confidence thresholds |
| `06_review_category_policy.csv` | Exact policy for each hardening category |
| `07_uploaded_review_samples_enriched_for_codex.csv` | The uploaded 150 rows enriched with recommended actions |
| `codex_prompt_paadal_pozhippurai_v4_hardening.md` | Full prompt to give Codex |

## Recommended implementation order

1. Load this pack.
2. Add lexicon and morphology modules.
3. Add expanded entity hierarchy.
4. Add ontology relation scoring.
5. Add sequence/global assignment reranker.
6. Add ambiguous-target resolver.
7. Add confidence recalibration.
8. Re-run full corpus.
9. Generate new manual review pack.
10. Add tests.

## Important rule

`empty_pozhippurai_secondary` rows should stay outside the main linked corpus and must not be counted as linker failure.
