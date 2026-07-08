# An Audit-First Digital Corpus Pipeline for Thevaram: Structuring Books 1-8 for Citation-Grounded Tamil Literary Research

## Abstract

Tamil devotional literature is increasingly available through digital library websites, but web availability alone does not make a corpus suitable for computational research, retrieval, or AI-assisted literary study. Classical Tamil corpora require stable source provenance, preservation of literary hierarchy, separation of verse and commentary, Unicode-safe normalization, and explicit accounting of source gaps. This paper presents an audit-first pipeline for structuring Thevaram books 1-8 from Tamil Virtual Academy/TamilVU material into a normalized, citation-grounded corpus resource. The current normalized resource contains 8 Thirumurai books, 841 paadal thogupugal, 9012 paadalgal, 9012 commentary records, and 64073 text spans. The pipeline preserves source URLs, line boundaries, record identifiers, and separate commentary fields, while generating quality reports for ingestion, normalization, table validation, commentary coverage, entity annotation, and paadal-pozhppurai linking. We distinguish between the broad Thevaram 1-8 normalized resource, the more mature audited Irandaam Thirumurai v1 release subset, and experimental downstream layers such as deterministic entity annotation and commentary alignment. The paper argues that audit-first corpus construction is a necessary foundation for citation-grounded Tamil literary retrieval, digital humanities research, and future question-answering systems.

## 1. Introduction

Digital access to Tamil literary material has improved substantially through institutional resources such as Tamil Virtual Academy/TamilVU. However, access through web pages is not the same as availability as a research corpus. A reader can navigate a hymn page manually, but computational systems require stable record boundaries, source URLs, normalized Unicode, metadata, and repeatable quality checks. This gap becomes especially important for classical Tamil devotional literature, where a useful record is not merely a block of text. It may include a hymn, a verse, commentary, place metadata, author information, musical or liturgical metadata, and source-specific identifiers.

This paper describes a corpus construction pipeline for Thevaram books 1-8. Thevaram is a major body of Tamil Saiva devotional poetry, and its computational use requires careful handling of poetic structure and commentary. A naive scraper can collect visible text, but it can also flatten literary hierarchy, mix commentary with verse, lose source URLs, and hide missing source material. Our central claim is that Tamil literary corpus construction should be treated as an audit and preservation problem before it is treated as a retrieval or language-modeling problem.

The resource described here currently covers Thevaram Thirumurai 1-8 in normalized relational tables. It contains 8 books, 841 paadal thogupugal, 9012 paadalgal, 9012 commentary records, and 64073 text spans. The pipeline also produces downstream evidence layers, including deterministic entity annotation and paadal-pozhppurai linking. These layers are useful for retrieval and future literary analysis, but they are not presented as final expert-validated scholarly annotation. The broader goal is to build a citation-grounded foundation for Tamil literary search, corpus analysis, and question answering.

The contributions of this work are:

1. A normalized Thevaram 1-8 corpus resource that preserves verse records, commentary records, text spans, source URLs, and literary identifiers.
2. An audit-first extraction and normalization workflow designed for heterogeneous TamilVU source structures.
3. Quantitative quality reports covering ingestion, normalization, table validation, commentary coverage, and downstream evidence layers.
4. A release strategy that separates broad normalized coverage from mature audited release subsets and experimental annotation layers.

## 2. Motivation and Design Requirements

Tamil literary users have different needs from ordinary document search users. A poet may search for recurring imagery, a researcher may need source-traceable citations, a student may need verse and commentary kept separate, and a future question-answering system must know whether an answer is supported by verse text, commentary, metadata, or an inferred annotation. These requirements shaped the pipeline design.

The main design requirements were:

- Preserve source provenance through source URLs and source-specific parameters.
- Preserve literary hierarchy instead of flattening texts into undifferentiated pages.
- Keep paadal text separate from pozhppurai and kurippurai commentary.
- Preserve line boundaries because they encode poetic structure.
- Normalize Unicode without damaging Tamil text.
- Record missing commentary explicitly instead of fabricating or silently dropping records.
- Produce reusable table outputs and quality reports.
- Support future retrieval, entity annotation, commentary alignment, and question answering.

These requirements also imply what the system should not do. It should not claim that top-k retrieval can support corpus-wide literary claims. It should not treat deterministic entity matches as expert interpretation. It should not hide gaps in the source or parser coverage. In this sense, the pipeline is designed to make uncertainty visible.

## 3. Source and Corpus Scope

The source material is Tamil Virtual Academy/TamilVU Thevaram content. The current paper focuses on Thevaram books 1-8. The normalized resource contains the following table-level scope:

| Table | Count |
| --- | ---: |
| Thirumurai books | 8 |
| Paadal thogupugal | 841 |
| Paadalgal | 9012 |
| Commentaries | 9012 |
| Text spans | 64073 |

