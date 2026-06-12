# Aggregation And Statistics Engine

## Purpose

Aggregation turns occurrence evidence into structured literary analytics. Phase 24 can
find every evidence row for a term or expanded concept; Phase 25 groups those rows into
counts, rankings, and distributions.

Retrieval answers "which contexts are most useful to read first?" Occurrence search
answers "where does this term appear?" Aggregation answers "how are those occurrences
distributed across authors, works, categories, record types, and sources?"

## Inputs

The engine consumes occurrence search results from:

```bash
python3 src/analytics/search_occurrences.py --term "சந்திரன்" --expand-query
```

It does not scrape, call an LLM, regenerate embeddings, rebuild vector indexes, or mutate
frozen corpus releases.

## Supported Groupings

Current grouping dimensions:

- `author`
- `category`
- `work`
- `record_type`
- `source`

Every group includes occurrence count, percentage share, unique record count, unique work
count, unique author count, matched-term counts, field counts, and a small evidence sample.

## Statistics

The statistics engine reports:

- total occurrences
- unique records
- unique works
- unique authors
- top-N rankings
- matched-term percentage distributions
- field percentage distributions

## Role In Literary Analytics

This is the bridge between evidence and future analytical retrieval. It can support
questions such as which author uses a concept most, which works mention a deity, or which
fields contain the most literary-device vocabulary. The output remains evidence-backed:
future answer generation should cite occurrence rows underneath each statistic.

## Limitations

Counts are literal occurrence counts. Expanded concept counts depend on the current
curated registry seeds. They are not yet morphology-aware and should not be read as final
scholarly claims without reviewer validation.
