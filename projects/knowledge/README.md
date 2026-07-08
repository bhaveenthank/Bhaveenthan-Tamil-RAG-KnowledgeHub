# Knowledge Project

Owns curated registries, span annotations, entity extraction, and literary knowledge extraction readiness.

## Inputs

- normalized corpus records
- reviewed annotation fixtures
- curated knowledge registries

## Outputs

- annotation records
- extraction candidates
- registry validation reports

Knowledge artifacts are derived evidence and must remain separate from source corpus records.

## Thevaram Entity Annotation

Use `knowledge.annotate_thevaram_entities` to enrich the normalized Thevaram 1-8
tables with entity mentions derived from reviewed pilot TSV seed datasets and manual QA
decision CSVs. The output is a separate derived artifact and does not modify the
normalized corpus.

```bash
python3 -m knowledge.annotate_thevaram_entities \
  --table-root data/processed/thevaram_normalized \
  --seed-dir "/Users/bhaveenthankajanikanth/Desktop/Tamil RAG/Pilot Entity datasets" \
  --review-dir "/Users/bhaveenthankajanikanth/Desktop/Tamil RAG/Entity Annotation" \
  --output-root data/processed/thevaram_entity_annotations_v2 \
  --report reports/thevaram-entity-annotation-v2-report.md
```

The entity pass supports `DEITY`, `SACRED_OBJECT`, `BODY_PART`, `NATURE`, `ACTION`, and
`THEOLOGICAL_CONCEPT`. It preserves exact character offsets, suppresses nested overlaps
within the same entity type, and keeps cross-type overlaps when the same poetic span
legitimately carries multiple categories.

The v2 pass applies the manual QA decision table:

- `KEEP` aliases are auto-accepted.
- `CONTEXT_ONLY` aliases remain but carry context status and adjusted confidence.
- `AMBIGUOUS_REVIEW` aliases are retained with lower confidence for review.
- `REJECT_OR_EXCLUDE` aliases are suppressed into `suppressed_candidates.jsonl`.

## Thevaram Entity Annotation v3

Use `knowledge.annotate_thevaram_entities_v3` to create the expanded ontology layer.
v3 preserves the reviewed v2 seed layer and adds curated/dynamic aliases for deity
epithets, divine forms, temples, sacred geography, sacred trees/flowers, saints,
mythological characters, weapons, rituals, musical instruments, iconographic features,
canonical mythological events, and candidate entity relationships.

```bash
python3 -m knowledge.annotate_thevaram_entities_v3 \
  --table-root data/processed/thevaram_normalized \
  --seed-dir "/Users/bhaveenthankajanikanth/Desktop/Tamil RAG/Pilot Entity datasets" \
  --review-dir "/Users/bhaveenthankajanikanth/Desktop/Tamil RAG/Entity Annotation" \
  --output-root data/processed/thevaram_entity_annotations_v3 \
  --report reports/thevaram-entity-annotation-v3-report.md
```

Main outputs:

- `entity_registry.jsonl`
- `entity_aliases.jsonl`
- `entity_mentions.jsonl`
- `entity_relationships.jsonl`
- `suppressed_candidates.jsonl`
- `annotation_summary.json`

Treat v3 as an aggressive retrieval/linking enrichment layer. It improves coverage and
candidate relationships, but context-only aliases and co-occurrence relationships still
need scholarly review before being treated as final gold.

## Thevaram Ontology v1

The ontology report has been operationalized as a machine-readable draft contract under
`data/knowledge/ontology/`.

Main artifacts:

- `thevaram_ontology_v1.json`: 25 entity types, 14 attributes, and the 20-event mythological canon.
- `thevaram_relations_v1.json`: relation schema for iconography, events, geography, devotion, and text structure.
- `guidelines/annotation_guidelines_v1.md`: annotation decision scaffold.
- `migration/v2_to_v1_type_map.csv`: first-pass migration map from the six v2 entity types.

Validate the ontology contract and measured v2/v3 baseline:

```bash
python3 -m knowledge.validate_thevaram_ontology
```

Outputs:

- `data/knowledge/ontology/thevaram_ontology_v1_validation.json`
- `reports/thevaram-ontology-v1-validation-report.md`

