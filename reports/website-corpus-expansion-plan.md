# Website Corpus Expansion Plan

## Principles

- Expand by parser diversity, not by category count.
- Inspect before ingesting.
- Use allowlisted books and bounded record limits.
- Freeze and audit successful corpora before indexing.
- Record rights and format availability per book.
- Keep OCR, external websites, embeddings, and answer generation as separate approvals.

## Stage 1: Proven Foundation

Completed:

- Irandaam Thirumurai: full frozen and retrieval-ready corpus.
- Fourth Thirumurai: five-hymn Appar pilot, normalized and `pilot_verified`.
- Verse/commentary SLET parser family, citation pipeline, retrieval benchmark, and readiness audits.

These artifacts remain the `thirumurai` collection family under the website-wide architecture.

## Stage 2: Representative Category Pilots

Select four to six allowlisted books after source inspection:

| Pilot Type | Recommended Category | Purpose |
| --- | --- | --- |
| Devotional verse | சைவம் or வைணவம் | Confirm another verse hierarchy without expanding all Thirumurai. |
| Classical poetry | சங்க இலக்கியம் | Test poem, poet, anthology, thinai, and commentary metadata. |
| Prose | இருபதாம் நூற்றாண்டு இலக்கியங்கள் உரைநடைகள் | Test chapter, section, paragraph, page, footnote, and rights fields. |
| Grammar | இலக்கணம் | Test sutra/rule, explanation, example, and commentator boundaries. |
| Dictionary / Nigandu | அகராதிகள், then நிகண்டுகள் | Test headword/sense parsing and prepare future synonym authority. |
| Optional encyclopedia/culture | கலைக்களஞ்சியங்கள் or பண்பாட்டுக் காட்சியகம் | Test article/media metadata without OCR-first scope. |

Selection criteria:

- static or clearly discoverable endpoints;
- small bounded work;
- useful metadata;
- text availability without mandatory OCR;
- source terms and rights notes reviewed;
- category adds a parser type not already proven.

## Stage 3: Category-Specific Pilot Parsers

For each selected book:

1. document navigation and page families;
2. save a small raw allowlist;
3. define native hierarchy and schema-v2 mapping;
4. create fixtures and parser tests;
5. ingest a bounded sample;
6. validate source URLs, IDs, Tamil text, hierarchy, and coverage;
7. produce a readiness report;
8. decide `pilot_verified`, repair, or defer.

Shared fetch, snapshot, provenance, reporting, and validation utilities should be reused. Content parsing remains source-family specific.

## Stage 4: Approved Category Expansion

Full category scraping happens only when:

- representative first/middle/last samples pass;
- parser variants are understood;
- rights and crawl policy are recorded;
- request count and disk estimate are approved;
- resume and immutable raw storage work;
- validation and audit thresholds are met;
- failures remain visible per book.

Expansion should proceed book by book, not as one website-recursive job.

## Deferred Tracks

- manuscript/image OCR;
- large PDF extraction;
- external-library crawling;
- cloud execution;
- embeddings/indexes for new categories;
- website-wide RAG answer generation.

These tracks depend on validated source records and separate cost, policy, and quality decisions.
