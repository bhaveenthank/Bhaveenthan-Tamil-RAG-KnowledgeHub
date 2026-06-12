# TamilVU Literary Corpus Scraper

Phase-one project scaffold for building a Tamil literary knowledge store from Tamil Virtual Academy library pages.

The first target catalog is:

https://www.tamilvu.org/ta/library-libcontnt-273141

This repository is intentionally set up in phases. It does not scrape the full site; it defines the architecture, storage layout, data contracts, crawler boundaries, and one controlled one-hymn pilot scrape.

## Goals

- Preserve Tamil literary works such as Thevaram, Thiruppugazh, Sangam works, devotional literature, grammar texts, dictionaries, commentaries, and modern poetry where available.
- Keep source provenance for every extracted unit.
- Store enough structure for RAG: work, section, poem, verse, commentary, glossary/entity references, source URL, and extraction confidence.
- Support both lexical search and embedding-based retrieval.
- Keep raw source snapshots so extractors can be improved without re-fetching.

## Project Layout

```text
configs/                 Crawl scope and runtime configuration
data/
  raw/                   Immutable HTTP snapshots, excluded from git
  processed/             Normalized JSONL/Parquet outputs, excluded from git
  indexes/               Search/vector indexes, excluded from git
docs/                    Architecture and phase plans
reports/                 Generated inspection/QA reports
src/inspector/           Allowlist-only inspection tools
src/scraper/             Controlled pilot scraping tools
src/tvu_scraper/         Scraper, extraction, and indexing package
tests/                   Parser and contract tests
```

## Phase Plan

1. **Phase 0: Site Reconnaissance**
   - Validate page families and URL patterns.
   - Confirm robots/copyright constraints before bulk fetching.
   - Produce seed manifest from the library catalog.

2. **Phase 1: Project Scaffold**
   - Define schemas, storage layout, crawler configuration, and dry-run tools.
   - Add tests using saved small HTML fixtures, not live scraping.

3. **Phase 2: Pilot Scrape**
   - Fetch a small allowlisted set: one Thevaram branch, one Thiruppugazh branch, one Sangam framed work, one Drupal `format=simple` node.
   - Save raw snapshots and extraction outputs.
   - Review Tamil text quality manually.

4. **Phase 3: Corpus Expansion**
   - Crawl all approved catalog branches with rate limits and resume support.
   - Add duplicate detection, broken-link reports, and encoding validation.

5. **Phase 4: RAG Index**
   - Chunk by literary structure before token windows.
   - Build BM25/full-text index plus vector index.
   - Attach citations back to exact source URLs and section titles.

## Local Commands

