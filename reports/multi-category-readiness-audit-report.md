# Multi-Category Readiness Audit Report

## Executive Summary

- Verified categories: `4`
- Verified records inspected: `16`
- TamilVU registry categories assessed: `32`
- Overall readiness: `76.5/100`
- Website-wide decision: `PARTIAL_NOT_SCALE_READY`
- Network requests: `0`
- LLM calls: `0`
- Frozen corpus mutations: `0`

Four pilots now exercise two distinct poetry hierarchies, one lexical hierarchy, and one
grammar-rule hierarchy through the same identity, provenance, validation, and normalization
envelope. They are not sufficient to declare the remaining parser families production-ready.

## Readiness Scores

| Dimension | Score |
| --- | ---: |
| `schema_readiness` | 81.9 |
| `parser_readiness` | 68.8 |
| `metadata_readiness` | 98.5 |
| `citation_readiness` | 97.5 |
| `analytics_readiness` | 68.9 |
| `expansion_readiness` | 43.1 |
| `overall_readiness` | 76.5 |

Scores are deterministic weighted evidence summaries. Schema emphasizes common-field
coverage while discounting unobserved record types. Parser readiness gives half its weight
to verified family coverage. Expansion readiness maps each category as ready `100`,
partial `55`, or not ready `20`. Overall readiness is the unweighted mean of the six
dimensions, preventing strong citations from hiding weak parser coverage.

## Evidence Learned

- **Saivam:** proves hymn/verse/commentary identity, author, devotional metadata, and exact source traceability.
- **Sangam:** proves anthology poem identity, thinai, situation, poet, colophon, and line preservation.
- **Dictionaries:** proves headword-definition records and lexical content without inventing absent part-of-speech metadata.
- **Grammar:** proves numbered rule text, chapter/section hierarchy, and exact commentary traceability.

## Schema Readiness

Common required-field coverage is `100.0%`.
Observed record-type evidence covers `37.5%`
of the eight schema v2 record types. The shared envelope is strong, but standalone
commentary, prose, encyclopedia, and image contracts remain partly or wholly
unverified.

## Parser Readiness Matrix

| Parser Family | Registry Categories | Status | Major Gap |
| --- | ---: | --- | --- |
| `dictionary_parser` | 4 | `pilot_verified` | Sense order, examples, cross-references, and encyclopedia article structure are not generally proven. |
| `external_link_registry` | 1 | `stub_unverified` | Institution, robots, rights, scope, and approval metadata need a registry-only pilot. |
| `grammar_parser` | 1 | `pilot_verified` | Sutra, explanation, example, exception, and commentator boundaries are unverified. |
| `image_metadata_parser` | 5 | `stub_unverified` | Image rights, folio identity, asset inventory, transcription, and OCR provenance are unverified. |
| `mixed_parser` | 10 | `stub_unverified` | No dispatch contract has been proven for pages combining verse, prose, tables, or media. |
| `prose_parser` | 3 | `stub_unverified` | Chapter, paragraph, page, footnote, edition, and rights metadata are unverified. |
| `table_parser` | 1 | `stub_unverified` | Column identity, multilingual cells, repeated headers, and domain labels are unverified. |
| `verse_parser` | 7 | `pilot_verified` | Work-specific numbering, colophons, meter, commentary, and author labels still require fixtures. |

## Metadata And Citation

- Author coverage: `93.8%`
- Title coverage: `100.0%`
- Source coverage: `100.0%`
- Category coverage: `100.0%`
- Citation source URL coverage: `100.0%`
- Citation identity traceability: `100.0%`

## Literary Analytics Readiness

