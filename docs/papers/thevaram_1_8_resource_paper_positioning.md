# Positioning Strategy for the First Thevaram 1-8 Paper

## Best Topic

Recommended title:

**An Audit-First Digital Corpus Pipeline for Thevaram: Structuring Books 1-8 for Citation-Grounded Tamil Literary Research**

Shorter option:

**Thevaram 1-8 as a Citation-Ready Tamil Literary Corpus Resource**

Most conference-friendly option:

**Building a Provenance-Preserving Thevaram 1-8 Corpus for Digital Libraries and Tamil Literary NLP**

## Central Thesis

The paper should argue that classical Tamil corpus construction is not only an extraction problem. It is a digital library and research-infrastructure problem requiring:

- preservation of literary hierarchy,
- separation of verse and commentary,
- stable source URLs,
- Unicode-safe normalization,
- reproducible table schemas,
- quality reports,
- explicit source-gap accounting,
- and downstream readiness for retrieval, annotation, and question answering.

The strongest single-sentence positioning:

> We present an audit-first pipeline that converts TamilVU Thevaram material from heterogeneous web structures into a normalized, citation-grounded corpus resource covering Thirumurai 1-8, while explicitly separating mature release-ready data from experimental annotation and alignment layers.

## Why This Is Stronger Than "Data Extraction"

"Data extraction" sounds like a technical preprocessing step. Your work is broader:

- a digital library resource,
- a corpus engineering workflow,
- a Tamil literary NLP foundation,
- an audit and release methodology,
- and a bridge from cultural heritage material to citation-grounded RAG.

That framing makes the paper useful to JCDL because JCDL values reusable collections, workflows, metadata, preservation, access, and reproducibility.

## Best Venue Fit

The best immediate fit is the **JCDL 2026 Resource Track**.

Why:

- JCDL explicitly welcomes datasets, corpora, workflows, tools, digital humanities resources, semantic search, metadata, preservation, and reusable research pipelines.
- Your resource has a concrete collection, schema, statistics, and reuse story.
- The resource-track format is 2-4 pages, which suits a first paper and avoids needing to prove a full NLP system.

Important JCDL dates verified on the official site:

- JCDL 2026 conference: October 13-16, 2026, Dallas, Texas.
- Resource paper submission deadline: July 31, 2026.
- Full/short research paper deadline: July 15, 2026.

Official pages:

- https://2026.jcdl.org/
- https://2026.jcdl.org/call-for-resources/
- https://2026.jcdl.org/key-dates/

## Best Submission Type

Submit as a **resource paper**, not a full research paper, unless you add a stronger user study or comparative evaluation.

Resource paper contribution:

1. Thevaram 1-8 normalized relational corpus tables.
2. A reproducible extraction-normalization-validation workflow.
3. Quality and coverage reports.
4. Experimental annotation/linking layers for future retrieval and literary QA.
5. A mature frozen subset: Irandaam Thirumurai v1.

## What Not To Claim

Avoid these claims:

- "Complete TamilVU corpus."
- "Complete Thevaram scholarly edition."
- "Gold-standard literary annotations."
- "Fully solved Tamil literary QA."
- "Expert-verified all records."
- "Commentary alignment is finished."

Stronger truthful claims:

- "Normalized Thevaram 1-8 table resource."
- "Audit-first corpus construction workflow."
- "Citation-grounded source preservation."
- "Release-ready audited subset for Irandaam Thirumurai."
- "Experimental entity and commentary-linking layers with clear quality diagnostics."

## Suggested Contributions Section

Use exactly this structure:

1. **Corpus resource:** A normalized relational Thevaram 1-8 corpus with 8 books, 841 paadal thogupugal, 9012 paadalgal, 9012 commentary records, and 64073 text spans.
2. **Pipeline:** A provenance-preserving extraction and normalization pipeline that keeps source URLs, line boundaries, Unicode normalization, and record identifiers.
3. **Audit model:** Quality reports that distinguish parser failures, source omissions, schema issues, commentary gaps, and downstream annotation uncertainty.
4. **Downstream readiness layers:** Deterministic entity annotation and paadal-pozhppurai linking outputs that support retrieval and future literary QA while remaining clearly marked as non-gold.

## The Paper's Narrative Arc

Open with the problem:

> Tamil literary materials are increasingly accessible online, but availability is not the same as computational usability. Classical devotional corpora require preservation of literary units, commentary boundaries, source provenance, and known gaps before they can safely support retrieval or AI-assisted research.

Then present your answer:

> We built an audit-first pipeline for Thevaram 1-8.

Then show evidence:

> 9012 paadalgal, 9012 commentaries, 64073 text spans, no table-quality issues, preserved line structure, and explicit commentary coverage diagnostics.

Then be honest:

> The full 1-8 tables are broad and useful; Irandaam Thirumurai v1 is the most mature fully audited release subset; commentary alignment and entity annotation are research layers requiring further review.

## Acceptance Chance for JCDL 2026 Resource Track

My estimate:

- **Current form, if submitted quickly without public resource packaging:** 25-35%.
- **With a clean 4-page paper, stable GitHub/Zenodo artifact, license/access statement, reproducibility instructions, and clear limitations:** 45-60%.
- **With anonymized resource access, a polished corpus card, example notebooks, and one external Tamil scholar/user validation note:** 60-70%.

The main acceptance risks:

- Resource accessibility and licensing uncertainty.
- Too much scope if the paper claims all Thevaram 1-8 is equally audited.
- Reviewer concern that this is "just scraped data."
- Lack of comparison against existing Tamil literary resources.
- Lack of stable public repository or DOI at submission time.

The best mitigation:

- Submit the resource as **pipeline + metadata/schema + derived statistics + reproducible scripts**, and be careful about text redistribution if copyright/source terms are uncertain.
- Make Irandaam Thirumurai v1 the release-quality example and Thevaram 1-8 the broader normalized resource under active curation.

## Minimum Submission Checklist

Before submitting:

- Create an anonymized resource page or repository for review.
- Include schema files and table descriptions.
- Include a small permitted sample if full text redistribution is uncertain.
- Include statistics from `thevaram_1_8_paper_statistics.md`.
- Include a resource access and rights statement.
- Include reproducibility commands.
- Include a corpus card or datasheet.
- Include a pipeline diagram.
- Include 2-3 sample records in the paper.
- Include limitations prominently.