The full Thevaram 1-8 resource should be understood as a broad normalized corpus under active curation. Within it, Irandaam Thirumurai v1 is the strongest mature audited subset. That release contains 122 hymns and 1331 verse records, with zero schema violations, zero failed hymns, zero duplicate song numbers, zero missing verse text records, and 100% sampled coverage. This distinction is important: the broad 1-8 resource demonstrates scale and pipeline coverage, while the Irandaam Thirumurai subset demonstrates the highest current audit maturity.

## 4. Pipeline Overview

The pipeline follows an audit-first design:

1. Inspect source structures and identify page families.
2. Ingest Thevaram records into relational tables.
3. Normalize Tamil text while preserving line boundaries.
4. Recompute text spans after normalization.
5. Validate table quality and schema consistency.
6. Generate commentary coverage statistics.
7. Build downstream evidence layers such as entity mentions and paadal-pozhppurai links.
8. Produce reports suitable for corpus review and future release decisions.

The normalized tables are designed to be useful independently of a future chat system. They can support digital library search, corpus statistics, annotation workflows, and retrieval experiments. The structure also supports future RAG systems because every answer can be grounded in a corpus record and, where available, a source URL.

## 5. Data Model

The corpus is represented as relational JSONL tables. The most important tables are:

- `thirumurai_books`: book-level records for Thirumurai 1-8.
- `paadal_thogupugal`: hymn or grouping-level records.
- `paadalgal`: verse or song records containing paadal text and identifiers.
- `commentaries`: commentary records, including pozhppurai and kurippurai fields.
- `text_spans`: span records rebuilt against normalized text.

A paadal record includes identifiers such as `paadal_id`, `thirumurai_no`, `thogupu_id`, `global_song_no`, `local_song_no`, source parameters, source URL, commentary URL, normalized paadal text, and tokenized paadal forms. Commentary records are linked to paadal records and preserve separate commentary fields where available.

This structure is intentionally more conservative than a single "document text" field. The separation of verse and commentary allows future systems to answer different kinds of questions: "Where does this phrase occur in the poem?" differs from "How does the commentary explain this phrase?"

## 6. Normalization and Integrity Checks

Normalization uses version `thevaram-normalized-v1`. The raw and parsed source tables are not modified during normalization. Instead, normalized tables are written separately. Existing line boundaries are preserved because they identify poem and commentary structure. Normalization canonicalizes Unicode, removes unsafe invisible or control characters, collapses repeated spaces within lines, trims line edges, and recomputes span offsets against normalized text.

The normalization report records that paadal newline counts were preserved exactly: 39766 newline characters before normalization and 39766 after normalization. This is important because line breaks are not decoration in a poetic corpus; they are part of the structure users expect to retrieve and cite.

The normalized table quality report records no issue counts across the five main tables. The ingestion report also records no failures.

## 7. Corpus Statistics

Table 1 summarizes the per-book corpus size.

| Thirumurai | Paadal thogupugal | Paadalgal | Commentaries | Text spans | Paadal chars | Paadal lines |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 136 | 1469 | 1469 | 10371 | 257235 | 8039 |
| 2 | 122 | 1331 | 1331 | 10383 | 245120 | 7728 |
| 3 | 126 | 1358 | 1358 | 11837 | 244926 | 9161 |
| 4 | 113 | 1070 | 1070 | 6412 | 206320 | 4281 |
| 5 | 86 | 1015 | 1015 | 6078 | 137676 | 4058 |
| 6 | 99 | 981 | 981 | 9800 | 287525 | 7841 |
| 7 | 99 | 1006 | 1006 | 5756 | 220378 | 4234 |
| 8 | 60 | 782 | 782 | 3436 | 163254 | 3436 |
| **Total** | **841** | **9012** | **9012** | **64073** | **1762434** | **48778** |

The resource therefore provides a substantial basis for search and analysis across Thevaram 1-8. At the same time, the commentary fields show important variation by book. Table 2 summarizes commentary coverage.

| Thirumurai | Commentaries | Pozhppurai coverage | Kurippurai coverage |
| ---: | ---: | ---: | ---: |
| 1 | 1469 | 79.17% | 79.58% |
| 2 | 1331 | 99.70% | 99.77% |
| 3 | 1358 | 98.75% | 98.31% |
| 4 | 1070 | 99.81% | 99.35% |
| 5 | 1015 | 99.21% | 99.80% |
| 6 | 981 | 99.90% | 99.80% |
| 7 | 1006 | 57.95% | 93.34% |
| 8 | 782 | 0.00% | 0.00% |

These coverage numbers are not merely descriptive. They directly affect what downstream systems can claim. For example, Thirumurai 8 can support paadal-level retrieval from the normalized table, but it cannot currently support pozhppurai- or kurippurai-grounded answers from the normalized commentary fields. Thirumurai 7 also requires caution for pozhppurai-based analysis.

