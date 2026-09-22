# SaanruGraph Phase 2 Data Cleaning

Dataset version: `saanrugraph-thevaram-1-7-phase2-cleaned-v1`

## Scope

Phase 2 keeps the Phase 1 paper boundary: Thevaram Thirumurai 1-7 only.
Thirumurai 8 remains excluded from the main evaluation because it has no usable Pozhippurai coverage in the frozen tables.

## Cleaned Output Files

| Output | Path |
| --- | --- |
| Cleaned paadal spans | `data/processed/saanrugraph_phase2/cleaned_paadal_spans.csv` |
| Cleaned commentary spans | `data/processed/saanrugraph_phase2/cleaned_commentary_spans.csv` |
| Missing commentary report | `data/processed/saanrugraph_phase2/missing_commentary_report.csv` |
| Final link candidate pool | `data/processed/saanrugraph_phase2/final_link_candidate_pool.csv` |
| Excluded link candidates | `data/processed/saanrugraph_phase2/excluded_link_candidates.csv` |
| Span quality issues | `data/processed/saanrugraph_phase2/span_quality_issues.csv` |
| Hierarchy validation | `data/processed/saanrugraph_phase2/hierarchy_validation_report.json` |
| Machine summary | `data/processed/saanrugraph_phase2/phase2_cleaning_summary.json` |

## Frozen Corpus After Cleaning

- Paadal rows in scope: `8230`
- Raw paadal line spans in scope: `45342`
- Cleaned paadal spans kept: `43913`
- Cleaned commentary spans kept: `15293`
- Cleaned Pozhippurai spans kept: `7469`
- Cleaned Kurippurai spans kept: `7824`

## Candidate Pool

- Input v5 primary rows: `40538`
- Final clean candidate rows: `40454`
- Excluded candidate rows: `84`
- Flagged but retained short-span rows: `10076`

Confidence distribution in the final candidate pool:

| Confidence | Rows |
| --- | ---: |
| `high` | 7,154 |
| `low` | 17,201 |
| `medium` | 16,099 |

Excluded candidate reasons:

| Reason | Rows |
| --- | ---: |
| `source_generic_single_token` | 55 |
| `source_numeric_only` | 18 |
| `source_offset_mismatch` | 2 |
| `target_field_not_pozhippurai` | 1 |
| `target_generic_single_token` | 4 |
| `target_numeric_only` | 2 |
| `target_offset_mismatch` | 1 |
| `target_too_few_tamil_chars` | 2 |

## Missing Commentary Separation

Rows with empty Pozhippurai are classified as true missing-commentary coverage, not linker failure.

| Category | Rows |
| --- | ---: |
| `true_missing_pozhippurai` | 761 |

## Hierarchy Validation

Status: `VALID`

| Check | Issues |
| --- | ---: |
| `missing_book_for_thogupu` | 0 |
| `missing_thogupu_for_paadal` | 0 |
| `missing_paadal_for_commentary` | 0 |
| `missing_parent_for_span` | 0 |
| `duplicate_span_ids` | 0 |

## Cleaning Rules Frozen For Phase 2

- Remove numeric-only source or target spans from positive linking candidates.
- Remove punctuation-only and empty spans.
- Keep valid single-token Tamil spans, but mark them with `short_but_valid_single_token`.
- Exclude non-Pozhippurai target links from the main Paadal-Pozhippurai candidate pool.
- Verify source and target character offsets against the full Paadal and Pozhippurai text.
- Keep true missing-commentary cases in a separate report.

## Phase 2 Acceptance

Phase 2 is accepted when the cleaned span tables, missing-commentary report, final candidate pool, and validation summary are produced without overwriting v3/v4/v5 outputs.
