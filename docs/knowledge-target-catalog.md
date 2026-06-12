# Knowledge Target Catalog

## Overview

This catalog lists the literary knowledge targets that future extraction phases should
produce. Each target must preserve provenance, exact evidence, source URLs, deterministic
IDs, and review status.

## Entity Targets

| Target | Examples | Evidence Fields | Future Uses |
| --- | --- | --- | --- |
| Deity | சிவன், முருகன், விஷ்ணு | verse, commentary, title | deity normalization, devotional analytics |
| Author | திருஞானசம்பந்தர், அப்பர் | metadata, titles, commentary | author comparison, work attribution |
| Place | சீர்காழி, மதுரை | verse, title, commentary | place-based literary maps |
| Work | தேவாரம், நன்னூல் | metadata, titles | cross-work analytics |
| Concept | அருள், பக்தி, ஞானம் | verse, commentary | theme and philosophy search |

## Motif And Theme Targets

| Target | Examples | Notes |
| --- | --- | --- |
| Motif | moon imagery, fire imagery, river imagery | Should link to concrete evidence spans. |
| Theme | grace, devotion, impermanence | Requires careful distinction from simple word matches. |
| Literary image | flower, ocean, mountain, flame | May overlap with motifs and metaphors. |

## Literary Device Targets

| Target | Examples | Detection Risk |
| --- | --- | --- |
| Simile | போல், ஒக்கும், அன்ன | Marker-based extraction is possible but ambiguous. |
| Metaphor | divine light, ocean of grace | Requires source-target interpretation. |
| Epithet | சடையன், கதிரவன் | Needs entity linking to avoid false positives. |
| Alliteration / sound pattern | repeated phonetic clusters | Requires later phonological tooling. |

## Relationship Targets

Relationships connect extracted candidates:

- deity to epithet
- author to work
- work to motif
- verse to literary device
- place to hymn
- motif to theme
- metaphor source image to target concept

Every relationship must include:

- `relationship_id`
- `subject_id`
- `object_id`
- `relationship_type`
- `evidence_record_id`
- `evidence_field`
- `source_url`
- `review_status`

## Initial Priority

1. Entity and deity extraction.
2. Author normalization.
3. Epithet extraction.
4. Simile marker extraction.
5. Motif and theme candidates.
6. Metaphor candidates.
7. Relationship graph construction.
