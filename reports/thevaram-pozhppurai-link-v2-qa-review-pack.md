# Thevaram Pozhippurai Link QA Review Pack

## Purpose

This pack gives a balanced sample of paadal-line to pozhppurai-segment links for manual
review. It is meant to produce a decision table for the next linker version, not to
review all generated links one by one.

## Files

- Review CSV: `data/processed/thevaram_pozhippurai_links_v2/qa_review_pack/paadal_pozhippurai_link_qa_samples.csv`

## How To Review

Fill `manual_decision` with one of:

- `ACCEPT`: target span correctly explains the paadal line.
- `WRONG_TARGET`: target span is the wrong pozhppurai segment.
- `PARTIAL_MATCH`: target is related but incomplete or too broad.
- `WRONG_RELATION_TYPE`: target is right, but relationship type is wrong.
- `NEEDS_SPLIT`: one line should map to multiple pozhppurai spans.
- `NO_LINK_POSSIBLE`: no useful pozhppurai span exists for this line.

Use `correct_relationship_type`, `correct_target_text_or_note`, and `v2_rule_suggestion`
only when you want the next linker to learn a correction.

## Sample Size

- Rows: `220`

## Confidence Coverage

| Confidence | Samples |
| --- | ---: |
| `high` | 38 |
| `low` | 113 |
| `medium` | 51 |
| `none` | 18 |

## Relationship Coverage

| Relationship | Samples |
| --- | ---: |
| `describes_entity` | 37 |
| `explains_line` | 10 |
| `explains_phrase` | 47 |
| `glosses_word` | 20 |
| `interprets_image` | 46 |
| `theological_explanation` | 42 |
| `unlinked` | 18 |

## Thirumurai Coverage

| Thirumurai | Samples |
| --- | ---: |
| `1` | 42 |
| `2` | 38 |
| `3` | 35 |
| `4` | 26 |
| `5` | 22 |
| `6` | 29 |
| `7` | 19 |
| `8` | 9 |

## Diagnostic Category Coverage

| Category | Samples |
| --- | ---: |
| `ambiguous_multiple_targets` | 51 |
| `low_lexical_overlap` | 17 |
| `missing_pozhippurai` | 18 |
| `no_shared_entity_anchor` | 20 |
| `order_only_weak_match` | 15 |
| `strong_link` | 38 |
| `usable_review` | 51 |
| `weak_similarity` | 10 |

## Sampling Reasons

| Reason | Samples |
| --- | ---: |
| `confidence_high` | 28 |
| `confidence_medium` | 29 |
| `diagnostic_ambiguous_multiple_targets` | 9 |
| `diagnostic_low_lexical_overlap` | 9 |
| `diagnostic_missing_pozhippurai` | 9 |
| `diagnostic_no_shared_entity_anchor` | 10 |
| `diagnostic_order_only_weak_match` | 10 |
| `diagnostic_strong_link` | 10 |
| `diagnostic_usable_review` | 9 |
| `diagnostic_weak_similarity` | 10 |
| `relationship_describes_entity` | 8 |
| `relationship_explains_line` | 8 |
| `relationship_explains_phrase` | 8 |
| `relationship_glosses_word` | 8 |
| `relationship_interprets_image` | 7 |
| `relationship_theological_explanation` | 8 |
| `thirumurai_1` | 5 |
| `thirumurai_2` | 5 |
| `thirumurai_3` | 5 |
| `thirumurai_4` | 5 |
| `thirumurai_5` | 5 |
| `thirumurai_6` | 5 |
| `thirumurai_7` | 5 |
| `thirumurai_8` | 5 |
