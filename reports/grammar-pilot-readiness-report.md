# Grammar Pilot Readiness Report

## Pilot Result

- Fixtures collected: `3`
- Records parsed: `2`
- Records normalized: `2`
- Validation errors: `0`
- Source URL coverage: `100.0%`
- Missing required grammar metadata: `0`

## Assessment

| Dimension | Result | Evidence |
| --- | --- | --- |
| Parser quality | `READY` | Two numbered Nannul rules parsed with preserved line breaks |
| Normalization quality | `READY` | Unified schema v2 retains rule, chapter, section, and source identity |
| Metadata quality | `READY` | Exact rule page, commentary URL, fixture checksum, work, and subid retained |
| Citation readiness | `READY` | Work, subsection, and rule number form stable citations |
| Linguistic-analysis contribution | `FOUNDATIONAL` | Adds explicit grammatical rules and classifications beyond literary and lexical records |

## Comparison With Existing Pilots

Verse records center on ordered poetic lines and literary hierarchy. Dictionary records
center on headwords and definitions. Grammar records center on a numbered rule within a
chapter and section, with explanation kept separate. The common envelope supports all
three shapes without reusing verse or dictionary fields incorrectly.

## Missing Metadata Findings

No required grammar field is missing. `explanation_text` is empty because the source places
commentary behind separate `உரை` endpoints and the approved fixture budget was exhausted.
The exact commentary URLs are retained for a later, separately approved inspection.

## Risks Before Expansion

- Other Nannul sections may contain different rule or commentary layouts.
- Examples, exceptions, commentator identity, and cross-rule references are not yet parsed.
- Tolkappiyam and other grammar works may use deeper chapter/commentary hierarchy.
- The parser must not treat metrical rule text as ordinary literary verse.

## Recommendation

`PILOT_VERIFIED` for the bounded Nannul fixture set.
Before broader grammar ingestion, inspect structurally different rules and one commentary
endpoint under a new allowlisted phase.
