# Retrieval Readiness Report

## Input Corpus Summary

- Source corpus: `irandaam-thirumurai-v1`
- Input: `data/releases/irandaam-thirumurai-v1/irandaam_thirumurai.jsonl`

## Enriched Corpus Summary

- Enriched records: `1331`
- Enriched version: `irandaam-thirumurai-v1.1`
- Schema version: `retrieval-ready-irandaam-thirumurai-v1.1`

## Normalization Summary

- Unicode normalized with NFC.
- Repeated whitespace and blank lines collapsed conservatively.
- Tamil words, punctuation meaning, and line-level verse content are preserved.
- Commentary labels are removed only when they appear as extracted prose labels.

## Chunk Counts

- `kurippurai_only`: `1328`
- `metadata_context`: `1331`
- `pozhppurai_only`: `1327`
- `verse_only`: `1331`
- `verse_plus_commentary`: `1331`

## Lexical Index Statistics

- Record terms: `38241`
- Chunk terms: `38241`
- Partial commentary record IDs: `7`

## Golden Query Statistics

- Golden queries: `42`

## Validation Results

- Validation OK: `True`

## Missing/Partial Commentary Handling

- Missing commentary fields are preserved as empty normalized strings.
- `partial_commentary` records are indexed in `partial_commentary_record_ids`.
- No missing commentary prose is fabricated.

## Deterministic Retrieval Design

Rule-based retrieval order:

1. Apply metadata filters first.
2. Exact `song_no` or `hymn_id` match.
3. Exact title/hymn term match.
4. Exact keyword match in verse.
5. Exact keyword match in `pozhppurai`.
6. Exact keyword match in `kurippurai`.
7. Combined `search_text` match.
8. Semantic/vector search later only if lexical retrieval is insufficient.
9. Fixed reranking order: exact identifier, exact title, exact verse, exact commentary, combined text, semantic score later.
10. Return fixed top-k with stable tie-breaking using `deterministic_rank_key`.

## Files Generated

- `enriched`: `data/processed/enriched/irandaam_thirumurai_enriched.jsonl`
- `chunks`: `data/processed/chunks/irandaam_thirumurai_chunks.jsonl`
- `lexical_index`: `data/processed/indexes/irandaam_thirumurai_lexical_index.json`
- `golden_queries`: `data/processed/eval/golden_queries.jsonl`
- `report`: `reports/retrieval-readiness-report.md`

## Readiness Recommendation

`RETRIEVAL_READY`