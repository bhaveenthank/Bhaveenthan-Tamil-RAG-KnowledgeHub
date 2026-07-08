# Statistical Evidence Pack for Thevaram Ontology / Literary Knowledge Paper

This file gathers the main evidence for a second paper about the Thevaram semantic ontology and literary knowledge layer. It is intended as a writing aid, not as a final submission artifact.

## Core Artifacts

Ontology and relation files:

- `data/knowledge/ontology/thevaram_ontology_v1.json`
- `data/knowledge/ontology/thevaram_relations_v1.json`
- `data/knowledge/ontology/thevaram_ontology_v1_validation.json`
- `data/knowledge/ontology/guidelines/annotation_guidelines_v1.md`

Annotation output:

- `data/processed/thevaram_entity_annotations_v3/`

Main reports:

- `reports/thevaram-ontology-v1-validation-report.md`
- `reports/thevaram-entity-annotation-v3-report.md`
- `reports/annotation-readiness-report.md`
- `reports/entity-extraction-report.md`
- `reports/entity-benchmark-impact.md`
- `reports/knowledge-readiness-report.md`

## Ontology v1 Validation Summary

| Metric | Value |
| --- | ---: |
| Validation status | `VALID` |
| Entity types | 25 |
| Relations | 29 |
| Attributes | 14 |
| Mythological event canon size | 20 |
| Deprecated v2 entity types | `ACTION`, `NATURE` |
| Validation errors | 0 |

## Entity Type Inventory

The v1 ontology defines the following entity type codes:

| Branch | Entity types |
| --- | --- |
| Agent | `DEITY`, `MANIFESTATION`, `DIVINE_EPITHET`, `MYTH_FIGURE`, `SAINT`, `PERSON`, `REL_GROUP` |
| Place | `SACRED_PLACE`, `REGION`, `MYTHIC_PLACE`, `RIVER`, `MOUNTAIN` |
| Object / Nature / Body | `SACRED_OBJECT`, `FLORA`, `FAUNA`, `CELESTIAL`, `BODY_PART` |
| Event / Concept / Practice | `MYTH_EVENT`, `THEO_CONCEPT`, `COSMO_CONCEPT`, `DEVOTIONAL_ACT`, `RITUAL` |
| Literary / Music / Text | `PAN`, `INSTRUMENT`, `TEXT_WORK` |

Tier counts from validation:

| Tier | Count |
| ---: | ---: |
| 1 | 13 |
| 2 | 11 |
| 3 | 1 |

## Relation Inventory

The v1 relation schema defines 29 relation names:

`wears`, `wears_on`, `holds`, `rides`, `smeared_with`, `adorns`, `consort_of`, `shares_body_with`, `parent_of`, `manifestation_of`, `personification_of`, `refers_to`, `agent_of`, `patient_of`, `instrument_of`, `beneficiary_of`, `event_mentioned_in`, `enshrined_at`, `located_on`, `located_in`, `flows_through`, `sung_at`, `composed_by`, `set_in_pan`, `praises`, `worshipped_by`, `grants`, `condemns`, `invoked_in`.

Relation categories include iconographic, divine relation, linking, event, place, composition, devotional, and polemical relations.

## v2 to v1 Migration Stance

The v1 ontology supersedes the earlier six-type v2 annotation layer.

Current migration recommendations:

- Convert `ACTION` to canonical `MYTH_EVENT` anchors.
- Split `NATURE` into more precise categories such as `FLORA`, `FAUNA`, `RIVER`, `MOUNTAIN`, and `CELESTIAL`.
- Narrow `SACRED_OBJECT` to artefacts/substances and move role semantics into relations.
- Add `DIVINE_EPITHET`, `SACRED_PLACE`, `SAINT`, `REL_GROUP`, `PAN`, and `TEXT_WORK`.
- Queue ambiguous lexemes such as `பதி`, `பசு`, `மெய்`, and `மால்` for word-sense review.

## Annotation v3 Summary

| Metric | Count |
| --- | ---: |
| Entity registry rows | 624 |
| Entity aliases | 823 |
| Seed terms loaded | 823 |
| Extra curated/dynamic terms loaded | 586 |
| Entity mentions | 107761 |
| Entity relationships | 4491 |
| Cross-type overlap records | 30710 |
| Suppressed same-type overlapping candidates | 12578 |
| Invalid bounds | 0 |
| Span text mismatches | 0 |
| Duplicate mention IDs | 0 |

## Mention Counts by Entity Type

