# Citation Grounding Report

## Summary

- Input context package: `data/processed/rag/sample_context.json`
- Contexts represented: `5`
- Citations generated: `5`
- Citation groups: `1`
- Citation coverage: `100.00%`
- Complete citations: `5`
- Incomplete citations: `0`
- Source URL coverage: `100.00%`
- Commentary URL coverage: `100.00%`
- Duplicate citations removed/detected: `0`

## Citation Coverage

| Citation ID | Context | Hymn ID | Song No | Source URL | Commentary URL | Complete |
| --- | --- | --- | --- | --- | --- | --- |
| `cit_001` | `ctx_001` | `1664` | `1470` | `True` | `True` | `True` |
| `cit_002` | `ctx_002` | `1664` | `1471` | `True` | `True` | `True` |
| `cit_003` | `ctx_003` | `1664` | `1472` | `True` | `True` | `True` |
| `cit_004` | `ctx_004` | `1664` | `1473` | `True` | `True` | `True` |
| `cit_005` | `ctx_005` | `1664` | `1474` | `True` | `True` | `True` |

## Missing Field Analysis

- No required citation fields are missing.

## Duplicate Analysis

- No duplicate citation records remain.

## Grounding Decision

- Package validation: `valid`
- Every citation retains exact corpus identifiers, retrieval rank, source title, and TamilVU URLs.
- These citation IDs can later be attached to one or more answer segments without changing source traceability.
