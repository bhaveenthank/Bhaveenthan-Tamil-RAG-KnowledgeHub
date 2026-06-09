# Retrieval Error Analysis

This phase diagnoses the existing semantic and hybrid retrieval benchmark results. It does not scrape, modify corpus releases, rebuild retrieval-ready data, regenerate embeddings, rebuild the vector index, use cloud services, or build RAG.

## Purpose

Aggregate retrieval metrics tell us whether a retriever performs well, but not why it fails. Error analysis turns failed queries into evidence for routing, ranking, chunking, and evaluation decisions.

This is especially important before RAG. A generation model cannot reliably repair a retrieval failure: if the expected verse or commentary never reaches the answer context, the final response may be incomplete, incorrectly attributed, or confidently wrong.

## Why Semantic Retrieval Underperformed

The current golden query set contains many exact and provenance-heavy tasks:

- song numbers
- hymn IDs
- record IDs
- hymn and place names
- literal Tamil keywords
- commentary availability or missing-field predicates
- metadata filters

The multilingual sentence-transformer model represents broad textual similarity. It is not an exact identifier index, a metadata database, or a classical Tamil morphological analyzer.

The semantic index also contains only `verse_plus_commentary` chunks. It does not directly encode the absence of `பொழிப்புரை` or `குறிப்புரை`, and it does not separately index metadata-only chunks. Therefore semantic similarity alone is not expected to match lexical retrieval on all current golden queries.

## Methodology

The diagnostic script reads existing artifacts only:

```text
data/processed/eval/retrieval_benchmark_results.json
data/processed/eval/golden_queries.jsonl
data/processed/indexes/irandaam_thirumurai_lexical_index.json
```

For each semantic query it:

1. Determines pass or failure from the saved benchmark.
2. Compares expected record and chunk IDs with the top retrieved results.
3. Records ranks and similarity scores.
4. Assigns a deterministic failure category and confidence.
5. Looks up literal-term document frequency in the lexical index.
6. Locates the matching hybrid query result.
7. Records whether hybrid rescued the failure.
8. Attributes the correction to lexical score, semantic score, exact boosts, metadata boosts, and matched fields.

No model inference or retrieval rerun is required.

## Failure Categories

### Exact Identifier Mismatch

The query depends on an exact record ID, chunk ID, hymn ID, or song number. Vector similarity is not a safe identifier lookup.

### Hymn/Song Reference Mismatch

The query names a hymn, location, title, or song reference, but semantic ranking selects a conceptually adjacent record.

### Rare Term Mismatch

The query depends on an exact Tamil term with low corpus document frequency. The multilingual embedding may not represent it strongly enough.

### Classical Tamil Phrase Mismatch

The query requires literal classical Tamil wording. Morphology, sandhi, orthography, or devotional vocabulary may weaken embedding similarity.

### Metadata Mismatch

The query targets author, `pann`, extraction status, commentary availability, or missing-field state. These are structured predicates rather than semantic text meanings.

### Chunking Limitation

The expected evidence belongs to a chunk type not indexed by the semantic retriever.

### Embedding Limitation

The query is text-oriented, but the expected record still falls outside the top semantic results.

### Unknown

The available evidence is insufficient for a stronger automatic classification.

## Confidence Scores

Confidence scores indicate how strongly the deterministic rule matches observable query structure. They do not measure statistical probability and do not describe the embedding model's internal reasoning.

Examples:

- exact identifier query: high confidence
- explicit metadata or missing-field query: high confidence
- Tamil keyword with known lexical document frequency: medium-to-high confidence
- general fallback: lower confidence

## Outputs

```text
data/processed/eval/retrieval_failure_analysis.json
reports/retrieval-error-analysis-report.md
```

The JSON contains query-level evidence. The report summarizes category distribution, score and rank distributions, hybrid recoveries, major findings, and recommendations for future retrieval routing.

## Command

```bash
python3 src/evaluation/analyze_retrieval_failures.py
```

