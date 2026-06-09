# Retrieval-Ready Corpus Enrichment

This phase derives retrieval-ready artifacts from the frozen `Irandaam Thirumurai Corpus v1`.

It does not scrape, modify the frozen release, create embeddings, create a vector database, or build RAG.

## Purpose

The purpose is to make the corpus normalized, deterministic, chunked, filterable, citation-ready, and testable before any embedding or retrieval system is introduced.

## Why Before Embeddings

Embedding pipelines amplify whatever structure they receive. Before creating vectors, we need stable IDs, normalized text, deterministic chunks, lexical lookup, citations, and golden queries. This lets us test retrieval behavior with exact methods first and gives future semantic search a reliable baseline.

## v1 vs v1.1

- Extracted corpus `v1`: frozen source-derived verse/commentary records.
- Retrieval-ready corpus `v1.1`: derived records with normalized fields, stable retrieval IDs, citation fields, chunks, lexical metadata, lexical index, and golden queries.

The `v1.1` artifacts are derived from `v1`; they do not replace or mutate it.

## Deterministic Retrieval Principles

1. Apply metadata filters first.
2. Exact `song_no` or `hymn_id` match.
3. Exact title/hymn term match.
4. Exact keyword match in verse.
5. Exact keyword match in `pozhppurai`.
6. Exact keyword match in `kurippurai`.
7. Combined `search_text` match.
8. Use semantic/vector search later only if lexical retrieval is insufficient.
9. Fixed reranking order: exact identifier, exact title, exact verse, exact commentary, combined text, semantic score later.
10. Return fixed top-k with stable tie-breaking using `deterministic_rank_key`.

## Normalization Strategy

- Unicode NFC normalization.
- Conservative whitespace normalization.
- Repeated blank lines removed.
- Line breaks normalized.
- Tamil words and meaningful punctuation preserved.
- Commentary labels removed only when they appear as extracted prose labels.
- No translation, stemming, or literary rewriting.

## Stable ID Strategy

IDs are derived from stable corpus identifiers:

- `record_id = thevaram_02_{hymn_id}_{song_no}`
- `verse_id = thevaram_02_{hymn_id}_{song_no}_verse`
- `canonical_id = tvu_thevaram_irandaam_thirumurai_{hymn_id}_{song_no}`

Row numbers are not used as primary IDs.

## Chunking Strategy

Each record produces deterministic chunks:

- `verse_only`
- `pozhppurai_only`, only when available
- `kurippurai_only`, only when available
- `verse_plus_commentary`
- `metadata_context`

The main future RAG chunk is `verse_plus_commentary`, but lexical evaluation can inspect each chunk type independently.

## Lexical Search Strategy

The lexical index maps:

- term to record IDs
- term to chunk IDs
- hymn ID to record IDs
- song number to record ID
- author to record IDs
- pann to record IDs
- hymn title terms to record IDs
- partial commentary record IDs

The tokenizer is deterministic and simple: split on whitespace and punctuation, preserve Tamil words, remove empty tokens, and avoid external ML models.

## Citation Strategy

Every record and chunk includes citation fields:

- source name
- collection
- thirumurai
- author
- hymn title
- hymn ID
- song number
- hymn URL
- commentary URL

Citation string:

`திருஞானசம்பந்தர், இரண்டாம் திருமுறை, {hymn_title}, பாடல் {song_no}, TamilVU.`

## Golden Query Strategy

Golden queries are derived from actual corpus records. They cover:

- exact lookups
- metadata filters
- keyword queries
- commentary availability queries
- mixed author/title/thirumurai queries
- deterministic manual spot checks

These queries validate the lexical baseline before embeddings.

## Limitations

- This phase does not judge semantic answer quality.
- This phase does not tokenize with a Tamil morphological analyzer.
- This phase does not build BM25 scores or embeddings.
- Partial commentary fields remain partial; no missing text is fabricated.