| Capability | Score | Status | Evidence |
| --- | ---: | --- | --- |
| `synonym_analysis` | 55 | `partial` | Dictionary structure is proven, but only one entry and no nigandu semantic groups are verified. |
| `motif_analysis` | 72 | `partial` | Two poetry traditions are represented, but motifs are not normalized annotations. |
| `entity_analysis` | 40 | `partial` | Authors and selected literary metadata exist; generalized entity extraction and confidence are absent. |
| `deity_analysis` | 75 | `partial` | Saivam supplies devotional evidence, but deity normalization is not proven across traditions. |
| `author_comparison` | 90 | `ready` | Saivam and Sangam records preserve normalized author identity and source citations. |
| `cross_corpus_comparison` | 85 | `ready` | The common envelope supports two verse traditions plus lexical evidence without flattening their identities. |
| `grammar_rule_analysis` | 65 | `partial` | Numbered Nannul rules are structured, but explanations, examples, exceptions, and cross-rule links remain unverified. |

## Future Category Readiness

| Category Family | Status | Evidence | Major Risk |
| --- | --- | --- | --- |
| `grammar` | `ready` | Nannul fixtures validate numbered grammar_rule records, hierarchy, citations, and deterministic identity. | Examples, exceptions, commentator identity, and explanation parsing need broader fixtures. |
| `prose` | `partial` | Schema v2 defines prose_section, but no prose fixture validates hierarchy or rights metadata. | Chapter, paragraph, page, footnote, edition, and rights boundaries. |
| `encyclopedias` | `not_ready` | The dictionary envelope is reusable, but the assigned parser has no article/media evidence. | Flattening sections, references, cross-links, tables, and media into a definition. |
| `mixed_content` | `not_ready` | MixedParser is a conservative schema stub with no proven source dispatch. | Losing relationships between verse, prose, commentary, tables, and assets. |

## Can The Current Architecture Support All 32 TamilVU Categories?

**Partially.** The registry, common schema, stable IDs, and provenance envelope can name
and trace all 32 categories. The extraction architecture is not scale-ready because only
three parser families have source evidence and mixed/image families remain unproven.

Status counts: `{"not_ready": 16, "partial": 12, "ready": 4}`.

## Category Readiness Matrix

