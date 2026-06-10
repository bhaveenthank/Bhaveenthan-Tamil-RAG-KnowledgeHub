# Pilot Category Validation Report

## Executive Summary

- Verified pilots compared: `3`
- Categories: `dictionaries, saivam, sangam_literature`
- Parser families: `dictionary_parser, verse_parser`
- Network requests: `0`
- LLM calls: `0`

The verified pilots validate the common schema envelope, deterministic IDs, Tamil text,
and exact source URLs across two verse traditions and one dictionary family. The
comparison also exposes an intentional schema gap: commentary is
preserved, but not yet modeled as an independent record.

## Cross-Parser Comparison

| Category | Parser | Record Type | Parsed | Normalized | Errors | Required | Optional | Source URL | Commentary URL | Metadata | Citation | Readiness |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| அகராதிகள் | `dictionary_parser` | `dictionary_entry` | 1 | 1 | 0 | 100.0% | 40.0% | 100.0% | N/A | 100.0% | `READY` | 97.8 |
| சைவம் | `verse_parser` | `verse` | 10 | 10 | 0 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | `READY` | 99.5 |
| சங்க இலக்கியம் | `verse_parser` | `verse` | 3 | 3 | 0 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | `READY` | 99.6 |

Optional-field coverage is descriptive, not a validation failure. Dictionary part of speech
is absent because the sampled source does not label it. Sangam `thurai` preserves source
colophon prose and is not treated as a controlled taxonomy.

## Schema Stress Test

| Schema Area | Status | Evidence | Recommended Change |
| --- | --- | --- | --- |
| `verse_records` | `supported` | 10 devotional and 3 Sangam verse records retain their distinct hierarchies, authorship, literary metadata, and source identity. | Keep hymn and anthology metadata optional and type-specific within the common envelope. |
| `commentary_records` | `partial` | Pozhppurai and kurippurai are preserved on verse records with commentary URLs, but commentary is not represented as an independent record type. | Define a standalone commentary record/link contract before cross-work commentary analysis. |
| `dictionary_entries` | `supported` | 1 normalized entry retains headword, definition, source URL, deterministic ID, and fixture provenance. | Add ordered sense, example, etymology, and cross-reference structures only after varied fixtures. |

## Analytical Usefulness

- **அகராதிகள்**: headword explanation; future synonym authority; rare-word support; lexical comparison with literary usage
- **சைவம்**: verse lookup; commentary comparison; deity and devotional motif analysis; poetic language study
- **சங்க இலக்கியம்**: anthology and poem lookup; poet comparison; thinai and situation analysis; classical poetic language comparison

## Risks

- Saivam evidence is a bounded Fourth Thirumurai seed, not all Saiva literature.
- Dictionary evidence is one entry from three fixture pages, not a dictionary-wide sample.
- Sangam evidence is three Natrinai poems from three fixture pages, not the anthology.
- Optional fields differ legitimately across record types.
- Standalone commentary identity and relationships remain undefined.
- Dictionary sense segmentation and part-of-speech extraction need varied fixtures.

## Next Pilot Recommendation

Recommend **grammar** using `grammar_parser`.

Grammar is the next simpler structured-text parser family.

Risk: `medium`. Next action: `collect exactly three allowlisted grammar fixtures`.
This recommendation authorizes fixture planning only, not ingestion or category scraping.
