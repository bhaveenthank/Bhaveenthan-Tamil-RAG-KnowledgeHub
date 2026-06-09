# Vector Index and Semantic Retrieval

This phase builds a local vector search index from the already generated Irandaam Thirumurai embedding artifacts and evaluates semantic retrieval against the existing golden query set.

It does not scrape TamilVU, modify frozen corpus v1, modify retrieval-ready corpus v1.1, regenerate embeddings, use GCP, create a managed vector database, or build RAG.

## Why a Vector Index Is Needed

The embedding artifact stores one vector per embedded chunk. A vector index makes those vectors searchable by similarity. Without an index, semantic retrieval would need to scan and compare raw JSONL vectors every time.

For this corpus, local vector search is enough for benchmarking:

- the embedded set has 1,331 vectors
- vectors are 384-dimensional
- the index is reproducible from the embedding JSONL
- local search avoids cloud cost and managed database decisions

## What Is Indexed

Input:

```text
data/processed/embeddings/irandaam_thirumurai_embeddings.jsonl
```

Indexed chunk type:

```text
verse_plus_commentary
```

Only `verse_plus_commentary` is indexed now because it is the primary semantic retrieval unit. It keeps the verse together with `பொழிப்புரை` and `குறிப்புரை`, giving the embedding model more interpretive context than the verse alone.

Other chunk types remain available in the retrieval-ready chunk file, but they were not embedded in the previous phase and are not indexed here.

## FAISS vs NumPy Fallback

The index builder prefers FAISS when the `faiss` Python package is available. FAISS gives a standard local vector index implementation and can scale better if the corpus grows.

If FAISS is not available, the builder saves a NumPy fallback:

- `embeddings.npy`
- `metadata.jsonl`
- `vector_index_manifest.json`

The NumPy fallback uses normalized vectors and cosine similarity through dot product. For 1,331 vectors, this is practical and fast enough.

No Qdrant, Chroma, Pinecone, Vertex AI Matching Engine, or other managed vector database is used.

## Semantic Retrieval Workflow

1. Load the vector index manifest.
2. Load normalized local vectors and chunk metadata.
3. Load the local sentence-transformers model named in the embedding manifest.
4. Embed the user query locally.
5. Normalize the query vector.
6. Compare query vector to indexed chunk vectors.
7. Sort by similarity score, then deterministic rank key, then chunk ID.
8. Return top-k semantic results with citation and source URLs.

Each result includes:

- rank
- similarity score
- retrieval mode
- chunk ID
- parent record ID
- chunk type
- citation text
- source URLs
- deterministic rank key

## Benchmark Update

Semantic mode is no longer marked `PENDING_EMBEDDINGS` when a local vector index exists. The evaluator now runs semantic retrieval against:

```text
data/processed/eval/golden_queries.jsonl
```

Metrics:

- Recall@1
- Recall@3
- Recall@5
- Recall@10
- MRR
- Exact match@1
- failed query analysis

Hybrid retrieval remains pending as `PENDING_HYBRID_IMPLEMENTATION`.

## Limitations

Semantic retrieval with a general multilingual model can be weak for classical Tamil because of:

- older vocabulary and morphology
- Saiva devotional terminology
- dense poetic compression
- orthographic variation
- source/commentary style differences
- queries that depend on exact song numbers, IDs, or `pann`

Lexical retrieval remains the stronger baseline for exact identifiers and source-specific Tamil terms. Semantic retrieval should be reviewed as a complementary recall layer, not as a replacement.

## Commands

Build local vector index:

```bash
python3 src/vector_index/build_faiss_index.py
```

Run semantic benchmark:

```bash
python3 src/evaluation/evaluate_retrieval.py --mode semantic
```

Compare lexical, semantic, and pending hybrid:

```bash
python3 src/evaluation/evaluate_retrieval.py --mode all
```

