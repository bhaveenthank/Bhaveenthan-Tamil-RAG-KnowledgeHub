# Corpus Audit Report

## Executive Summary

- Corpus records audited: `1331`
- Unique hymns: `122`
- Partial commentary records: `7`
- Schema violations: `0`
- Duplicate song_no: `0`
- Coverage sample average: `100.00%`
- Freeze recommendation: `FREEZE_READY`

## Corpus Statistics

- Total hymns: `122`
- Total verses: `1331`
- Average verses per hymn: `10.91`
- Minimum verses per hymn: `10`
- Maximum verses per hymn: `12`
- Commentary coverage: `100.00%`
- Pozhppurai coverage: `99.70%`
- Kurippurai coverage: `99.77%`
- Verse length distribution: `{'min': 54, 'p50': 185.0, 'p95': 248.0, 'max': 304}`
- Commentary length distribution: `{'min': 79, 'p50': 509.0, 'p95': 988.0, 'max': 3350}`
- Verse line count distribution: `{2: 1, 3: 1, 4: 429, 5: 336, 6: 147, 7: 123, 8: 93, 9: 175, 10: 21, 11: 5}`

## Integrity Validation

- Missing verse text: `0`
- Missing commentary URLs: `0`
- Missing pozhppurai: `4`
- Missing kurippurai: `3`
- Duplicate song_no: `0`
- Duplicate hymn URLs across hymn IDs: `0`
- Duplicate commentary URLs: `0`
- Song/commentary URL mismatches: `0`
- Hymn/commentary URL mismatches: `0`
- Null values: `0`
- Empty required strings: `0`
- Status inconsistencies: `0`
- Malformed source parameters: `0`
- Malformed extraction metadata: `0`
- Corrupted Tamil text signals: `0`
- Unusual non-Tamil content signals: `0`
- Suspiciously short verses: `0`
- Suspiciously short commentary: `0`

## Schema Validation

- Schema violations: `0`
- Missing required fields: `0`
- Invalid field types: `0`

## Coverage Validation

- Sampled hymns: `30`
- Average coverage: `100.00%`

## Partial Commentary Audit

| Hymn ID | Song No | Missing | Source Contains Field | Parser Extracted | Classification | Action |
| --- | --- | --- | --- | --- | --- | --- |
| `1704` | `1914` | pozhppurai | {'pozhppurai': False, 'kurippurai': True} | {'pozhppurai': False, 'kurippurai': True} | `SOURCE_MISSING` | Human review TamilVU page; accept partial record if source truly omits section. |
| `1717` | `2053` | pozhppurai | {'pozhppurai': False, 'kurippurai': True} | {'pozhppurai': False, 'kurippurai': True} | `SOURCE_MISSING` | Human review TamilVU page; accept partial record if source truly omits section. |
| `1720` | `2082` | pozhppurai | {'pozhppurai': False, 'kurippurai': True} | {'pozhppurai': False, 'kurippurai': True} | `SOURCE_MISSING` | Human review TamilVU page; accept partial record if source truly omits section. |
| `1721` | `2097` | kurippurai | {'pozhppurai': True, 'kurippurai': False} | {'pozhppurai': True, 'kurippurai': False} | `SOURCE_MISSING` | Human review TamilVU page; accept partial record if source truly omits section. |
| `1742` | `2325` | pozhppurai | {'pozhppurai': False, 'kurippurai': True} | {'pozhppurai': False, 'kurippurai': True} | `SOURCE_MISSING` | Human review TamilVU page; accept partial record if source truly omits section. |
| `1759` | `2517` | kurippurai | {'pozhppurai': True, 'kurippurai': False} | {'pozhppurai': True, 'kurippurai': False} | `SOURCE_MISSING` | Human review TamilVU page; accept partial record if source truly omits section. |
| `1776` | `2701` | kurippurai | {'pozhppurai': True, 'kurippurai': False} | {'pozhppurai': True, 'kurippurai': False} | `SOURCE_MISSING` | Human review TamilVU page; accept partial record if source truly omits section. |

## Top Unusual Records

These are the shortest total-commentary records, useful for manual spot checks.

| Hymn ID | Song No | Commentary Chars | Status | URL |
| --- | --- | ---: | --- | --- |
| `1759` | `2517` | 79 | `partial_commentary` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=2517&book_id=110&head_id=60&sub_id=1759` |
| `1702` | `1890` | 116 | `success` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=1890&book_id=110&head_id=60&sub_id=1702` |
| `1702` | `1892` | 161 | `success` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=1892&book_id=110&head_id=60&sub_id=1702` |
| `1737` | `2269` | 197 | `success` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=2269&book_id=110&head_id=60&sub_id=1737` |
| `1736` | `2258` | 203 | `success` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=2258&book_id=110&head_id=60&sub_id=1736` |
| `1702` | `1888` | 204 | `success` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=1888&book_id=110&head_id=60&sub_id=1702` |
| `1737` | `2271` | 207 | `success` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=2271&book_id=110&head_id=60&sub_id=1737` |
| `1691` | `1774` | 218 | `success` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=1774&book_id=110&head_id=60&sub_id=1691` |
| `1690` | `1763` | 220 | `success` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=1763&book_id=110&head_id=60&sub_id=1690` |
| `1737` | `2268` | 234 | `success` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=2268&book_id=110&head_id=60&sub_id=1737` |

## Records Requiring Human Review

| Hymn ID | Song No | Missing | Classification | URL |
| --- | --- | --- | --- | --- |
| `1704` | `1914` | pozhppurai | `SOURCE_MISSING` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=1914&book_id=110&head_id=60&sub_id=1704` |
| `1717` | `2053` | pozhppurai | `SOURCE_MISSING` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=2053&book_id=110&head_id=60&sub_id=1717` |
| `1720` | `2082` | pozhppurai | `SOURCE_MISSING` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=2082&book_id=110&head_id=60&sub_id=1720` |
| `1721` | `2097` | kurippurai | `SOURCE_MISSING` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=2097&book_id=110&head_id=60&sub_id=1721` |
| `1742` | `2325` | pozhppurai | `SOURCE_MISSING` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=2325&book_id=110&head_id=60&sub_id=1742` |
| `1759` | `2517` | kurippurai | `SOURCE_MISSING` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=2517&book_id=110&head_id=60&sub_id=1759` |
| `1776` | `2701` | kurippurai | `SOURCE_MISSING` | `https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=2701&book_id=110&head_id=60&sub_id=1776` |

## Identified Risks

- Seven records have partial commentary. Automated evidence classifies them as source-missing unless manual inspection proves otherwise.
- Freeze decision should preserve partial records with explicit status rather than fabricating missing commentary.
- Future parser work must use fixtures and a separate repair phase.

## Freeze Recommendation

`FREEZE_READY`