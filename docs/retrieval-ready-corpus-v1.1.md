# Retrieval-Ready Corpus v1.1

## Source Corpus Version

- Source corpus: `Irandaam Thirumurai Corpus v1`
- Source file: `data/releases/irandaam-thirumurai-v1/irandaam_thirumurai.jsonl`
- Source records: `1331`
- Source hymns: `122`

## Enriched Corpus Version

- Enriched version: `irandaam-thirumurai-v1.1`
- Schema version: `retrieval-ready-irandaam-thirumurai-v1.1`
- Recommendation: `RETRIEVAL_READY`

## Generated Files

- `data/processed/enriched/irandaam_thirumurai_enriched.jsonl`
- `data/processed/chunks/irandaam_thirumurai_chunks.jsonl`
- `data/processed/indexes/irandaam_thirumurai_lexical_index.json`
- `data/processed/eval/golden_queries.jsonl`
- `reports/retrieval-readiness-report.md`

## Schema Changes

The enriched records preserve the original corpus fields and add:

- normalized text fields
- deterministic IDs
- retrieval search fields
- citation fields
- filter metadata
- lexical token fields
- deterministic rank keys

## Record Counts

- Enriched records: `1331`
- Partial commentary records: `7`
- Missing commentary indexed records: `7`

## Chunk Counts

- Total chunks: `6648`
- `verse_only`: `1331`
- `verse_plus_commentary`: `1331`
- `metadata_context`: `1331`
- `pozhppurai_only`: `1327`
- `kurippurai_only`: `1328`

## Lexical Index Summary

- Record terms: `38241`
- Chunk terms: `38241`
- Indexed hymn IDs: `122`
- Indexed song numbers: `1331`
- Partial commentary record IDs: `7`

## Golden Query Set Summary

- Golden queries: `42`
- Query families: exact lookup, metadata, keyword, commentary, mixed, manual spot check
- Expected IDs are derived from the actual enriched corpus.

## Validation Results

- Enriched record count equals source record count.
- Record IDs are unique.
- Chunk IDs are unique.
- Every record has `verse_only`, `verse_plus_commentary`, and `metadata_context` chunks.
- Commentary-only chunks are created only when that commentary field exists.
- Citation fields exist for every record and chunk.
- Lexical index contains known lookup terms and metadata mappings.
- Golden queries have expected records.
- Validation result: `True`

## Known Limitations

- No embeddings or vector index are created.
- Tokenization is deterministic and simple, not morphological.
- Seven source-missing commentary fields remain empty and are explicitly indexed.
- The enriched corpus is scoped only to Irandaam Thirumurai.

## Recommended Next Step

Run deterministic lexical retrieval evaluation against `golden_queries.jsonl` before designing embeddings or RAG.
