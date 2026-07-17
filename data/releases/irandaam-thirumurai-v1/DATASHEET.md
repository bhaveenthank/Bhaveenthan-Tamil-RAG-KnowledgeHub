# Datasheet: Irandaam Thirumurai Corpus v1

## Motivation

This release supports citation-grounded Tamil literary research, retrieval, and
future question-answering systems. It converts Tamil Virtual Academy/TamilVU
Irandaam Thirumurai pages into structured JSONL records while preserving source
URLs, verse text, commentary fields, and audit evidence.

## Creators

- Bhaveenthan Kajanikanth, University of Peradeniya, `e22051@eng.pdn.ac.lk`
- Prof. Uthayasanker Thayasivam, University of Moratuwa, `rtuthaya@cse.mrt.ac.lk`

## Source

- Source institution: Tamil Virtual Academy / TamilVU
- Source site: `https://www.tamilvu.org/`
- Navigation source: `https://www.tamilvu.org/slet/l4120/l4120lft.jsp`
- Scope: Irandaam Thirumurai only

Every corpus record includes a `hymn_url` and `commentary_url` when available.

## Composition

- Corpus: `Irandaam Thirumurai Corpus`
- Version: `v1`
- Schema: `irandaam-thirumurai-jsonl-v0.1`
- Records: `1331`
- Hymns: `122`
- Successful records: `1324`
- Partial commentary records: `7`
- Missing verse text records: `0`
- Duplicate song numbers: `0`
- Schema violations: `0`

Primary files:

- `irandaam_thirumurai.jsonl`: one `verse_with_commentary` record per verse/song.
- `schema.json`: JSON Schema for release records.
- `corpus_manifest.json`: release-level metadata.
- `corpus_checksum.sha256`: SHA-256 checksums for release integrity.
- `corpus-audit-report.md`: audit summary.
- `corpus-coverage-report.md`: coverage evidence.
- `manual-audit-sample.md`: manually inspected samples.

## Collection And Processing

The builder discovered strict Irandaam Thirumurai hymn links from the TamilVU
left-frame navigation endpoint, fetched hymn pages and commentary pages, parsed
verse and commentary fields, and wrote one normalized JSONL record per verse.
Raw snapshots are stored outside the public release package to avoid repeatedly
fetching the source site and to keep the public release compact.

## Recommended Uses

- Tamil literary search and citation experiments.
- Verse/commentary retrieval experiments.
- Corpus statistics and quality-audit studies.
- Educational tools with clear TamilVU attribution.
- Future RAG pipelines that preserve source URLs.

## Out-of-Scope Uses

- Do not present this as an official TamilVU mirror.
- Do not remove TamilVU source attribution.
- Do not fabricate or infer missing commentary fields.
- Do not treat this as a complete Thevaram or TamilVU corpus.
- Do not make high-stakes historical, religious, or scholarly claims without
  human expert review.

## Rights And Access

See `RIGHTS_AND_ACCESS.md`. The project software and release metadata are open
under the repository license. TamilVU-derived source text may be subject to
separate rights, so users should preserve attribution and verify permitted reuse
for their own jurisdiction and use case.

## Maintenance

Corrections should be released as a new version rather than editing v1 files in
place. Future versions may add richer metadata, stronger commentary coverage,
and expert-reviewed annotations.

## AI-Use Statement

AI tools, including OpenAI Codex/ChatGPT, were used to assist with repository
documentation, code and script drafting, validation planning, analysis summaries,
and manuscript drafting. The named authors remain responsible for checking all
code, corpus records, statistics, claims, and release decisions before
publication or submission.

