# Entity Extraction Pilot

## Purpose

Entity extraction is the first practical knowledge-extraction pilot because later literary
analytics depend on knowing who or what a passage refers to. Motifs, epithets, similes,
metaphors, and relationships all need stable entity anchors before their evidence can be
counted and compared.

This pilot supports only four entity labels:

- deity
- author
- place
- work

It uses deterministic registry and local-metadata matching only. It does not use machine
learning, LLMs, scraping, embeddings, vector indexes, or corpus-wide extraction.

## Why Entities Are Foundational

Entity extraction provides normalized anchors for:

- deity mention analytics
- author comparison
- work-level grouping
- place references
- future deity-to-epithet relationships
- future motif and literary-device attribution

Without entity anchors, higher-level extraction can count words but cannot reliably answer
questions such as which deity receives a given epithet or which author uses a theme.

## Relationship To Future Motif Extraction

Motif extraction will need entities to distinguish literal imagery from literary usage
associated with a deity, author, work, or place. For example, moon imagery becomes more
useful when it can be linked to a hymn, author, or deity context.

## Relationship To Future Epithet Extraction

Epithet extraction depends directly on entity extraction. A phrase such as `செஞ்சடை` is
analytically useful only when it can be linked to `சிவன்` or another target entity.

## Methodology

The extractor builds a gazetteer from:

- curated deity registry
- curated author registry
- place registry
- work registry
- local normalized corpus metadata for authors and titles
- local Thirumurai hymn-title metadata for place-like title fragments

It then performs deterministic exact substring matching with stable tie-breaking and
deduplication.

## Evaluation

The evaluator compares extracted spans against `data/knowledge/annotations/entities_gold.json`.
Metrics include precision, recall, F1, and exact-match count. Missed entities and false
positive spans are written to a machine-readable result file and summarized in a Markdown
report.

## Limitations

- The matcher is exact-string only.
- It does not infer entities from context.
- It may miss entities absent from registries or local metadata.
- It does not extract epithets, motifs, similes, metaphors, or relationships.