This validation performs no scraping, extraction, or LLM calls. It checks the ontology
contract and measures the current v2/v3 annotation counts, including v2 cross-type
overlap spans and v3 temple/thalam coverage.

## Thevaram Pozhippurai To Paadal Links

Use `knowledge.link_thevaram_pozhippurai` to create corpus-wide links from
`paadal_text` lines to `pozhppurai` explanation segments. This is a complete first-pass
alignment layer: every paadal line receives either a link to a `pozhppurai` segment or a
`no_pozhippurai` coverage record when commentary text is unavailable.

```bash
python3 -m knowledge.link_thevaram_pozhippurai \
  --table-root data/processed/thevaram_normalized \
  --entity-root data/processed/thevaram_entity_annotations_v2 \
  --seed-dir "/Users/bhaveenthankajanikanth/Desktop/Tamil RAG/Paadal - Pozhippurai Annotation/thevaram_pozhippurai_paadallink_seed_dataset" \
  --output-root data/processed/thevaram_pozhippurai_links_v2 \
  --report reports/thevaram-pozhppurai-paadallink-v2-report.md
```

The linker uses the human seed relation dataset for relationship labels, Entity
Annotation v2 for entity overlap, lexical/character similarity, phrase containment, and
poem-order alignment for selecting the best `pozhppurai` window. High/medium links are
useful for downstream retrieval and analysis; low-confidence links should be sampled
before scholarly claims.

Build a manual QA review pack from the generated links:

```bash
python3 -m knowledge.build_pozhippurai_link_qa_pack \
  --links data/processed/thevaram_pozhippurai_links_v2/paadal_pozhippurai_links.jsonl \
  --output-dir data/processed/thevaram_pozhippurai_links_v2/qa_review_pack \
  --report reports/thevaram-pozhppurai-link-v2-qa-review-pack.md \
  --target-count 220
```

The review CSV has blank decision columns for `ACCEPT`, `WRONG_TARGET`,
`PARTIAL_MATCH`, `WRONG_RELATION_TYPE`, `NEEDS_SPLIT`, and `NO_LINK_POSSIBLE`.

## Thevaram Pozhippurai Linker v3

Use `knowledge.link_thevaram_pozhippurai_v3` after focused Phase 3 manual QA. It keeps
the v2 full-corpus coverage layer, then adds focused QA-derived exact phrase rules and
accepted split links. Rows marked no-link, unresolved, or manual-review-only are kept
out of positive training data.

```bash
python3 -m knowledge.link_thevaram_pozhippurai_v3 \
  --input-root data/processed/thevaram_normalized \
  --qa-bundle "/Users/bhaveenthankajanikanth/Downloads/paadal_pozhippurai_phase3_focused_manual_qa_outputs" \
  --output-root data/processed/thevaram_pozhippurai_links/v3 \
  --report reports/thevaram-pozhppurai-paadallink-v3-report.md
```

Main outputs:

- `paadal_pozhippurai_links_v3_full.jsonl`
- `paadal_pozhippurai_links_v3_high_confidence.jsonl`
- `paadal_pozhippurai_links_v3_medium_confidence.jsonl`
- `paadal_pozhippurai_links_v3_low_confidence_review.csv`
- `paadal_pozhippurai_links_v3_no_link_or_unresolved.csv`
- `paadal_pozhippurai_links_v3_corrected_usable.iob.conll`
- `paadal_pozhippurai_links_v3_manual_review_pack.csv`
- `paadal_pozhippurai_links_v3_summary.json`

Treat v3 as a stronger rule-backed training and review layer. It is not final scholarly
gold until the new manual review pack is checked.

Build a local browser viewer for quick review without waiting on TamilVU pages:

```bash
python3 -m knowledge.build_pozhippurai_review_viewer \
  --review-pack data/processed/thevaram_pozhippurai_links/v3/paadal_pozhippurai_links_v3_manual_review_pack.csv \
  --table-root data/processed/thevaram_normalized \
  --output data/processed/thevaram_pozhippurai_links/v3/review_viewer/paadal_pozhippurai_v3_review_viewer.html
```

