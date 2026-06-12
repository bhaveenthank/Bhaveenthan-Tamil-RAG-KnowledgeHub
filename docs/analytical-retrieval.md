# Analytical Retrieval

## Purpose

Analytical retrieval converts a Tamil or English analytical question into a structured
operation over the existing evidence and statistics layers. It does not generate prose
answers. Instead, it returns the detected intent, target term, expansion choice, grouping
dimension, ranked statistics, and evidence samples.

## Difference From Retrieval And RAG

Normal retrieval returns top-k contexts for reading. RAG would later use those contexts
to generate an answer. Analytical retrieval asks a different question: which deterministic
analytics operation should run, and what grouped evidence does it produce?

This phase uses:

- registry-driven query expansion;
- corpus-wide occurrence search;
- aggregation and statistics.

It performs no scraping, automatic extraction, LLM calls, GCP work, embedding generation,
vector-index rebuild, or frozen-corpus mutation.

## Supported Intents

- `term_occurrence`
- `group_by_author`
- `group_by_work`
- `group_by_category`
- `group_by_record_type`
- `compare_sources`
- `unsupported`

The classifier is rule-based. It detects cue words such as `ஆசிரியர்`, `works`,
`corpus`, `record types`, and `source`, then extracts a registry-backed target term where
possible.

## Output Shape

The analytical retriever returns:

- original query;
- intent;
- target term;
- whether query expansion was used;
- grouping dimension;
- total occurrences;
- ranked top results;
- evidence samples;
- limitations.

## Limitations

Term extraction is intentionally conservative. It is not a general Tamil parser. Counts
are literal occurrence counts, and expanded counts depend on the current curated registry
seeds. This layer prepares structured evidence for future answer composition; it is not
yet natural-language answer generation.
