# Tamil Literary RAG Question Taxonomy Report

## Summary

- Total questions: `100`
- Ordinary RAG questions: `27`
- Corpus-wide aggregation questions: `67`
- Synonym expansion questions: `14`
- Cross-corpus questions: `16`
- Questions marked for future LLM generation: `27`

## Category Distribution

| Category | Questions |
| --- | ---: |
| A. Basic lookup | 12 |
| B. Verse identification | 12 |
| C. Word occurrence | 12 |
| D. Synonym expansion | 10 |
| E. Deity and epithet | 12 |
| F. Simile and metaphor | 12 |
| G. Poet/Nayanmar comparison | 10 |
| H. Cross-hymn and cross-corpus | 12 |
| I. Failure diagnosis | 8 |

## Difficulty Distribution

| Difficulty | Questions |
| --- | ---: |
| Easy | 14 |
| Hard | 69 |
| Medium | 17 |

## Architecture Implications

- Current RAG context builder can answer lookup/retrieval questions.
- Analytical questions require an additional corpus analysis layer.
- Synonym-based questions require a Tamil literary synonym lexicon.
- Cross-Nayanmar comparison requires multi-corpus metadata normalization.
- Parser quality must be audited before scaling to 3-4 more Thirumurai.
- Citation grounding remains mandatory for lookup, lists, counts, and future generated explanations.
- Literary-device questions need curated annotations or a separately evaluated analysis pipeline; retrieval scores alone do not prove a simile or metaphor.

## Scope Decision

This phase defines and validates the evaluation space only. It makes no LLM calls, performs no scraping, and does not alter corpus, embedding, or vector-index artifacts.
