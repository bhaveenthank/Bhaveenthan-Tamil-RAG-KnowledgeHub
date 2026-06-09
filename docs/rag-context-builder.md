# RAG Context Builder

This phase converts local hybrid retrieval results into deterministic, citation-ready context packages. It does not generate answers, call an LLM, scrape content, use cloud services, or modify corpus, embedding, or vector-index artifacts.

## Why Context Building Is Needed

Retrieval results are optimized for ranking. They contain scores, IDs, and brief citation fields, but they are not yet an ideal input for future answer generation.

A context builder creates a stable boundary between retrieval and generation. It joins each retrieved record with:

- normalized verse text
- `பொழிப்புரை`
- `குறிப்புரை`
- metadata context
- citation metadata
- TamilVU source URLs
- retrieval evidence

This lets future answer-generation work consume a validated package rather than reading retrieval indexes directly.

## Why Hybrid Is the Default

Hybrid retrieval matched lexical retrieval on the current 42-query benchmark while recovering all 11 semantic failures. Retrieval diagnostics showed that exact Tamil terms, hymn references, and metadata predicates require lexical evidence, while semantic retrieval remains useful for conceptual expansion.

The context builder therefore uses the existing lexical-heavy hybrid retriever as its default source.

## Context Construction

For each query:

1. Retrieve a larger hybrid candidate set.
2. Preserve the hybrid deterministic ordering.
3. Deduplicate by `parent_record_id` and `chunk_id`.
4. Join each result to the retrieval-ready enriched record.
5. Copy verse, commentary, metadata, citations, URLs, scores, and matched modes.
6. Assign deterministic IDs: `ctx_001`, `ctx_002`, and so on.
7. Stop after the requested `top_k`.
8. Validate the completed package.

`matched_modes: ["both"]` from hybrid retrieval is expanded to:

```json
["lexical", "semantic"]
```

## Context Limits

The default package budget is `100000` content characters. Contexts are added in rank order.

Within a context, text is budgeted in this order:

1. verse text
2. `பொழிப்புரை`
3. `குறிப்புரை`
4. metadata context

If the remaining budget is insufficient, the affected field is deterministically truncated and marked through:

- `content_truncated`
- `content_char_count`
- `context_limits.truncated_contexts`

The package also records a conservative token estimate based on character count. This estimate is operational metadata, not a tokenizer-specific guarantee.

## Duplicate Handling

Only one context is emitted for each parent corpus record. Duplicate chunk IDs are also rejected.

This prevents repeated lexical and semantic candidates from consuming context budget while still preserving `matched_modes` and both normalized component scores in the retained context.

## Citation Preservation

Every context includes:

- source name
- source title
- citation text
- author
- collection
- Thirumurai
- hymn ID
- song number
- hymn URL
- commentary URL

The builder fails validation if a context lacks its record ID, chunk ID, citation text, or source title.

## Package Shape

```json
{
  "query": "திருப்பூந்தராய்",
  "retrieval_mode": "hybrid",
  "context_count": 1,
  "contexts": [
    {
      "context_id": "ctx_001",
      "rank": 1,
      "parent_record_id": "thevaram_02_1664_1470",
      "chunk_id": "thevaram_02_1664_1470_verse_plus_commentary",
      "chunk_type": "verse_plus_commentary",
      "matched_modes": ["lexical", "semantic"],
      "hybrid_score": 1.0,
      "citation": {
        "source_title": "2.1 திருப்பூந்தராய் - வினா உரை - இந்தளம்",
        "song_no": "1470",
        "hymn_id": "1664",
        "source_urls": []
      },
      "content": {
        "verse_text": "",
        "pozhppurai": "",
        "kurippurai": "",
        "metadata_context": ""
      }
    }
  ]
}
```

## Why No Answer Generation

This phase establishes the evidence package only. Answer generation requires separate decisions about prompting, Tamil response style, quotation policy, citation rendering, refusal behavior, and factual grounding checks.

Keeping those concerns separate makes retrieval and citation quality testable before any LLM is introduced.

## Commands

Print a context package:

```bash
python3 src/rag/build_context.py --query "திருப்பூந்தராய்" --top-k 5
```

Write a context package:

```bash
python3 src/rag/build_context.py \
  --query "திருப்பூந்தராய்" \
  --top-k 5 \
  --output data/processed/rag/sample_context.json
```

