# Corpus Readiness Audit Report

## Executive Summary

- Records audited: `51`
- Unique hymns: `5`
- Available corpora: `thirumurai_02, thirumurai_04`
- Retrieval chunks inspected: `0`
- Overall readiness score: `71/100`
- Scaling decision: `READY_FOR_CONTROLLED_PILOT_EXPANSION`

This audit covers `data/processed/normalized/thirumurai_04_normalized.jsonl`. Structural extraction is strong, but broad multi-Thirumurai analytical claims remain blocked by incomplete cross-corpus coverage, no synonym authority, no literary-entity annotations, and no exhaustive aggregation layer.

## Readiness Scores

| Area | Score |
| --- | ---: |
| Data Quality Score | 100 |
| Parser Readiness Score | 99 |
| Metadata Readiness Score | 90 |
| Citation Readiness Score | 100 |
| Retrieval Readiness Score | 0 |
| Analytical Readiness Score | 30 |
| Scaling Readiness Score | 75 |
| Overall Readiness Score | 71 |

## Field Coverage

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| `record_id` | 51 | 0 | 100.00% |
| `verse_text` | 51 | 0 | 100.00% |
| `pozhppurai` | 50 | 1 | 98.04% |
| `kurippurai` | 50 | 1 | 98.04% |
| `title` | 51 | 0 | 100.00% |
| `hymn_id` | 51 | 0 | 100.00% |
| `pathigam_id` | 51 | 0 | 100.00% |
| `song_no` | 51 | 0 | 100.00% |
| `author` | 51 | 0 | 100.00% |
| `nayanmar` | 51 | 0 | 100.00% |
| `deity` | 51 | 0 | 100.00% |
| `place` | 51 | 0 | 100.00% |
| `thirumurai_no` | 51 | 0 | 100.00% |
| `source_url` | 51 | 0 | 100.00% |
| `commentary_url` | 51 | 0 | 100.00% |

## Data And Parser Risks

- Empty records: `0`
- Duplicate record IDs: `0`
- Duplicate verse-text groups: `0`
- Unusually short verses: `0`
- Unusually long verses: `0`
- Malformed Tamil text: `0`
- Missing Tamil text: `0`
- Missing pozhppurai: `1`
- Missing kurippurai: `1`
- Field consistency issues: `0`

Empty commentary field count across both commentary columns: `2`. Source and parser evidence must be reviewed before assigning blame; the pilot's known missing pair is caused by a TamilVU endpoint null-pointer response.

### Duplicate Verse Review

| Group | Record IDs |
| ---: | --- |
| None | None |

These exact-text groups require source-aware human review. Repeated devotional refrains can be legitimate, so the audit does not automatically classify them as parser corruption.

## Citation And Source Readiness

- Traceable records: `51` (`100.00%`)
- Missing source URLs: `0`
- Missing commentary URLs: `0`
- Missing citation text: `0`
- Malformed URLs: `0`
- URL identifier mismatches: `0`

## Retrieval And Chunking

- Verse-only retrieval supported: `False`
- Commentary retrieval supported: `False`
- Metadata retrieval supported: `False`
- Missing chunk types: `['kurippurai_only', 'metadata_context', 'pozhppurai_only', 'verse_only', 'verse_plus_commentary']`
- Records without chunks: `51`

Current chunk readiness is reported exactly as observed. Even when chunks exist, they support passage retrieval and citation rather than exhaustive corpus analysis.

## Capability Readiness

