# Pilot Category Validation Report

## Executive Summary

- Verified pilots compared: `5`
- Categories: `dictionaries, grammar, saivam, sangam_literature, twentieth_century_prose`
- Parser families: `dictionary_parser, grammar_parser, prose_parser, verse_parser`
- Network requests: `0`
- LLM calls: `0`

The verified pilots validate the common schema envelope, deterministic IDs, Tamil text,
and exact source URLs across two verse traditions, one dictionary family, structured
grammar rules, and paragraph-based prose. The
comparison also exposes an intentional schema gap: commentary is
preserved, but not yet modeled as an independent record.

## Cross-Parser Comparison

| Category | Parser | Record Type | Parsed | Normalized | Errors | Required | Optional | Source URL | Commentary URL | Metadata | Citation | Readiness |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| அகராதிகள் | `dictionary_parser` | `dictionary_entry` | 1 | 1 | 0 | 100.0% | 40.0% | 100.0% | N/A | 100.0% | `READY` | 97.8 |
| இலக்கணம் | `grammar_parser` | `grammar_rule` | 2 | 2 | 0 | 100.0% | 85.7% | 100.0% | 100.0% | 100.0% | `READY` | 98.8 |
| சைவம் | `verse_parser` | `verse` | 10 | 10 | 0 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | `READY` | 99.5 |
| சங்க இலக்கியம் | `verse_parser` | `verse` | 3 | 3 | 0 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | `READY` | 99.6 |
| இருபதாம் நூற்றாண்டு இலக்கியங்கள் உரைநடைகள் | `prose_parser` | `prose_section` | 2 | 2 | 0 | 100.0% | 100.0% | 100.0% | N/A | 100.0% | `READY` | 99.2 |

Optional-field coverage is descriptive, not a validation failure. Dictionary part of speech
is absent because the sampled source does not label it. Sangam `thurai` preserves source
colophon prose and is not treated as a controlled taxonomy. Grammar explanation coverage
is optional because commentary endpoints were outside its three-page fixture scope.

## Schema Stress Test

| Schema Area | Status | Evidence | Recommended Change |
| --- | --- | --- | --- |
| `verse_records` | `supported` | 10 devotional and 3 Sangam verse records retain their distinct hierarchies, authorship, literary metadata, and source identity. | Keep hymn and anthology metadata optional and type-specific within the common envelope. |
| `commentary_records` | `partial` | Pozhppurai and kurippurai are preserved on verse records with commentary URLs, but commentary is not represented as an independent record type. | Define a standalone commentary record/link contract before cross-work commentary analysis. |
| `dictionary_entries` | `supported` | 1 normalized entry retains headword, definition, source URL, deterministic ID, and fixture provenance. | Add ordered sense, example, etymology, and cross-reference structures only after varied fixtures. |
| `grammar_rules` | `supported` | 2 normalized grammar rules retain rule number, rule text, chapter, section, commentary URL, and provenance. | Add structured examples, exceptions, commentator identity, and cross-rule links after varied fixtures. |
| `prose_sections` | `supported` | 2 normalized prose paragraphs retain work, chapter, section, title, author, source URL, and rights metadata. | Add page, footnote, quotation, and edition structures after permissioned source fixtures. |

## Analytical Usefulness

- **அகராதிகள்**: headword explanation; future synonym authority; rare-word support; lexical comparison with literary usage
- **இலக்கணம்**: grammar rule lookup; rule-to-literary-usage comparison; linguistic classification; future example and exception analysis
- **சைவம்**: verse lookup; commentary comparison; deity and devotional motif analysis; poetic language study
- **சங்க இலக்கியம்**: anthology and poem lookup; poet comparison; thinai and situation analysis; classical poetic language comparison
- **இருபதாம் நூற்றாண்டு இலக்கியங்கள் உரைநடைகள்**: paragraph and section lookup; author style comparison; theme and motif analysis; cross-genre literary comparison

## Risks

- Saivam evidence is a bounded Fourth Thirumurai seed, not all Saiva literature.
- Dictionary evidence is one entry from three fixture pages, not a dictionary-wide sample.
- Sangam evidence is three Natrinai poems from three fixture pages, not the anthology.
- Grammar evidence is two Nannul rules from three fixture pages, not the full work.
- Prose evidence is two synthetic paragraphs shaped by three inspected pages; source-text
  ingestion remains permission-gated.
- Optional fields differ legitimately across record types.
- Standalone commentary identity and relationships remain undefined.
- Dictionary sense segmentation and part-of-speech extraction need varied fixtures.

## Next Pilot Recommendation

Recommend **encyclopedias** using `dictionary_parser`.

Inspect encyclopedia article structure before deciding its final parser family.

Risk: `high`. Next action: `complete rights and structure inspection before collecting exactly three allowlisted encyclopedia fixtures`.
This recommendation authorizes fixture planning only, not ingestion or category scraping.
