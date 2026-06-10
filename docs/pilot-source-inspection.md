# Pilot Source Inspection And Fixture Collection

## Why Inspection Comes First

TamilVU categories do not share one reliable document structure. A poem may have stanza,
poet, thinai, colophon, and commentary boundaries; grammar may separate sutra, explanation,
example, and exception; dictionaries need headword and sense ordering; prose needs chapters,
paragraphs, pages, and footnotes; encyclopedia articles may mix text, tables, links, and
images.

Applying a parser before seeing these boundaries can silently flatten valuable literary
hierarchy. Source inspection therefore precedes ingestion for every new category family.

## Why Fixtures Are Safer

Fixtures let parser development use a tiny, reviewed, reproducible sample instead of a live
website or full category. They:

- prevent accidental recursive crawling;
- keep tests independent of network availability and website changes;
- expose unusual HTML or text structures in code review;
- preserve UTF-8 Tamil examples and source provenance;
- make parser changes deterministic and regression-testable;
- limit copyright and storage risk by excluding full books and bulk exports.

This phase creates only fixture plans and placeholder directories. It does not collect live
HTML or ingest the five remaining categories.

## Remaining Pilot Risks

| Category Type | Main Parser Risk |
| --- | --- |
| Grammar | Confusing rule text with explanation, example, exception, or commentary |
| Sangam poetry | Losing anthology, poem, poet, thinai/thurai, colophon, or commentary hierarchy |
| Twentieth-century prose | Paragraph/page/footnote boundaries plus edition and rights questions |
| Dictionary | Losing sense order, labels, examples, etymology, or cross-references |
| Encyclopedia | Treating mixed article, reference, table, link, and media content as a simple dictionary entry |

## Fixture Contract

Each category receives a target of three fixtures:

1. a navigation or structural example;
2. a simple content unit;
3. a complex content unit containing the category's important edge case.

Fixtures must be small, allowlisted, source-attributed, and manually reviewed. Full books,
full category dumps, credentials, generated corpora, image archives, and unapproved
copyrighted bulk text are prohibited.

## Development Order

Start with `dictionary_parser` for ordinary dictionary entries because bounded headword and
sense structures are likely to be the simplest new structured-text unit. Continue with
`grammar_parser`, the Sangam `verse_parser` variant, `prose_parser` after rights review, and
encyclopedia adaptation last.

The encyclopedia use of `dictionary_parser` is the highest-risk assignment: fixtures may
prove that a dedicated adapter or `mixed_parser` delegation is necessary.

## Readiness Gate

A category becomes ready for pilot ingestion only after:

- its source navigation and content endpoint are allowlisted;
- three small fixtures cover simple and edge-case structures;
- exact source URLs and rights notes are recorded;
- parser tests preserve native hierarchy and Tamil text;
- dry-run and bounded ingestion limits remain enforced;
- validation demonstrates deterministic IDs and complete provenance.
