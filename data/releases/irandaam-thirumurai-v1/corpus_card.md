# Corpus Card: Irandaam Thirumurai Corpus v1

## Purpose

This corpus preserves structured Tamil devotional poetry and commentary records for Irandaam Thirumurai, supporting future Tamil literary research, corpus analysis, citation-aware search, and educational applications.

## Creators

- Bhaveenthan Kajanikanth, University of Peradeniya, `e22051@eng.pdn.ac.lk`
- Prof. Uthayasanker Thayasivam, University of Moratuwa, `rtuthaya@cse.mrt.ac.lk`

## Source

- Source: Tamil Virtual Academy / TamilVU
- Source site: `https://www.tamilvu.org/`
- Navigation source: `https://www.tamilvu.org/slet/l4120/l4120lft.jsp`
- Scope: Irandaam Thirumurai only

Each record includes source provenance through `hymn_url` and `commentary_url`.

## Schema

The corpus is JSONL with one `verse_with_commentary` record per verse/song.

Primary identifiers:

- `hymn_id`
- `song_no`
- `hymn_url`
- `commentary_url`

Text fields:

- `verse_text`
- `pozhppurai`
- `kurippurai`

Metadata fields include collection, work, thirumurai, author, pann, source parameters, text statistics, and extraction metadata.

See `schema.json` for the release schema.

## Limitations

- Seven records have partial commentary because the source HTML appears to omit one commentary section.
- The corpus is not a complete TamilVU corpus.
- The corpus is not a translation dataset.
- The corpus has not yet been manually verified record-by-record by Tamil literary experts.
- This release does not include embeddings, vector indexes, or RAG chunks.

## Recommended Uses

- Tamil literary research support
- Thevaram/Thirumurai corpus analysis
- Tamil text normalization experiments
- Citation-aware retrieval experiments after separate indexing design
- Educational tools with clear TamilVU source attribution

## Prohibited Uses

- Do not present the corpus as a complete or official TamilVU mirror.
- Do not remove source attribution.
- Do not fabricate missing commentary sections.
- Do not use the corpus to make unsupported religious, historical, or scholarly claims without human review.
- Do not use this release as a substitute for expert Tamil scholarship where precision matters.

## Rights And Access

Project software, schemas, scripts, and original documentation are released under the repository license. TamilVU-derived source text may be subject to separate rights. Preserve TamilVU attribution and source URLs. If full-text redistribution permission is not confirmed before DOI publication, publish either a restricted-file Zenodo record or an open metadata/schema/checksum/sample package.

See `RIGHTS_AND_ACCESS.md`.

## AI-Use Statement

AI tools, including OpenAI Codex/ChatGPT, were used to assist with repository documentation, code and script drafting, validation planning, analysis summaries, and manuscript drafting. The named authors remain responsible for checking all code, corpus records, statistics, claims, and release decisions before publication or submission.

## Version

- Release: `v1`
- Schema: `irandaam-thirumurai-jsonl-v0.1`
- Record count: `1331`
- Hymn count: `122`
