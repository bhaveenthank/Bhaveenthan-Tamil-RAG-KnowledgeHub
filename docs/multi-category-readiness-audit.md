# Multi-Category Readiness Audit

## Why Audit After Four Pilots

The first three verified categories provided the smallest useful architectural stress
test. Saivam
and Sangam both contain poetry, but their native hierarchies differ: hymns, sacred places,
pann, and commentary versus anthology poems, thinai, situation, poet, and colophon.
Dictionaries introduce a non-poetry record centered on a headword and definition. Grammar
now adds numbered normative rules inside chapter and section hierarchy.

Together they test whether unified schema v2 can reuse identity, content, provenance,
language, validation, and citation fields without flattening category-specific evidence.
They do not prove prose, mixed, table, image, or external-link parsing.

## Lessons From Verified Pilots

### Saivam

Saivam proves stable hymn and verse identities, ordered Tamil text, commentary separation,
author metadata, and exact source URLs across legacy frame/JSP endpoints.

### Sangam

Natrinai proves that `verse_parser` can support a second literary tradition. It preserves
poem number, thinai, situation, poet, colophon, line order, source URL, and commentary URL
without forcing those values into Thirumurai fields.

### Dictionaries

The dictionary pilot proves a distinct lexical record type. It also establishes a useful
discipline: optional metadata such as part of speech remains empty when the source does not
label it.

### Grammar

The Nannul pilot proves that `grammar_parser` can preserve rule number, rule text, chapter,
section, source identity, and commentary traceability without treating metrical sutra text
as literary verse.

## Architectural Strengths

- deterministic source-scoped record IDs;
- a common schema envelope with type-specific fields;
- exact source URLs and fixture provenance;
- raw, processed, report, release, and index separation;
- parser-family boundaries and bounded pilot gates;
- UTF-8 Tamil preservation and offline fixture tests;
- compatibility across devotional verse, classical anthology verse, lexical entries, and
  grammar rules.

## Architectural Weaknesses

- only `verse_parser`, `dictionary_parser`, and `grammar_parser` have verified source evidence;
- standalone commentary records and relationships remain partial;
- entities, motifs, themes, places, deity normalization, and synonym relationships are not
  general corpus contracts;
- grammar explanation/example variants and prose hierarchy remain unverified;
- `mixed_parser` has no proven dispatch strategy;
- encyclopedia content may not fit `dictionary_parser`;
- image/manuscript rights, asset metadata, transcription, and OCR provenance are unproven.

## Scaling Risks

The largest risk is confusing schema compatibility with extraction readiness. A category
can fit the common envelope while still requiring a source-specific parser for hierarchy,
numbering, commentary, tables, media, rights, or edition metadata.

Website-wide expansion must therefore continue through source inspection, exactly bounded
fixtures, parser tests, normalization, validation, and readiness audit. Mixed and
image-heavy categories should remain deferred until simpler structured-text families are
proven.

## Scoring Method

The audit uses deterministic evidence:

- schema readiness combines common required-field coverage, schema stress results, and
  observed record-type coverage;
- parser readiness combines verified-family coverage, validation consistency, and output
  compatibility;
- metadata and citation scores come from actual verified records;
- analytics readiness uses explicit capability evidence and known missing contracts;
- expansion readiness maps every registry category to ready, partial, or not ready;
- overall readiness is the unweighted mean of the six dimensions.

This deliberately penalizes untested parser families even when schema v2 already names
their future record type.

## Scientific Next Step

Twentieth-century prose is the next recommended parser-family pilot, but only after
book-level rights and public-domain review. It introduces chapter, section, paragraph,
page, and footnote hierarchy. Encyclopedia remains deferred because its article,
reference, table, cross-link, and media structure may require a parser different from the
current dictionary assignment.