```bash
python3 -m tvu_scraper --help
PYTHONPATH=src python3 -m tvu_scraper inspect-config configs/tamilvu.yaml
python3 src/inspector/site_inspector.py --dry-run
python3 src/inspector/site_inspector.py --delay 2.0
python3 src/inspector/discover_dynamic_content.py
python3 src/inspector/discover_dynamic_content.py --print-hymn-neighborhood
python3 src/inspector/inspect_iframe_endpoints.py
python3 src/inspector/inspect_iframe_endpoints.py --print-links
python3 src/inspector/inspect_hymn_endpoint.py
python3 src/inspector/inspect_hymn_endpoint.py --print-text-blocks
python3 src/inspector/inspect_hymn_endpoint.py --print-links
python3 src/inspector/inspect_commentary_endpoint.py
python3 src/inspector/inspect_commentary_endpoint.py --print-text-blocks
python3 src/inspector/inspect_commentary_endpoint.py --print-links
python3 src/scraper/pilot_hymn_scraper.py
python3 src/scraper/pilot_hymn_scraper.py --delay 2.0
python3 src/scraper/irandaam_thirumurai_builder.py --dry-run
python3 src/scraper/irandaam_thirumurai_builder.py --limit 3 --delay 2.0
python3 src/scraper/irandaam_thirumurai_builder.py --delay 2.0 --resume
python3 src/validation/sample_hymn_validator.py
python3 src/enrichment/build_retrieval_ready_corpus.py
python3 src/enrichment/build_retrieval_ready_corpus.py \
  --input data/releases/irandaam-thirumurai-v1/irandaam_thirumurai.jsonl \
  --output-enriched data/processed/enriched/irandaam_thirumurai_enriched.jsonl \
  --output-chunks data/processed/chunks/irandaam_thirumurai_chunks.jsonl \
  --output-lexical-index data/processed/indexes/irandaam_thirumurai_lexical_index.json \
  --output-golden-queries data/processed/eval/golden_queries.jsonl \
  --report reports/retrieval-readiness-report.md
python3 src/evaluation/evaluate_retrieval.py --mode lexical
python3 src/evaluation/evaluate_retrieval.py --mode all
python3 -m pip install -e '.[embeddings]'
python3 src/embeddings/build_embeddings.py \
  --input data/processed/chunks/irandaam_thirumurai_chunks.jsonl \
  --output data/processed/embeddings/irandaam_thirumurai_embeddings.jsonl \
  --manifest data/processed/embeddings/embedding_manifest.json
python3 src/embeddings/build_embeddings.py \
  --input data/processed/chunks/irandaam_thirumurai_chunks.jsonl \
  --output data/processed/embeddings/irandaam_thirumurai_all_chunk_embeddings.jsonl \
  --manifest data/processed/embeddings/all_chunk_embedding_manifest.json \
  --all-chunk-types
python3 src/vector_index/build_faiss_index.py
python3 src/evaluation/evaluate_retrieval.py --mode semantic
python3 src/evaluation/evaluate_retrieval.py --mode hybrid
python3 src/evaluation/evaluate_retrieval.py --mode hybrid --lexical-weight 0.65 --semantic-weight 0.35
python3 src/evaluation/evaluate_retrieval.py --mode all
python3 src/evaluation/analyze_retrieval_failures.py
python3 src/rag/build_context.py --query "திருப்பூந்தராய்" --top-k 5
python3 src/rag/build_context.py --query "திருப்பூந்தராய்" --top-k 5 --output data/processed/rag/sample_context.json
python3 src/rag/export_citations.py --input sample_context.json
python3 src/evaluation/build_question_taxonomy.py
python3 src/corpus/normalize_corpus.py
python3 src/corpus/validate_corpus.py
python3 src/corpus/audit_corpus_readiness.py
python3 src/corpus/pilot_ingest_thirumurai.py --thirumurai-no 4
python3 src/corpus/normalize_corpus.py --corpus-id thirumurai_04
python3 src/corpus/validate_corpus.py --corpus-id thirumurai_04
python3 src/corpus/audit_corpus_readiness.py --corpus-id thirumurai_04
python3 -m pytest
```

Dependencies are declared in `pyproject.toml`; install them in a virtual environment when we begin implementation/testing.

The site inspector is not a full scraper. It only fetches the default manual-inspection allowlist or URLs explicitly passed with `--url`, saves raw HTML under `data/raw/inspection/`, and writes `reports/site-inspection-report.md`.

The dynamic content discovery script reads the saved Thirumurai snapshot by default and writes `reports/dynamic-content-discovery.md`. It does not recurse or use browser automation. Pass `--fetch` only if you intentionally want to refresh the single target page.

The iframe endpoint inspector fetches only the two discovered frame URLs, saves snapshots under `data/raw/inspection/frames/`, and writes `reports/iframe-endpoint-inspection.md`.

The hymn endpoint inspector fetches only one selected hymn endpoint by default, saves its snapshot under `data/raw/inspection/hymns/`, and writes `reports/hymn-endpoint-inspection.md`.

The commentary endpoint inspector fetches only one selected commentary endpoint by default, saves its snapshot under `data/raw/inspection/commentary/`, and writes `reports/commentary-endpoint-inspection.md`.

The pilot hymn scraper extracts exactly one hymn, `subid=1664`, fetches its 10 discovered commentary pages, writes JSONL to `data/processed/pilot/thevaram_hymn_1664.jsonl`, and writes `reports/pilot-hymn-1664-report.md`.

The Irandaam Thirumurai builder starts from the left-frame navigation endpoint, discovers the 122 strict hymn endpoint links, and can build a controlled corpus with `--limit` or resume from saved snapshots with `--resume`. It is still scoped to Irandaam Thirumurai only.

The corpus validation sampler checks first/middle/last hymn samples before a full Irandaam Thirumurai run and writes `reports/corpus-validation-sampling-report.md`.

The retrieval-ready corpus builder derives v1.1 enrichment artifacts from the frozen v1 release. It normalizes text, creates deterministic IDs and chunks, builds a lexical index, and writes golden retrieval queries without creating embeddings or a vector database.

The retrieval benchmark evaluates deterministic lexical retrieval against golden queries and scaffolds semantic/hybrid modes as `PENDING_EMBEDDINGS`.

