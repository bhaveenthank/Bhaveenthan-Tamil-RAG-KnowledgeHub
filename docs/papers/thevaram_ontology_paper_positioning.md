# Positioning Strategy for the Thevaram Ontology / Literary Knowledge Paper

## Best Topic

Recommended title:

**A Semantic Ontology for Thevaram Literary Analysis: Modeling Deities, Sacred Places, Iconography, Nature Imagery, and Commentary Evidence**

Shorter option:

**A Thevaram Ontology for Citation-Grounded Tamil Literary Analysis**

More NLP-oriented option:

**From Entity Mentions to Literary Evidence: A Semantic Ontology for Thevaram Retrieval and Analysis**

## Central Thesis

The strongest thesis is:

> Classical Tamil literary QA cannot be solved by text retrieval alone. It needs a semantic evidence layer that models deities, epithets, sacred places, iconographic objects, nature imagery, theological concepts, musical metadata, and commentary relations while preserving citation links back to the corpus.

This paper should be the second paper, after the corpus/resource paper, because it depends on the structured Thevaram corpus as its evidence base.

## Best Positioning

Frame it as a **semantic resource and annotation framework**, not as a finished AI system.

Strong positioning:

> We present a corpus-driven ontology for Thevaram literary analysis and show how it supports deterministic entity annotation, review-aware evidence extraction, and future citation-grounded question answering.

Avoid positioning it as:

- a complete knowledge graph,
- a final expert-validated ontology,
- a complete literary interpretation system,
- a solved metaphor/simile detector,
- or a production-ready QA system.

## Contributions

Use four contributions:

1. **Ontology design:** A 25-type Thevaram ontology with 29 relation types and 14 attributes covering agents, sacred places, objects, nature, body imagery, mythic events, theological concepts, devotional acts, music, and text metadata.
2. **Migration model:** A principled migration from a broad six-type v2 layer to a finer v1 ontology, including the split of `NATURE`, deprecation of `ACTION`, and introduction of `DIVINE_EPITHET`, `SACRED_PLACE`, `PAN`, and `TEXT_WORK`.
3. **Annotation layer:** A deterministic annotation pass over the Thevaram 1-8 corpus producing 107761 mentions, 624 registry rows, 823 aliases, and validation checks with zero invalid bounds, zero span mismatches, and zero duplicate mention IDs.
4. **Literary QA bridge:** A discussion of how ontology-grounded evidence supports questions about deities, temples, epithets, iconography, nature imagery, commentary evidence, and later RAG systems.

## Why This Should Be Separate From Paper 1

Paper 1 should establish:

- corpus extraction,
- normalization,
- schema,
- source provenance,
- table quality,
- commentary coverage,
- release readiness.

Paper 2 should establish:

- ontology design,
- semantic categories,
- entity annotation,
- relation modeling,
- literary use cases,
- limits of deterministic extraction,
- expert-review roadmap.

If both are merged, the first paper becomes too broad and reviewers can attack the ontology for not having full expert validation. Splitting them gives each paper a clean spine.

## Best Venues

Strong venue targets:

- **JCDL**: if framed as semantic enrichment of a digital library collection.
- **Digital Humanities**: if framed around Tamil literary interpretation, cultural heritage, and scholarly use.
- **LREC/COLING resource track or workshop**: if framed as a language resource and annotation schema.
- **ACL/EMNLP workshops**: especially workshops on low-resource NLP, cultural heritage NLP, computational humanities, knowledge graphs, or NLP for classical/ancient languages.

Main conference acceptance is less likely until you add:

- expert validation,
- inter-annotator agreement,
- comparison to baselines,
- downstream retrieval or QA improvement,
- and a public artifact package.

## Acceptance Readiness Estimate

Current form as a concept/resource paper:

- JCDL short/resource-style paper: **35-50%**
- Digital humanities paper/poster: **45-60%**
- NLP workshop paper: **40-60%**
- ACL/EMNLP main paper: **10-20%**

With expert review and a downstream retrieval/QA experiment:

- JCDL or DH: **60-75%**
- NLP workshop: **55-70%**
- ACL/EMNLP Findings/main: **25-40%**

The paper becomes much stronger after adding:

- 2 Tamil expert reviewers or one serious annotation pass,
- inter-annotator agreement on 100-200 mentions,
- a before/after retrieval evaluation showing ontology expansion improves deity/place/epithet questions,
- a small gold set for ambiguous terms such as `பதி`, `மால்`, `மெய்`, and `பசு`,
- example queries that fail with raw text but succeed with ontology evidence.

## Suggested Paper Shape

1. **Introduction:** Retrieval alone cannot answer literary questions reliably.
2. **Motivation:** Thevaram questions need deities, places, epithets, imagery, theology, commentary evidence, and musical/text metadata.
3. **Ontology Design:** 25 entity types, 29 relations, 14 attributes.
4. **Migration From v2:** Why broad categories were insufficient.
5. **Annotation Pipeline:** Registry, aliases, deterministic matching, review statuses, offset validation.
6. **Results:** Mention counts, field coverage, relation counts, validation results.
7. **Use Cases:** Deity/temple queries, epithet resolution, iconography, nature imagery, commentary-grounded answers.
8. **Limitations:** Not expert-gold, needs WSD, relation extraction not mature, motif/metaphor/simile not solved.
9. **Conclusion:** A semantic evidence layer for citation-grounded Tamil literary QA.

## One-Sentence Paper Pitch

> This paper introduces a Thevaram ontology and annotation layer that turns structured Tamil devotional text into typed, review-aware literary evidence for future retrieval, analysis, and citation-grounded question answering.

## Most Important Warning

Do not overclaim the annotation layer.

Say:

> "deterministic, review-aware semantic evidence layer"

Do not say:

> "gold-standard literary ontology"

until expert validation is complete.

