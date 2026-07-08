# Thevaram Entity Annotation Report

## Summary

- Schema version: `thevaram-entity-annotation-v1`
- Output root: `data/processed/thevaram_entity_annotations`
- Entity registry rows: `195`
- Entity aliases: `237`
- Seed terms loaded: `237`
- Entity mentions: `62856`
- Suppressed same-type overlapping candidates: `941`
- Validation status: `VALID`
- Invalid bounds: `0`
- Span text mismatches: `0`
- Duplicate mention IDs: `0`
- Cross-type overlap pairs: `11275`

Cross-type overlaps are allowed for v1 when a poetic span is legitimately both, for example, `NATURE` and `SACRED_OBJECT`.

## Entity Type Coverage

| Entity type | Mentions | Seed terms |
| --- | ---: | ---: |
| `ACTION` | 121 | 37 |
| `BODY_PART` | 28268 | 28 |
| `DEITY` | 1303 | 52 |
| `NATURE` | 15330 | 41 |
| `SACRED_OBJECT` | 11829 | 44 |
| `THEOLOGICAL_CONCEPT` | 6005 | 35 |

## Field Coverage

| Field | Mentions |
| --- | ---: |
| `commentaries.kurippurai` | 23548 |
| `commentaries.pozhppurai` | 19184 |
| `paadalgal.paadal_text` | 20124 |

## Sample Mentions

- `DEITY` `நான்முகனும்` -> `பிரமன்/நான்முகன்` in `thirumurai_01_paadal_1000_commentary` `pozhppurai` `0:11`
- `DEITY` `மாலும்` -> `விஷ்ணு/திருமால்` in `thirumurai_01_paadal_1000_commentary` `pozhppurai` `16:22`
- `BODY_PART` `அடி` -> `அடி` in `thirumurai_01_paadal_1000_commentary` `pozhppurai` `23:26`
- `BODY_PART` `தலையை` -> `தலையை` in `thirumurai_01_paadal_1001_commentary` `kurippurai` `31:36`
- `SACRED_OBJECT` `மழு` -> `மழு` in `thirumurai_01_paadal_1001_commentary` `pozhppurai` `99:102`
- `BODY_PART` `அடி` -> `அடி` in `thirumurai_01_paadal_1001_commentary` `pozhppurai` `132:135`
- `THEOLOGICAL_CONCEPT` `பதி` -> `பதி` in `thirumurai_01_paadal_1002_commentary` `pozhppurai` `9:12`
- `THEOLOGICAL_CONCEPT` `பதி` -> `பதி` in `thirumurai_01_paadal_1002_commentary` `pozhppurai` `25:28`
- `NATURE` `நீர்` -> `நீர்` in `thirumurai_01_paadal_1004_commentary` `pozhppurai` `0:4`
- `NATURE` `நீர்` -> `நீர்` in `thirumurai_01_paadal_1005_commentary` `pozhppurai` `50:54`
- `BODY_PART` `கை` -> `கை` in `thirumurai_01_paadal_1005_commentary` `pozhppurai` `58:60`
- `BODY_PART` `மெய்` -> `மெய்` in `thirumurai_01_paadal_1005_commentary` `pozhppurai` `78:82`
- `BODY_PART` `கை` -> `கை` in `thirumurai_01_paadal_1005_commentary` `pozhppurai` `96:98`
- `NATURE` `நீர்` -> `நீர்` in `thirumurai_01_paadal_1006_commentary` `pozhppurai` `23:27`
- `NATURE` `நீர்` -> `நீர்` in `thirumurai_01_paadal_1008_commentary` `pozhppurai` `58:62`
- `SACRED_OBJECT` `விடை` -> `விடை` in `thirumurai_01_paadal_1009_commentary` `pozhppurai` `18:22`
- `BODY_PART` `சடை` -> `சடை` in `thirumurai_01_paadal_100_commentary` `kurippurai` `254:257`
- `BODY_PART` `சடை` -> `சடை` in `thirumurai_01_paadal_100_commentary` `pozhppurai` `167:170`
- `DEITY` `மாலும்` -> `விஷ்ணு/திருமால்` in `thirumurai_01_paadal_1011_commentary` `kurippurai` `16:22`
- `NATURE` `நீர்` -> `நீர்` in `thirumurai_01_paadal_1012_commentary` `pozhppurai` `115:119`

## Review Notes

- This is a deterministic seed-lexicon annotation pass based on the six pilot TSV datasets.
- `review_status` is `pending`; this is intentionally ready for human sampling, not a final gold corpus.
- Exact offsets are calculated against `data/processed/thevaram_normalized`.
- Same-type nested overlaps are suppressed by preferring the longer phrase.
- Cross-type overlaps are retained because the pilot data intentionally uses multi-category poetic imagery.