The embedding builder derives local sentence-transformer embedding artifacts from retrieval-ready chunks. It defaults to `verse_plus_commentary`, preserves deterministic chunk IDs and source metadata, and does not create a vector database or call paid/cloud embedding APIs.

The local vector index builder indexes generated `verse_plus_commentary` embeddings with FAISS when available, or a NumPy cosine-similarity fallback otherwise. Semantic benchmark mode uses that local index.

The hybrid retriever combines lexical and semantic candidates with deterministic weighted scoring, exact-match boosts, metadata boosts, and fixed ablation reporting.

The retrieval error analyzer reads saved benchmark results, classifies semantic failures, measures score/rank patterns, and explains how hybrid lexical signals recovered failed queries without rerunning retrieval.

The RAG context builder packages hybrid retrieval results with normalized verse text, commentary, metadata, deterministic context IDs, citations, source URLs, and bounded context-size metadata. It does not call an LLM or generate answers.

The citation exporter converts context packages into validated song-level citations with deterministic IDs, hymn grouping, exact TamilVU source URLs, and optional mappings for multiple citations per future answer segment.

The question taxonomy builder generates and validates 100 deterministic Tamil literary evaluation questions spanning lookup, verse identification, word occurrence, synonym expansion, deity and epithet analysis, literary devices, poet comparison, cross-corpus analysis, and failure diagnosis. It defines evaluation requirements only and makes no LLM or network calls.

The multi-Thirumurai normalization framework registers all twelve Thirumurai, maps the existing Irandaam Thirumurai v1.1 records into a shared cross-corpus schema, and validates stable IDs, literary hierarchy, text fields, and source provenance. It does not fetch any new content.

The corpus readiness audit measures data, parser, metadata, citation, retrieval, analytical, and scaling readiness before any additional Thirumurai scrape. It is read-only and produces deterministic JSON and Markdown evidence.

The controlled Fourth Thirumurai pilot ingests only five Appar hymns, preserving raw snapshots and source URLs separately from existing corpora. It proves a source-specific adapter, unified normalization, validation, and readiness audit without authorizing full Fourth Thirumurai extraction.

## Website-Wide Tamil Corpus Architecture

Thirumurai is now treated as one proven pilot collection family inside a future website-wide Tamil Literary KnowledgeHub. The category registry and schema v2 cover poetry, prose, grammar, dictionaries, encyclopedias, terminology tables, manuscripts, image collections, public-domain books, and external-library references.

Scraping remains controlled and book-specific. No full website crawl is authorized; each parser family must pass source inspection, a bounded pilot, validation, and audit first.

## Controlled Multi-Category Pilot Ingestion

The category pilot framework is capped at one approved local book and ten records. It has
no network fetch path and writes only to category-specific pilot directories. The current
verification category is `saivam`, using the existing validated Fourth Thirumurai pilot as
a read-only seed; other pilot categories remain blocked pending source inspection.

```bash
python3 src/corpus/pilot_ingest_category.py --category-id CATEGORY_ID --dry-run
python3 src/corpus/pilot_ingest_category.py --category-id CATEGORY_ID --max-books 1 --max-records 10
python3 src/corpus/normalize_category_corpus.py --category-id CATEGORY_ID
python3 src/corpus/validate_category_corpus.py --category-id CATEGORY_ID
```

## Pilot Source Inspection And Fixtures

The source inspection planner identifies unverified pilot categories from the registry and
creates only small fixture requirements, placeholder directories, and a deterministic
report. It does not fetch TamilVU pages or ingest category content.

```bash
python3 src/corpus/inspect_pilot_sources.py --dry-run
python3 src/corpus/inspect_pilot_sources.py
```

## Dictionary Pilot

The first non-Thirumurai pilot uses exactly three allowlisted pages from the Tamil–Tamil
Agaramuthali by M. Shanmugampillai. Navigation fixtures are retained for provenance; only
the exact single-entry fixture produces a corpus record.

```bash
python3 src/corpus/pilot_ingest_category.py --category-id dictionaries
python3 src/corpus/normalize_category_corpus.py --category-id dictionaries
python3 src/corpus/validate_category_corpus.py --category-id dictionaries
```

## Sangam Literature Pilot

The Sangam pilot uses exactly three allowlisted Natrinai pages. The committed source
fixture contains a bounded excerpt of poems 1-3 and preserves poem number, thinai, verse
lines, situation, poet, source URL, and commentary URL. It performs no live fetch.

