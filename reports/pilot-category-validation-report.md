# Pilot Category Validation Report

## Executive Summary

- Verified pilots compared: `4`
- Categories: `dictionaries, grammar, saivam, sangam_literature`
- Parser families: `dictionary_parser, grammar_parser, verse_parser`
- Network requests: `0`
- LLM calls: `0`

The verified pilots validate the common schema envelope, deterministic IDs, Tamil text,
and exact source URLs across two verse traditions, one dictionary family, and structured
grammar rules. The
comparison also exposes an intentional schema gap: commentary is
preserved, but not yet modeled as an independent record.

## Cross-Parser Comparison

| Category | Parser | Record Type | Parsed | Normalized | Errors | Required | Optional | Source URL | Commentary URL | Metadata | Citation | Readiness |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| அகராதிகள் | `dictionary_parser` | `dictionary_entry` | 1 | 1 | 0 | 100.0% | 40.0% | 100.0% | N/A | 100.0% | `READY` | 97.8 |
| இலக்கணம் | `grammar_parser` | `grammar_rule` | 2 | 2 | 0 | 100.0% | 85.7% | 100.0% | 100.0% | 100.0% | `READY` | 98.8 |
| சைவம் | `verse_parser` | `verse` | 10 | 10 | 0 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | `READY` | 99.5 |
| சங்க இலக்கியம் | `verse_parser` | `verse` | 3 | 3 | 0 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | `READY` | 99.6 |

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

## Analytical Usefulness

- **அகராதிகள்**: headword explanation; future synonym authority; rare-word support; lexical comparison with literary usage
- **இலக்கணம்**: grammar rule lookup; rule-to-literary-usage comparison; linguistic classification; future example and exception analysis
- **சைவம்**: verse lookup; commentary comparison; deity and devotional motif analysis; poetic language study
- **சங்க இலக்கியம்**: anthology and poem lookup; poet comparison; thinai and situation analysis; classical poetic language comparison

## Risks

- Saivam evidence is a bounded Fourth Thirumurai seed, not all Saiva literature.
- Dictionary evidence is one entry from three fixture pages, not a dictionary-wide sample.
- Sangam evidence is three Natrinai poems from three fixture pages, not the anthology.
- Grammar evidence is two Nannul rules from three fixture pages, not the full work.
- Optional fields differ legitimately across record types.
- Standalone commentary identity and relationships remain undefined.
- Dictionary sense segmentation and part-of-speech extraction need varied fixtures.

## Next Pilot Recommendation

Recommend **twentieth_century_prose** using `prose_parser`.

Prose is the next distinct typed-text hierarchy after grammar, while encyclopedia content remains a higher-risk mixed article/media shape.

Risk: `high`. Next action: `complete rights review, then collect exactly three allowlisted prose fixtures`.
This recommendation authorizes fixture planning only, not ingestion or category scraping.
