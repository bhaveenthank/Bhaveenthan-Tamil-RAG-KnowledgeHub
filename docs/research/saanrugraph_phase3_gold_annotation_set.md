# SaanruGraph Phase 3 Gold Annotation Set

Dataset version: `saanrugraph-thevaram-1-7-gold-annotation-v1`

## Output Files

| Output | Path |
| --- | --- |
| Gold annotation dataset | `data/processed/saanrugraph_phase3/gold_linking_dataset_500.csv` |
| Double annotation subset | `data/processed/saanrugraph_phase3/gold_double_annotation_subset_100.csv` |
| Relation distribution | `data/processed/saanrugraph_phase3/relation_distribution_table.csv` |
| Agreement summary | `data/processed/saanrugraph_phase3/agreement_summary.json` |
| Machine summary | `data/processed/saanrugraph_phase3/gold_annotation_summary.json` |
| Annotation guideline | `docs/research/saanrugraph_phase3_annotation_guideline.md` |

## Sample Composition

| Stratum | Rows |
| --- | ---: |
| `hard_negative_same_paadal` | 30 |
| `high_confidence` | 120 |
| `low_confidence` | 150 |
| `medium_confidence` | 150 |
| `true_missing_pozhippurai` | 50 |

## Relation Distribution

| Model relation label | Rows |
| --- | ---: |
| `candidate_no_link` | 30 |
| `describes_entity` | 70 |
| `explains_line` | 70 |
| `explains_phrase` | 70 |
| `glosses_word` | 70 |
| `interprets_image` | 70 |
| `theological_explanation` | 70 |
| `unlinked` | 50 |

## Hard Case Coverage

| Hard case tag | Rows |
| --- | ---: |
| `ambiguous_commentary` | 110 |
| `ambiguous_span` | 110 |
| `borderline_score_calibration` | 1 |
| `broad_commentary_target` | 51 |
| `broad_or_unsplit_target` | 51 |
| `hard_negative` | 30 |
| `high_pattern_but_blocked` | 17 |
| `low_learned_pattern_support` | 186 |
| `low_lexical_overlap` | 386 |
| `missing_anchor` | 301 |
| `missing_commentary` | 50 |
| `no_link_case` | 50 |
| `no_shared_entity_or_missing_anchor` | 301 |
| `poetic_imagery` | 70 |
| `polysemy_context` | 11 |
| `relation_granularity_mismatch` | 7 |
| `shared_paadal_wrong_target` | 30 |
| `single_token_phrase` | 62 |
| `theological_interpretation` | 70 |
| `weak_semantic_signal` | 230 |

## Agreement Status

Agreement is pending because manual labels have not been filled yet.
After at least 100 rows are double annotated, compute observed agreement and Cohen's kappa from `annotator1_label` and `annotator2_label`.
