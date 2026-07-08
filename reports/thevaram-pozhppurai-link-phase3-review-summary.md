# Thevaram Phase 3 Paadal-Pozhippurai QA Review Summary

## Scope

- Reviewed CSV: `data/processed/thevaram_pozhippurai_links/qa_review_pack/paadal_pozhippurai_link_qa_samples.csv`
- Rows reviewed: `210`
- Validation status: `VALID`
- Validation errors: `0`

This is a machine-assisted Phase 3 correction pass. It keeps every stable `link_id`,
fills the requested review columns, applies the provided gold correction examples, and
flags rows that still need human judgement.

## Manual Decisions

| Decision | Rows |
| --- | ---: |
| `ACCEPT` | 50 |
| `NEEDS_SPLIT` | 3 |
| `NO_LINK_POSSIBLE` | 9 |
| `PARTIAL_MATCH` | 113 |
| `WRONG_RELATION_TYPE` | 28 |
| `WRONG_TARGET` | 7 |

## Correct Relationship Types

| Relationship | Rows |
| --- | ---: |
| `describes_entity` | 53 |
| `explains_line` | 3 |
| `explains_phrase` | 17 |
| `glosses_word` | 17 |
| `interprets_image` | 65 |
| `theological_explanation` | 46 |
| `unlinked` | 9 |

## Updated Confidence

| Confidence | Rows |
| --- | ---: |
| `HIGH` | 32 |
| `LOW` | 92 |
| `MEDIUM` | 77 |
| `NO_LINK` | 9 |

## Thirumurai Coverage

| Thirumurai | Rows |
| --- | ---: |
| `1` | 39 |
| `2` | 40 |
| `3` | 37 |
| `4` | 20 |
| `5` | 19 |
| `6` | 32 |
| `7` | 18 |
| `8` | 5 |

## How The Review Was Done

- Applied the Phase 3 gold examples exactly where their source phrases appeared.
- Used the stronger v2 multi-segment candidate as the correction target for older v1 QA rows.
- Classified weak links by evidence type: missing pozhppurai, ambiguous target, low lexical overlap, no shared entity anchor, or order-only matching.
- Preserved the original source span, target span evidence, and stable `link_id`.

## What Still Needs Human Review

- `WRONG_TARGET`: replace with the correct visible pozhppurai span where possible.
- `PARTIAL_MATCH`: decide whether to trim, expand, or accept the span.
- `NEEDS_SPLIT`: split one broad row into multiple source-target pairs before treating it as gold.
- `LOW` confidence rows: use for model guidance only after spot-checking.
