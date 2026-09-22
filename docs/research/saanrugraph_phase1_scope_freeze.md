# SaanruGraph Phase 1 Scope Freeze

## Decision

The main paper will study **Thevaram Thirumurai 1-7 only**.

Thirumurai 8 is excluded from the main Paadal-Pozhippurai linking, retrieval, and generation evaluation because the current normalized corpus has paadal text for Thirumurai 8 but no usable Pozhippurai coverage. It should be reported as a coverage limitation, not treated as linker failure.

Stable dataset version name:

`saanrugraph-thevaram-1-7-freeze-v1`

## Frozen Source Artifacts

| Layer | Artifact |
| --- | --- |
| Normalized tables | `data/processed/thevaram_normalized/` |
| PaCoLink current baseline | `data/processed/thevaram_pozhippurai_links/v5_auto_hardened/` |
| Supervisor CSV | `data/exports/thevaram_pozhippurai_v5_supervisor_share_20260726/main_table_v5_auto_hardened_primary_clean_full_context.csv` |
| Ontology | `data/knowledge/ontology/thevaram_ontology_v1.json` |
| Ontology relations | `data/knowledge/ontology/thevaram_relations_v1.json` |
| Entity annotations | `data/processed/thevaram_entity_annotations_v3/` |

## Final Corpus Statistics

| Scope | Thirumurai | Books | Pathigam | Paadal | Commentary rows | Extraction-success rows | Usable Pozhippurai rows | Empty Pozhippurai rows | Text spans | Paadal line spans | Kurippurai spans | Pozhippurai spans | v5 primary links | v5 high | v5 medium | v5 low |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Main paper | 1-7 | 7 | 781 | 8,230 | 8,230 | 7,371 | 7,469 | 761 | 60,637 | 45,342 | 7,826 | 7,469 | 40,538 | 7,155 | 16,106 | 17,277 |
| Excluded coverage note | 8 | 1 | 60 | 782 | 782 | 0 | 0 | 782 | 3,436 | 3,436 | 0 | 0 | 0 | 0 | 0 | 0 |
| Available normalized tables | 1-8 | 8 | 841 | 9,012 | 9,012 | 7,371 | 7,469 | 1,543 | 64,073 | 48,778 | 7,826 | 7,469 | 40,538 | 7,155 | 16,106 | 17,277 |

## Per-Thirumurai Scope Statistics

| Thirumurai | Pathigam | Paadal | Usable Pozhippurai rows | Empty Pozhippurai rows | Text spans | Paadal line spans | Pozhippurai spans | v5 primary links | v5 high | v5 medium | v5 low |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 136 | 1,469 | 1,163 | 306 | 10,371 | 8,039 | 1,163 | 6,647 | 1,263 | 1,875 | 3,509 |
| 2 | 122 | 1,331 | 1,327 | 4 | 10,383 | 7,728 | 1,327 | 7,700 | 1,292 | 2,404 | 4,004 |
| 3 | 126 | 1,358 | 1,341 | 17 | 11,837 | 9,161 | 1,341 | 7,663 | 1,222 | 3,072 | 3,369 |
| 4 | 113 | 1,070 | 1,068 | 2 | 6,412 | 4,281 | 1,068 | 4,263 | 987 | 2,080 | 1,196 |
| 5 | 86 | 1,015 | 1,007 | 8 | 6,078 | 4,058 | 1,007 | 4,022 | 850 | 1,909 | 1,263 |
| 6 | 99 | 981 | 980 | 1 | 9,800 | 7,841 | 980 | 7,821 | 1,032 | 3,482 | 3,307 |
| 7 | 99 | 1,006 | 583 | 423 | 5,756 | 4,234 | 583 | 2,422 | 509 | 1,284 | 629 |

## Frozen Terminology

