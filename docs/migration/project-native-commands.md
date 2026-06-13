# Project-Native Commands

The reorganized workspace exposes stable `tvu-*` console commands from the root
`pyproject.toml` and from the owning subproject `pyproject.toml` files. The older
`python3 src/...` commands are compatibility shims only.

## Crawler

| Command | Owner | Replaces |
| --- | --- | --- |
| `tvu-scraper` | `projects/crawler` | `PYTHONPATH=src python3 -m tvu_scraper` |
| `tvu-inspect-site` | `projects/crawler` | `python3 src/inspector/site_inspector.py` |
| `tvu-discover-dynamic-content` | `projects/crawler` | `python3 src/inspector/discover_dynamic_content.py` |
| `tvu-inspect-iframes` | `projects/crawler` | `python3 src/inspector/inspect_iframe_endpoints.py` |
| `tvu-inspect-hymn` | `projects/crawler` | `python3 src/inspector/inspect_hymn_endpoint.py` |
| `tvu-inspect-commentary` | `projects/crawler` | `python3 src/inspector/inspect_commentary_endpoint.py` |

## Parser

| Command | Owner | Replaces |
| --- | --- | --- |
| `tvu-scrape-pilot-hymn` | `projects/parser` | `python3 src/scraper/pilot_hymn_scraper.py` |
| `tvu-build-irandaam-thirumurai` | `projects/parser` | `python3 src/scraper/irandaam_thirumurai_builder.py` |
| `tvu-pilot-ingest-thirumurai` | `projects/parser` | `python3 src/corpus/pilot_ingest_thirumurai.py` |
| `tvu-pilot-ingest-category` | `projects/parser` | `python3 src/corpus/pilot_ingest_category.py` |
| `tvu-validate-sample-hymn` | `projects/parser` | `python3 src/validation/sample_hymn_validator.py` |

## Normalizer

| Command | Owner | Replaces |
| --- | --- | --- |
| `tvu-normalize-corpus` | `projects/normalizer` | `python3 src/corpus/normalize_corpus.py` |
| `tvu-normalize-category` | `projects/normalizer` | `python3 src/corpus/normalize_category_corpus.py` |
| `tvu-validate-corpus` | `projects/normalizer` | `python3 src/corpus/validate_corpus.py` |
| `tvu-validate-category` | `projects/normalizer` | `python3 src/corpus/validate_category_corpus.py` |
| `tvu-audit-corpus-readiness` | `projects/normalizer` | `python3 src/corpus/audit_corpus_readiness.py` |
| `tvu-audit-multi-category-readiness` | `projects/normalizer` | `python3 src/corpus/audit_multi_category_readiness.py` |
| `tvu-inspect-pilot-sources` | `projects/normalizer` | `python3 src/corpus/inspect_pilot_sources.py` |

## Retrieval

| Command | Owner | Replaces |
| --- | --- | --- |
| `tvu-build-retrieval-corpus` | `projects/retrieval` | `python3 src/enrichment/build_retrieval_ready_corpus.py` |
| `tvu-build-embeddings` | `projects/retrieval` | `python3 src/embeddings/build_embeddings.py` |
| `tvu-build-vector-index` | `projects/retrieval` | `python3 src/vector_index/build_faiss_index.py` |
| `tvu-expand-query` | `projects/retrieval` | `python3 src/retrieval/expand_query.py` |
| `tvu-build-context` | `projects/retrieval` | `python3 src/rag/build_context.py` |
| `tvu-export-citations` | `projects/retrieval` | `python3 src/rag/export_citations.py` |
| `tvu-build-occurrence-index` | `projects/retrieval` | `python3 src/analytics/build_occurrence_index.py` |
| `tvu-search-occurrences` | `projects/retrieval` | `python3 src/analytics/search_occurrences.py` |
| `tvu-analyze-term` | `projects/retrieval` | `python3 src/analytics/analyze_term.py` |
| `tvu-ask-analytics` | `projects/retrieval` | `python3 src/analytics/ask_analytics.py` |

## Evaluation

| Command | Owner | Replaces |
| --- | --- | --- |
| `tvu-build-question-taxonomy` | `projects/evaluation` | `python3 src/evaluation/build_question_taxonomy.py` |
| `tvu-evaluate-retrieval` | `projects/evaluation` | `python3 src/evaluation/evaluate_retrieval.py` |
| `tvu-evaluate-query-expansion` | `projects/evaluation` | `python3 src/evaluation/evaluate_query_expansion.py` |
| `tvu-evaluate-analytics` | `projects/evaluation` | `python3 src/evaluation/evaluate_analytics.py` |
| `tvu-analyze-retrieval-failures` | `projects/evaluation` | `python3 src/evaluation/analyze_retrieval_failures.py` |
| `tvu-run-comprehensive-benchmark` | `projects/evaluation` | `python3 src/evaluation/run_comprehensive_benchmark.py` |
| `tvu-validate-pilot-categories` | `projects/evaluation` | `python3 src/corpus/validate_pilot_categories.py` |
| `tvu-failure-attribution` | `projects/evaluation` | `python3 src/evaluation/failure_attribution.py` |

## Knowledge

| Command | Owner | Replaces |
| --- | --- | --- |
| `tvu-validate-registries` | `projects/knowledge` | `python3 src/knowledge/validate_registries.py` |
| `tvu-analyze-knowledge-readiness` | `projects/knowledge` | `python3 src/knowledge/analyze_knowledge_readiness.py` |
| `tvu-validate-annotations` | `projects/knowledge` | `python3 src/knowledge/validate_annotations.py` |
| `tvu-analyze-annotation-readiness` | `projects/knowledge` | `python3 src/knowledge/analyze_annotation_readiness.py` |
| `tvu-evaluate-entity-extraction` | `projects/knowledge` | `python3 src/knowledge/evaluate_entity_extraction.py` |
| `tvu-analyze-extraction-readiness` | `projects/knowledge` | `python3 src/knowledge/analyze_extraction_readiness.py` |

## Compatibility Policy

Legacy `src/...` shims may remain while historical commands and notebooks still use
them, but new work should prefer the project-native commands above. Removing the shims is
a release-management decision, not a required step for project ownership boundaries.
