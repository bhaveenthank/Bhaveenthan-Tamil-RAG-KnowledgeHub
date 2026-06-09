# Embedding Design

This phase prepares local embedding artifacts for the retrieval-ready Irandaam Thirumurai chunks. It does not scrape TamilVU, modify frozen corpus v1, modify retrieval-ready corpus v1.1, build RAG, use GCP, or create a managed vector database.

## Why Embeddings Are Needed

Lexical retrieval works well when the query shares exact words, identifiers, hymn titles, `pann`, or metadata with the corpus. That is valuable for researchers who know what they are looking for.

Semantic retrieval is different. It can later support queries where the user expresses an idea rather than an exact phrase, for example devotional concepts, poetic imagery, theological motifs, or prose questions that do not reuse the same Tamil words found in the verse or commentary.

Embeddings convert text chunks into numeric vectors that can be compared by similarity. The local artifacts created in this phase will allow the pending semantic and hybrid benchmark modes to be implemented later.

## Chunk Types

The retrieval-ready corpus v1.1 contains five deterministic chunk types:

- `verse_only`
- `pozhppurai_only`
- `kurippurai_only`
- `verse_plus_commentary`
- `metadata_context`

The embedding generator defaults to `verse_plus_commentary`.

`verse_plus_commentary` is the primary semantic retrieval unit because it keeps the original verse together with both available commentary layers. For classical Tamil, the verse alone can be compact, metaphorical, or syntactically difficult. The commentary often expands names, places, theological references, and interpretive context, making the vector representation more useful for researchers and Tamil literature lovers.

The script can optionally embed all chunk types with `--all-chunk-types`, but the first semantic benchmark should start with `verse_plus_commentary` to keep the retrieval unit clear and comparable.

## Model Strategy

Preferred local model:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

This model is practical for a student machine because it is multilingual and relatively small compared with larger transformer encoders. The implementation uses `sentence-transformers` locally and does not call paid APIs, OpenAI APIs, or external cloud embedding services.

The dependency is declared as an optional project extra:

```bash
python3 -m pip install -e '.[embeddings]'
```

The first model load may download model weights from Hugging Face if they are not already cached locally. After that, generation can run from the local cache.

By default, the script stores the model cache under `data/processed/embeddings/hf_cache/` so local generation works in restricted environments without writing to a home-directory cache.

## Determinism

The generator preserves:

- `chunk_id`
- `parent_record_id`
- `chunk_type`
- source URLs
- citation metadata
- filter metadata
- deterministic rank key

It does not generate random IDs. Embedding rows are sorted by deterministic rank key and chunk ID before writing. Each row includes a SHA-256 hash of the embedded normalized chunk text. The manifest includes the input file hash, selected chunk types, model name, vector dimension, and a deterministic build fingerprint.

The actual numeric vectors depend on the selected model version and local `sentence-transformers`/PyTorch stack. For strict reproducibility across machines, pinning an exact model revision should be added before publishing semantic benchmark numbers.

## Lexical vs Semantic Retrieval

Lexical retrieval:

- matches exact tokens, metadata, IDs, and Tamil terms
- is deterministic and explainable
- performs strongly for known hymn, song, `pann`, and phrase queries

Semantic retrieval:

- compares vector similarity between query and corpus chunks
- can find conceptually related material when exact terms differ
- is less transparent and may be weaker for rare classical Tamil terms if the model has limited training coverage

Hybrid retrieval will later combine both approaches: lexical precision for citations and identifiers, semantic recall for broader concept matching.

## Limitations for Classical Tamil

General multilingual embedding models may not fully understand:

- classical Tamil morphology
- devotional and Saiva Siddhanta terminology
- old orthography and sandhi forms
- poetic compression
- culturally specific allusions
- distinction between verse text and later commentary

For this reason, embeddings should be benchmarked against the existing golden queries and manually reviewed before being trusted for user-facing retrieval.

## Why No Vector DB Yet

This phase writes local JSONL embedding artifacts only. A managed vector database would add deployment, cost, schema, and operational decisions before we know whether the embeddings perform well.

The local artifact-first approach lets us:

- inspect vectors and metadata
- benchmark semantic retrieval later
- compare lexical, semantic, and hybrid modes
- choose a vector store only after the retrieval quality is proven

## Commands

Default `verse_plus_commentary` embeddings:

```bash
python3 src/embeddings/build_embeddings.py \
  --input data/processed/chunks/irandaam_thirumurai_chunks.jsonl \
  --output data/processed/embeddings/irandaam_thirumurai_embeddings.jsonl \
  --manifest data/processed/embeddings/embedding_manifest.json
```

All chunk types:

```bash
python3 src/embeddings/build_embeddings.py \
  --input data/processed/chunks/irandaam_thirumurai_chunks.jsonl \
  --output data/processed/embeddings/irandaam_thirumurai_all_chunk_embeddings.jsonl \
  --manifest data/processed/embeddings/all_chunk_embedding_manifest.json \
  --all-chunk-types
```
