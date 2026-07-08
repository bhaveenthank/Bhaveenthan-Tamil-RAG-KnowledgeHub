# Thevaram Paadal-Pozhippurai Linker v4 Statistical Analysis

Generated from `data/processed/thevaram_pozhippurai_links/v4/paadal_pozhippurai_links_v4_full.jsonl`.

## Executive Summary

- Total span-level link records: `49019` across `9012` paadalgal.
- High confidence: `975` (1.99%).
- Medium confidence: `10316` (21.04%).
- Low confidence: `30859` (62.95%).
- No-link: `6869` (14.01%).
- Manual-review-required rows: `37830`.

The main reason confidence stays low is not one single issue. It is a combination of:

1. many rows with ambiguous target choices,
2. many rows with no shared entity anchor,
3. many rows with weak lexical overlap between poetic paadal and prose explanation,
4. no-link rows caused by missing/empty pozhppurai coverage records,
5. short or numeric-only source spans that should probably be filtered or handled separately.

## Confidence Numeric Feature Summary

| confidence | rows | pct | avg_score | median_score | avg_source_tokens | avg_target_tokens | avg_token_overlap | avg_char_overlap | avg_containment_score | avg_source_entities | avg_target_entities | avg_shared_entities | manual_review_rows | numeric_source_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| high | 975 | 1.99 | 0.6352 | 0.5731 | 4.7969 | 8.2164 | 0.2516 | 0.3289 | 0.5925 | 1.0359 | 1.0708 | 0.9795 | 27 | 0 |
| medium | 10316 | 21.04 | 0.3758 | 0.3603 | 5.1007 | 13.4148 | 0.0881 | 0.1589 | 0.4416 | 0.6872 | 1.088 | 0.5527 | 75 | 2 |
| low | 30859 | 62.95 | 0.2286 | 0.2186 | 4.7015 | 14.0029 | 0.0186 | 0.0753 | 0.1352 | 0.1962 | 0.7435 | 0.0216 | 30859 | 1333 |
| no_link | 6869 | 14.01 | 0.0 | 0.0 | 6.4385 | 0.0 | 0.0 | 0.0 | 0.0 | 0.3771 | 0.0 | 0.0 | 6869 | 17 |

## Confidence By Diagnostic Group

| diagnostic_group | total | high | medium | low | no_link | high_pct | low_pct | no_link_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ambiguous_multiple_targets | 20003 | 0 | 0 | 20003 | 0 | 0.0 | 100.0 | 0.0 |
| medium_similarity | 10141 | 0 | 10141 | 0 | 0 | 0.0 | 0.0 | 0.0 |
| missing_or_unlinked | 6869 | 0 | 0 | 0 | 6869 | 0.0 | 0.0 | 100.0 |
| no_shared_entity_anchor | 4259 | 0 | 0 | 4259 | 0 | 0.0 | 100.0 | 0.0 |
| order_only_weak_match | 3692 | 0 | 0 | 3692 | 0 | 0.0 | 100.0 | 0.0 |
| low_lexical_overlap | 2647 | 0 | 0 | 2647 | 0 | 0.0 | 100.0 | 0.0 |
| strong_link | 809 | 809 | 0 | 0 | 0 | 100.0 | 0.0 | 0.0 |
| overlaps_reviewed_split_or_gold | 240 | 27 | 75 | 138 | 0 | 11.25 | 57.5 | 0.0 |
| focused_qa_rule_match | 171 | 78 | 93 | 0 | 0 | 45.61 | 0.0 | 0.0 |
| weak_similarity | 120 | 0 | 0 | 120 | 0 | 0.0 | 100.0 | 0.0 |
| v4_gold_match | 68 | 61 | 7 | 0 | 0 | 89.71 | 0.0 | 0.0 |

## Confidence By Score Bin

