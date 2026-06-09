# Tamil Literary RAG Question Taxonomy

## Purpose

The corpus pipeline now retrieves deterministic, citation-ready contexts, but retrieval quality alone does not define what a useful Tamil literary system must answer. A question taxonomy gives the project a stable target before adding more Thirumurai, more metadata, or answer generation.

The taxonomy represents Tamil poets searching for language and imagery, researchers tracing evidence across works, and students locating and understanding passages. Every question requires retrieval and a citation, even when the eventual answer also needs counting, comparison, or interpretation.

## Question Families

### Lookup Questions

Lookup questions request one known fact: author, Thirumurai, hymn ID, song number, pann, title, or source URL. The current hybrid retriever, context builder, and citation builder can support these when the metadata exists.

### Retrieval Questions

Retrieval questions begin with a verse line, phrase, commentary excerpt, place, or epithet and ask for the matching literary record. They test Tamil text fidelity, field-aware search, parent-child links, and source grounding.

### Analytical Questions

Analytical questions ask for occurrence counts, rankings, imagery inventories, epithets, similes, metaphors, or recurring patterns. A top-k RAG context is not a complete corpus scan, so these need a corpus analysis layer that can query every relevant record and return auditable evidence.

### Comparative Questions

Comparative questions contrast hymns, Thirumurai, poets, Nayanmars, commentaries, or literary collections. They require normalized author, work, place, deity, pann, and entity metadata. Cross-corpus claims cannot be reliable while only Irandaam Thirumurai is available.

## Normal RAG And Corpus Aggregation

Normal RAG is suitable when a small number of retrieved passages can answer the question, such as identifying a hymn from a line. In the generated report, "ordinary RAG" means the question needs none of corpus aggregation, synonym expansion, cross-corpus support, or future LLM interpretation. Corpus-wide aggregation is required when the wording includes ideas such as all, most, count, frequency, repeated, or compare across a collection.

The two paths should remain explicit:

1. Retrieval path: hybrid search, deterministic context package, citation package.
2. Analysis path: exhaustive filtered scan, normalized grouping/counting, evidence records, then citation packaging.

This prevents a plausible top-k sample from being presented as a complete corpus result.

## Architectural Guidance

- **Scraper:** preserve source hierarchy, stable identifiers, commentary boundaries, and raw snapshots.
- **Parser:** retain verse, pozhppurai, kurippurai, headings, pann, place, author, and source URLs as separate fields.
- **Metadata:** normalize authors, Nayanmars, deities, epithets, places, pann, imagery, and literary devices without overwriting source text.
- **Retrieval:** keep hybrid retrieval as the default for lookup and passage identification; add field filters and synonym expansion as separately measurable capabilities.
- **Analysis:** add deterministic occurrence, grouping, ranking, and comparison operations before claiming corpus-wide answers.
- **Evaluation:** evaluate exact facts, citations, list recall, aggregation correctness, and human-reviewed literary interpretation separately.

## Current Boundary

The current RAG context builder can answer lookup and retrieval questions. Analytical questions require a corpus analysis layer. Synonym questions require a curated Tamil literary synonym lexicon. Cross-Nayanmar comparison requires multi-corpus metadata normalization. Parser quality must be audited before scaling to three or four more Thirumurai.

This phase creates no answers and calls no LLM. It does not scrape, modify corpus releases, regenerate embeddings, or rebuild the vector index.