| Term | Definition for the paper |
| --- | --- |
| Paadal | The canonical hymn/song text row from `paadalgal.jsonl`. |
| Paadal span | A bounded source phrase or line inside `paadal_text`, with stable source ID and character offsets. |
| Pozhippurai | The explanatory commentary field named `pozhppurai` in the normalized tables. The paper should display it as `Pozhippurai`. |
| Commentary span | A bounded target phrase or sentence inside `pozhppurai` or `kurippurai`, with source ID, field name, and character offsets. |
| Evidence path | The citation chain from Thirumurai to Pathigam to Paadal to Paadal span to Commentary/Pozhippurai span, including confidence and relation label. |

## Frozen SaanruGraph Node Types

For the main paper, use these graph node types only:

| Node type | Meaning |
| --- | --- |
| `CORPUS_VERSION` | Frozen dataset release used by the paper. |
| `THIRUMURAI` | One Thevaram Thirumurai book/work. |
| `PATHIGAM` | Paadal thogupu/pathigam within a Thirumurai. |
| `PAADAL` | Canonical song/hymn text. |
| `COMMENTARY` | Commentary row attached to a Paadal. |
| `PAADAL_SPAN` | Bounded source span inside `paadal_text`. |
| `COMMENTARY_SPAN` | Bounded target span inside `pozhppurai` or `kurippurai`. |
| `ENTITY` | Canonical or mentioned entity from the ontology/entity registry. |
| `KNOWLEDGE_ASSERTION` | Evidence-backed higher-level claim for later knowledge annotation. |

## Frozen SaanruGraph Edge Types

| Edge type | Source | Target | Purpose |
| --- | --- | --- | --- |
| `INCLUDES_THIRUMURAI` | `CORPUS_VERSION` | `THIRUMURAI` | Dataset scope. |
| `HAS_PATHIGAM` | `THIRUMURAI` | `PATHIGAM` | Literary hierarchy. |
| `HAS_PAADAL` | `PATHIGAM` | `PAADAL` | Literary hierarchy. |
| `HAS_COMMENTARY` | `PAADAL` | `COMMENTARY` | Commentary attachment. |
| `HAS_PAADAL_SPAN` | `PAADAL` | `PAADAL_SPAN` | Source span containment. |
| `HAS_COMMENTARY_SPAN` | `COMMENTARY` | `COMMENTARY_SPAN` | Commentary span containment. |
| `EXPLAINED_BY` | `PAADAL_SPAN` | `COMMENTARY_SPAN` | PaCoLink evidence edge. |
| `MENTIONS_ENTITY` | Text node/span | `ENTITY` | Entity anchoring. |
| `SUPPORTED_BY` | `KNOWLEDGE_ASSERTION` | Text span | Evidence grounding. |
| `NEXT_SPAN` | Text span | Text span | Local sequence/order support. |

## Frozen PaCoLink Relation Labels

These labels are fixed for Phase 3 gold annotation and Phase 4 PaCoLink evaluation:

- `glosses_word`
- `explains_phrase`
- `explains_line`
- `interprets_image`
- `describes_entity`
- `theological_explanation`

Current v5 relation distribution over the 40,538 primary clean links:

| Relation label | Count |
| --- | ---: |
| `explains_phrase` | 11,183 |
| `interprets_image` | 8,920 |
| `theological_explanation` | 8,773 |
| `describes_entity` | 6,794 |
| `glosses_word` | 3,635 |
| `explains_line` | 1,233 |

## Phase 1 Acceptance

Phase 1 is accepted when:

- the paper scope is fixed to Thevaram Thirumurai 1-7,
- Thirumurai 8 is excluded from main evaluation with a clear missing-commentary reason,
- `saanrugraph-thevaram-1-7-freeze-v1` is used as the stable dataset version,
- corpus statistics are frozen in `data/processed/saanrugraph_phase1/thevaram_1_7_corpus_statistics.csv`,
- node and edge types are frozen in `data/processed/saanrugraph_phase1/saanrugraph_schema_definition_v1.json`,
- later phases do not overwrite v3/v4/v5 artifacts.
