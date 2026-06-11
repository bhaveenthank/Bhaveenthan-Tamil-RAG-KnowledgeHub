# Pilot Source Inspection Report

## Scope

This is a metadata-only source inspection and fixture plan. It reads the controlled pilot
registry and does not fetch TamilVU pages, traverse links, ingest records, or write raw
source content.

## Status

- Already verified: `grammar, sangam_literature, saivam, twentieth_century_prose, dictionaries`
- Remaining pilot categories: `1`
- Planned fixtures per category: `3`
- Network requests: `0`
- Source-specific structures: `unconfirmed until allowlisted fixture collection`

## Remaining Categories

| Order | Category | Parser Family | Fixture Type | Count | Risk | Expected Source Structure | Inspection Note |
| ---: | --- | --- | --- | ---: | --- | --- | --- |
| 5 | கலைக்களஞ்சியங்கள் | `dictionary_parser` | `mixed` | 3 | high | Headword article with sections, references, author/editor metadata, cross-links, tables, and possible images. | The current dictionary-parser assignment may need a dedicated encyclopedia adapter after fixtures expose mixed article and media structure. |

## Parser Development Recommendation

Develop `grammar_parser` next using a tiny grammar fixture set. Dictionary
entry parsing is now pilot-verified, so grammar provides the simplest new hierarchy:
rule, explanation, example, exception, and commentary. Follow with the Sangam
`verse_parser` variant.

The highest-risk parser application is `dictionary_parser` for encyclopedias because
articles may contain sections, references, tables, cross-links, and media that exceed a
simple headword/sense model. Treat it as a separate adapter decision after fixtures.

## Recommended Order

1. Grammar: rule, explanation, and example boundaries.
2. Sangam literature: poem hierarchy and literary metadata.
3. Twentieth-century prose: chapter/paragraph extraction after rights review.
4. Encyclopedias: mixed article/media structure after simpler dictionary evidence.

Image, manuscript, OCR, PDF-heavy, mixed-site, and full-category work remains deferred.
