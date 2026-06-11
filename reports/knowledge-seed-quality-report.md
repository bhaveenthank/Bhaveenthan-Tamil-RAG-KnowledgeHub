# Knowledge Seed Quality Report

## Summary

- Validation: `VALID`
- Registry files: `9`
- Total records: `19`
- Curated records: `15`
- Foundation readiness: `79.4/100`
- Analytical readiness: `47.5/100`
- Phase 21 baseline: `70.0` foundation,
  `35.0` analytical
- Extraction performed: `false`
- Scraping performed: `false`
- LLM calls: `0`

## Registry Counts

| Registry | Records | Curated |
| --- | ---: | ---: |
| `authors` | 3 | 3 |
| `deities` | 3 | 3 |
| `entities` | 1 | 0 |
| `literary_devices` | 3 | 3 |
| `motifs` | 3 | 3 |
| `places` | 1 | 0 |
| `synonyms` | 3 | 3 |
| `themes` | 1 | 0 |
| `works` | 1 | 0 |

## Focus Counts

- Synonym concepts: `3`
- Synonym canonical/alias/variant forms: `9`
- Deities: `3`
- Deity canonical/alias forms: `12`
- Authors: `3`
- Author canonical/alias forms: `8`
- Motifs: `3`
- Literary devices: `3`

## Quality Findings

- IDs and canonical names are unique within each registry.
- Curated aliases do not repeat canonical names or collide within a registry.
- Records are sorted by deterministic ID and have stable content digests.
- Five registries contain three curated seeds each.
- Foundation-only entity, place, work, and theme registries remain unchanged.

## Coverage Limits

- The vocabulary is a small evaluation seed, not a comprehensive Tamil lexicon.
- No lexical source citations or named reviewer sign-offs are attached yet.
- No corpus spans are linked, so occurrence coverage remains zero.
- Contextual ambiguity is unresolved; aliases cannot be expanded blindly.
- Motif and literary-device records are classification targets, not extracted findings.

## Recommended Expansion

Add cited lexical authorities and Tamil researcher review, then create a small manually
annotated corpus sample with positive, negative, and ambiguous examples. Only after that
sample is accepted should entity extraction or query expansion be evaluated.
