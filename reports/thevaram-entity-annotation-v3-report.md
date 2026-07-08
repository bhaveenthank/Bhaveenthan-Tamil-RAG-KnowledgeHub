# Thevaram Entity Annotation v3 Report

## Summary

- Schema version: `thevaram-entity-annotation-v3`
- Output root: `data/processed/thevaram_entity_annotations_v3`
- Entity registry rows: `624`
- Entity aliases: `823`
- Seed terms loaded: `823`
- Entity mentions: `107761`
- Suppressed same-type overlapping candidates: `12578`
- Validation status: `VALID`
- Invalid bounds: `0`
- Span text mismatches: `0`
- Duplicate mention IDs: `0`
- Cross-type overlap pairs: `30710`

Cross-type overlaps are allowed for v2 when a poetic span is legitimately both, for example, `NATURE` and `SACRED_OBJECT`.

## Entity Type Coverage

| Entity type | Mentions | Seed terms |
| --- | ---: | ---: |
| `ACTION` | 121 | 37 |
| `BODY_PART` | 17304 | 35 |
| `DEITY` | 13847 | 95 |
| `DIVINE_EPITHET` | 347 | 7 |
| `DIVINE_FORM` | 4 | 5 |
| `FESTIVAL` | 33 | 3 |
| `ICONOGRAPHIC_FEATURE` | 2373 | 5 |
| `MUSICAL_INSTRUMENT` | 741 | 5 |
| `MYTHOLOGICAL_CHARACTER` | 1556 | 13 |
| `MYTHOLOGICAL_EVENT` | 398 | 21 |
| `NATURE` | 23831 | 47 |
| `RELATIONSHIP` | 2000 | 6 |
| `RITUAL` | 1624 | 6 |
| `SACRED_FLOWER` | 1062 | 5 |
| `SACRED_MOUNTAIN` | 1160 | 4 |
| `SACRED_OBJECT` | 16191 | 57 |
| `SACRED_RIVER` | 2303 | 3 |
| `SACRED_TREE` | 1828 | 5 |
| `SAINT` | 949 | 7 |
| `TEMPLE` | 4036 | 400 |
| `TEMPLE_ARCHITECTURE` | 1043 | 6 |
| `THEOLOGICAL_CONCEPT` | 11238 | 46 |
| `WEAPON` | 3772 | 5 |

## Entity Subtype Coverage

| Entity subtype | Mentions |
| --- | ---: |
| `ACTION:unspecified` | 121 |
| `BODY_PART:divine_body_part` | 3276 |
| `BODY_PART:unspecified` | 14028 |
| `DEITY:deity` | 3883 |
| `DEITY:goddess` | 2031 |
| `DEITY:principal_deity` | 6630 |
| `DEITY:unspecified` | 1303 |
| `DIVINE_EPITHET:shiva_epithet` | 347 |
| `DIVINE_FORM:shiva_form` | 4 |
| `FESTIVAL:festival` | 33 |
| `ICONOGRAPHIC_FEATURE:iconographic_feature` | 2373 |
| `MUSICAL_INSTRUMENT:musical_instrument` | 741 |
| `MYTHOLOGICAL_CHARACTER:death_deity` | 582 |
| `MYTHOLOGICAL_CHARACTER:mythic_figure` | 974 |
| `MYTHOLOGICAL_EVENT:mythological_event` | 398 |
| `NATURE:animal` | 8501 |
| `NATURE:unspecified` | 15330 |
| `RELATIONSHIP:relationship_role` | 2000 |
| `RITUAL:ritual` | 1624 |
| `SACRED_FLOWER:sacred_flower` | 1062 |
| `SACRED_MOUNTAIN:sacred_mountain` | 1160 |
| `SACRED_OBJECT:ornament_or_symbol` | 2711 |
| `SACRED_OBJECT:unspecified` | 9708 |
| `SACRED_OBJECT:weapon` | 3772 |
| `SACRED_RIVER:sacred_river` | 2303 |
| `SACRED_TREE:sacred_tree` | 1828 |
| `SAINT:saint` | 949 |
| `TEMPLE:paadapatta_thalam` | 4036 |
| `TEMPLE_ARCHITECTURE:temple_architecture` | 1043 |
| `THEOLOGICAL_CONCEPT:saiva_siddhanta_concept` | 7748 |
| `THEOLOGICAL_CONCEPT:unspecified` | 3490 |
| `WEAPON:weapon` | 3772 |

## Field Coverage

| Field | Mentions |
| --- | ---: |
| `commentaries.kurippurai` | 39618 |
| `commentaries.pozhppurai` | 37803 |
| `paadalgal.paadal_text` | 30340 |

## Manual Review Decisions Applied

| Decision | Mentions |
| --- | ---: |
| `AMBIGUOUS_REVIEW` | 2176 |
| `CONTEXT_ONLY` | 31958 |
| `KEEP` | 73627 |

## Review Status

| Status | Mentions |
| --- | ---: |
| `ambiguous_review` | 2176 |
| `auto_accepted` | 73627 |
| `context_supported` | 20582 |
| `needs_context_review` | 11376 |

## Suppressed Candidates

| Reason | Candidates |
| --- | ---: |
| `review_decision_exclude` | 359 |
| `same_type_overlap` | 12219 |

## Sample Mentions

