# Comprehensive Benchmark

## Purpose

The comprehensive benchmark establishes the official baseline for the current Tamil
Literary KnowledgeHub. It asks what the system can answer today, what it can partially
support with structured evidence, what it cannot answer, and which capability blocks each
failure.

## Methodology

The runner loads the existing 100-question taxonomy from
`data/processed/eval/literary_analysis_questions.jsonl`. It routes each question through
deterministic components where appropriate:

- lexical retrieval;
- registry-driven query expansion;
- corpus-wide occurrence search;
- aggregation and statistics;
- analytical retrieval;
- failure attribution.

No LLM, scraping, extraction, GCP work, embedding regeneration, vector-index rebuild, or
frozen-corpus mutation is performed.

## Benchmark Categories

The taxonomy is summarized into benchmark categories:

- ordinary retrieval
- author questions
- deity questions
- synonym questions
- occurrence questions
- aggregation questions
- analytical questions
- cross-corpus questions
- unsupported questions

## Current Limitations

The system can perform retrieval, occurrence search, and aggregation on the currently
normalized local corpora. It cannot yet perform motif extraction, epithet extraction,
metaphor extraction, simile extraction, full website-wide coverage, or fluent answer
generation.

## Future Evolution

Future benchmark phases should add human-reviewed gold answers, source-level extraction
checks, expanded multi-corpus coverage, and later grounded answer-generation evaluation.
