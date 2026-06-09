# Retrieval Benchmark

This phase benchmarks deterministic lexical retrieval against the retrieval-ready corpus v1.1 and prepares the same interface for future semantic and hybrid retrieval.

It does not scrape, modify frozen corpus v1, modify enriched corpus v1.1, create embeddings, create a vector database, or build RAG.

## Purpose

The benchmark gives us a measurable lexical baseline before adding embeddings. It verifies that exact IDs, metadata filters, Tamil keyword lookup, citations, stable ranking, and golden-query expectations all work deterministically.

## Why Before Embeddings And RAG

Embeddings and RAG should improve retrieval, not hide basic failures. A lexical benchmark catches issues in IDs, citations, filters, query expectations, and ranking before semantic retrieval enters the system.

## Benchmark Inputs

- Enriched records: `data/processed/enriched/irandaam_thirumurai_enriched.jsonl`
- Chunks: `data/processed/chunks/irandaam_thirumurai_chunks.jsonl`
- Lexical index: `data/processed/indexes/irandaam_thirumurai_lexical_index.json`
- Golden queries: `data/processed/eval/golden_queries.jsonl`

## Golden Query Format

Each query includes:

- `query_id`
- `query_text`
- `query_type`
- `expected_record_ids`
- `expected_chunk_ids`
- `required_filters`
- `expected_min_results`
- `notes`

Expected IDs are derived from the actual v1.1 corpus.

## Retrieval Modes

- `lexical`: evaluated now using deterministic exact and keyword matching.
- `semantic`: `PENDING_EMBEDDINGS`.
- `hybrid`: `PENDING_EMBEDDINGS`.

## Evaluation Metrics

- queries evaluated
- queries skipped
- recall@1
- recall@3
- recall@5
- recall@10
- MRR
- exact_match@1
- expected minimum results satisfied
- failed query analysis
- missing expected record IDs
- missing expected chunk IDs

## Deterministic Ranking Rules

1. Exact record ID or chunk ID match.
2. Exact `song_no` match.
3. Exact `hymn_id` match.
4. Exact hymn title match.
5. Exact verse keyword match.
6. Exact `pozhppurai` keyword match.
7. Exact `kurippurai` keyword match.
8. Combined search text match.
9. Metadata text match.
10. Stable tie-break using `deterministic_rank_key`.

## Limitations

- Lexical matching is exact-token oriented and does not understand morphology.
- Semantic and hybrid comparisons are not meaningful until embeddings exist.
- Recall metrics use the golden query set, not exhaustive human relevance judgments.

## Future Semantic And Hybrid Comparison

The evaluator already supports `--mode semantic`, `--mode hybrid`, and `--mode all`. Semantic and hybrid modes currently return `PENDING_EMBEDDINGS`; once embedding artifacts exist, those modes can be filled in while keeping the same metrics and comparison report.
