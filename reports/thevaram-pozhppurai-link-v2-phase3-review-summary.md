# Thevaram Phase 3 Paadal-Pozhippurai QA Review Summary

## Scope

- Reviewed CSV: `data/processed/thevaram_pozhippurai_links_v2/qa_review_pack/paadal_pozhippurai_link_qa_samples.csv`
- Rows reviewed: `220`
- Validation status: `VALID`
- Validation errors: `0`

This is a machine-assisted Phase 3 correction pass. It keeps every stable `link_id`,
fills the requested review columns, applies the provided gold correction examples, and
flags rows that still need human judgement.

## Manual Decisions

| Decision | Rows |
| --- | ---: |
| `ACCEPT` | 49 |
| `NEEDS_SPLIT` | 3 |
| `NO_LINK_POSSIBLE` | 18 |
| `PARTIAL_MATCH` | 78 |
| `WRONG_RELATION_TYPE` | 41 |
| `WRONG_TARGET` | 31 |

## Correct Relationship Types

| Relationship | Rows |
| --- | ---: |
| `describes_entity` | 52 |
| `explains_line` | 7 |
| `explains_phrase` | 20 |
| `glosses_word` | 14 |
| `interprets_image` | 64 |
| `theological_explanation` | 45 |
| `unlinked` | 18 |

## Updated Confidence

| Confidence | Rows |
| --- | ---: |
| `HIGH` | 43 |
| `LOW` | 97 |
| `MEDIUM` | 62 |
| `NO_LINK` | 18 |

## Thirumurai Coverage

| Thirumurai | Rows |
| --- | ---: |
| `1` | 42 |
| `2` | 38 |
| `3` | 35 |
| `4` | 26 |
| `5` | 22 |
| `6` | 29 |
| `7` | 19 |
| `8` | 9 |

## How The Review Was Done

- Applied the Phase 3 gold examples exactly where their source phrases appeared.
- Reviewed the candidate target already present in the QA CSV without replacing it from another pack.
- Classified weak links by evidence type: missing pozhppurai, ambiguous target, low lexical overlap, no shared entity anchor, or order-only matching.
- Preserved the original source span, target span evidence, and stable `link_id`.

## What Still Needs Human Review

- `WRONG_TARGET`: replace with the correct visible pozhppurai span where possible.
- `PARTIAL_MATCH`: decide whether to trim, expand, or accept the span.
- `NEEDS_SPLIT`: split one broad row into multiple source-target pairs before treating it as gold.
- `LOW` confidence rows: use for model guidance only after spot-checking.
