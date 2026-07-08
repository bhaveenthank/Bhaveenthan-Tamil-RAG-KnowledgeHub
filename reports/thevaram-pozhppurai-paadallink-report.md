# Thevaram Pozhippurai Paadal-Link Report

## Strategy

This pass creates corpus-wide `paadal_text` line to `pozhppurai` segment links. The seed
dataset is used to guide relation labels, but the full corpus pass is deterministic and
reviewable: exact spans are stored, confidence is explicit, and paadal lines without
available `pozhppurai` are retained as `no_pozhippurai` coverage records.

The linker scores candidate `pozhppurai` segments using token overlap, Tamil character
n-gram overlap, and entity overlap from Entity Annotation v2. It then classifies each
link as `explains_line`, `explains_phrase`, `glosses_word`, `interprets_image`,
`theological_explanation`, or `describes_entity`.

## Summary

- Schema version: `thevaram-pozhppurai-paadallink-v1`
- Output root: `data/processed/thevaram_pozhippurai_links`
- Paadal rows: `9012`
- Commentary rows: `9012`
- Seed relation examples: `57`
- Link / coverage rows: `48778`
- Paadal with linked `pozhppurai`: `7469`
- Paadal with no `pozhppurai`: `1543`
- Validation status: `VALID`
- Invalid bounds: `0`
- Span mismatches: `0`
- Duplicate link IDs: `0`

## Link Status

| Status | Lines |
| --- | ---: |
| `linked` | 12587 |
| `linked_low_confidence` | 29322 |
| `no_pozhippurai` | 6869 |

## Confidence

| Confidence | Lines |
| --- | ---: |
| `high` | 729 |
| `low` | 29322 |
| `medium` | 11858 |
| `none` | 6869 |

## Relationship Types

| Relationship | Lines |
| --- | ---: |
| `describes_entity` | 6146 |
| `explains_line` | 1499 |
| `explains_phrase` | 12026 |
| `glosses_word` | 4165 |
| `interprets_image` | 9047 |
| `theological_explanation` | 9026 |
| `unlinked` | 6869 |

## Thirumurai Coverage

| Thirumurai | Lines |
| --- | ---: |
| `1` | 8039 |
| `2` | 7728 |
| `3` | 9161 |
| `4` | 4281 |
| `5` | 4058 |
| `6` | 7841 |
| `7` | 4234 |
| `8` | 3436 |

## Review Guidance

- Treat `high` and `medium` as useful automatic links.
- Review `low` links before using them for scholarly claims.
- `no_pozhippurai` rows are not failures; they document missing commentary text in the current corpus.
- This is a complete corpus-wide first pass, not a final gold commentary alignment.
