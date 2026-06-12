# Benchmark To Knowledge Gap Mapping

## Purpose

The comprehensive benchmark identified questions that cannot be solved by retrieval,
occurrence search, aggregation, and analytical retrieval alone. This report maps those
gaps to future literary knowledge extraction targets.

## Gap Mapping

| Benchmark Gap | Missing Knowledge | Extraction Target | Why It Matters |
| --- | --- | --- | --- |
| `registry_gap` | Aliases and normalized literary concepts are incomplete | entity, deity, author, motif | Query expansion cannot cover forms that are not registered. |
| `data_gap` | Evidence exists as text but not as structured knowledge | motif, epithet, simile, metaphor | Analytics needs typed evidence, not only raw matches. |
| `architecture_gap` | No relationship layer connects evidence types | relationship | Cross-entity and cross-device questions require links. |
| `unsupported_literary_device` | Devices are named but not detected in evidence | simile, metaphor, epithet | Counts and comparisons need device candidates. |
| `cross_corpus_gap` | Multi-work knowledge is not normalized enough | entity, relationship | Website-wide expansion needs comparable records. |

## Example Questions And Required Knowledge

| Question Type | Current Limitation | Required Extraction |
| --- | --- | --- |
| Which hymns contain moon imagery? | Exact term expansion finds moon words but not imagery without explicit terms. | motif extraction |
| Which deity receives the most similes? | Deity and simile evidence are not linked. | deity, simile, relationship extraction |
| Where is Shiva referred to through epithets? | Epithet-to-deity mapping is not populated. | epithet and relationship extraction |
| Which authors share the same themes? | Themes are not extracted across works. | theme and author relationship extraction |

## Framework Decision

The next unlock is not answer generation. It is structured candidate extraction with exact
evidence, review status, and deterministic IDs.
