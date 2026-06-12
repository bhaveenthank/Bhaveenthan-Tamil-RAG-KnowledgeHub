# Annotation Guidelines

## General Rules

- Annotate exact spans using Python-style character offsets: `start` inclusive and `end`
  exclusive.
- Preserve the exact Tamil text in the `text` field of each annotation.
- Use `review_status: manual_gold_seed` for these fixtures.
- Do not infer beyond the example unless the label is explicitly a relationship.
- Mark uncertainty in `notes`; do not hide ambiguity.

## Entity

Definition: A named or normalized referent such as a deity, author, place, work, or
concept.

Boundary rule: Include only the named expression, not surrounding particles or verbs.

Example: In `சிவன் , திருமால் , பிரமன்`, annotate `சிவன்` as an entity with label
`deity`.

Ambiguity: If a term can be literal or symbolic, annotate the literal entity only when
the local context supports it.

## Deity

Definition: A divine figure or divine class mention.

Examples: `சிவன்`, `திருமால்`, `முருகன்`.

Boundary rule: Do not include punctuation or parenthetical markers.

Ambiguity: Honorific references such as `கழலீர்` may refer to a deity in devotional
verse, but should be annotated only when the fixture intentionally demonstrates that use.

## Author

Definition: A named writer, poet, commentator, or traditional author.

Examples: `திருஞானசம்பந்தர்`, `பவணந்தி முனிவர்`, `சுப்பிரமணிய பாரதி`.

Boundary rule: Include the full conventional name.

Ambiguity: Titles of works are not author annotations even when adjacent to the author.

## Place

Definition: A named geographic or sacred location.

Example: `திருப்பூந்தராய்`.

Boundary rule: Include the place name only.

Ambiguity: Landscape words such as mountain or sea are motifs unless used as place names.

## Work

Definition: A named literary work or collection.

Examples: `தேவாரம்`, `நன்னூல்`, `யாரைத் தொழுவது`.

Boundary rule: Include the title, not verbs such as `பாடினார்` or `எழுதிய`.

## Motif

Definition: A recurring image or symbolic pattern.

Examples: moon imagery, snake imagery, conch imagery, rain imagery.

Boundary rule: Annotate the surface image word and store the normalized motif label.

Ambiguity: A literal object can also support a motif label, but the annotation should not
claim interpretation beyond the fixture note.

## Theme

Definition: A broad conceptual concern such as grace, devotion, knowledge, or truth.

Boundary rule: Prefer explicit lexical evidence for seed fixtures.

Ambiguity: Theme annotation is high-level; future phases should require reviewer notes.

## Epithet

Definition: A descriptive name or attribute used to refer to an entity.

Examples: `செஞ்சடை`, `சடையன்`, `கதிரவன்`.

Boundary rule: Annotate the descriptive expression and link to a target entity only when
the fixture is designed to test that relationship.

## Simile

Definition: An explicit comparison, usually with a marker such as `போல்`, `போல`,
`போலத்`, `அன்ன`, or `ஒக்கும்`.

Boundary rule: Annotate the comparison phrase containing the marker. Store marker,
subject, and object when known.

Ambiguity: Marker detection alone is not enough; future extraction must distinguish true
comparison from idiomatic usage.

## Metaphor

Definition: A figurative mapping where one domain frames another without an explicit
comparison marker.

Examples: `அருள் ஒளி`, `பக்தி கடல்`, `ஞானம் தீயாய்`.

Boundary rule: Annotate the compact metaphor phrase and store source/target domains.

Ambiguity: Metaphor annotation requires human review before registry promotion.

## Relationship

Definition: A structured link between two annotations or concepts.

Examples:

- deity to epithet
- author to work
- motif to surface form

Relationship annotations must include `source`, `target`, and `relationship_type`.
