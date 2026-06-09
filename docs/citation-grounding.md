# Citation and Source Grounding

This phase converts validated RAG context packages into deterministic citation packages. It does not generate answers, call an LLM, scrape content, use cloud services, or modify corpus, embedding, or vector-index artifacts.

## Why Source Grounding Matters

Retrieval identifies potentially useful evidence. Source grounding proves where that evidence came from.

For Tamil literature research, an answer without precise provenance is difficult to verify. The same devotional theme, place name, poetic image, or commentary concept may occur across many hymns. Researchers need to know the exact:

- collection
- Thirumurai
- hymn
- song number
- source page
- commentary page

Grounding also prevents a future answer generator from presenting commentary as original verse, combining unrelated hymns without disclosure, or citing only a broad collection when an exact source exists.

## Citation Quality for Tamil Literature

Citation quality is especially important because:

- classical Tamil terms can have context-dependent meanings
- verse and commentary are distinct evidence layers
- hymn titles may include location, note, and `பண்`
- researchers may need to inspect the original TamilVU rendering
- commentary can contain later interpretation not present in the verse

The citation layer preserves exact corpus identifiers and both hymn and commentary URLs.

## Citation Flow

```text
TamilVU source
  -> frozen corpus record
  -> retrieval-ready record and chunks
  -> lexical / semantic / hybrid retrieval
  -> deterministic context package
  -> deterministic citation package
  -> future answer-segment citations
```

Every citation remains traceable to:

- `parent_record_id`
- `chunk_id`
- `hymn_id`
- `song_no`
- source title
- citation text
- retrieval rank
- source URL
- commentary URL

## Citation Granularity

The current citation unit is one retrieved verse record. It corresponds to a song number and its associated commentary.

This is more precise than citing an entire hymn, while still keeping verse and commentary together for interpretation. The citation also records the retrieved chunk type so future systems can distinguish how the record entered the evidence set.

## Deterministic Citation IDs

Citations are sorted by:

1. retrieval rank
2. deterministic rank key
3. parent record ID
4. chunk ID

They receive stable sequential IDs:

```text
cit_001
cit_002
cit_003
```

Duplicate `(parent_record_id, chunk_id)` pairs are removed before IDs are assigned.

## Citation Grouping

Citations are grouped by:

- collection
- Thirumurai
- hymn ID
- source title

Groups receive deterministic IDs such as `grp_001`. A group can contain multiple song-level citations from the same hymn.

## Multiple Citations Per Answer Segment

The citation package supports an `answer_segment_citations` mapping:

```json
[
  {
    "segment_id": "segment_001",
    "citation_ids": ["cit_001", "cit_002"]
  }
]
```

This infrastructure is prepared for future answer generation, but this phase does not create segments or answer text.

## Validation and Traceability

Validation checks:

- required citation fields
- deterministic IDs
- missing source URLs
- malformed HTTP/HTTPS URLs
- missing record, chunk, hymn, or song identifiers
- invalid retrieval ranks
- duplicate citations
- unknown citation IDs in groups or answer segments

The export fails rather than silently producing an invalid citation package.

## Export

Given:

```text
data/processed/rag/sample_context.json
```

Run:

```bash
python3 src/rag/export_citations.py --input sample_context.json
```

The exporter resolves the short filename under `data/processed/rag/` and writes:

```text
data/processed/rag/sample_citations.json
reports/citation-grounding-report.md
```

## Future Answer Integration

A future answer generator should only cite the generated `citation_id` values. Rendering can then convert those IDs into TamilVU links, footnotes, inline references, or source panels without losing the underlying record and chunk traceability.

No answer generation is implemented in this phase.

