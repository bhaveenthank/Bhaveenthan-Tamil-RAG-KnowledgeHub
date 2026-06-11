# Twentieth-Century Prose Pilot

## Why Prose Is Next

Verse, dictionary entries, and grammar rules are already represented by verified pilots.
Prose is the next distinct typed-text shape: long sentences and paragraphs arranged into
sections and chapters rather than lines, headword senses, or numbered sutras.

## Differences From Existing Content

- Verse depends on line order, poem numbering, meter, and commentary hierarchy.
- Dictionary records center on a headword and one or more definitions.
- Grammar records center on a numbered rule and optional explanation.
- Prose depends on paragraph order, section continuity, chapter hierarchy, author,
  edition, page markers, notes, and possibly footnotes.

## Controlled Fixture Strategy

The pilot inspected exactly three pages: a work wrapper, a contents page, and one essay
wrapper. TamilVU's policy requires permission before reproduction, so committed fixtures
retain only the inspected structure, source URLs, and hashes. The content fixture uses two
synthetic Tamil paragraphs and does not reproduce TamilVU essay text.

## Parser And Schema Mapping

`prose_parser` recognizes explicit prose-section containers and emits one deterministic
`prose_section` record per marked paragraph. Each record retains:

- category, parser family, book, work, chapter, and section identity
- title and author
- paragraph text in `content_text`
- exact inspected source URL
- source link ID, paragraph index, fixture status, rights status, and citation text

The normalized output is
`data/processed/normalized_categories/prose_normalized.jsonl`.

## Segmentation Strategy

Paragraphs are the pilot retrieval unit because they are readable, citable, and smaller
than a full essay. IDs combine the inspected section identity with an ordered paragraph
number. The parser does not infer paragraphs from arbitrary page-wide text; source
adapters must mark the approved content container explicitly.

## Challenges And Limits

- The selected section page is itself an iframe wrapper.
- Its legacy content endpoint was outside the three-request pilot budget.
- Page markers, footnotes, quotations, lists, and multi-part essays are unproven.
- Modern works need per-edition rights and access review.
- This phase validates architecture and parser behavior, not source-text ingestion.

## Analytical Value

Prose supports author-style comparison, narrative and essay themes, explanatory passages,
historical vocabulary, quotation study, and cross-genre comparison with poetry, grammar,
and dictionary evidence.
