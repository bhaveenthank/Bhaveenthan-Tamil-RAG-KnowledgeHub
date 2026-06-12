# Comprehensive Benchmark Report

## Overall Metrics

- Total questions: `100`
- Success rate: `43.00%`
- Partial success rate: `13.00%`
- Failure rate: `44.00%`
- Successes: `43`
- Partials: `13`
- Failures: `44`

## Per-Category Metrics

| Category | Questions | Success | Partial | Failure | Success Rate |
| --- | ---: | ---: | ---: | ---: | ---: |
| `aggregation questions` | 2 | 2 | 0 | 0 | 100.00% |
| `author questions` | 2 | 1 | 0 | 1 | 50.00% |
| `cross-corpus questions` | 21 | 0 | 1 | 20 | 0.00% |
| `deity questions` | 5 | 4 | 0 | 1 | 80.00% |
| `occurrence questions` | 12 | 10 | 2 | 0 | 83.33% |
| `ordinary retrieval` | 21 | 21 | 0 | 0 | 100.00% |
| `synonym questions` | 5 | 5 | 0 | 0 | 100.00% |
| `unsupported questions` | 32 | 0 | 10 | 22 | 0.00% |

## Top Failure Causes

| Failure Type | Count |
| --- | ---: |
| `architecture_gap` | 27 |
| `evaluation_gap` | 10 |
| `data_gap` | 9 |
| `registry_gap` | 8 |
| `aggregation_gap` | 3 |

## Methodology

This benchmark routes the 100-question taxonomy through deterministic retrieval,
query expansion, occurrence search, aggregation, and analytical retrieval where current
capabilities permit. It does not call an LLM and does not grade fluent answer text.
