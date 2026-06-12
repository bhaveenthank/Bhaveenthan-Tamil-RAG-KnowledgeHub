# Literary Knowledge Extraction Framework

## Purpose

The Tamil Literary KnowledgeHub now has retrieval, query expansion, occurrence search,
aggregation, analytical retrieval, evaluation, and failure attribution. The comprehensive
benchmark shows the next major gap: the system can count exact terms, but it cannot yet
recognize literary knowledge such as motifs, epithets, metaphors, similes, entity
relationships, or normalized author/deity mentions across phrasing variants.

This phase defines the extraction framework only. It does not extract from the corpus,
scrape TamilVU, call an LLM, mutate frozen corpora, or populate production registries.

## Why Extraction Is Needed

Occurrence search can answer questions about exact words and registry-expanded terms.
Literary questions often require interpreted evidence:

- a deity mention may appear through an epithet rather than a canonical name
- a motif may be expressed without using the registry label directly
- a simile may be indicated by markers such as `போல்`, `ஒக்கும்`, or `அன்ன`
- a metaphor may require identifying a source and target image
- a relationship may link an author, work, deity, place, motif, or literary device

Future extraction will convert these patterns into reviewed candidate records with exact
source evidence and provenance.

## Target Families

The framework covers eight initial extraction targets:

| Target | Purpose | Current Status |
| --- | --- | --- |
| Entity extraction | Detect normalized people, places, works, deities, and concepts | Framework only |
| Deity extraction | Normalize deity mentions and aliases | Framework only |
| Author extraction | Normalize author names and aliases | Framework only |
| Motif extraction | Detect recurring imagery and thematic motifs | Framework only |
| Epithet extraction | Link descriptive names to entities, especially deities | Framework only |
| Simile extraction | Detect explicit comparison structures | Framework only |
| Metaphor extraction | Detect figurative source-target mappings | Framework only |
| Relationship extraction | Link entities, motifs, devices, works, authors, and evidence | Framework only |

## Pipeline Shape

Future extraction should follow this controlled sequence:

1. Select a small reviewed corpus sample.
2. Define positive, negative, and ambiguous fixture examples.
3. Generate candidate records locally.
4. Validate candidate schema and deterministic identifiers.
5. Attach exact evidence spans, source URLs, record IDs, and field names.
6. Human-review accepted candidates before registry promotion.
7. Re-run occurrence, aggregation, analytical retrieval, and benchmark diagnostics.

## Why No Automatic Extraction Yet

Automatic extraction would be premature because the current registries are curated seed
knowledge, not exhaustive authorities. Classical Tamil also contains compact poetic
forms, variant spellings, sandhi, epithets, and rhetorical structures that require careful
review. The project needs target schemas, candidate stores, readiness scoring, and quality
gates before population begins.

## Relationship To Analytics And RAG

Extraction will unlock evidence-backed literary analytics: deity-epithet statistics,
motif distributions, author comparisons, figurative-device counts, and cross-work
relationships. Later RAG answer generation can use these structured candidates as
grounding, but this phase does not generate answers.

## Guardrails

- No scraping.
- No LLM calls.
- No automatic extraction.
- No registry promotion.
- No mutation of frozen corpus artifacts.
- No embeddings or vector-index rebuild.
- Placeholder candidate files are examples of schema shape only.
