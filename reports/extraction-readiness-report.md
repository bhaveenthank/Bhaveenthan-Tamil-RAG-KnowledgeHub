# Extraction Readiness Report

## Summary

- Phase: `phase_29`
- Framework status: `FRAMEWORK_READY_POPULATION_NOT_STARTED`
- Extraction targets: `8`
- Overall readiness: `46.9/100`
- Automatic extraction performed: `false`
- Scraping performed: `false`
- Registry population performed: `false`
- LLM calls: `0`
- Next recommended phase: `deity and author extraction pilot`
- Entity extraction pilot available: `true`
- Entity extraction pilot F1: `0.9231`

## Target Readiness

| Target | Candidate Store | Score | Status | Main Blockers |
| --- | --- | ---: | --- | --- |
| `entity_extraction` | `entities_candidates.json` | 78.1 | `PILOT_EVALUATED_DETERMINISTIC_MATCHER` | needs broader negative and ambiguous fixtures, needs missing authority review before registry expansion |
| `deity_extraction` | `entities_candidates.json` | 52.0 | `FRAMEWORK_READY_REQUIRES_ALIAS_REVIEW` | needs deity epithet mapping, needs false-positive examples |
| `author_extraction` | `entities_candidates.json` | 52.0 | `FRAMEWORK_READY_REQUIRES_METADATA_ALIGNMENT` | needs author authority review, needs work-attribution checks |
| `motif_extraction` | `motif_candidates.json` | 45.0 | `SCHEMA_READY_EXTRACTION_RULES_NOT_STARTED` | needs motif annotation guidelines, needs negative examples |
| `epithet_extraction` | `epithet_candidates.json` | 40.0 | `SCHEMA_READY_ENTITY_LINKING_REQUIRED` | needs entity linking, needs reviewed epithet inventory |
| `simile_extraction` | `simile_candidates.json` | 38.0 | `SCHEMA_READY_MARKER_RULES_REQUIRED` | needs marker list, needs subject-object parsing |
| `metaphor_extraction` | `metaphor_candidates.json` | 36.0 | `SCHEMA_READY_HIGH_REVIEW_REQUIRED` | needs interpretation guidelines, needs human review workflow |
| `relationship_extraction` | `relationship_candidates.json` | 34.0 | `SCHEMA_READY_DEPENDS_ON_OTHER_TARGETS` | depends on accepted candidates, needs relationship ontology |

## Candidate Store Validation

| Store | Exists | Placeholder Records | Errors |
| --- | --- | ---: | --- |
| `entities_candidates.json` | `True` | 1 | none |
| `epithet_candidates.json` | `True` | 1 | none |
| `metaphor_candidates.json` | `True` | 1 | none |
| `motif_candidates.json` | `True` | 1 | none |
| `relationship_candidates.json` | `True` | 1 | none |
| `simile_candidates.json` | `True` | 1 | none |
| `theme_candidates.json` | `True` | 1 | none |

## Interpretation

The framework is ready for controlled annotation design, but not for automatic extraction
or registry promotion. The lowest-readiness targets are relationship, metaphor, and simile
extraction because they require accepted lower-level candidates, rhetorical interpretation
rules, and human review.
