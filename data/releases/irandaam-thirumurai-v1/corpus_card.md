# Corpus Card: Irandaam Thirumurai Corpus v1

## Purpose

This corpus preserves structured Tamil devotional poetry and commentary records for Irandaam Thirumurai, supporting future Tamil literary research, corpus analysis, citation-aware search, and educational applications.

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

## Version

- Release: `v1`
- Schema: `irandaam-thirumurai-jsonl-v0.1`
- Record count: `1331`
- Hymn count: `122`
