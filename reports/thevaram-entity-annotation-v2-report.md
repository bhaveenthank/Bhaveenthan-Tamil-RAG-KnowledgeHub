# Thevaram Entity Annotation Report

## Summary

- Schema version: `thevaram-entity-annotation-v2`
- Output root: `data/processed/thevaram_entity_annotations_v2`
- Entity registry rows: `195`
- Entity aliases: `237`
- Seed terms loaded: `237`
- Entity mentions: `48962`
- Suppressed same-type overlapping candidates: `1300`
- Validation status: `VALID`
- Invalid bounds: `0`
- Span text mismatches: `0`
- Duplicate mention IDs: `0`
- Cross-type overlap pairs: `7992`

Cross-type overlaps are allowed for v2 when a poetic span is legitimately both, for example, `NATURE` and `SACRED_OBJECT`.

## Entity Type Coverage

| Entity type | Mentions | Seed terms |
| --- | ---: | ---: |
| `ACTION` | 121 | 37 |
| `BODY_PART` | 14374 | 28 |
| `DEITY` | 1303 | 52 |
| `NATURE` | 15330 | 41 |
| `SACRED_OBJECT` | 11829 | 44 |
| `THEOLOGICAL_CONCEPT` | 6005 | 35 |

## Field Coverage

| Field | Mentions |
| --- | ---: |
| `commentaries.kurippurai` | 17387 |
| `commentaries.pozhppurai` | 14980 |
| `paadalgal.paadal_text` | 16595 |

## Manual Review Decisions Applied

| Decision | Mentions |
| --- | ---: |
| `AMBIGUOUS_REVIEW` | 4691 |
| `CONTEXT_ONLY` | 20385 |
| `KEEP` | 23886 |

## Review Status

| Status | Mentions |
| --- | ---: |
| `ambiguous_review` | 4691 |
| `auto_accepted` | 23886 |
| `context_supported` | 11128 |
| `needs_context_review` | 9257 |

## Suppressed Candidates

| Reason | Candidates |
| --- | ---: |
| `review_decision_exclude` | 359 |
| `same_type_overlap` | 941 |

## Sample Mentions

- `DEITY` `நான்முகனும்` -> `பிரமன்/நான்முகன்` in `thirumurai_01_paadal_1000_commentary` `pozhppurai` `0:11` status=`auto_accepted` decision=`KEEP`
- `DEITY` `மாலும்` -> `விஷ்ணு/திருமால்` in `thirumurai_01_paadal_1000_commentary` `pozhppurai` `16:22` status=`auto_accepted` decision=`KEEP`
- `BODY_PART` `அடி` -> `அடி` in `thirumurai_01_paadal_1000_commentary` `pozhppurai` `23:26` status=`context_supported` decision=`CONTEXT_ONLY`
- `BODY_PART` `தலையை` -> `தலையை` in `thirumurai_01_paadal_1001_commentary` `kurippurai` `31:36` status=`context_supported` decision=`CONTEXT_ONLY`
- `SACRED_OBJECT` `மழு` -> `மழு` in `thirumurai_01_paadal_1001_commentary` `pozhppurai` `99:102` status=`auto_accepted` decision=`KEEP`
- `BODY_PART` `அடி` -> `அடி` in `thirumurai_01_paadal_1001_commentary` `pozhppurai` `132:135` status=`needs_context_review` decision=`CONTEXT_ONLY`
- `THEOLOGICAL_CONCEPT` `பதி` -> `பதி` in `thirumurai_01_paadal_1002_commentary` `pozhppurai` `9:12` status=`ambiguous_review` decision=`AMBIGUOUS_REVIEW`
- `THEOLOGICAL_CONCEPT` `பதி` -> `பதி` in `thirumurai_01_paadal_1002_commentary` `pozhppurai` `25:28` status=`ambiguous_review` decision=`AMBIGUOUS_REVIEW`
- `NATURE` `நீர்` -> `நீர்` in `thirumurai_01_paadal_1004_commentary` `pozhppurai` `0:4` status=`context_supported` decision=`CONTEXT_ONLY`
- `NATURE` `நீர்` -> `நீர்` in `thirumurai_01_paadal_1005_commentary` `pozhppurai` `50:54` status=`context_supported` decision=`CONTEXT_ONLY`
- `BODY_PART` `மெய்` -> `மெய்` in `thirumurai_01_paadal_1005_commentary` `pozhppurai` `78:82` status=`ambiguous_review` decision=`AMBIGUOUS_REVIEW`
- `NATURE` `நீர்` -> `நீர்` in `thirumurai_01_paadal_1006_commentary` `pozhppurai` `23:27` status=`context_supported` decision=`CONTEXT_ONLY`
- `NATURE` `நீர்` -> `நீர்` in `thirumurai_01_paadal_1008_commentary` `pozhppurai` `58:62` status=`context_supported` decision=`CONTEXT_ONLY`
- `SACRED_OBJECT` `விடை` -> `விடை` in `thirumurai_01_paadal_1009_commentary` `pozhppurai` `18:22` status=`context_supported` decision=`CONTEXT_ONLY`
- `BODY_PART` `சடை` -> `சடை` in `thirumurai_01_paadal_100_commentary` `kurippurai` `254:257` status=`auto_accepted` decision=`KEEP`
- `BODY_PART` `சடை` -> `சடை` in `thirumurai_01_paadal_100_commentary` `pozhppurai` `167:170` status=`auto_accepted` decision=`KEEP`
- `DEITY` `மாலும்` -> `விஷ்ணு/திருமால்` in `thirumurai_01_paadal_1011_commentary` `kurippurai` `16:22` status=`auto_accepted` decision=`KEEP`
- `NATURE` `நீர்` -> `நீர்` in `thirumurai_01_paadal_1012_commentary` `pozhppurai` `115:119` status=`context_supported` decision=`CONTEXT_ONLY`
- `THEOLOGICAL_CONCEPT` `பதி` -> `பதி` in `thirumurai_01_paadal_1013_commentary` `pozhppurai` `77:80` status=`ambiguous_review` decision=`AMBIGUOUS_REVIEW`
- `BODY_PART` `மெய்` -> `மெய்` in `thirumurai_01_paadal_1015_commentary` `pozhppurai` `69:73` status=`ambiguous_review` decision=`AMBIGUOUS_REVIEW`

## Review Notes

- This is a deterministic seed-lexicon annotation pass based on the six pilot TSV datasets and the manual QA decision CSVs.
- `review_status` records whether each mention is `auto_accepted`, `context_supported`, `needs_context_review`, `ambiguous_review`, or `unreviewed_seed`.
- Exact offsets are calculated against `data/processed/thevaram_normalized`.
- Same-type nested overlaps are suppressed by preferring the longer phrase.
- Cross-type overlaps are retained because the pilot data intentionally uses multi-category poetic imagery.
