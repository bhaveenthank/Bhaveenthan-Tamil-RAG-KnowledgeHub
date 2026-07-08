# Thevaram Paadal-Pozhippurai Linker v3 Report

## What Changed From v2

v3 keeps the v2 full-corpus coverage layer, then adds focused QA-derived exact phrase
rules and accepted split links. Human-corrected rows are used only when they are marked
usable, accepted split links, and high/medium confidence. Unresolved/no-link rows remain
diagnostics and are not promoted to positive training data.

## Outputs

- Output root: `data/processed/thevaram_pozhippurai_links/v3`
- Schema version: `thevaram-pozhppurai-paadallink-v3`
- Total links / coverage rows: `48951`
- Positive training links: `11126`
- Manual review required: `37825`
- No-link rows: `6869`
- Split/child or split-parent diagnostic rows: `195`
- Rules loaded: `159`
- Rules matched in corpus: `157`
- Validation status: `VALID`
- Invalid bounds: `0`
- Span mismatches: `0`
- Duplicate link IDs: `0`

## Confidence Distribution

| Confidence | Rows |
| --- | ---: |
| `high` | 914 |
| `low` | 30859 |
| `medium` | 10309 |
| `no_link` | 6869 |

## Relationship Distribution

| Relationship | Rows |
| --- | ---: |
| `describes_entity` | 7053 |
| `explains_line` | 1068 |
| `explains_phrase` | 11139 |
| `glosses_word` | 3139 |
| `interprets_image` | 10066 |
| `theological_explanation` | 9617 |
| `unlinked` | 6869 |

## Thirumurai Distribution

| Thirumurai | Rows |
| --- | ---: |
| `1` | 8073 |
| `2` | 7760 |
| `3` | 9182 |
| `4` | 4304 |
| `5` | 4074 |
| `6` | 7881 |
| `7` | 4241 |
| `8` | 3436 |

## How QA Decisions Were Used

- `usable_corrected` single rows became source-target phrase rules.
- `ACCEPT_SPLIT_LINK` rows became split-child rules.
- `NO_LINK_POSSIBLE`, unresolved wrong-target rows, and manual-review-only rows were excluded from positive training.
- v2 line links that overlap focused split/phrase rules are retained only as review diagnostics.

## Remaining Error Patterns

- Some human-corrected targets are not visible verbatim in the current normalized commentary, so they do not become exact-span rules.
- Low-confidence v2 baseline rows still require manual review before scholarly use.
- Broad theological explanations may still need trimming to the exact explanatory clause.
- Split coverage is rule-based and conservative; it does not infer every possible sub-phrase yet.

## Next Manual QA Recommendation

Review `paadal_pozhippurai_links_v3_manual_review_pack.csv`, prioritizing low-confidence,
split-parent, and wrong-target-risk rows. Treat v3 as a stronger training/evaluation
layer, not final scholarly gold.
