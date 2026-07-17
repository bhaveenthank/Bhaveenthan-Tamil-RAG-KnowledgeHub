# JCDL 2026 Resource Paper Strategy

## Core Positioning

Submit the work as a **full public GitHub resource** for Tamil digital-library
research:

> Tamil literary works are visible on the web, but they are not automatically
> reusable research corpora. This resource turns TamilVU Thevaram pages into a
> structured, provenance-preserving, auditable corpus resource for citation-
> grounded search, analysis, annotation, and future Tamil literary QA.

Recommended title:

**An Audit-First Public Corpus Resource for Thevaram 1-8**

The paper should not be framed as a scraper paper. The strong claim is the
resource design:

- public GitHub repository available without login;
- normalized Thevaram 1-8 JSONL tables;
- schema and checksums;
- corpus card and datasheet;
- source URLs and source parameters;
- poem/commentary separation;
- Irandaam Thirumurai as the strongest audited subset;
- entity and commentary-linking layers marked as experimental evidence, not gold
  annotation.

## Reviewer View

### Novelty

The novelty is not simply that Tamil text was collected. The contribution is an
audit-first corpus model for classical Tamil literature: literary hierarchy,
source provenance, Unicode normalization, verse/commentary boundaries, table
quality checks, release documentation, and derived evidence layers.

### Availability

The public GitHub repository is enough for the JCDL requirement because the call
allows stable public repositories such as GitHub, Zenodo, or institutional
repositories. Zenodo can be created later, but it is not mandatory for
submission.

The paper should point to:

`https://github.com/bhaveenthank/Bhaveenthan-Tamil-RAG-KnowledgeHub`

### Utility

Make reuse concrete. Mention:

- JSONL tables for books, groups, poems, commentaries, and spans;
- `schema.json`;
- checksum file;
- `README`, `DATASHEET.md`, `corpus_card.md`, `RIGHTS_AND_ACCESS.md`,
  `USAGE.md`;
- command-line examples;
- existing tests and validation reports.

### Impact

The resource enables:

- Tamil literary search with citations;
- comparative corpus analysis across Thirumurai books;
- commentary-aware retrieval;
- annotation review workflows for entities, places, deities, imagery, and
  concepts;
- future retrieval-augmented Tamil literary question answering.

## Required Honesty

Be explicit about limitations. This will make the paper stronger, not weaker.

Use:

> Thevaram 1-8 is the full public corpus resource. Irandaam Thirumurai v1 is the
> most mature audited subset. Entity annotation and paadal-pozhppurai linking are
> experimental evidence layers.

Avoid:

- "complete TamilVU corpus";
- "official TamilVU mirror";
- "gold-standard annotations";
- "expert-verified every record";
- "solved Tamil literary QA";
- "full open redistribution license for TamilVU text."

## Paper Structure

1. **Problem:** web access is not enough for reusable corpus research.
2. **Resource:** public GitHub resource for Thevaram 1-8.
3. **Design:** source-linked relational JSONL tables with strict separation of
   poem text, commentary, metadata, and spans.
4. **Documentation:** schema, datasheet, corpus card, checksums, rights/access,
   usage examples.
5. **Evidence:** corpus counts, commentary coverage, Irandaam audited subset,
   entity layer, commentary-linking layer.
6. **Limitations:** rights, uneven commentary, experimental layers, no claim of
   official status.
7. **Impact:** citation-grounded Tamil literary search, digital humanities, and
   future QA.

## Best Reviewer-Safe Claim

> We contribute a public, documented, and reproducible Thevaram 1-8 corpus
> resource that makes Tamil literary text reusable for computational research
> while preserving provenance, literary hierarchy, and uncertainty.

## Submission Checklist

- Public GitHub repository works without login.
- Top-level `README.md` explains setup, reuse, limits, and AI use.
- `LICENSE` explains MIT project material and separate source-text rights.
- `data/releases/thevaram-1-8-v1/` contains corpus card, datasheet, schema,
  checksums, usage, and rights/access files.
- Paper is 2-4 pages excluding references in ACM `sigconf`.
- Paper uses author names because JCDL Resources is single-blind.
- AI-use statement is included because AI assisted research code, validation
  planning, analysis summaries, and drafting.
- DOI language is removed or marked optional.

