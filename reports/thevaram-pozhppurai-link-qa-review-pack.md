# Thevaram Pozhippurai Link QA Review Pack

## Purpose

This pack gives a balanced sample of paadal-line to pozhppurai-segment links for manual
review. It is meant to produce a decision table for the next linker version, not to
review all generated links one by one.

## Files

- Review CSV: `data/processed/thevaram_pozhippurai_links/qa_review_pack/paadal_pozhippurai_link_qa_samples.csv`

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

- Rows: `210`

## Confidence Coverage

| Confidence | Samples |
| --- | ---: |
| `high` | 32 |
| `low` | 97 |
| `medium` | 72 |
| `none` | 9 |

## Relationship Coverage

| Relationship | Samples |
| --- | ---: |
| `describes_entity` | 35 |
| `explains_line` | 11 |
| `explains_phrase` | 42 |
| `glosses_word` | 29 |
| `interprets_image` | 45 |
| `theological_explanation` | 39 |
| `unlinked` | 9 |

## Thirumurai Coverage

| Thirumurai | Samples |
| --- | ---: |
| `1` | 39 |
| `2` | 40 |
| `3` | 37 |
| `4` | 20 |
| `5` | 19 |
| `6` | 32 |
| `7` | 18 |
| `8` | 5 |

## Sampling Reasons

| Reason | Samples |
| --- | ---: |
| `confidence_high` | 30 |
| `confidence_low` | 45 |
| `confidence_medium` | 49 |
| `relationship_describes_entity` | 8 |
| `relationship_explains_line` | 8 |
| `relationship_explains_phrase` | 8 |
| `relationship_glosses_word` | 8 |
| `relationship_interprets_image` | 7 |
| `relationship_theological_explanation` | 7 |
| `thirumurai_1` | 5 |
| `thirumurai_2` | 5 |
| `thirumurai_3` | 5 |
| `thirumurai_4` | 5 |
| `thirumurai_5` | 5 |
| `thirumurai_6` | 5 |
| `thirumurai_7` | 5 |
| `thirumurai_8` | 5 |
