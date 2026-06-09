# Retrieval Comparison Report

| Mode | Status | Queries Evaluated | Recall@10 | MRR | Failed Queries |
| --- | --- | ---: | --- | --- | ---: |
| lexical | `EVALUATED` | 42 | 1.0000 | 1.0000 | 0 |
| semantic | `EVALUATED` | 42 | 0.7381 | 0.5827 | 11 |
| hybrid | `EVALUATED` | 42 | 1.0000 | 1.0000 | 0 |

- Hybrid improved over semantic: `True`
- Hybrid matched lexical: `True`
- Hybrid failed queries: `0`

## Failure Analysis

- Hybrid had no failed queries.

## Recommendation

Use hybrid retrieval as the default RAG retrieval candidate only if it matches lexical on exact benchmark queries while adding semantic recall. Otherwise keep lexical as the precision baseline and use semantic results as a secondary expansion layer.