| score_bin | total | high | medium | low | no_link | high_pct | medium_pct | low_pct | no_link_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.21-0.32 | 25941 | 0 | 2400 | 23541 | 0 | 0.0 | 9.25 | 90.75 | 0.0 |
| 0.33-0.52 | 7814 | 0 | 7814 | 0 | 0 | 0.0 | 100.0 | 0.0 | 0.0 |
| 0.01-0.20 | 7318 | 0 | 0 | 7318 | 0 | 0.0 | 0.0 | 100.0 | 0.0 |
| 0 | 6869 | 0 | 0 | 0 | 6869 | 0.0 | 0.0 | 0.0 | 100.0 |
| 0.53-0.75 | 794 | 794 | 0 | 0 | 0 | 100.0 | 0.0 | 0.0 | 0.0 |
| 0.76+ | 283 | 181 | 102 | 0 | 0 | 63.96 | 36.04 | 0.0 | 0.0 |

## Confidence By Source Shape

| source_shape | total | high | medium | low | no_link | high_pct | medium_pct | low_pct | no_link_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| punctuated_phrase | 26459 | 536 | 5908 | 15533 | 4482 | 2.03 | 22.33 | 58.71 | 16.94 |
| ordinary_phrase | 14347 | 338 | 3564 | 9112 | 1333 | 2.36 | 24.84 | 63.51 | 9.29 |
| single_token | 4172 | 49 | 349 | 3572 | 202 | 1.17 | 8.37 | 85.62 | 4.84 |
| question | 1353 | 38 | 210 | 629 | 476 | 2.81 | 15.52 | 46.49 | 35.18 |
| numeric_only | 1352 | 0 | 2 | 1333 | 17 | 0.0 | 0.15 | 98.59 | 1.26 |
| long_line | 1336 | 14 | 283 | 680 | 359 | 1.05 | 21.18 | 50.9 | 26.87 |

## Confidence By Token Overlap

| token_overlap_bin | total | high | medium | low | no_link | high_pct | medium_pct | low_pct | no_link_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 32747 | 119 | 3361 | 22398 | 6869 | 0.36 | 10.26 | 68.4 | 20.98 |
| 0.06-0.15 | 8496 | 299 | 3466 | 4731 | 0 | 3.52 | 40.8 | 55.69 | 0.0 |
| 0.01-0.05 | 4791 | 29 | 1317 | 3445 | 0 | 0.61 | 27.49 | 71.91 | 0.0 |
| 0.16-0.30 | 2267 | 256 | 1737 | 274 | 0 | 11.29 | 76.62 | 12.09 | 0.0 |
| 0.31-0.50 | 570 | 154 | 405 | 11 | 0 | 27.02 | 71.05 | 1.93 | 0.0 |
| 0.51+ | 148 | 118 | 30 | 0 | 0 | 79.73 | 20.27 | 0.0 | 0.0 |

## Confidence By Shared Entity Count

| shared_entity_bin | total | high | medium | low | no_link | high_pct | medium_pct | low_pct | no_link_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 43368 | 239 | 5997 | 30263 | 6869 | 0.55 | 13.83 | 69.78 | 15.84 |
| 1 | 4314 | 555 | 3224 | 535 | 0 | 12.87 | 74.73 | 12.4 | 0.0 |
| 2+ | 1337 | 181 | 1095 | 61 | 0 | 13.54 | 81.9 | 4.56 | 0.0 |

## Confidence By Source Token Size

| source_token_bin | total | high | medium | low | no_link | high_pct | medium_pct | low_pct | no_link_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4-6 | 25772 | 633 | 6272 | 15953 | 2914 | 2.46 | 24.34 | 61.9 | 11.31 |
| 7-10 | 11849 | 135 | 2153 | 6337 | 3224 | 1.14 | 18.17 | 53.48 | 27.21 |
| 1 | 5524 | 49 | 351 | 4905 | 219 | 0.89 | 6.35 | 88.79 | 3.96 |
| 2-3 | 5447 | 156 | 1480 | 3492 | 319 | 2.86 | 27.17 | 64.11 | 5.86 |
| 11+ | 427 | 2 | 60 | 172 | 193 | 0.47 | 14.05 | 40.28 | 45.2 |