- `DEITY` `நான்முகனும்` -> `பிரமன்/நான்முகன்` in `thirumurai_01_paadal_1000_commentary` `pozhppurai` `0:11` status=`auto_accepted` decision=`KEEP`
- `DEITY` `மாலும்` -> `விஷ்ணு/திருமால்` in `thirumurai_01_paadal_1000_commentary` `pozhppurai` `16:22` status=`auto_accepted` decision=`KEEP`
- `BODY_PART` `அடி` -> `அடி` in `thirumurai_01_paadal_1000_commentary` `pozhppurai` `23:26` status=`context_supported` decision=`CONTEXT_ONLY`
- `TEMPLE` `திருவீழிமிழலை` -> `திருவீழிமிழலை` in `thirumurai_01_paadal_1000_commentary` `pozhppurai` `101:114` status=`auto_accepted` decision=`KEEP`
- `BODY_PART` `தலையை` -> `தலையை` in `thirumurai_01_paadal_1001_commentary` `kurippurai` `31:36` status=`context_supported` decision=`CONTEXT_ONLY`
- `SACRED_OBJECT` `மழு` -> `திருவாயுதங்கள்` in `thirumurai_01_paadal_1001_commentary` `pozhppurai` `99:102` status=`auto_accepted` decision=`KEEP`
- `WEAPON` `மழு` -> `ஆயுதங்கள்` in `thirumurai_01_paadal_1001_commentary` `pozhppurai` `99:102` status=`auto_accepted` decision=`KEEP`
- `TEMPLE` `திருவீழிமிழலை` -> `திருவீழிமிழலை` in `thirumurai_01_paadal_1001_commentary` `pozhppurai` `105:118` status=`auto_accepted` decision=`KEEP`
- `BODY_PART` `அடி` -> `அடி` in `thirumurai_01_paadal_1001_commentary` `pozhppurai` `132:135` status=`needs_context_review` decision=`CONTEXT_ONLY`
- `THEOLOGICAL_CONCEPT` `வினை` -> `சைவ சித்தாந்தக் கருத்துகள்` in `thirumurai_01_paadal_1002_commentary` `kurippurai` `85:89` status=`context_supported` decision=`CONTEXT_ONLY`
- `THEOLOGICAL_CONCEPT` `பதி` -> `சைவ சித்தாந்தக் கருத்துகள்` in `thirumurai_01_paadal_1002_commentary` `pozhppurai` `9:12` status=`needs_context_review` decision=`CONTEXT_ONLY`
- `TEMPLE` `சீகாழி` -> `சீகாழி` in `thirumurai_01_paadal_1002_commentary` `pozhppurai` `16:22` status=`auto_accepted` decision=`KEEP`
- `THEOLOGICAL_CONCEPT` `பதி` -> `சைவ சித்தாந்தக் கருத்துகள்` in `thirumurai_01_paadal_1002_commentary` `pozhppurai` `25:28` status=`needs_context_review` decision=`CONTEXT_ONLY`
- `SAINT` `ஞானசம்பந்தன்` -> `சைவ நாயன்மார்கள்` in `thirumurai_01_paadal_1002_commentary` `pozhppurai` `61:73` status=`auto_accepted` decision=`KEEP`
- `TEMPLE` `திருவீழிமிழலை` -> `திருவீழிமிழலை` in `thirumurai_01_paadal_1002_commentary` `pozhppurai` `74:87` status=`auto_accepted` decision=`KEEP`
- `DEITY` `இறைவர்` -> `சிவன்` in `thirumurai_01_paadal_1002_commentary` `pozhppurai` `88:94` status=`auto_accepted` decision=`KEEP`
- `TEMPLE` `திருமுதுகுன்றம்` -> `திருமுதுகுன்றம்` in `thirumurai_01_paadal_1003_commentary` `pozhppurai` `6:21` status=`auto_accepted` decision=`KEEP`
- `NATURE` `நீர்` -> `நீர்` in `thirumurai_01_paadal_1004_commentary` `pozhppurai` `0:4` status=`context_supported` decision=`CONTEXT_ONLY`
- `DEITY` `இறைவன்` -> `சிவன்` in `thirumurai_01_paadal_1004_commentary` `pozhppurai` `44:50` status=`auto_accepted` decision=`KEEP`
- `NATURE` `நீர்` -> `நீர்` in `thirumurai_01_paadal_1005_commentary` `pozhppurai` `50:54` status=`context_supported` decision=`CONTEXT_ONLY`

## Review Notes

- This is a deterministic seed-lexicon annotation pass based on the six pilot TSV datasets and the manual QA decision CSVs.
- `review_status` records whether each mention is `auto_accepted`, `context_supported`, `needs_context_review`, `ambiguous_review`, or `unreviewed_seed`.
- Exact offsets are calculated against `data/processed/thevaram_normalized`.
- Same-type nested overlaps are suppressed by preferring the longer phrase.
- Cross-type overlaps are retained because the pilot data intentionally uses multi-category poetic imagery.

## v3 Ontology Expansion

- Extra curated/dynamic terms loaded: `586`
- Entity relationships written: `4491`
- Cross-type overlap records written: `30710`
- Relationship sources: `{'corpus_cooccurrence': 4474, 'v3_curated_ontology': 17}`
- Relationship types: `{'associated_with': 3, 'co_occurs_in_paadal': 4474, 'consort_of': 2, 'defeats': 2, 'epithet_of': 1, 'manifestation_of': 1, 'performed_by': 6, 'weapon_of': 1, 'worn_or_held_by': 1}`

v3 is an aggressive deterministic expansion layer. It improves coverage for retrieval and linking, but new/context-only aliases should still be reviewed before being treated as final scholarly gold.
