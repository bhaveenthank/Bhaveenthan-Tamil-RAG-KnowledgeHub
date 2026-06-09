# Corpus Quality, Parser, And Analytical Readiness Audit

## Why Audit Before Scaling

A successful extraction from one Thirumurai proves one source path, not the final Tamil Literary Knowledge System. Additional corpora can introduce different page structures, multi-author attribution, non-pathigam literary units, missing commentary, identifier collisions, and inconsistent place or deity labels.

This audit asks what can fail later before more data makes those problems expensive to repair.

## Parser Readiness Is Not Enough

A parser can faithfully extract verse text while the system still cannot answer comparative or analytical questions. Parser readiness checks source structure, text boundaries, identifiers, and commentary fields. Analytical readiness additionally requires normalized entities, literary concepts, exhaustive aggregation, and multiple comparable corpora.

Passing parser checks must therefore never be presented as proof that synonym, motif, epithet, simile, metaphor, or cross-Nayanmar analysis is ready.

## Quality And RAG

RAG depends on complete text, stable parent-child relationships, field-aware chunks, and deterministic citations. Empty or malformed verse text harms retrieval. Flattened commentary can cause the system to quote an explanation as though it were the poem. Duplicate records distort ranking and occurrence counts.

The audit measures these risks without changing the normalized corpus.

## Metadata And Aggregation

Corpus-wide counts require normalized dimensions. Author aliases, Nayanmar identity, place names, deity names, corpus IDs, hymn IDs, and song numbers must be stable before grouping or comparison. A top-k retriever cannot answer “all,” “most,” or “which author uses more” because it does not scan the complete eligible set.

The audit treats scan-ready data and a complete aggregation capability as separate states.

## Citation Trust

Researchers need to trace every verse and commentary claim to the exact source. The audit checks source and commentary URLs, citation text, source identifiers, malformed URLs, and URL-to-record identifier consistency. Citation completeness is scored separately from retrieval performance.

## Synonym, Entity, And Motif Readiness

Exact strings such as `சந்திரன்`, `நிலவு`, `மதி`, and `திங்கள்` may already occur in the text, but they are not automatically interchangeable. Reliable synonym expansion needs a versioned Tamil literary lexicon with concept IDs, forms, evidence, and review metadata.

Likewise, corpus-level `deity = Siva` does not identify every textual deity mention or epithet. Similes, metaphors, natural imagery, and motifs need evidence-bearing annotations before the system can make literary claims.

## Failure Attribution

Future diagnostics should distinguish:

- `data_gap`
- `parser_gap`
- `metadata_gap`
- `citation_gap`
- `retrieval_gap`
- `synonym_gap`
- `aggregation_gap`
- `architecture_gap`
- `llm_gap`

This prevents a missing corpus or parser field from being misreported as an LLM failure, and prevents a retrieval miss from triggering unnecessary re-scraping.

## Deterministic Scoring

Scores are computed from observed coverage and explicit capability checks. Structural errors reduce data, parser, metadata, citation, or retrieval scores. Missing analytical infrastructure reduces analytical and scaling scores even when the current corpus is clean.

The overall score is the rounded mean of:

- data quality
- parser readiness
- metadata readiness
- citation readiness
- retrieval readiness
- analytical readiness
- scaling readiness

Scores are decision aids, not substitutes for the detailed issues and capability table.

## Scope

The audit is read-only. It performs no scraping, network access, corpus mutation, embedding generation, vector-index rebuilding, or answer generation.
