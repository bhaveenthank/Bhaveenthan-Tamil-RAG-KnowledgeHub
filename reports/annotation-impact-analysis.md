# Annotation Impact Analysis

## Purpose

This report estimates how gold annotations can reduce benchmark failures after future
extractors are implemented and evaluated.

## Impact By Extraction Type

| Extraction Type | Potential Failure Reduction | Reason |
| --- | --- | --- |
| Entity extraction | `registry_gap`, `data_gap` | Normalized mentions allow broader query and evidence matching. |
| Deity extraction | `registry_gap`, `data_gap` | Devotional questions need deity aliases and honorifics. |
| Author extraction | `registry_gap` | Author comparison depends on normalized names and works. |
| Motif extraction | `data_gap` | Motif questions need imagery evidence beyond literal term search. |
| Epithet extraction | `architecture_gap`, `data_gap` | Epithet-to-deity links support indirect deity mentions. |
| Simile extraction | `architecture_gap` | Literary-device questions need typed comparison evidence. |
| Metaphor extraction | `architecture_gap` | Figurative mapping needs reviewed source-target annotations. |
| Relationship extraction | `architecture_gap` | Cross-entity and cross-device analytics need structured links. |

## Expected Benchmark Effect

The most immediate gains should come from entity, deity, author, and epithet extraction.
Metaphor and relationship extraction will likely improve harder analytical questions, but
only after lower-level candidates are reliable.

## Limitation

This is an impact estimate. It is not a benchmark result and does not claim any automatic
extraction has occurred.
