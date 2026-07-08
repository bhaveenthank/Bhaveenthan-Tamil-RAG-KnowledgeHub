# Thevaram Pozhippurai Paadal-Link Report

## Strategy

This pass creates corpus-wide `paadal_text` line to `pozhppurai` segment links. The seed
dataset is used to guide relation labels, but the full corpus pass is deterministic and
reviewable: exact spans are stored, confidence is explicit, and paadal lines without
available `pozhppurai` are retained as `no_pozhippurai` coverage records.

The linker scores candidate `pozhppurai` windows using token overlap, Tamil character
n-gram overlap, phrase containment, entity overlap from Entity Annotation v2, and
paadal/commentary order alignment. It then classifies each link as `explains_line`,
`explains_phrase`, `glosses_word`, `interprets_image`, `theological_explanation`, or
`describes_entity`.

## Summary

- Schema version: `thevaram-pozhppurai-paadallink-v2`
- Output root: `data/processed/thevaram_pozhippurai_links_v2`
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
| `linked` | 11050 |
| `linked_low_confidence` | 30859 |
| `no_pozhippurai` | 6869 |

## Confidence

| Confidence | Lines |
| --- | ---: |
| `high` | 836 |
| `low` | 30859 |
| `medium` | 10214 |
| `none` | 6869 |

## Relationship Types

| Relationship | Lines |
| --- | ---: |
| `describes_entity` | 7024 |
| `explains_line` | 1065 |
| `explains_phrase` | 11101 |
| `glosses_word` | 3123 |
| `interprets_image` | 10027 |
| `theological_explanation` | 9569 |
| `unlinked` | 6869 |

## Diagnostic Categories

| Category | Lines | Meaning |
| --- | ---: | --- |
| `ambiguous_multiple_targets` | 20063 | The best target is close to the second-best target, so several pozhppurai spans may be plausible. |
| `low_lexical_overlap` | 2678 | The paadal line and selected pozhppurai target share little surface vocabulary. |
| `missing_pozhippurai` | 6869 | The commentary row has no pozhppurai text. |
| `no_shared_entity_anchor` | 4300 | No accepted Entity v2 anchor overlaps both source and target spans. |
| `order_only_weak_match` | 3698 | The selected target is mainly supported by poem/commentary order, with little lexical or entity evidence. |
| `strong_link` | 836 | High-confidence link with strong lexical/entity/containment evidence. |
| `usable_review` | 10214 | Medium-confidence link; likely useful but should be sampled before scholarly use. |
| `weak_similarity` | 120 | The link has only weak combined similarity evidence. |

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
