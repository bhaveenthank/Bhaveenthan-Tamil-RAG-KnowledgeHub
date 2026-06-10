# Controlled Multi-Category Pilot Ingestion

## Purpose

Website-wide architecture is useful only if it can preserve different Tamil literary
structures without flattening them into a Thirumurai-only record. This phase introduces a
small, deterministic ingestion contract for several parser families before any category is
approved for broad extraction.

Small samples limit network, rights, parser, and data-quality risk. Each pilot is capped at
one inspected book and ten records. The framework contains no recursive crawler and makes
no network request in this phase.

## Selected Pilots

| Category | Parser Family | Current Source State |
| --- | --- | --- |
| இலக்கணம் | `grammar_parser` | Source inspection required |
| சங்க இலக்கியம் | `verse_parser` | Source inspection required |
| சைவம் | `verse_parser` | Existing Fourth Thirumurai validated seed |
| இருபதாம் நூற்றாண்டு இலக்கியங்கள் உரைநடைகள் | `prose_parser` | Source and rights inspection required |
| அகராதிகள் | `dictionary_parser` | Source inspection required |
| கலைக்களஞ்சியங்கள் | `dictionary_parser` | Source inspection required |

The Saivam verification reads ten records at most from the existing local Fourth
Thirumurai pilot. It does not refetch TamilVU and does not change that source artifact.

## Pipeline

1. Read the category registry and controlled pilot plan.
2. Reject categories outside the plan.
3. Enforce `max_books=1` and `max_records<=10`.
4. Read only an approved local seed.
5. Preserve a write-once source snapshot under `data/raw/pilot_categories/`.
6. Parse through the registered parser-family interface.
7. Write pilot records under `data/processed/pilot_categories/`.
8. Normalize separately to website corpus schema v2.
9. Validate IDs, hierarchy, Tamil content, parser identity, and source URLs.

## Difference From Thirumurai Ingestion

The Thirumurai scraper understands SLET hymn, verse, and commentary endpoints. This
framework instead defines a common envelope for poetry, prose, grammar, dictionary,
table, image, mixed, and external-reference parsers. Category-specific extraction remains
unimplemented until fixtures prove each source structure.

This prevents a verse parser from making destructive assumptions about grammar rules,
dictionary senses, prose paragraphs, or manuscript images.

## Safety And Determinism

- No full-category or website-wide crawl.
- No HTTP library is used by the category pilot CLI.
- Raw and processed pilot paths are separate from frozen corpora.
- Existing files are reused only when byte-identical; changed output is never overwritten.
- IDs are SHA-256-derived from category, book, work, native identity, URL, and content.
- No timestamps or random IDs enter normalized records.
- Source URLs and parser-family metadata remain attached to every record.

## Expansion Gate

Each remaining pilot requires navigation inspection, an allowlisted source, local fixtures,
rights notes where relevant, parser-specific tests, sample validation, and a readiness
decision. Only then may its plan status move from `planned` to a local-seed-ready state.