## Confidence By Relationship Type

| relationship_type | total | high | medium | low | no_link | high_pct | medium_pct | low_pct | no_link_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| explains_phrase | 11158 | 247 | 2771 | 8140 | 0 | 2.21 | 24.83 | 72.95 | 0.0 |
| interprets_image | 10072 | 204 | 2561 | 7307 | 0 | 2.03 | 25.43 | 72.55 | 0.0 |
| theological_explanation | 9638 | 245 | 2507 | 6886 | 0 | 2.54 | 26.01 | 71.45 | 0.0 |
| describes_entity | 7070 | 184 | 1754 | 5132 | 0 | 2.6 | 24.81 | 72.59 | 0.0 |
| unlinked | 6869 | 0 | 0 | 0 | 6869 | 0.0 | 0.0 | 0.0 | 100.0 |
| glosses_word | 3144 | 82 | 524 | 2538 | 0 | 2.61 | 16.67 | 80.73 | 0.0 |
| explains_line | 1068 | 13 | 199 | 856 | 0 | 1.22 | 18.63 | 80.15 | 0.0 |

## Confidence By Method

| method | total | high | medium | low | no_link | high_pct | medium_pct | low_pct | no_link_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| v3_baseline_carried_forward_v4 | 48951 | 914 | 10309 | 30859 | 6869 | 1.87 | 21.06 | 63.04 | 14.03 |
| v4_gold_seed_exact_or_morphology_match | 68 | 61 | 7 | 0 | 0 | 89.71 | 10.29 | 0.0 | 0.0 |

## Confidence By Thirumurai

| thirumurai_no | total | high | medium | low | no_link | high_pct | medium_pct | low_pct | no_link_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | 9183 | 80 | 1599 | 7344 | 160 | 0.87 | 17.41 | 79.97 | 1.74 |
| 1 | 8139 | 167 | 1815 | 4768 | 1389 | 2.05 | 22.3 | 58.58 | 17.07 |
| 6 | 7881 | 281 | 2026 | 5566 | 8 | 3.57 | 25.71 | 70.63 | 0.1 |
| 2 | 7761 | 158 | 1983 | 5595 | 25 | 2.04 | 25.55 | 72.09 | 0.32 |
| 4 | 4304 | 64 | 898 | 3334 | 8 | 1.49 | 20.86 | 77.46 | 0.19 |
| 7 | 4241 | 32 | 524 | 1874 | 1811 | 0.75 | 12.36 | 44.19 | 42.7 |
| 5 | 4074 | 193 | 1471 | 2378 | 32 | 4.74 | 36.11 | 58.37 | 0.79 |
| 8 | 3436 | 0 | 0 | 0 | 3436 | 0.0 | 0.0 | 0.0 | 100.0 |


## Commentary Coverage By Thirumurai

This separates linker weakness from missing commentary data. If `pozhppurai` is empty, the linker cannot create a pozhppurai target.

| thirumurai_no | commentaries | has_pozhppurai | empty_pozhppurai | pozhppurai_coverage_pct | has_kurippurai | empty_kurippurai | kurippurai_coverage_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1469 | 1163 | 306 | 79.17 | 1169 | 300 | 79.58 |
| 2 | 1331 | 1327 | 4 | 99.7 | 1328 | 3 | 99.77 |
| 3 | 1358 | 1341 | 17 | 98.75 | 1335 | 23 | 98.31 |
| 4 | 1070 | 1068 | 2 | 99.81 | 1063 | 7 | 99.35 |
| 5 | 1015 | 1007 | 8 | 99.21 | 1013 | 2 | 99.8 |
| 6 | 981 | 980 | 1 | 99.9 | 979 | 2 | 99.8 |
| 7 | 1006 | 583 | 423 | 57.95 | 939 | 67 | 93.34 |
| 8 | 782 | 0 | 782 | 0.0 | 0 | 782 | 0.0 |

