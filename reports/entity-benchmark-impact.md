# Entity Benchmark Impact Projection

## Purpose

This projection estimates which benchmark failures may improve after entity extraction
becomes reliable. It is not a new benchmark result and does not claim corpus-wide
extraction.

## Likely Impact

| Benchmark Gap | Entity Extraction Impact |
| --- | --- |
| `registry_gap` | Normalized deity, author, place, and work mentions can improve query expansion and matching. |
| `data_gap` | Entity spans turn raw text evidence into typed evidence. |
| `architecture_gap` | Entity anchors prepare the system for relationships, epithets, motifs, and device attribution. |

## Question Types Helped

- Which authors mention a deity?
- Which works contain a place reference?
- Which hymns mention Shiva, Vishnu, or Murugan by known forms?
- Which records can later support deity-to-epithet relationships?

## Remaining Gaps

Entity extraction alone does not solve motif, epithet, simile, metaphor, or relationship
questions. Those require later phases and separate gold evaluation.
