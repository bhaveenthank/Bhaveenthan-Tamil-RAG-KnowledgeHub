# Annotated Fixture Framework

## Purpose

The Literary KnowledgeHub needs a small gold-standard annotation layer before any
automatic extraction is attempted. These fixtures define what a correct extraction should
look like for entities, deities, authors, motifs, epithets, similes, metaphors, and
relationships.

This phase creates manually curated evaluation examples only. It does not scrape,
extract automatically, populate registries, call an LLM, build answer generation, mutate
frozen corpora, regenerate embeddings, or rebuild vector indexes.

## Role In Literary NLP

Classical Tamil literary analysis needs more than word matching. A phrase may signal a
deity through an epithet, a motif through imagery, or a literary device through a compact
comparison marker. Gold annotations give future extraction systems a stable target for
precision, recall, and error analysis.

## Role In Evaluation

The annotations will later support:

- entity extraction evaluation
- deity and author normalization evaluation
- motif and theme detection evaluation
- epithet linking evaluation
- simile and metaphor detection evaluation
- relationship extraction evaluation

Each fixture stores exact text spans where possible and relationship links where a span
alone is not enough.

## Relationship To Benchmark Improvement

The comprehensive benchmark currently fails many questions because the system lacks
structured literary knowledge. Annotated fixtures create the evaluation foundation needed
to reduce `architecture_gap`, `registry_gap`, and `data_gap` failures through later
extraction phases.

## Relationship To Future Extraction

Future extraction algorithms must be tested against these gold fixtures before their
outputs can be promoted into candidate stores or curated registries. Candidate generation
and registry promotion remain separate phases.

## Publication-Quality Experiments

A publication-quality experiment should report:

- annotation guideline version
- fixture counts by target type
- inter-review status, when available
- extraction precision, recall, and F1
- error categories
- source provenance
- limitations for classical Tamil

The present fixtures are seed examples for method development, not a finished benchmark
release.
