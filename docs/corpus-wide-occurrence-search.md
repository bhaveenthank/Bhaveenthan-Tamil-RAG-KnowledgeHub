# Corpus-Wide Occurrence Search

## Purpose

Occurrence search finds every literal evidence occurrence of a term across the currently
normalized local corpora. It answers "where does this word or reviewed concept occur?"
rather than "what are the best top-k contexts for this query?"

Retrieval ranks a small result set for reading or future RAG context. Occurrence search
returns evidence rows with exact fields, snippets, record IDs, authors, and source URLs.
That difference matters for literary analytics: questions about frequency, distribution,
author comparison, motif vocabulary, and cross-corpus usage need complete evidence, not
only the top few retrieval hits.

## Indexed Sources

The indexer reads only local normalized artifacts:

- `data/processed/normalized/*.jsonl`
- `data/processed/normalized_categories/*.jsonl`

It does not scrape, fetch, extract from raw HTML, call an LLM, rebuild embeddings, or
modify frozen corpus releases.

## Indexed Fields

The first index covers common literary and reference fields:

- `verse_text`
- `commentary_text`
- `pozhppurai`
- `kurippurai`
- `content_text`
- `definition`
- `rule_text`
- `explanation_text`
- `title`
- `author`

Every index row preserves `corpus_id`, `category_id`, `record_id`, `record_type`, author,
title, `source_url`, commentary URL when present, and citation metadata when available.

## Query Expansion

Occurrence search can use registry-driven query expansion:

```bash
python3 src/analytics/search_occurrences.py --term "சந்திரன்" --expand-query
```

For a curated synonym concept, this searches the original term plus reviewed equivalents
and variants from `data/knowledge/`. The output records which terms were searched, so
future aggregation can separate literal counts by term while still grouping them under a
concept.

## Foundation For Aggregation

This phase creates evidence rows only. Phase 25 can aggregate those rows by author,
corpus, field, hymn, category, or concept. Keeping occurrence search separate from
aggregation makes each future statistic traceable back to exact source snippets and URLs.

## Limitations

Matching is literal substring matching. It does not yet handle morphology, sandhi,
inflection, spelling variants beyond curated registry forms, or ambiguous literary
meaning. Motif and literary-device hits are vocabulary evidence only, not automatic
annotations.
