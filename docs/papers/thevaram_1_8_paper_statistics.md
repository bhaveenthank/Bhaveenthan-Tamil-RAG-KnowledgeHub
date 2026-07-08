# Statistical Evidence Pack for Thevaram 1-8 Resource Paper

This file gathers the main quantitative details that can support a resource paper about the Thevaram 1-8 corpus pipeline. It is intended as a writing aid, not as a final frozen release statement.

## Core Corpus Scope

Source artifacts:

- Ingestion report: `reports/thevaram-1-8-ingestion-report.md`
- Normalization report: `reports/thevaram-normalization-report.md`
- Table quality report: `reports/thevaram-normalized-table-quality-report.md`
- Commentary-linking statistics: `reports/thevaram-pozhppurai-link-v4-statistical-analysis.md`
- Entity annotation report: `reports/thevaram-entity-annotation-v3-report.md`

Primary normalized table root:

- `data/processed/thevaram_normalized`

## Relational Table Counts

| Table | Count |
| --- | ---: |
| `thirumurai_books` | 8 |
| `paadal_thogupugal` | 841 |
| `paadalgal` | 9012 |
| `commentaries` | 9012 |
| `text_spans` | 64073 |

The ingestion report records no failures. The normalized table quality report records no issue counts.

## Per-Thirumurai Coverage

| Thirumurai | Paadal thogupugal | Paadalgal | Commentaries | Text spans | Paadal chars | Paadal lines |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 136 | 1469 | 1469 | 10371 | 257235 | 8039 |
| 2 | 122 | 1331 | 1331 | 10383 | 245120 | 7728 |
| 3 | 126 | 1358 | 1358 | 11837 | 244926 | 9161 |
| 4 | 113 | 1070 | 1070 | 6412 | 206320 | 4281 |
| 5 | 86 | 1015 | 1015 | 6078 | 137676 | 4058 |
| 6 | 99 | 981 | 981 | 9800 | 287525 | 7841 |
| 7 | 99 | 1006 | 1006 | 5756 | 220378 | 4234 |
| 8 | 60 | 782 | 782 | 3436 | 163254 | 3436 |
| **Total** | **841** | **9012** | **9012** | **64073** | **1762434** | **48778** |

## Commentary Field Coverage

| Thirumurai | Commentaries | Has pozhppurai | Empty pozhppurai | Pozhppurai coverage | Has kurippurai | Empty kurippurai | Kurippurai coverage |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 1469 | 1163 | 306 | 79.17% | 1169 | 300 | 79.58% |
| 2 | 1331 | 1327 | 4 | 99.70% | 1328 | 3 | 99.77% |
| 3 | 1358 | 1341 | 17 | 98.75% | 1335 | 23 | 98.31% |
| 4 | 1070 | 1068 | 2 | 99.81% | 1063 | 7 | 99.35% |
| 5 | 1015 | 1007 | 8 | 99.21% | 1013 | 2 | 99.80% |
| 6 | 981 | 980 | 1 | 99.90% | 979 | 2 | 99.80% |
| 7 | 1006 | 583 | 423 | 57.95% | 939 | 67 | 93.34% |
| 8 | 782 | 0 | 782 | 0.00% | 0 | 782 | 0.00% |
| **Total** | **9012** | **7469** | **1543** | **82.88%** | **7826** | **1186** | **86.84%** |

Important interpretation:

- Thirumurai 2 is the strongest fully audited subset from earlier release work.
- Thirumurai 8 has no pozhppurai or kurippurai coverage in the normalized commentary table; this should be described as a source/data availability or parser-coverage limitation, not as a successful commentary extraction.
- Thirumurai 7 has lower pozhppurai coverage than books 2-6.

## Normalization Integrity

Normalization version:

- `thevaram-normalized-v1`

Normalization behavior:

- Raw and parsed source tables were not modified.
- Existing line boundaries were preserved because they encode poem and commentary structure.
- Unicode normalization, unsafe invisible/control character removal, repeated-space collapse, line-edge trimming, and span offset recomputation were applied.

Line preservation:

| Field group | Before newline count | After newline count |
| --- | ---: | ---: |
| `paadal_text` | 39766 | 39766 |
| `commentary_text` | 0 | 0 |

Changed fields:

- `paadalgal.local_song_no`: 2 rows
- `paadalgal.paadal_text`: 3 rows
- `paadalgal.tokenized_paadal`: 3 rows
- `commentaries.kurippurai`: 8 rows
- `text_spans`: 64073 rows rebuilt from normalized text

## Paadal-Pozhippurai Linking Statistics

Linking output:

- `data/processed/thevaram_pozhippurai_links/v4/paadal_pozhippurai_links_v4_full.jsonl`

Overall:

| Metric | Value |
| --- | ---: |
| Span-level link records | 49019 |
| Paadalgal covered | 9012 |
| High confidence | 975 (1.99%) |
| Medium confidence | 10316 (21.04%) |
| Low confidence | 30859 (62.95%) |
| No-link | 6869 (14.01%) |
| Manual-review-required rows | 37830 |

Main diagnostic groups:

| Diagnostic group | Rows |
| --- | ---: |
| `ambiguous_multiple_targets` | 20003 |
| `medium_similarity` | 10141 |
| `missing_or_unlinked` | 6869 |
| `no_shared_entity_anchor` | 4259 |
| `order_only_weak_match` | 3692 |
| `low_lexical_overlap` | 2647 |
| `strong_link` | 809 |
| `overlaps_reviewed_split_or_gold` | 240 |
| `focused_qa_rule_match` | 171 |
| `weak_similarity` | 120 |
| `v4_gold_match` | 68 |

Interpretation for the paper:

- Do not present the linker as a final gold alignment.
- Present it as an evidence layer and quality-diagnostic system for future annotation.
- Emphasize that low lexical overlap is expected when poetic text is explained through prose commentary.

## Entity Annotation Layer

Annotation report:

- `reports/thevaram-entity-annotation-v3-report.md`

Summary:

| Metric | Count |
| --- | ---: |
| Entity registry rows | 624 |
| Entity aliases | 823 |
| Seed terms loaded | 823 |
| Entity mentions | 107761 |
| Suppressed same-type overlapping candidates | 12578 |
| Invalid bounds | 0 |
| Span text mismatches | 0 |
| Duplicate mention IDs | 0 |
| Cross-type overlap pairs | 30710 |

Top entity types:

| Entity type | Mentions |
| --- | ---: |
| `NATURE` | 23831 |
| `BODY_PART` | 17304 |
| `SACRED_OBJECT` | 16191 |
| `DEITY` | 13847 |
| `THEOLOGICAL_CONCEPT` | 11238 |
| `TEMPLE` | 4036 |
| `WEAPON` | 3772 |

Review interpretation:

- The entity layer is deterministic and useful for retrieval and diagnostics.
- It should not yet be described as expert-validated scholarly annotation.
- Context-only and ambiguous mentions require further human review before literary claims are made from them.

## Strongest Audited Subset

Irandaam Thirumurai v1 remains the strongest frozen release subset.

Key statistics:

| Metric | Value |
| --- | ---: |
| Hymns | 122 |
| Verse records | 1331 |
| Schema violations | 0 |
| Failed hymns | 0 |
| Duplicate `song_no` values | 0 |
| Missing verse text records | 0 |
| Sampled coverage | 100% |
| Partial commentary records | 7 |

Recommended paper wording:

> The full Thevaram 1-8 corpus currently provides broad normalized table coverage, while Irandaam Thirumurai v1 serves as the most mature audited release subset.

