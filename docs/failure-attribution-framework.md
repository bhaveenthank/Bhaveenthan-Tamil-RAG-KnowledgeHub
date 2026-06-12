# Failure Attribution Framework

## Purpose

Evaluation matters because this project is moving from retrieval into Tamil literary
analytics. Accuracy alone is not enough. When a query fails, we need to know whether the
fault came from data coverage, parser output, metadata, query expansion, occurrence
matching, aggregation, analytical routing, registry coverage, or the benchmark itself.

This framework creates deterministic failure attribution for:

- retrieval evaluation;
- query expansion evaluation;
- occurrence evaluation;
- aggregation evaluation;
- analytical retrieval evaluation;
- future extraction and RAG evaluation.

## Evaluation Hierarchy

1. Registry and query expansion: are reviewed aliases and synonyms available?
2. Occurrence search: are literal evidence rows found?
3. Aggregation: are evidence rows grouped and ranked correctly?
4. Analytical retrieval: did the natural-language question route to the correct operation?
5. Future answer generation: does a fluent answer cite the correct evidence?

Each layer should report structured outputs that the next layer can test. This makes
failures explainable rather than mysterious.

## Research Value

For a Tamil literary KnowledgeHub, explainable failures are publication-grade evidence.
They show what the system can do, where the corpus is incomplete, which parser families
need work, and which Tamil linguistic phenomena require better modeling. The goal is not
to hide errors, but to classify them carefully enough that each next phase can improve
the right part of the pipeline.

## Current Scope

Phase 27 evaluates structured analytics only. It does not scrape, extract new knowledge,
call an LLM, build answer generation, use GCP, regenerate embeddings, rebuild indexes, or
mutate frozen corpus artifacts.
