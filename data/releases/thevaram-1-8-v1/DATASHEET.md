# Datasheet: Thevaram 1-8 Corpus Resource

## Motivation

This resource supports citation-grounded Tamil literary research by transforming
TamilVU Thevaram pages into structured, source-linked, reusable corpus tables.
The goal is not only to extract text, but to preserve literary hierarchy,
source URLs, poem/commentary boundaries, and known quality limits.

## Creators

- Bhaveenthan Kajanikanth, University of Peradeniya, e22051@eng.pdn.ac.lk
- Uthayasanker Thayasivam, University of Moratuwa, rtuthaya@cse.mrt.ac.lk

## Composition

- Source collection: Tamil Virtual Academy/TamilVU Thevaram pages.
- Scope: Thevaram books 1-8.
- Language: Tamil.
- Main format: JSONL relational tables.
- Thirumurai books: 8.
- Paadal thogupugal: 841.
- Paadalgal: 9012.
- Commentary records: 9012.
- Text spans: 64073.

The main tables are:

- `thirumurai_books.jsonl`
- `paadal_thogupugal.jsonl`
- `paadalgal.jsonl`
- `commentaries.jsonl`
- `text_spans.jsonl`

## Collection And Processing

The pipeline used allowlisted TamilVU Thevaram sources. The extracted records
were normalized using NFC Unicode normalization, unsafe control-character
removal, repeated-space cleanup, line-edge trimming, and span offset rebuilding.
Line boundaries in poem text were preserved.

Raw extraction, normalized tables, release reports, and experimental evidence
layers are kept separate.

## Recommended Uses

- Tamil literary corpus analysis.
- Citation-aware search and retrieval.
- Digital humanities teaching and exploration.
- Annotation task creation for deities, places, imagery, and commentary links.
- Evaluation of retrieval over poem-plus-commentary material.

## Non-Recommended Uses

- Do not treat this as an official TamilVU release.
- Do not treat the entity and paadal-pozhppurai layers as expert gold labels.
- Do not make claims about complete commentary coverage without checking the
  coverage tables.
- Do not redistribute TamilVU-derived source text without checking rights.

## Known Limitations

- Irandaam Thirumurai is the most mature audited subset.
- Thevaram 1-8 is broader normalized coverage under active curation.
- Commentary coverage is uneven. Book 8 currently has poem-level coverage but
  no pozhppurai or kurippurai coverage in the normalized commentary table.
- Entity and commentary-linking outputs are deterministic review aids, not final
  expert scholarly annotation.

## AI-Use Statement

AI tools, including OpenAI Codex/ChatGPT, were used to assist with repository
documentation, code/script drafting, validation planning, analysis summaries,
and manuscript drafting. The named authors remain responsible for checking all
code, corpus records, statistics, rights statements, and paper claims.

