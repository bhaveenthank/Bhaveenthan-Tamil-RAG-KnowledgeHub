# Hybrid Retrieval

This phase implements and benchmarks local hybrid retrieval for the Irandaam Thirumurai corpus. It does not scrape, modify corpus files, regenerate embeddings, rebuild the vector index, use cloud services, create a managed vector database, or build RAG.

## Why Hybrid Retrieval Is Needed

Lexical retrieval is excellent for exact matches: `song_no`, `hymn_id`, record IDs, hymn titles, `pann`, and Tamil phrases that occur directly in the corpus.

Semantic retrieval can help when a query expresses a concept rather than the exact corpus wording. It is useful as a recall layer, especially when users ask about meaning, imagery, or interpretive themes.

The current semantic benchmark underperformed lexical retrieval because the golden query set is deliberately exact and provenance-heavy. Many queries expect precise records, source IDs, metadata filters, or specific Tamil terms. A general multilingual embedding model is not guaranteed to preserve those exact distinctions for classical Tamil.

Hybrid retrieval combines both strengths:

- lexical precision for exact corpus references
- semantic recall for related concepts
- deterministic ranking for reproducible benchmarking

## Combination Strategy

The hybrid retriever calls:

- `LexicalRetriever`
- `SemanticRetriever`

It requests a larger candidate set from both, merges candidates by record ID, and preserves the best available chunk/source metadata. If a candidate appears in both modes, it is marked as `both`; otherwise it is marked as `lexical` or `semantic`.

Every result includes:

- rank
- hybrid score
- record ID
- parent record ID
- chunk ID
- chunk type
- matched modes
- matched fields
- lexical score
- semantic score
- normalized lexical score
- normalized semantic score
- boosts
- citation text
- source URLs
- deterministic rank key

## Scoring

Default weights:

```text
lexical_weight = 0.65
semantic_weight = 0.35
```

Formula:

```text
hybrid_score =
  lexical_weight * normalized_lexical_score
  + semantic_weight * normalized_semantic_score
  + exact_match_boost
  + metadata_filter_boost
```

Boosts are applied for:

- exact `song_no`
- exact `hymn_id`
- exact `record_id`
- exact `chunk_id`
- exact hymn title
- query terms found in verse text
- query terms found in `பொழிப்புரை`
- query terms found in `குறிப்புரை`
- metadata filter matches

Tie-break order:

1. hybrid score descending
2. deterministic rank key ascending
3. record ID ascending
4. chunk ID ascending

## Ablations

The evaluator runs fixed ablations for the hybrid report:

| Setting | Lexical | Semantic |
| --- | ---: | ---: |
| lexical-heavy | 0.80 | 0.20 |
| balanced | 0.50 | 0.50 |
| semantic-heavy | 0.30 | 0.70 |

Custom weights are supported:

```bash
python3 src/evaluation/evaluate_retrieval.py --mode hybrid --lexical-weight 0.65 --semantic-weight 0.35
```

## Limitations

Hybrid retrieval cannot fix all semantic-model limitations. Classical Tamil morphology, devotional terms, poetic compression, and commentary style can still confuse general multilingual embeddings.

The current golden queries are exact-match heavy, so a successful hybrid system should at least match lexical retrieval on those queries. If it does not, lexical retrieval should remain the precision baseline and semantic retrieval should be used as a secondary expansion layer.

## RAG Implication

Hybrid retrieval is the most likely retrieval mode for future RAG, but only after benchmark review. A good RAG retriever should:

- preserve exact citation behavior
- retrieve the expected verse/commentary record
- use semantic expansion without displacing precise lexical hits
- expose enough metadata for source-grounded Tamil answers

This phase benchmarks retrieval only. It does not generate answers.

