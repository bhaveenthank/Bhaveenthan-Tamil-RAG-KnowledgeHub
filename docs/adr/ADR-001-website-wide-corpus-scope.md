# ADR-001: Website-Wide Tamil Corpus Scope

## Status

Accepted

## Context

The project began with a carefully inspected and audited Irandaam Thirumurai corpus, followed by a bounded Fourth Thirumurai pilot. The evaluation taxonomy showed that the target users need broader literary, lexical, grammatical, historical, comparative, and reference capabilities. TamilVU exposes many categories beyond Thirumurai.

A Thirumurai-only architecture would overfit record structure, metadata, parsers, and retrieval behavior to devotional verse.

## Decision

Expand the architectural scope to a website-wide Tamil Literary KnowledgeHub.

The system will use:

- a website category registry;
- a future book/work registry;
- category-specific parser families;
- immutable raw snapshots;
- unified website corpus schema v2;
- source-family validation and coverage audits;
- separate retrieval and exhaustive analysis layers.

Thirumurai remains a first-class `collection_family` and the project's most mature corpus, not the boundary of the product.

## Consequences

- One universal HTML parser is explicitly rejected.
- Book discovery, content ingestion, normalization, retrieval, and analysis become separate stages.
- Parser-family pilots are required before category-wide extraction.
- Rights and format availability must be tracked per book.
- Manuscript/image categories require metadata-first handling and separately approved OCR.
- Cross-category search will require record-type-aware chunking and ranking.
- Corpus-wide analysis must respect category, work, record type, and completeness.

## Not Done Immediately

- No website-wide scrape.
- No new category ingestion.
- No OCR, PDF processing, cloud deployment, embedding regeneration, vector-index rebuild, or answer generation.
- No migration or mutation of frozen Thirumurai artifacts.
- No external-library crawling.

## Preservation Of Existing Work

- `thirumurai_02` remains `available`.
- `thirumurai_04` remains `available` and `pilot_verified`, explicitly incomplete.
- Existing source URLs, IDs, releases, reports, retrieval artifacts, and tests remain valid.
- The Thirumurai registry receives only `collection_family = "thirumurai"` to place it under the wider architecture.
