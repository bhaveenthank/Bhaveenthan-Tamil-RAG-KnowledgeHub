# Thevaram Ontology v1 Annotation Guidelines

This is the repo-native guideline scaffold derived from the ontology report.

## Global Rules

- Span equals the maximal referring expression, excluding honorific verbs.
- Link mentions at lemma level; store inflected surface text on the mention.
- Annotate nested entities when a phrase both refers to a person and contains an object/place.
- Do not assign two entity types to the same exact span. Use relations for roles.
- Preserve `layer`: verse, pozhppurai, or kurippurai.
- Mark simile-scoped mentions with `in_simile=true`; relation extraction must respect certainty.
- If a phrase picks out a person through body/object imagery, prefer `DIVINE_EPITHET` plus inner entities.

## Decision-Critical Rules

- `சடையன்`, `செவியன்`, `தோடுடைய செவியன்` refer to Shiva: `DIVINE_EPITHET`, not `BODY_PART`.
- `கொன்றை`, `அரவு`, `மதி`, `கங்கை` keep their intrinsic type; sacredness is represented by `wears`, `holds`, `rides`, or related relations.
- `ACTION` is deprecated as an entity type. Convert event phrases to `MYTH_EVENT` anchors.
- `பதி`, `பசு`, `மெய்`, and `மால்` require word-sense disambiguation.
- `SACRED_PLACE`, `SAINT`, `PAN`, and `TEXT_WORK` should be populated from structural metadata where possible.

## Worked Opening Verse Sketch

In `தோடு உடைய செவியன், விடை ஏறி, ஓர் தூ வெண்மதி சூடி`:

- `தோடு உடைய செவியன்` -> `DIVINE_EPITHET`, refers_to Shiva.
- `தோடு` -> `SACRED_OBJECT`.
- `விடை` -> `FAUNA`, relation `rides(Shiva, விடை)`.
- `தூ வெண்மதி` -> `CELESTIAL`, relation `wears(Shiva, மதி)` with colour/purity attributes.