| Capability | Readiness | Blocking Issues | Recommended Fix |
| --- | --- | --- | --- |
| ordinary RAG | not_ready | No corpus-specific chunks or retrieval index exist. | Create and benchmark pilot-specific retrieval artifacts in a separate approved phase. |
| verse lookup | partial | Normalized verse text exists, but verse-only chunks do not. | Retain exact Tamil text and add deterministic verse-only chunks. |
| author lookup | ready | None | Preserve normalized and original author labels. |
| hymn identification | ready | None | Keep hymn, pathigam, song, and source URL identifiers aligned. |
| word occurrence search | partial | No dedicated exhaustive aggregation command or morphology handling. | Add a deterministic field-aware occurrence and count layer. |
| synonym expansion | not_ready | No versioned Tamil literary synonym lexicon or concept IDs. | Create a curated synonym authority with source forms and review metadata. |
| deity/epithet analysis | not_ready | Deity is corpus-level normalized; epithets are not extracted or linked. | Add reviewed deity aliases, epithet spans, entity IDs, and evidence offsets. |
| simile/metaphor analysis | not_ready | No simile or metaphor annotations exist. | Design a versioned literary-device annotation schema and human-reviewed sample. |
| Nayanmar comparison | partial | The Appar corpus is a five-hymn pilot, not complete coverage. | Complete and audit comparable author corpora before quantitative comparison. |
| cross-corpus comparison | partial | The second corpus is pilot-sized and cannot support exhaustive claims. | Pilot each new corpus family and normalize shared author, place, work, and deity metadata. |
| corpus-wide aggregation | partial | The data is scan-ready but no dedicated aggregation result contract exists. | Add deterministic group/count/list operations with complete evidence and citations. |
| failure diagnosis | partial | Failure categories exist, but later analysis and LLM stages are not instrumented. | Carry failure attribution and evidence through every future pipeline stage. |

## Synonym Readiness

Exact surface-form evidence exists, but the forms are not linked under a shared literary concept.

| Term | Verse Records | Commentary Records |
| --- | ---: | ---: |
| `சந்திரன்` | 0 | 1 |
| `நிலவு` | 0 | 3 |
| `மதி` | 7 | 11 |
| `திங்கள்` | 2 | 2 |

A versioned Tamil literary synonym lexicon is required before combining these forms in a complete, auditable result.

## Motif And Entity Readiness

The normalized corpus carries a corpus-level deity value, but does not yet contain evidence spans or authority records for epithets, similes, metaphors, natural imagery, or repeated motifs. These capabilities are not ready for automated literary claims.

## Scaling Risks

- **HIGH - parser_family_variation:** The proven parser targets SLET Tevaram hymn/commentary pages; Thirumurai 8-12 may use different work and section structures.
- **HIGH - multi_author_attribution:** Thirumurai 9 and 11 require record-level author attribution rather than one corpus-level author.
- **MEDIUM - identifier_collision:** Source song and hymn numbers must remain namespaced by corpus and work.
- **HIGH - metadata_false_uniformity:** Pathigam, place, deity, and commentary assumptions cannot be forced onto structurally different works.
- **HIGH - analytical_claim_overreach:** Top-k retrieval cannot support claims such as all, most, or compare across the corpus.
- **HIGH - annotation_absence:** Synonyms, epithets, imagery, motifs, similes, and metaphors are not yet normalized.

## Failure Attribution

Future failures should be attributed to: `data_gap, parser_gap, metadata_gap, citation_gap, retrieval_gap, synonym_gap, aggregation_gap, architecture_gap, llm_gap`.

This separates missing source data from parser, metadata, citation, retrieval, synonym, aggregation, architecture, and future LLM failures.

## Recommendations

1. Inspect and pilot one additional Tevaram corpus before broadening to a structurally different Thirumurai.
2. Create source-family adapters that emit the unified schema without assuming every work is a Tevaram pathigam.
3. Build deterministic corpus-wide occurrence and aggregation operations before analytical answer generation.
4. Design a versioned Tamil literary synonym lexicon with concept IDs, variants, citations, and reviewer metadata.
5. Add evidence-bearing entity, epithet, imagery, motif, simile, and metaphor annotation contracts.
6. Require source inspection, parser sampling, normalization validation, and corpus audit for every new registry entry.


## Comparison With Thirumurai 02

| Measure | Thirumurai 02 | Pilot |
| --- | ---: | ---: |
| Overall readiness | 80 | 71 |
| Parser readiness | 100 | 99 |
| Metadata readiness | 85 | 90 |
| Citation readiness | 100 | 100 |
| Retrieval readiness | 100 | 0 |
| Pozhppurai coverage | 99.70% | 98.04% |
| Kurippurai coverage | 99.77% | 98.04% |

The pilot parser is source-family specific. Its richer commentary labels and hymn-local song numbering must remain explicit rather than being forced through the Second Thirumurai assumptions.

