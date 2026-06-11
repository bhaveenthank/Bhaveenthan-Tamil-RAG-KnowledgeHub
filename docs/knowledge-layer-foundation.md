# Tamil Literary Knowledge Layer Foundation

## Purpose

A literary knowledge layer is a reviewed set of stable concepts, names, relationships,
and annotation contracts placed between the corpus and analytical applications. It does
not replace source text. It gives repeated literary ideas a shared identity so evidence
from many verses, authors, works, and commentaries can be compared safely.

## Why Retrieval Is Insufficient

Retrieval finds passages relevant to a query. It does not prove that a top-k result is a
complete list, resolve whether `மதி`, `திங்கள்`, and `நிலவு` express the same concept,
distinguish a deity name from an epithet, or count a motif exhaustively across authors.
Those tasks need curated authorities, evidence-bearing annotations, and deterministic
aggregation.

## Knowledge Needed For Literary Analytics

Literary research depends on structure beyond strings:

- canonical authors, works, places, and deities
- aliases, spelling variants, and concept-level synonyms
- motifs, themes, imagery, epithets, similes, and metaphors
- relationships such as author-wrote-work, deity-has-epithet, and motif-occurs-in-record
- exact evidence spans, corpus record IDs, source URLs, method, confidence, and review state

The files in `data/knowledge/` establish authority records only. They do not annotate the
corpus or claim extraction coverage.

## Integration With RAG

Future RAG will use the knowledge layer in three controlled steps:

1. Resolve query terms to canonical registry IDs and reviewed variants.
2. Retrieve or aggregate corpus records linked to those IDs.
3. Package the evidence and registry definitions with citations for answer generation.

Lookup questions can still use hybrid retrieval. Questions asking for all occurrences,
frequency, ranking, comparison, or literary interpretation must use an exhaustive analysis
path before any answer is written.

## Research Questions Enabled

The architecture prepares for questions about lunar vocabulary across hymns, Siva's
epithets, deity attributes, author-specific imagery, shared motifs, recurring metaphors,
and cross-corpus themes. Each answer must remain traceable from a canonical knowledge ID
to annotation evidence, corpus record, and original source.

## Publication-Quality Evaluation

Publication-quality claims require versioned registries, reviewer identity, evidence
spans, inter-reviewer disagreement handling, corpus coverage statements, deterministic
aggregation, and reproducible release manifests. Retrieval metrics alone cannot validate
an analytical claim.

## Current Boundary

This phase defines schemas, directories, seed examples, readiness analysis, question
mapping, extraction targets, and a roadmap. It performs no scraping, corpus extraction,
annotation, analytics, embedding, vector indexing, LLM call, or answer generation.