```bash
python3 src/corpus/pilot_ingest_category.py --category-id sangam_literature
python3 src/corpus/normalize_category_corpus.py --category-id sangam_literature
python3 src/corpus/validate_category_corpus.py --category-id sangam_literature
```

## Grammar Pilot

The grammar pilot uses exactly three allowlisted Nannul pages and parses rules 56 and 57
from `எழுத்து இயல்`. Rule text, hierarchy, source URL, and commentary URL are preserved;
commentary text is not fetched within this pilot.

```bash
python3 src/corpus/pilot_ingest_category.py --category-id grammar
python3 src/corpus/normalize_category_corpus.py --category-id grammar
python3 src/corpus/validate_category_corpus.py --category-id grammar
python3 src/corpus/validate_pilot_categories.py
python3 src/corpus/audit_multi_category_readiness.py
```

## Twentieth-Century Prose Pilot

The prose pilot inspects exactly three allowlisted Bharathiyar Essays pages, then uses
compact rights-safe structural fixtures because TamilVU's policy requires permission
before reproducing site data. Two synthetic Tamil paragraphs validate deterministic
paragraph segmentation, schema v2 normalization, source traceability, and rights metadata.
This does not authorize source-text ingestion or category scraping.

```bash
python3 src/corpus/pilot_ingest_category.py --category-id twentieth_century_prose
python3 src/corpus/normalize_category_corpus.py --category-id twentieth_century_prose
python3 src/corpus/validate_category_corpus.py --category-id twentieth_century_prose
python3 src/corpus/validate_pilot_categories.py
python3 src/corpus/audit_multi_category_readiness.py
```

## Cross-Pilot Validation

The cross-pilot validator compares the verified Saivam, Sangam, and dictionary artifacts,
measures schema and citation coverage, and recommends the next fixture category. It is
offline and read-only with respect to pilot corpora.

```bash
python3 src/corpus/validate_pilot_categories.py
```

## Multi-Category Readiness Audit

The readiness audit uses the five verified local pilots to score schema, parser,
metadata, citation, analytics, and 32-category expansion readiness. It performs no network
access, ingestion, embedding, indexing, or corpus mutation.

```bash
python3 src/corpus/audit_multi_category_readiness.py
```

## Tamil Literary Knowledge Layer

The knowledge-layer foundation defines deterministic registries for entities, synonyms,
motifs, authors, deities, places, works, themes, and literary devices. Current entries are
small illustrative seeds only: they are not extracted corpus annotations and are not
evidence for analytical claims.

The readiness analyzer validates registry schemas and reports foundation readiness
separately from analytical readiness. Future phases will populate reviewed authorities,
link exact corpus evidence, extract literary devices, build exhaustive aggregation, and
add analytical retrieval. This layer will resolve query concepts before retrieval and
provide evidence-backed groupings to future RAG, while citation grounding remains tied to
the original corpus records and TamilVU source URLs.

```bash
python3 src/knowledge/analyze_knowledge_readiness.py
```

Planned sequence: entity population, synonym population, motif population, literary-device
extraction, aggregation engine, then analytical retrieval. No answer generation is part of
the current phase.

### Curated Knowledge Layer Status

Five registries now contain manually curated gold-standard seeds:

- 3 synonym concepts with 9 canonical, synonym, and variant forms
- 3 deities with normalized aliases
- 3 Tevaram authors with known-work identifiers
- 3 imagery motifs
- 3 literary devices

Foundation readiness is `79.4/100`, up from `70.0`; analytical readiness is `47.5/100`,
up from `35.0`. The remaining gap is intentional: there are still no corpus evidence spans,
automatic extractions, aggregation results, or query-expansion behavior.

```bash
python3 src/knowledge/validate_registries.py
python3 src/knowledge/analyze_knowledge_readiness.py
python3 src/retrieval/expand_query.py --query "அப்பர் பாடல்கள்"
python3 src/retrieval/expand_query.py --query "சந்திரன் வரும் பாடல்கள்"
python3 src/rag/build_context.py --query "அப்பர் பாடல்கள்" --top-k 5 --expand-query
python3 src/evaluation/evaluate_query_expansion.py
python3 src/analytics/build_occurrence_index.py
python3 src/analytics/search_occurrences.py --term "சந்திரன்"
python3 src/analytics/search_occurrences.py --term "சந்திரன்" --expand-query
python3 src/analytics/analyze_term.py --term "சந்திரன்"
python3 src/analytics/analyze_term.py --term "சந்திரன்" --expand-query
python3 src/analytics/analyze_term.py --term "சிவன்" --group-by author
python3 src/analytics/ask_analytics.py --query "எந்த ஆசிரியர் சந்திரன் தொடர்பான சொற்களை அதிகம் பயன்படுத்துகிறார்?"
python3 src/analytics/ask_analytics.py --query "எந்த corpus-இல் சிவன் அதிகமாக குறிப்பிடப்படுகிறார்?"
python3 src/analytics/ask_analytics.py --query "உவமை எந்த works-இல் அதிகம் வருகிறது?"
python3 src/evaluation/evaluate_analytics.py
python3 src/evaluation/failure_attribution.py
```