| Category ID | Tamil Category | Expected Parser | Status | Major Risk | Recommended Next Step |
| --- | --- | --- | --- | --- | --- |
| `word_index` | சொல்லடைவு | `dictionary_parser` | `partial` | Sense order, examples, cross-references, and encyclopedia article structure are not generally proven. | Collect three work-specific fixtures and validate hierarchy before ingestion. |
| `tamil_numeral_manuscript` | தமிழ் எண் சுவடி | `image_metadata_parser` | `not_ready` | Image rights, folio identity, asset inventory, transcription, and OCR provenance are unverified. | Run source inspection and a three-fixture parser-family pilot before ingestion. |
| `grammar` | இலக்கணம் | `grammar_parser` | `ready` | Bounded pilot evidence validates parser output, schema mapping, and provenance. | Retain bounded expansion gates and sample structural variants before scale. |
| `sangam_literature` | சங்க இலக்கியம் | `verse_parser` | `ready` | Bounded pilot evidence validates parser output, schema mapping, and provenance. | Retain bounded expansion gates and sample structural variants before scale. |
| `eighteen_minor_works` | பதினெண் கீழ்க்கணக்கு | `verse_parser` | `partial` | Work-specific numbering, colophons, meter, commentary, and author labels still require fixtures. | Collect three work-specific fixtures and validate hierarchy before ingestion. |
| `epics` | காப்பியங்கள் | `mixed_parser` | `not_ready` | No dispatch contract has been proven for pages combining verse, prose, tables, or media. | Run source inspection and a three-fixture parser-family pilot before ingestion. |
| `religious_literature` | சமய இலக்கியங்கள் | `mixed_parser` | `not_ready` | No dispatch contract has been proven for pages combining verse, prose, tables, or media. | Run source inspection and a three-fixture parser-family pilot before ingestion. |
| `saivam` | சைவம் | `verse_parser` | `ready` | Bounded pilot evidence validates parser output, schema mapping, and provenance. | Retain bounded expansion gates and sample structural variants before scale. |
| `vaishnavam` | வைணவம் | `verse_parser` | `partial` | Work-specific numbering, colophons, meter, commentary, and author labels still require fixtures. | Collect three work-specific fixtures and validate hierarchy before ingestion. |
| `christian_literature` | கிறித்துவம் | `mixed_parser` | `not_ready` | No dispatch contract has been proven for pages combining verse, prose, tables, or media. | Run source inspection and a three-fixture parser-family pilot before ingestion. |
| `islamic_literature` | இசுலாம் | `mixed_parser` | `not_ready` | No dispatch contract has been proven for pages combining verse, prose, tables, or media. | Run source inspection and a three-fixture parser-family pilot before ingestion. |
| `minor_literary_forms` | சிற்றிலக்கியங்கள் | `verse_parser` | `partial` | Work-specific numbering, colophons, meter, commentary, and author labels still require fixtures. | Collect three work-specific fixtures and validate hierarchy before ingestion. |
| `ethical_works` | நெறி நூல்கள் | `mixed_parser` | `not_ready` | No dispatch contract has been proven for pages combining verse, prose, tables, or media. | Run source inspection and a three-fixture parser-family pilot before ingestion. |
| `siddhar_literature` | சித்தர் இலக்கியம் | `verse_parser` | `partial` | Work-specific numbering, colophons, meter, commentary, and author labels still require fixtures. | Collect three work-specific fixtures and validate hierarchy before ingestion. |
| `twentieth_century_poetry` | இருபதாம் நூற்றாண்டு இலக்கியங்கள் கவிதைகள் | `verse_parser` | `partial` | Work-specific numbering, colophons, meter, commentary, and author labels still require fixtures. | Collect three work-specific fixtures and validate hierarchy before ingestion. |
| `twentieth_century_prose` | இருபதாம் நூற்றாண்டு இலக்கியங்கள் உரைநடைகள் | `prose_parser` | `partial` | Chapter, paragraph, page, footnote, edition, and rights metadata are unverified. | Validate this parser family with three allowlisted fixtures and schema-specific tests. |
| `folk_literature` | நாட்டுப்புற இலக்கியங்கள் | `mixed_parser` | `not_ready` | No dispatch contract has been proven for pages combining verse, prose, tables, or media. | Run source inspection and a three-fixture parser-family pilot before ingestion. |
| `childrens_literature` | சிறுவர் இலக்கியங்கள் | `mixed_parser` | `not_ready` | No dispatch contract has been proven for pages combining verse, prose, tables, or media. | Run source inspection and a three-fixture parser-family pilot before ingestion. |
| `romanized_literature` | ரோமன் வடிவம் | `mixed_parser` | `not_ready` | No dispatch contract has been proven for pages combining verse, prose, tables, or media. | Run source inspection and a three-fixture parser-family pilot before ingestion. |
| `dictionaries` | அகராதிகள் | `dictionary_parser` | `ready` | Bounded pilot evidence validates parser output, schema mapping, and provenance. | Retain bounded expansion gates and sample structural variants before scale. |
| `nigandus` | நிகண்டுகள் | `dictionary_parser` | `partial` | Sense order, examples, cross-references, and encyclopedia article structure are not generally proven. | Collect three work-specific fixtures and validate hierarchy before ingestion. |
| `tamil_books_in_other_languages` | பிற மொழியில் தமிழ் நூல்கள் | `mixed_parser` | `not_ready` | No dispatch contract has been proven for pages combining verse, prose, tables, or media. | Run source inspection and a three-fixture parser-family pilot before ingestion. |
| `encyclopedias` | கலைக்களஞ்சியங்கள் | `dictionary_parser` | `not_ready` | The registry assigns dictionary_parser, but mixed article, reference, table, and media structure is unproven. | Inspect three fixtures and decide whether a dedicated encyclopedia adapter is required. |
| `terminology_collections` | கலைச்சொல் தொகுப்புகள் | `table_parser` | `partial` | Column identity, multilingual cells, repeated headers, and domain labels are unverified. | Validate this parser family with three allowlisted fixtures and schema-specific tests. |
| `manuscript_gallery` | சுவடிக்காட்சியகம் | `image_metadata_parser` | `not_ready` | Image rights, folio identity, asset inventory, transcription, and OCR provenance are unverified. | Run source inspection and a three-fixture parser-family pilot before ingestion. |
| `cultural_gallery` | பண்பாட்டுக் காட்சியகம் | `image_metadata_parser` | `not_ready` | Image rights, folio identity, asset inventory, transcription, and OCR provenance are unverified. | Run source inspection and a three-fixture parser-family pilot before ingestion. |
| `public_domain_books` | நாட்டுடைமை நூல்கள் | `mixed_parser` | `not_ready` | No dispatch contract has been proven for pages combining verse, prose, tables, or media. | Run source inspection and a three-fixture parser-family pilot before ingestion. |
| `public_domain_scholars_image_books` | நாட்டுடைமையாக்கப்பட்ட தமிழறிஞர்களின் நூல்கள் உருப்பட வடிவில் | `image_metadata_parser` | `not_ready` | Image rights, folio identity, asset inventory, transcription, and OCR provenance are unverified. | Run source inspection and a three-fixture parser-family pilot before ingestion. |
| `public_domain_scholars_typed_books` | நாட்டுடைமையாக்கப்பட்ட தமிழறிஞர்களின் நூல்கள் தட்டச்சு வடிவில் | `prose_parser` | `partial` | Chapter, paragraph, page, footnote, edition, and rights metadata are unverified. | Validate this parser family with three allowlisted fixtures and schema-specific tests. |
| `image_books` | உருப்பட நூல்கள் | `image_metadata_parser` | `not_ready` | Image rights, folio identity, asset inventory, transcription, and OCR provenance are unverified. | Run source inspection and a three-fixture parser-family pilot before ingestion. |
| `tamil_history_culture_literature_books` | தமிழக வரலாறு, கலைப் பண்பாடு, இலக்கியம் தொடர்பான நூல்கள் | `prose_parser` | `partial` | Chapter, paragraph, page, footnote, edition, and rights metadata are unverified. | Validate this parser family with three allowlisted fixtures and schema-specific tests. |
| `external_library_websites` | பிற நூலக இணையத் தளங்கள் | `external_link_registry` | `partial` | Institution, robots, rights, scope, and approval metadata need a registry-only pilot. | Validate this parser family with three allowlisted fixtures and schema-specific tests. |

