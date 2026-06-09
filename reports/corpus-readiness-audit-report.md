# Corpus Readiness Audit Report

## Executive Summary

- Records audited: `1331`
- Unique hymns: `122`
- Available corpora: `thirumurai_02`
- Retrieval chunks inspected: `6648`
- Overall readiness score: `80/100`
- Scaling decision: `READY_FOR_CONTROLLED_PILOT_EXPANSION`

The existing Irandaam Thirumurai corpus is strong for grounded retrieval. Controlled pilot expansion is reasonable, but broad multi-Thirumurai analytical claims remain blocked by unproven parser families, one-corpus coverage, no synonym authority, no literary-entity annotations, and no exhaustive aggregation layer.

## Readiness Scores

| Area | Score |
| --- | ---: |
| Data Quality Score | 98 |
| Parser Readiness Score | 100 |
| Metadata Readiness Score | 85 |
| Citation Readiness Score | 100 |
| Retrieval Readiness Score | 100 |
| Analytical Readiness Score | 15 |
| Scaling Readiness Score | 60 |
| Overall Readiness Score | 80 |

## Field Coverage

| Field | Present | Missing | Coverage |
| --- | ---: | ---: | ---: |
| `record_id` | 1331 | 0 | 100.00% |
| `verse_text` | 1331 | 0 | 100.00% |
| `pozhppurai` | 1327 | 4 | 99.70% |
| `kurippurai` | 1328 | 3 | 99.77% |
| `title` | 1331 | 0 | 100.00% |
| `hymn_id` | 1331 | 0 | 100.00% |
| `pathigam_id` | 1331 | 0 | 100.00% |
| `song_no` | 1331 | 0 | 100.00% |
| `author` | 1331 | 0 | 100.00% |
| `nayanmar` | 1331 | 0 | 100.00% |
| `deity` | 1331 | 0 | 100.00% |
| `place` | 1331 | 0 | 100.00% |
| `thirumurai_no` | 1331 | 0 | 100.00% |
| `source_url` | 1331 | 0 | 100.00% |
| `commentary_url` | 1331 | 0 | 100.00% |

## Data And Parser Risks

- Empty records: `0`
- Duplicate record IDs: `0`
- Duplicate verse-text groups: `2`
- Unusually short verses: `0`
- Unusually long verses: `0`
- Malformed Tamil text: `0`
- Missing Tamil text: `0`
- Missing pozhppurai: `4`
- Missing kurippurai: `3`
- Field consistency issues: `0`

The seven empty commentary fields are known source omissions. No verified parser bug is inferred from them.

### Duplicate Verse Review

| Group | Record IDs |
| ---: | --- |
| 1 | `thevaram_02_1715_2036`, `thevaram_02_1724_2134` |
| 2 | `thevaram_02_1725_2138`, `thevaram_02_1725_2139` |

These exact-text groups require source-aware human review. Repeated devotional refrains can be legitimate, so the audit does not automatically classify them as parser corruption.

## Citation And Source Readiness

- Traceable records: `1331` (`100.00%`)
- Missing source URLs: `0`
- Missing commentary URLs: `0`
- Missing citation text: `0`
- Malformed URLs: `0`
- URL identifier mismatches: `0`

## Retrieval And Chunking

- Verse-only retrieval supported: `True`
- Commentary retrieval supported: `True`
- Metadata retrieval supported: `True`
- Missing chunk types: `none`
- Records without chunks: `0`

Current chunks are suitable for passage retrieval and citation. They are not an exhaustive analytical query engine.

## Capability Readiness

| Capability | Readiness | Blocking Issues | Recommended Fix |
| --- | --- | --- | --- |
| ordinary RAG | ready | None | Keep hybrid retrieval and citation validation as the default path. |
| verse lookup | ready | None | Retain exact Tamil text and verse-only chunks. |
| author lookup | ready | None | Preserve normalized and original author labels. |
| hymn identification | ready | None | Keep hymn, pathigam, song, and source URL identifiers aligned. |
| word occurrence search | partial | No dedicated exhaustive aggregation command or morphology handling. | Add a deterministic field-aware occurrence and count layer. |
| synonym expansion | not_ready | No versioned Tamil literary synonym lexicon or concept IDs. | Create a curated synonym authority with source forms and review metadata. |
| deity/epithet analysis | not_ready | Deity is corpus-level normalized; epithets are not extracted or linked. | Add reviewed deity aliases, epithet spans, entity IDs, and evidence offsets. |
| simile/metaphor analysis | not_ready | No simile or metaphor annotations exist. | Design a versioned literary-device annotation schema and human-reviewed sample. |
| Nayanmar comparison | not_ready | Only one available Nayanmar corpus is normalized. | Normalize at least one additional audited author corpus before comparison. |
| cross-corpus comparison | not_ready | Only thirumurai_02 is available. | Pilot each new corpus family and normalize shared author, place, work, and deity metadata. |
| corpus-wide aggregation | partial | The data is scan-ready but no dedicated aggregation result contract exists. | Add deterministic group/count/list operations with complete evidence and citations. |
| failure diagnosis | partial | Failure categories exist, but later analysis and LLM stages are not instrumented. | Carry failure attribution and evidence through every future pipeline stage. |

## Synonym Readiness

Exact surface-form evidence exists, but the forms are not linked under a shared literary concept.

| Term | Verse Records | Commentary Records |
| --- | ---: | ---: |
| `சந்திரன்` | 0 | 10 |
| `நிலவு` | 4 | 15 |
| `மதி` | 181 | 181 |
| `திங்கள்` | 22 | 30 |

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
