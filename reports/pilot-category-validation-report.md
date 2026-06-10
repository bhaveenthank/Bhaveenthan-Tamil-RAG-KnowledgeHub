# Pilot Category Validation Report

## Executive Summary

- Verified pilots compared: `2`
- Categories: `dictionaries, saivam`
- Parser families: `dictionary_parser, verse_parser`
- Network requests: `0`
- LLM calls: `0`

Both pilots validate the common schema envelope, deterministic IDs, Tamil text, and exact
source URLs. The comparison also exposes an intentional schema gap: commentary is
preserved, but not yet modeled as an independent record.

## Cross-Parser Comparison

| Category | Parser | Record Type | Parsed | Normalized | Errors | Required | Optional | Source URL | Commentary URL | Metadata | Citation | Readiness |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| அகராதிகள் | `dictionary_parser` | `dictionary_entry` | 1 | 1 | 0 | 100.0% | 40.0% | 100.0% | N/A | 100.0% | `READY` | 97.8 |
| சைவம் | `verse_parser` | `verse` | 10 | 10 | 0 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | `READY` | 99.5 |

Optional-field coverage is descriptive, not a validation failure. Dictionary part of speech
is absent because the sampled source does not label it.

## Schema Stress Test

| Schema Area | Status | Evidence | Recommended Change |
| --- | --- | --- | --- |
| `verse_records` | `supported` | 10 normalized verse records retain verse, hymn, author, commentary, and source identity. | Promote frequently queried poetry metadata only after another verse family proves it. |
| `commentary_records` | `partial` | Pozhppurai and kurippurai are preserved on verse records with commentary URLs, but commentary is not represented as an independent record type. | Define a standalone commentary record/link contract before cross-work commentary analysis. |
| `dictionary_entries` | `supported` | 1 normalized entry retains headword, definition, source URL, deterministic ID, and fixture provenance. | Add ordered sense, example, etymology, and cross-reference structures only after varied fixtures. |

## Analytical Usefulness

- **அகராதிகள்**: headword explanation; future synonym authority; rare-word support; lexical comparison with literary usage
- **சைவம்**: verse lookup; commentary comparison; deity and devotional motif analysis; poetic language study

## Risks

- Saivam evidence is a bounded Fourth Thirumurai seed, not all Saiva literature.
- Dictionary evidence is one entry from three fixture pages, not a dictionary-wide sample.
- Optional fields differ legitimately across record types.
- Standalone commentary identity and relationships remain undefined.
- Dictionary sense segmentation and part-of-speech extraction need varied fixtures.

## Next Pilot Recommendation

Recommend **sangam_literature** using `verse_parser`.

Grammar and Sangam both still require fixtures; Sangam is recommended because it contributes poem, poet, thinai/thurai, colophon, and commentary evidence directly to literary comparison. Collect fixtures before ingestion.

Risk: `high`. Next action: `collect exactly three allowlisted Sangam fixtures`.
This recommendation authorizes fixture planning only, not ingestion or category scraping.
