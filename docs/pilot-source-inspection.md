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

## Remaining Pilot Risks

| Category Type | Main Parser Risk |
| --- | --- |
| Grammar | Confusing rule text with explanation, example, exception, or commentary |
| Twentieth-century prose | Paragraph/page/footnote boundaries plus edition and rights questions |
| Encyclopedia | Treating mixed article, reference, table, link, and media content as a simple dictionary entry |

## Fixture Contract

Each category receives a target of three fixtures:

1. a navigation or structural example;
2. a simple content unit;
3. a complex content unit containing the category's important edge case.

Fixtures must be small, allowlisted, source-attributed, and manually reviewed. Full books,
full category dumps, credentials, generated corpora, image archives, and unapproved
copyrighted bulk text are prohibited.

## Sangam Inspection Result

The Natrinai pilot confirms why inspection is necessary. Its public work page is an iframe
wrapper, the left frame contains ten-poem navigation ranges, and a legacy JSP endpoint
contains multiple poems plus literary metadata.

Exactly three allowlisted pages were inspected and represented locally: wrapper,
navigation, and one bounded poem-group excerpt. Original response SHA-256 values and exact
URLs are stored separately in fixture metadata.

The fixtures prove poem number, thinai, verse lines, commentary URL, situation, and poet
for the sample. They do not prove all Natrinai variants, commentary parsing, or other
Sangam anthologies.

## Development Order

With dictionary and Sangam pilots validated, continue with `grammar_parser`, then
`prose_parser` after rights review, and encyclopedia adaptation last. Encyclopedia use of
`dictionary_parser` remains the highest-risk assignment because fixtures may prove that a
dedicated adapter or `mixed_parser` delegation is necessary.

## Readiness Gate

A category becomes ready for pilot ingestion only after:

- its source navigation and content endpoint are allowlisted;
- three small fixtures cover simple and edge-case structures;
- exact source URLs and rights notes are recorded;
- parser tests preserve native hierarchy and Tamil text;
- dry-run and bounded ingestion limits remain enforced;
- validation demonstrates deterministic IDs and complete provenance.
