# Retrieval Error Analysis Report

## Executive Summary

- Semantic queries analyzed: `42`
- Semantic successes: `31`
- Semantic failures: `11`
- Semantic failures rescued by hybrid: `11`
- Hybrid recovery rate: `100.00%`
- Remaining hybrid failures: `0`

## Failure Categories

| Category | Count | Percentage |
| --- | ---: | ---: |
| classical Tamil phrase mismatch | 7 | 63.64% |
| hymn/song reference mismatch | 1 | 9.09% |
| metadata mismatch | 2 | 18.18% |
| rare term mismatch | 1 | 9.09% |

## Retrieval Score Analysis

| Population | Results | Minimum | Mean | Median | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| Failed semantic queries | 110 | 0.20467809 | 0.29884945 | 0.28143196 | 0.57770962 |
| Successful semantic queries | 217 | 0.10144313 | 0.29178783 | 0.27019128 | 0.72779942 |

- Failed queries with no expected result in top 10: `11`

Similarity magnitude alone did not separate success from failure. Exact identifiers, literal Tamil terms, and metadata state require lexical evidence.

## Query-Level Failures

| Query | Type | Category | Confidence | Semantic Top Record | Top Score | Hybrid Recovered | Hybrid Rank |
| --- | --- | --- | ---: | --- | ---: | --- | ---: |
| `known_hymn_title_thiruppoontharai` | exact_title | hymn/song reference mismatch | 0.95 | `thevaram_02_1775_2685` | 0.57770962 | `True` | 1 |
| `keyword_sivan` | keyword | classical Tamil phrase mismatch | 0.84 | `thevaram_02_1688_1740` | 0.29318413 | `True` | 1 |
| `keyword_sivaperuman` | keyword | classical Tamil phrase mismatch | 0.84 | `thevaram_02_1740_2310` | 0.33816892 | `True` | 1 |
| `keyword_thiruppoontharai` | keyword | rare term mismatch | 0.88 | `thevaram_02_1737_2273` | 0.36234424 | `True` | 1 |
| `commentary_missing_pozhppurai` | commentary | metadata mismatch | 0.98 | `thevaram_02_1737_2273` | 0.24301583 | `True` | 1 |
| `commentary_missing_kurippurai` | commentary | metadata mismatch | 0.98 | `thevaram_02_1737_2273` | 0.233905 | `True` | 1 |
| `keyword_ae51c91b` | keyword | classical Tamil phrase mismatch | 0.84 | `thevaram_02_1775_2684` | 0.26179248 | `True` | 1 |
| `keyword_7411594e` | keyword | classical Tamil phrase mismatch | 0.84 | `thevaram_02_1687_1727` | 0.26341686 | `True` | 1 |
| `keyword_e8067692` | keyword | classical Tamil phrase mismatch | 0.84 | `thevaram_02_1688_1740` | 0.28689766 | `True` | 1 |
| `keyword_f2ac554e` | keyword | classical Tamil phrase mismatch | 0.84 | `thevaram_02_1687_1727` | 0.31771505 | `True` | 1 |
| `keyword_e48daa8f` | keyword | classical Tamil phrase mismatch | 0.84 | `thevaram_02_1688_1740` | 0.30588353 | `True` | 1 |

## Hybrid Diagnostics

| Query | Matched Modes | Lexical Normalized | Semantic Normalized | Exact Boost | Metadata Boost |
| --- | --- | ---: | ---: | ---: | ---: |
| `known_hymn_title_thiruppoontharai` | `['lexical']` | 1.0 | 0.0 | 0.3 | 0.0 |
| `keyword_sivan` | `['both']` | 0.95652174 | 0.76961273 | 0.15 | 0.0 |
| `keyword_sivaperuman` | `['both']` | 0.6875 | 0.89132017 | 0.05 | 0.0 |
| `keyword_thiruppoontharai` | `['lexical']` | 1.0 | 0.0 | 0.05 | 0.0 |
| `commentary_missing_pozhppurai` | `['lexical']` | 1.0 | 0.0 | 0.0 | 0.0 |
| `commentary_missing_kurippurai` | `['lexical']` | 1.0 | 0.0 | 0.0 | 0.0 |
| `keyword_ae51c91b` | `['both']` | 0.66666667 | 0.8948401 | 0.05 | 0.0 |
| `keyword_7411594e` | `['both']` | 0.73913043 | 0.87073644 | 0.1 | 0.0 |
| `keyword_e8067692` | `['both']` | 0.55555556 | 0.91591211 | 0.05 | 0.0 |
| `keyword_f2ac554e` | `['both']` | 0.95652174 | 0.83734472 | 0.15 | 0.0 |
| `keyword_e48daa8f` | `['lexical']` | 0.94444444 | 0.0 | 0.1 | 0.0 |

## Major Findings

- Literal Tamil title and keyword queries are not safely replaceable with semantic similarity.
- Queries about missing commentary fields are metadata predicates; their absence is not represented by verse-plus-commentary vectors.
- Hybrid retrieval recovered semantic failures by restoring exact lexical terms, title matches, commentary availability signals, and metadata filters.
- Similarity scores overlap substantially between successful and failed queries, so a global similarity threshold alone is not a sufficient fix.

## Recommendations

1. Keep lexical-heavy hybrid retrieval as the default candidate for future RAG.
2. Route identifiers, titles, song numbers, hymn IDs, `pann`, and commentary availability predicates through lexical/metadata retrieval.
3. Use semantic retrieval for conceptual expansion after precise lexical candidates are secured.
4. Preserve deterministic boosts and citations in any future RAG retriever.
5. Expand the golden set with natural Tamil research questions before interpreting semantic quality as production-ready.