The viewer shows the candidate source/target spans, the full paadal containing that
phrase or line, the full `pozhppurai`, and the `kurippurai`, with proposed spans
highlighted. Review choices are saved in browser local storage and can be exported as a
CSV from the page.

## Thevaram Pozhippurai Linker v4

Use `knowledge.build_pozhippurai_links_v4` after adding the 60 manually corrected gold
seed examples. v4 keeps the v3 corpus coverage layer and applies gold-seed rules for
exact target spans, punctuation-guided splits, relationship labels, confidence
recalibration, morphology-aware case endings, and `kurippurai` fallback when the
explanation is absent from `pozhppurai`.

```bash
python3 -m knowledge.build_pozhippurai_links_v4 \
  --input-root data/processed/thevaram_normalized \
  --qa-bundle "/Users/bhaveenthankajanikanth/Downloads/paadal_pozhippurai_phase3_focused_manual_qa_outputs" \
  --gold-seed data/processed/thevaram_pozhippurai_links/v4/gold/paadal_pozhippurai_v4_gold_seed.csv \
  --output-root data/processed/thevaram_pozhippurai_links/v4 \
  --report data/processed/thevaram_pozhippurai_links/v4/paadal_pozhippurai_links_v4_report.md
```

Main outputs:

- `gold/paadal_pozhippurai_v4_gold_seed.csv`
- `paadal_pozhippurai_links_v4_full.jsonl`
- `paadal_pozhippurai_links_v4_full.tsv`
- `paadal_pozhippurai_links_v4_high_confidence.jsonl`
- `paadal_pozhippurai_links_v4_medium_confidence.jsonl`
- `paadal_pozhippurai_links_v4_low_confidence_review.csv`
- `paadal_pozhippurai_links_v4_no_link_or_unresolved.csv`
- `paadal_pozhippurai_links_v4_corrected_usable.iob.conll`
- `paadal_pozhippurai_links_v4_manual_review_pack.csv`
- `paadal_pozhippurai_links_v4_summary.json`
- `paadal_pozhippurai_links_v4_report.md`

Build the v4 local review viewer:

```bash
python3 -m knowledge.build_pozhippurai_review_viewer \
  --review-pack data/processed/thevaram_pozhippurai_links/v4/paadal_pozhippurai_links_v4_manual_review_pack.csv \
  --table-root data/processed/thevaram_normalized \
  --output data/processed/thevaram_pozhippurai_links/v4/review_viewer/paadal_pozhippurai_v4_review_viewer.html
```

Treat v4 as a stronger rule-backed training and review layer. It is not final scholarly
gold until the low-confidence/manual-review rows are checked.

## Thevaram Pozhippurai Linker v4 Hardened

Use `knowledge.build_pozhippurai_links_v4_hardened` to apply the v4 hardening pack on
top of the v4 corpus links without overwriting v3 or v4 outputs. The hardened layer
adds semantic lexicon scoring, morphology-aware matching, ontology relation cues,
expanded entity anchors, global/reverse sequence features, neighbouring span evidence,
ambiguous-target penalties, and confidence recalibration.

```bash
python3 -m knowledge.build_pozhippurai_links_v4_hardened
```

By default, the command reuses
`data/processed/thevaram_pozhippurai_links/v4/paadal_pozhippurai_links_v4_full.jsonl`
when present. Pass `--rebuild-base-v4` only when the base v4 links themselves need to be
regenerated.

Main outputs:

- `paadal_pozhippurai_links_v4_hardened_full.jsonl`
- `paadal_pozhippurai_links_v4_hardened_primary_clean_links.csv`
- `paadal_pozhippurai_links_v4_hardened_secondary_no_link.csv`
- `paadal_pozhippurai_links_v4_hardened_high_confidence.jsonl`
- `paadal_pozhippurai_links_v4_hardened_medium_confidence.jsonl`
- `paadal_pozhippurai_links_v4_hardened_low_confidence_review.csv`
- `paadal_pozhippurai_links_v4_hardened_manual_review_pack.csv`
- `paadal_pozhippurai_links_v4_hardened_corrected_usable.iob.conll`
- `paadal_pozhippurai_links_v4_hardened_summary.json`
- `paadal_pozhippurai_links_v4_hardened_report.md`
