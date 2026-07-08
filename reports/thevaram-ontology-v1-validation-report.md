# Thevaram Ontology v1 Validation Report

## Summary

- Status: `VALID`
- Entity types: `25`
- Relations: `29`
- Attributes: `14`
- Mythological event canon size: `20`
- Deprecated v2 entity types: `ACTION, NATURE`

## Current Annotation Baseline

- v2 registry entities: `195`
- v2 mentions: `48962`
- v2 cross-type overlap spans: `7809`
- v3 registry entities: `624`
- v3 mentions: `107761`
- v3 relationships: `4491`
- v3 temple mentions: `4036`
- v3 paadapatta-thalam mentions: `4036`

## v2 Mention Counts

| Type | Mentions |
| --- | ---: |
| `ACTION` | 121 |
| `BODY_PART` | 14374 |
| `DEITY` | 1303 |
| `NATURE` | 15330 |
| `SACRED_OBJECT` | 11829 |
| `THEOLOGICAL_CONCEPT` | 6005 |

## v3 Mention Counts

| Type | Mentions |
| --- | ---: |
| `ACTION` | 121 |
| `BODY_PART` | 17304 |
| `DEITY` | 13847 |
| `DIVINE_EPITHET` | 347 |
| `DIVINE_FORM` | 4 |
| `FESTIVAL` | 33 |
| `ICONOGRAPHIC_FEATURE` | 2373 |
| `MUSICAL_INSTRUMENT` | 741 |
| `MYTHOLOGICAL_CHARACTER` | 1556 |
| `MYTHOLOGICAL_EVENT` | 398 |
| `NATURE` | 23831 |
| `RELATIONSHIP` | 2000 |
| `RITUAL` | 1624 |
| `SACRED_FLOWER` | 1062 |
| `SACRED_MOUNTAIN` | 1160 |
| `SACRED_OBJECT` | 16191 |
| `SACRED_RIVER` | 2303 |
| `SACRED_TREE` | 1828 |
| `SAINT` | 949 |
| `TEMPLE` | 4036 |
| `TEMPLE_ARCHITECTURE` | 1043 |
| `THEOLOGICAL_CONCEPT` | 11238 |
| `WEAPON` | 3772 |

## Migration Stance

The v1 ontology supersedes the six-type v2 layer. The first operational migration should:

1. Convert `ACTION` to canonical `MYTH_EVENT` anchors.
2. Split `NATURE` into `FLORA`, `FAUNA`, `RIVER`, `MOUNTAIN`, and `CELESTIAL`.
3. Narrow `SACRED_OBJECT` to artefacts/substances and move role semantics into relations.
4. Add `DIVINE_EPITHET`, `SACRED_PLACE`, `SAINT`, `REL_GROUP`, `PAN`, and `TEXT_WORK`.
5. Queue WSD-heavy lexemes such as `பதி`, `பசு`, `மெய்`, and `மால்` for review.
