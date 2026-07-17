# Corpus Card: Thevaram 1-8 Corpus Resource

## Summary

The Thevaram 1-8 Corpus Resource is a provenance-preserving Tamil literary
corpus resource derived from Tamil Virtual Academy/TamilVU source pages. It
provides normalized JSONL tables for books, hymn groups, poems, commentary
records, and text spans. The resource is designed for citation-grounded Tamil
literary retrieval, corpus analysis, and future digital-library research.

## Resource Layers

| Layer | Status | Purpose |
| --- | --- | --- |
| Thevaram 1-8 normalized tables | Public GitHub resource | Broad structured corpus coverage |
| Irandaam Thirumurai v1 | Audited subset | Strongest frozen release package |
| Entity annotations v3 | Experimental evidence layer | Retrieval and review support |
| Paadal-pozhppurai links v5 | Experimental evidence layer | Commentary alignment diagnostics |

## Main Counts

| Item | Count |
| --- | ---: |
| Thirumurai books | 8 |
| Paadal thogupugal | 841 |
| Paadalgal | 9012 |
| Commentary records | 9012 |
| Text spans | 64073 |

## Strengths

- Preserves source URLs and source parameters.
- Separates poem text from commentary fields.
- Preserves Tamil line boundaries.
- Provides schema, checksums, corpus documentation, and reuse commands.
- Separates audited release data from experimental evidence layers.

## Limitations

The resource should not be described as a complete expert-reviewed scholarly
edition. Commentary coverage differs by book. The entity and commentary-linking
outputs are useful for review workflows but are not gold annotations.

## Rights

Project software, schemas, scripts, and original documentation are MIT licensed.
TamilVU-derived source text is attributed to Tamil Virtual Academy/TamilVU and
may be subject to separate rights. See `RIGHTS_AND_ACCESS.md`.