| Entity type | Mentions | Seed terms |
| --- | ---: | ---: |
| `NATURE` | 23831 | 47 |
| `BODY_PART` | 17304 | 35 |
| `SACRED_OBJECT` | 16191 | 57 |
| `DEITY` | 13847 | 95 |
| `THEOLOGICAL_CONCEPT` | 11238 | 46 |
| `TEMPLE` | 4036 | 400 |
| `WEAPON` | 3772 | 5 |
| `ICONOGRAPHIC_FEATURE` | 2373 | 5 |
| `SACRED_RIVER` | 2303 | 3 |
| `RELATIONSHIP` | 2000 | 6 |
| `SACRED_TREE` | 1828 | 5 |
| `RITUAL` | 1624 | 6 |
| `MYTHOLOGICAL_CHARACTER` | 1556 | 13 |
| `SACRED_MOUNTAIN` | 1160 | 4 |
| `SACRED_FLOWER` | 1062 | 5 |
| `SAINT` | 949 | 7 |
| `MUSICAL_INSTRUMENT` | 741 | 5 |
| `MYTHOLOGICAL_EVENT` | 398 | 21 |
| `DIVINE_EPITHET` | 347 | 7 |
| `ACTION` | 121 | 37 |
| `FESTIVAL` | 33 | 3 |
| `DIVINE_FORM` | 4 | 5 |

Note: the v3 annotation labels still include legacy categories such as `NATURE`, `TEMPLE`, and `WEAPON`. The v1 ontology defines the cleaner target model for future migration.

## Mention Counts by Field

| Field | Mentions |
| --- | ---: |
| `commentaries.kurippurai` | 39618 |
| `commentaries.pozhppurai` | 37803 |
| `paadalgal.paadal_text` | 30340 |

## Review Status

| Review status | Mentions |
| --- | ---: |
| `auto_accepted` | 73627 |
| `context_supported` | 20582 |
| `needs_context_review` | 11376 |
| `ambiguous_review` | 2176 |

Manual review decisions applied:

| Decision | Mentions |
| --- | ---: |
| `KEEP` | 73627 |
| `CONTEXT_ONLY` | 31958 |
| `AMBIGUOUS_REVIEW` | 2176 |

## Relationship Output

| Relationship type | Count |
| --- | ---: |
| `co_occurs_in_paadal` | 4474 |
| `performed_by` | 6 |
| `associated_with` | 3 |
| `consort_of` | 2 |
| `defeats` | 2 |
| `epithet_of` | 1 |
| `manifestation_of` | 1 |
| `weapon_of` | 1 |
| `worn_or_held_by` | 1 |

Relationship sources:

| Source | Count |
| --- | ---: |
| `corpus_cooccurrence` | 4474 |
| `v3_curated_ontology` | 17 |

Interpretation:

- Most current relationships are corpus co-occurrence edges.
- Curated ontology relations are still small and should be expanded through expert review.

## Annotation Readiness

| Metric | Value |
| --- | ---: |
| Overall annotation readiness | 59.8/100 |
| Annotation files | 8 |
| Records | 24 |
| Annotations | 39 |
| Validation valid | `true` |
| Decision | `ANNOTATION_SEED_READY_EXTRACTION_NOT_STARTED` |

Target readiness:

| Target | Score | Status |
| --- | ---: | --- |
| Entity annotation | 72.0 | `GOLD_SEED_READY_NEEDS_MORE_NEGATIVES` |
| Deity annotation | 68.0 | `GOLD_SEED_READY_NEEDS_EPITHET_VARIANTS` |
| Author annotation | 66.0 | `GOLD_SEED_READY_NEEDS_METADATA_VARIANTS` |
| Motif annotation | 62.0 | `GOLD_SEED_READY_NEEDS_AMBIGUOUS_CASES` |
| Epithet annotation | 58.0 | `GOLD_SEED_READY_ENTITY_LINKING_REQUIRED` |
| Simile annotation | 56.0 | `GOLD_SEED_READY_NEEDS_FALSE_POSITIVES` |
| Metaphor annotation | 50.0 | `GOLD_SEED_READY_HIGH_REVIEW_REQUIRED` |
| Relationship annotation | 46.0 | `GOLD_SEED_READY_DEPENDS_ON_ACCEPTED_CANDIDATES` |

## Entity Extraction Pilot

| Metric | Value |
| --- | ---: |
| Supported entity types | `deity`, `author`, `place`, `work` |
| Expected entities | 7 |
| Extracted entities | 6 |
| True positives | 6 |
| False positives | 0 |
| False negatives | 1 |
| Precision | 1.0000 |
| Recall | 0.8571 |
| F1 | 0.9231 |
| Exact match | 0.8571 |

Important limitation:

- This was a pilot, not a corpus-wide gold evaluation.
- The false negative was `பிரமன்`.

## Knowledge Readiness Context

| Area | Score |
| --- | ---: |
| Foundation readiness | 79.4/100 |
| Analytical readiness | 47.5/100 |
| Evidence readiness | 62.5/100 |
| Aggregation readiness | 66.0/100 |
| Evaluation readiness | 68.0/100 |

Interpretation:

- The ontology and registry foundation is strong enough for a design/resource paper.
- It is not yet strong enough for a paper claiming completed literary interpretation or production QA.

