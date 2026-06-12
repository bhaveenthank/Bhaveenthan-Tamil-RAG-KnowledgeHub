# Annotation Readiness Report

## Summary

- Phase: `phase_30`
- Overall readiness: `59.8/100`
- Annotation files: `8`
- Records: `24`
- Annotations: `39`
- Validation valid: `true`
- Decision: `ANNOTATION_SEED_READY_EXTRACTION_NOT_STARTED`
- Automatic extraction performed: `false`
- Scraping performed: `false`
- Registry population performed: `false`
- LLM calls: `0`

## Target Readiness

| Target | Score | Status | Fixture Counts |
| --- | ---: | --- | --- |
| `entity_annotation_readiness` | 72.0 | `GOLD_SEED_READY_NEEDS_MORE_NEGATIVES` | {'entity': 10} |
| `deity_annotation_readiness` | 68.0 | `GOLD_SEED_READY_NEEDS_EPITHET_VARIANTS` | {'deity': 5} |
| `author_annotation_readiness` | 66.0 | `GOLD_SEED_READY_NEEDS_METADATA_VARIANTS` | {'author': 4} |
| `motif_annotation_readiness` | 62.0 | `GOLD_SEED_READY_NEEDS_AMBIGUOUS_CASES` | {'motif': 7} |
| `epithet_annotation_readiness` | 58.0 | `GOLD_SEED_READY_ENTITY_LINKING_REQUIRED` | {'epithet': 4} |
| `simile_annotation_readiness` | 56.0 | `GOLD_SEED_READY_NEEDS_FALSE_POSITIVES` | {'simile': 3} |
| `metaphor_annotation_readiness` | 50.0 | `GOLD_SEED_READY_HIGH_REVIEW_REQUIRED` | {'metaphor': 3} |
| `relationship_annotation_readiness` | 46.0 | `GOLD_SEED_READY_DEPENDS_ON_ACCEPTED_CANDIDATES` | {'relationship': 3} |

## Annotation Type Counts

| Type | Count |
| --- | ---: |
| `author` | 4 |
| `deity` | 5 |
| `entity` | 10 |
| `epithet` | 4 |
| `metaphor` | 3 |
| `motif` | 7 |
| `relationship` | 3 |
| `simile` | 3 |

## Interpretation

The annotation framework is ready for future extractor evaluation, but the fixture set is
still a seed layer. The next step should add negative and ambiguous examples before any
algorithmic extraction is implemented.
