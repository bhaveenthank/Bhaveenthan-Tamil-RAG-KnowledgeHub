# Dictionary Pilot Validation Report

## Summary

- Records validated: `1`
- Status: `VALID`
- Validation errors: `0`
- Source URL coverage: `100.0%`
- Duplicate record IDs: `0`
- Non-deterministic IDs: `0`
- Malformed source URLs: `0`

## Dictionary Fields

| Missing Field | Count |
| --- | ---: |
| None | 0 |

`part_of_speech` is optional because the selected source table does not label it
explicitly. The parser leaves it empty and records `part_of_speech_source=not_provided`
instead of inferring a grammatical category.

## Decision

The dictionary pilot is `PILOT_VERIFIED`.
This decision applies only to the three-page fixture set and does not authorize category
scraping.