Key reading: Thirumurai 8 currently has `0%` pozhppurai and `0%` kurippurai coverage in the normalized commentary table, so its no-link rows are data availability/parse coverage records, not ordinary linker mistakes. Thirumurai 7 also has lower pozhppurai coverage than the other books.

## Top Low-Confidence Source Patterns

These are important because repeated weak source patterns can reveal parser/linker noise.

| text | rows |
| --- | --- |
| 2 | 125 |
| 4 | 125 |
| 3 | 123 |
| 1 | 122 |
| 9 | 122 |
| 8 | 121 |
| 11 | 120 |
| 6 | 119 |
| 5 | 118 |
| 10 | 118 |
| 7 | 116 |
| கோயில் | 27 |
| ஆமே. | 27 |
| ஆம் | 23 |
| அமர்ந்தாரே. | 23 |

## Main Heuristic Findings

### 1. Ambiguity is the biggest low-confidence driver
Rows tagged `ambiguous_multiple_targets` dominate the weak area. This means the best candidate and second-best candidate are too close, so the linker cannot confidently choose one pozhppurai span.

Fix direction: use reviewed examples to learn tie-breakers: local commentary order, source phrase type, deity/object anchor, and phrase-level split rules.

### 2. Entity anchors matter
Rows with shared entities are much easier to trust. Rows with `shared_entity_bin=0` contain most of the hard cases.

Fix direction: improve entity annotations and add cross-field aliases, especially deity names, sacred objects, places, nature images, and theological terms.

### 3. Very short or numeric-only source spans are suspicious
Numeric-only source spans are almost certainly not meaningful paadal phrases. Single-token spans can be valid, but they need stronger evidence than ordinary lines.

Fix direction: filter numeric-only source rows from positive training and treat single-token links as high only if exact/gloss/entity evidence exists.

### 4. Low lexical overlap is expected in poetic commentary
Some correct links will have low token overlap because pozhppurai explains meaning rather than repeating words.

Fix direction: add Tamil morphology, synonym/alias tables, and reviewed metaphor/action/theology patterns instead of relying only on word overlap.

### 5. No-link is partly a data availability problem
No-link rows are not always linker failure. Many are coverage records where pozhppurai text is missing or empty.

Fix direction: separate `true_no_link_due_to_missing_commentary` from `linker_failed_to_find_target` before judging quality.

## Recommended Next Work

1. Filter or quarantine numeric-only source spans.
2. Build a v5 review pack from the biggest weak groups: `ambiguous_multiple_targets`, `no_shared_entity_anchor`, `low_lexical_overlap`, and single-token links.
3. Improve pozhppurai segmentation, because target ambiguity is a major issue.
4. Add learned confidence calibration from manually reviewed rows instead of relying only on fixed score thresholds.
5. Expand entity alias coverage and use shared entity/type overlap as a stronger confidence signal.

## Generated Files

- `data/processed/thevaram_pozhippurai_links/v4/statistics/confidence_numeric_feature_summary.csv`
- `data/processed/thevaram_pozhippurai_links/v4/statistics/confidence_by_diagnostic_group.csv`
- `data/processed/thevaram_pozhippurai_links/v4/statistics/confidence_by_score_bin.csv`
- `data/processed/thevaram_pozhippurai_links/v4/statistics/confidence_by_source_shape.csv`
- `data/processed/thevaram_pozhippurai_links/v4/statistics/confidence_by_token_overlap_bin.csv`
- `data/processed/thevaram_pozhippurai_links/v4/statistics/confidence_by_shared_entity_bin.csv`
- `data/processed/thevaram_pozhippurai_links/v4/statistics/low_medium_no_link_problem_matrix.csv`
- `data/processed/thevaram_pozhippurai_links/v4/statistics/top_patterns_by_confidence.csv`
- `data/processed/thevaram_pozhippurai_links/v4/statistics/representative_samples_for_review.csv`
- `data/processed/thevaram_pozhippurai_links/v4/statistics/paadal_level_confidence_concentration.csv`

- `data/processed/thevaram_pozhippurai_links/v4/statistics/commentary_coverage_by_thirumurai.csv`