## 8. Downstream Evidence Layers

The corpus includes two important downstream layers: entity annotation and paadal-pozhppurai linking.

The entity annotation v3 layer contains 624 entity registry rows, 823 aliases, and 107761 entity mentions. The largest mention categories include nature, body parts, sacred objects, deities, theological concepts, temples, and weapons. Validation reports show zero invalid bounds, zero span text mismatches, and zero duplicate mention identifiers.

This layer is useful for retrieval and exploratory analysis, but it should not yet be treated as final expert-validated annotation. Some mentions are context-supported or marked for review. This distinction matters because literary interpretation requires more than surface-form matching.

The paadal-pozhppurai linker v4 layer contains 49019 span-level link records across 9012 paadalgal. The confidence distribution is intentionally diagnostic: 975 high-confidence links, 10316 medium-confidence links, 30859 low-confidence links, and 6869 no-link records. The most frequent low-confidence diagnostic group is `ambiguous_multiple_targets`, followed by medium-similarity cases, missing or unlinked cases, missing entity anchors, order-only weak matches, and low lexical overlap.

This result should not be read as a failed system. It is a useful finding about the difficulty of linking classical poetic language to explanatory prose. Low lexical overlap is expected when commentary explains rather than repeats a poem. The linker therefore functions as an evidence and review prioritization layer rather than a final gold alignment.

## 9. Resource Use Cases

The Thevaram 1-8 corpus supports several research and application scenarios:

- citation-aware Tamil literary search,
- verse and commentary retrieval,
- corpus statistics by book or grouping,
- entity-assisted search for deities, temples, sacred objects, and nature imagery,
- preparation of human annotation workflows,
- retrieval benchmarks for Tamil literary question answering,
- future RAG systems that cite source records rather than generating unsupported answers.

The corpus is especially useful because it preserves distinctions that ordinary scraping tends to erase. A future QA system can know whether evidence comes from a verse, a commentary field, a metadata field, an entity annotation, or an uncertain alignment layer.

## 10. Limitations

This resource has several limitations.

First, the full Thevaram 1-8 normalized corpus is not yet a fully expert-reviewed scholarly edition. Irandaam Thirumurai v1 is the most mature audited subset, while the broader 1-8 tables require continued review.

Second, commentary coverage varies substantially. Thirumurai 8 currently has no pozhppurai or kurippurai coverage in the normalized commentary table, and Thirumurai 7 has reduced pozhppurai coverage.

Third, deterministic entity annotation is not the same as literary interpretation. Mentions marked as context-only or ambiguous require human review before they are used for scholarly claims.

Fourth, paadal-pozhppurai linking remains a review-prioritization layer, not a gold alignment. Many links are low-confidence because poetic and explanatory prose often differ lexically.

Fifth, rights and access conditions must be handled carefully. The paper should provide clear attribution to TamilVU and should avoid representing the resource as an official mirror of TamilVU.

## 11. Ethical and Release Considerations

The project follows a controlled-scope approach rather than broad uncontrolled scraping. The design preserves source attribution and makes source gaps visible. Any public release should include a rights/access statement, corpus card, schema documentation, and reproducibility instructions. If full text redistribution is not appropriate, the resource can still provide code, schemas, derived statistics, metadata, checksums, and small review samples where permitted.

For digital library reviewers, the release model is as important as the extraction itself. A useful cultural heritage resource must be findable, reusable, documented, and honest about its limits.

## 12. Conclusion

This paper presented an audit-first pipeline for structuring Thevaram books 1-8 into a normalized, citation-grounded Tamil literary corpus resource. The current resource contains 8 books, 841 paadal thogupugal, 9012 paadalgal, 9012 commentary records, and 64073 text spans. It preserves source URLs, line boundaries, verse/commentary separation, normalized text, and downstream evidence layers for future retrieval and analysis.

The main contribution is not simply that text was extracted. The contribution is a corpus construction model for classical Tamil literature in which provenance, hierarchy, normalization, audit reports, and known gaps are first-class parts of the resource. This foundation is necessary before Tamil literary RAG, question answering, and computational literary analysis can be made trustworthy.

## References and Resource Notes

- Tamil Virtual Academy/TamilVU source material: https://www.tamilvu.org/
- JCDL 2026 Resource Track: https://2026.jcdl.org/call-for-resources/
- JCDL 2026 Key Dates: https://2026.jcdl.org/key-dates/
- Local evidence reports: `reports/thevaram-1-8-ingestion-report.md`, `reports/thevaram-normalization-report.md`, `reports/thevaram-normalized-table-quality-report.md`, `reports/thevaram-pozhppurai-link-v4-statistical-analysis.md`, `reports/thevaram-entity-annotation-v3-report.md`.
- Mature audited subset: `data/releases/irandaam-thirumurai-v1/`.

