# Pilot Category Validation

## Why Cross-Pilot Validation Matters

A category can pass its own parser tests while still exposing incompatibilities at the
website-corpus level. Cross-pilot validation checks whether record identity, provenance,
content fields, citations, and metadata remain comparable when fundamentally different
Tamil sources share unified schema v2.

Validating one category at a time is not enough because local success can hide:

- fields that mean different things across content types;
- required fields that unfairly assume poetry or prose;
- source and citation metadata that cannot be aggregated;
- analytical gaps that appear only when records are compared;
- optional fields mistakenly treated as universal requirements.

## Current Pilots

### Saivam

The Saivam pilot uses devotional verse with hymn and song identity, poetic line structure,
author, commentary, and separate hymn/commentary URLs. Its analytical strengths are verse
lookup, commentary comparison, deity language, devotional motifs, and poetic expression.

### Dictionaries

The dictionary pilot uses a headword and definition as its primary unit. It has no hymn,
verse, or commentary hierarchy. Its strengths are lexical explanation, rare-word support,
future synonym authority, and comparison between dictionary meaning and literary usage.

### Sangam Literature

The Natrinai pilot adds anthology poem identity, line-preserving verse text, explicit
thinai, source colophon prose, poet attribution, and commentary URLs. It proves that
`verse_parser` can support both devotional hymn records and Sangam poem records while
keeping their distinct literary metadata optional and type-specific.

## Unified Schema v2 Findings

The shared envelope successfully supports deterministic record IDs, category/book/work
identity, Tamil content, parser-family metadata, and exact source URLs for all three
verified pilots.

Verse records are supported with preserved Thirumurai-specific and Sangam-specific
fields. Dictionary entries are supported with headword and definition fields. Commentary is currently partial at
schema level: `pozhppurai`, `kurippurai`, and commentary URLs are preserved on verse
records, but commentary does not yet have an independent record identity or relationship
contract.

This is acceptable for current retrieval, but standalone commentary records will be needed
before corpus-wide commentator comparison or commentary-specific citation.

## Coverage Interpretation

Required-field coverage measures the common schema contract. Optional-field coverage is
descriptive and must not be used to penalize a dictionary for lacking hymn fields or a
verse for lacking a dictionary headword.

Citation readiness requires exact source URLs and enough native identity to name the
source unit. Metadata completeness measures parser, pilot, and provenance fields relevant
to each source family.

## Next Pilot

Grammar is recommended next. It adds rule, explanation, example, exception, and commentary
boundaries to the unified schema without taking on the mixed-media risks of encyclopedia
content.

This recommendation is only for collecting exactly three allowlisted fixtures. It does not
authorize grammar ingestion or category scraping.