The next phase depends on cited lexical authorities, Tamil researcher review, and a small
manually annotated corpus sample with positive, negative, and ambiguous examples.

## Registry-Driven Query Expansion

The curated synonym, author, deity, motif, and literary-device registries can now expand
queries before hybrid retrieval. Expansion is opt-in, deterministic, and records every
matched registry and added term. Ordinary context building remains unchanged unless
`--expand-query` is supplied.

```bash
python3 src/retrieval/expand_query.py --query "அப்பர் பாடல்கள்"
python3 src/retrieval/expand_query.py --query "சந்திரன் வரும் பாடல்கள்"
python3 src/rag/build_context.py --query "அப்பர் பாடல்கள்" --top-k 5 --expand-query
python3 src/evaluation/evaluate_query_expansion.py
```

The evaluation compares baseline and expanded hybrid retrieval for four curated queries.
Its improved/degraded/neutral label is based on a transparent local corpus-evidence proxy,
not on human relevance judgment. No scraping, LLM call, embedding generation, or vector
index rebuild is performed.

## Corpus-Wide Occurrence Search

The occurrence index searches all currently normalized local corpora and returns exact
evidence occurrences with field names, snippets, record IDs, authors, and source URLs.
It is different from top-k retrieval: occurrence search is exhaustive evidence collection
for future aggregation and statistics.

```bash
python3 src/analytics/build_occurrence_index.py
python3 src/analytics/search_occurrences.py --term "சந்திரன்"
python3 src/analytics/search_occurrences.py --term "சந்திரன்" --expand-query
```

The `--expand-query` option uses the curated registries to search concept terms such as
`சந்திரன்`, `நிலா`, `மதி`, and `திங்கள்` together. This phase does not aggregate counts
into literary claims, build analytical retrieval, call an LLM, scrape, or modify frozen
corpus artifacts.

## Aggregation And Statistics

The aggregation engine groups occurrence evidence by author, category, work, record type,
or source and reports counts, top-N rankings, unique record/work/author counts, and
percentage distributions. It consumes the occurrence index only; it does not scrape,
generate answers, call an LLM, or perform analytical retrieval.

```bash
python3 src/analytics/analyze_term.py --term "சந்திரன்"
python3 src/analytics/analyze_term.py --term "சந்திரன்" --expand-query
python3 src/analytics/analyze_term.py --term "சிவன்" --group-by author
```

## Analytical Retrieval

The analytical retriever maps simple Tamil or English analytical questions to structured
occurrence, expansion, aggregation, and statistics operations. It returns JSON with the
intent, term, grouping dimension, ranked groups, and evidence samples. It is rule-based
and does not generate fluent answers.

```bash
python3 src/analytics/ask_analytics.py --query "எந்த ஆசிரியர் சந்திரன் தொடர்பான சொற்களை அதிகம் பயன்படுத்துகிறார்?"
python3 src/analytics/ask_analytics.py --query "எந்த corpus-இல் சிவன் அதிகமாக குறிப்பிடப்படுகிறார்?"
python3 src/analytics/ask_analytics.py --query "உவமை எந்த works-இல் அதிகம் வருகிறது?"
```

## Evaluation And Failure Attribution

The analytics evaluation framework runs a deterministic benchmark over analytical
retrieval, query expansion, occurrence search, aggregation, and statistics. Failure
attribution classifies non-successful cases into explainable categories such as
`analytics_gap`, `synonym_gap`, `occurrence_gap`, and `aggregation_gap`.

```bash
python3 src/evaluation/evaluate_analytics.py
python3 src/evaluation/failure_attribution.py
```

The workflow produces machine-readable evaluation results, failure-attribution results,
and Markdown reports. It performs no scraping, extraction, answer generation, LLM call,
GCP work, embedding regeneration, or vector-index rebuild.
