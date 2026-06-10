# Pilot Source Inspection Report

## Scope

This is a metadata-only source inspection and fixture plan. It reads the controlled pilot
registry and does not fetch TamilVU pages, traverse links, ingest records, or write raw
source content.

## Status

- Already verified: `saivam`
- Remaining pilot categories: `5`
- Planned fixtures per category: `3`
- Network requests: `0`
- Source-specific structures: `unconfirmed until allowlisted fixture collection`

## Remaining Categories

| Order | Category | Parser Family | Fixture Type | Count | Risk | Expected Source Structure | Inspection Note |
| ---: | --- | --- | --- | ---: | --- | --- | --- |
| 1 | அகராதிகள் | `dictionary_parser` | `dictionary_entry` | 3 | medium | Headword navigation with one or more senses, grammatical labels, examples, etymology, and cross-references. | A bounded dictionary entry is the simplest new structured-text parser pilot. |
| 2 | இலக்கணம் | `grammar_parser` | `html` | 3 | medium | Book/chapter headings with numbered sutra or rule text, explanation, examples, exceptions, and possible commentary. | Rule boundaries and explanation labels must be confirmed from source HTML. |
| 3 | சங்க இலக்கியம் | `verse_parser` | `html` | 3 | high | Anthology/work hierarchy with poem number, poet, thinai/thurai metadata, verse lines, colophon, and optional commentary. | Poem boundaries and source-provided literary metadata must not be flattened. |
| 4 | இருபதாம் நூற்றாண்டு இலக்கியங்கள் உரைநடைகள் | `prose_parser` | `text` | 3 | high | Book, chapter, section, paragraph, page, footnote, and author or edition metadata in typed HTML or document-oriented pages. | Rights and public-domain status must be confirmed before any source capture. |
| 5 | கலைக்களஞ்சியங்கள் | `dictionary_parser` | `mixed` | 3 | high | Headword article with sections, references, author/editor metadata, cross-links, tables, and possible images. | The current dictionary-parser assignment may need a dedicated encyclopedia adapter after fixtures expose mixed article and media structure. |

## Parser Development Recommendation

Develop `dictionary_parser` next using the `dictionaries` category. A small headword entry
is likely to provide the clearest new structured-text boundary after the proven verse
parser. Follow with `grammar_parser`, then the Sangam `verse_parser` variant.

The highest-risk parser application is `dictionary_parser` for encyclopedias because
articles may contain sections, references, tables, cross-links, and media that exceed a
simple headword/sense model. Treat it as a separate adapter decision after fixtures.

## Recommended Order

1. Dictionaries: bounded headword and sense structures.
2. Grammar: rule, explanation, and example boundaries.
3. Sangam literature: poem hierarchy and literary metadata.
4. Twentieth-century prose: chapter/paragraph extraction after rights review.
5. Encyclopedias: mixed article/media structure after simpler dictionary evidence.

Image, manuscript, OCR, PDF-heavy, mixed-site, and full-category work remains deferred.