## Architecture Strengths

- Stable source-scoped IDs and a shared provenance envelope work across verse, dictionary, and grammar records.
- Two poetry traditions retain distinct hierarchy without schema fragmentation.
- Numbered grammar rules retain chapter, section, rule text, and commentary traceability.
- All verified records retain exact source URLs and validation passes with zero errors.
- Raw/processed/report separation and fixture-first testing support controlled expansion.

## Architecture Weaknesses

- Only three of eight parser families have bounded source evidence.
- Standalone commentary, entity, motif, and normalized literary-concept contracts remain incomplete.
- Mixed-content dispatch and encyclopedia article modeling are not proven.
- Image/manuscript rights, asset metadata, transcription, and OCR provenance are not proven.

## Scaling Risks

- Treating a shared schema envelope as proof that source-specific parsers are interchangeable.
- Flattening work-specific hierarchy when expanding verse_parser to new traditions.
- Using dictionary_parser for encyclopedias without proving article and media boundaries.
- Scaling modern prose before rights, edition, page, and footnote metadata are explicit.
- Introducing OCR or mixed-content ingestion without confidence and source-image traceability.

## Strategic Recommendation

Choose **twentieth-century prose** using `prose_parser`.

With grammar now verified, prose is the next distinct typed-text hierarchy. It tests chapters, sections, paragraphs, pages, and footnotes while remaining structurally clearer than encyclopedia articles that may mix references, tables, cross-links, and media.

- **Precondition:** Complete book-level rights and public-domain review before collecting any prose fixture.
- **Why not encyclopedia yet:** The current dictionary_parser assignment may be structurally wrong for articles containing sections, references, tables, and media.
- **Next action:** After rights review, collect exactly three allowlisted prose fixtures in a separately approved phase.
