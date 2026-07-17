# JCDL 2026 Resource Paper Strategy

## Best Positioning

Submit this as a resource paper about a reusable Tamil literary corpus pipeline and pilot release, not as a generic scraper paper.

Recommended title:

**An Audit-First Corpus Resource for Citation-Grounded Tamil Literary Research**

Core claim:

> We present an audit-first pipeline and release package that transforms TamilVU Thevaram material into a provenance-preserving, citation-grounded Tamil literary corpus resource, with clear separation between release-ready records, audit reports, and experimental evidence layers.

This is strong for JCDL because the Resources Track values public datasets, reusable pipelines, documentation, provenance, open access, FAIR alignment, and impact for digital libraries.

## Reviewer Lens

Reviewers will likely ask four questions:

1. **Novelty:** Is this more than scraping?
   Answer: Yes. The novelty is the audit-first resource design: literary hierarchy, verse/commentary separation, source URLs, immutable provenance, schema validation, quality reports, and retrieval-ready evidence layers.

2. **Availability:** Can reviewers access it?
   Answer needed before submission: create a public GitHub or Zenodo record. The paper currently uses placeholders. Do not submit until those links work without login.

3. **Utility:** Can others reuse it?
   Answer: Provide JSONL data or a rights-safe sample, schemas, corpus card, checksums, quality reports, and commands.

4. **Impact:** What research does it enable?
   Answer: citation-aware Tamil literary search, corpus analysis, digital humanities, annotation workflows, Tamil literary QA/RAG, and evaluation of retrieval over verse-plus-commentary material.

## Strongest Narrative

Open with this problem:

Tamil literary works are online, but online pages are not reusable research corpora. A useful corpus must preserve source trails, hierarchy, verse/commentary boundaries, Unicode integrity, and known gaps.

Then show the answer:

An audit-first pipeline for Thevaram books 1-8, with a freeze-ready Irandaam Thirumurai v1 release subset.

Then show evidence:

- 8 Thirumurai books.
- 841 paadal thogupugal.
- 9012 paadalgal.
- 9012 commentary records.
- 64073 text spans.
- 122 hymns and 1331 verse records in the freeze-ready Irandaam Thirumurai v1 release.
- 0 schema violations in the release subset.
- Checksums, corpus card, schema, audit reports, and sample audit evidence.

Then be honest:

The full 1-8 resource is broad normalized coverage under curation. The Irandaam Thirumurai subset is the strongest audited release. Entity annotation and paadal-pozhppurai links are evidence layers, not gold scholarly annotation.

## What To Include In The Final Submission

- Stable public repository or Zenodo DOI.
- Explicit license for code and data, or a rights-safe release model if full text cannot be redistributed.
- Corpus card or datasheet.
- Schema file.
- Checksums.
- Setup and reuse commands.
- One small usage example.
- Clear limitations.
- AI-use statement if AI was used for research code, data construction, validation, analysis, figures, or other research lifecycle steps.

## What Not To Claim

Avoid:

- "Complete TamilVU corpus."
- "Official TamilVU mirror."
- "Gold-standard annotations."
- "Expert-verified every record."
- "Solved Tamil literary QA."

Use instead:

- "Provenance-preserving corpus resource."
- "Audit-first pipeline."
- "Release-ready audited subset."
- "Experimental evidence layers for retrieval and review."
- "Citation-grounded foundation for future Tamil literary QA."

## Suggested Submission Checklist

- Replace all placeholders in the LaTeX file.
- Make the repository public or deposit a release on Zenodo.
- Add a `LICENSE` file.
- Add a short `README` with installation and reuse commands.
- Add a `DATASHEET.md` or expand `corpus_card.md`.
- Confirm source rights and redistribution rules.
- Compile in ACM `sigconf` format and keep the body within 2-4 pages excluding references.
- Submit by July 31, 2026 AoE.

