# Failure Taxonomy

| Failure Type | Definition | Examples | Detection Criteria | Mitigation |
| --- | --- | --- | --- | --- |
| `data_gap` | Expected evidence is absent from the current local corpus. | Query asks about a work not ingested yet. | Zero or too few occurrences despite correct routing. | Ingest reviewed source scope or mark unsupported. |
| `parser_gap` | Source evidence exists but parser output does not expose it. | Commentary omitted from normalized records. | Source fixture contains field but normalized field is empty. | Add parser fixture and parser repair phase. |
| `metadata_gap` | Required metadata is missing or inconsistent. | Author or work labels unavailable for grouping. | Correct occurrences but wrong or unknown groups. | Normalize metadata fields and registry mappings. |
| `retrieval_gap` | Ranked retrieval misses expected evidence. | Semantic top-k omits exact song record. | Expected record absent from top-k retrieval result. | Tune lexical/hybrid retrieval or filters. |
| `query_expansion_gap` | Expansion was expected but not applied correctly. | Alias not added for an author query. | Expected expansion true but observed false. | Improve registry matching and expansion rules. |
| `synonym_gap` | Equivalent terms are missing from registry or matched-term set. | Moon query lacks `நிலா` or `மதி`. | Required matched terms are not a subset of observed terms. | Curate registry additions with review. |
| `occurrence_gap` | Occurrence search fails to find expected rows. | Literal term exists in index but count is low. | Correct expansion but occurrence threshold not met. | Inspect index fields, normalization, and matching. |
| `aggregation_gap` | Grouping, ranking, or counting is wrong. | Expected top corpus differs from observed top corpus. | Occurrences exist but top group/count mismatches. | Inspect group metadata and aggregation sort rules. |
| `analytics_gap` | Question classification, term extraction, or routing fails. | Author question routed to category grouping. | Intent or extracted term mismatches expected values. | Add deterministic classifier rule or term pattern. |
| `registry_gap` | Curated registry coverage is insufficient or wrong. | Deity alias missing from `deities.json`. | Failure traces to absent or stale registry record. | Add reviewed curated seed or authority-backed entry. |
| `architecture_gap` | Required component path cannot execute. | Missing artifact prevents evaluation. | No observed output or missing component result. | Repair CLI/artifact wiring. |
| `evaluation_gap` | Benchmark expectation is wrong, stale, or underspecified. | Expected top group no longer matches updated corpus. | Evidence contradicts benchmark assumption. | Update benchmark with reviewed expected outcome. |
| `unknown` | Evidence is insufficient for a stronger diagnosis. | Multiple components could explain mismatch. | No attribution rule matches. | Add diagnostics and a new deterministic rule. |
