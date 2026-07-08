# Thevaram 1-8 Schema And Ingestion

## Architectural Verdict

Use normalized relational-style tables, not one flat table.

A flat table would repeat Thirumurai, author, paadal thogupu, thalam, pann, and source
metadata on every paadal row. That makes correction, annotation, and RAG chunking harder.
The better shape is:

```text
thirumurai_books
  1 -> many paadal_thogupugal
paadal_thogupugal
  1 -> many paadalgal
paadalgal
  1 -> 0/1 commentaries
paadalgal/commentaries
  1 -> many text_spans
```

This preserves the hierarchy the TamilVU pages expose:

- திருமுறை
- பாடல் தொகுப்பு / பதிகம்
- பாடல்
- உரை: குறிப்புரை and பொழிப்புரை
- spans over paadal/commentary text

## Table Outputs

The command `tvu-build-thevaram-tables` writes JSONL tables under
`data/processed/thevaram/`.

| Table | Purpose |
| --- | --- |
| `thirumurai_books.jsonl` | One row per Thirumurai/work source. |
| `paadal_thogupugal.jsonl` | One row per TamilVU paadal thogupu/pathigam link. |
| `paadalgal.jsonl` | One row per paadal, including normalized text and tokenized paadal. |
| `commentaries.jsonl` | One row per paadal commentary, split into `kurippurai` and `pozhppurai`. |
| `text_spans.jsonl` | Line/commentary spans with offsets and span types. |

All rows include `schema_version = thevaram-relational-v1`. The table bundle contract is
also recorded as `shared/tvu-schemas/schemas/thevaram_relational_tables.schema.json`.

## Important Columns

### `thirumurai_books`

- `thirumurai_no`
- `corpus_id`
- `title`
- `work_id`
- `work_title`
- `author`
- `nayanmar`
- `source_url`
- `verified_navigation`

### `paadal_thogupugal`

- `thogupu_id`
- `thirumurai_no`
- `ordinal`
- `title`
- `paadapatta_thalam`
- `title_note`
- `pann`
- `source_url`
- `source_subid`

### `paadalgal`

- `paadal_id`
- `thogupu_id`
- `thirumurai_no`
- `global_song_no`
- `source_song_no`
- `local_song_no`
- `verse_index_in_thogupu`
- `paadal_text`
- `tokenized_paadal`
- `source_url`
- `commentary_url`
- `source_parameters`

### `commentaries`

- `commentary_id`
- `paadal_id`
- `kurippurai`
- `pozhppurai`
- `extraction_status`
- `warnings`

### `text_spans`

- `span_id`
- `parent_id`
- `field_name`
- `span_type`
- `start_char`
- `end_char`
- `text`
- `metadata`

## Current Implementation Status

Implemented:

- Config-driven table builder: `projects/parser/src/scraper/thevaram_corpus.py`
- Project command: `tvu-build-thevaram-tables`
- Raw snapshot preservation under `data/raw/corpus/thevaram/...`
- Resume mode
- Offline rebuild mode (`--offline`) for parsing only cached raw snapshots
- Targeted failure-fetch mode (`--fetch-failures`) for retrying only missing raw URLs
- Navigation dry-run mode
- Live execution for the approved Thirumurai 1-8 allowlist
- Paadal tokenization
- Commentary attachment by `paadal_id`
- Paadal and commentary line spans
- Layout support for the nested/separate-table poem layouts used by Thirumurai 5 and 8
- Stable song-number disambiguation for TamilVU source `song_no` collisions. `global_song_no`
  is table-safe and unique within a Thirumurai; `source_song_no` preserves the original
  TamilVU URL `song_no` for provenance.
- Compact summary output for large scrape runs
- Multi-method targeted retry reporting for missing raw pages. The retry mode still
  preserves the original TamilVU logical URL as the raw snapshot key, while recording
  the actual fetch method in `failure_fetch_summary.json`.

Latest offline rebuild from cached raw snapshots:

```bash
python3 -m scraper.thevaram_corpus \
  --thirumurai 1-8 \
  --resume \
  --execute \
  --offline \
  --delay 0
```

Observed output:

- `thirumurai_books`: 8
- `paadal_thogupugal`: 841
- `paadalgal`: 5450
- `commentaries`: 5450
- `text_spans`: 28646
- remaining missing cached raw snapshots: 4994
  - missing hymn/thogupu pages: 331
  - missing commentary pages: 4663

Paadal rows currently parsed by Thirumurai:

| Thirumurai | Parsed paadal rows |
| --- | ---: |
| 1 | 763 |
| 2 | 111 |
| 3 | 0 |
| 4 | 802 |
| 5 | 1015 |
| 6 | 971 |
| 7 | 1006 |
| 8 | 782 |

This is not yet a complete Thirumurai 1-8 corpus. It is the best table build from the
raw snapshots currently captured. Local live fetches began timing out with zero response
bytes from TamilVU during the completion pass, so the remaining raw pages need a later
resume run or an alternate approved fetch environment.

Latest retry status on 2026-06-14:

- Local `curl`, Python `requests`, and the in-app browser all failed to fetch direct
  SLET pages from this workspace network path.
- Official legacy wrapper pages such as
  `https://www.tamilvu.org/library/l4110/html/l4110in2.htm` and
  `https://www.tamilvu.org/library/l4110/html/l4110ind.htm` are reachable, but they
  expose only frame/header content, not the missing hymn/commentary bodies.
- The direct SLET retry was tested with default curl, browser-like headers, IPv4/HTTP1.0,
  TLS 1.2, and plain HTTP. A two-page missing hymn retry fetched `0/2`; every method
  timed out after receiving zero bytes.
- Cloud Run was also tested on 2026-06-14 using the missing-only fetch job:
  - `asia-south1`: first 10 missing commentary pages fetched `0/10`.
  - `us-central1`: one missing commentary page fetched `0/1`.
  - `us-central1`: one missing hymn/thogupu page fetched `0/1`.
  - Every Cloud Run attempt timed out with zero bytes across the same method set.
- The current blocker is source/network availability for TamilVU SLET servlet pages,
  not parser/schema readiness.

Use this command when TamilVU is healthy again to retry only missing raw snapshots:

```bash
python3 -m scraper.thevaram_corpus \
  --fetch-failures \
  --failure-kind all \
  --timeout 10 \
  --delay 0.2 \
  --progress-every 25 \
  --compact-summary
```

After new raw pages are fetched, rebuild the processed tables from cache:

```bash
python3 -m scraper.thevaram_corpus \
  --thirumurai 1-8 \
  --resume \
  --execute \
  --offline \
  --delay 0 \
  --compact-summary
```

## Scope Notes For Full 1-8 Scrape

The safe full command shape is:

```bash
tvu-build-thevaram-tables \
  --thirumurai 1-8 \
  --resume \
  --execute \
  --delay 2.0
```

Do not run the full command until navigation for Thirumurai 5, 6, and 7 is verified.
Current live reconnaissance verified direct SLET navigation for Thirumurai 1-8:

- 1: `https://www.tamilvu.org/slet/l4110/l4110lft.jsp`
- 2: `https://www.tamilvu.org/slet/l4120/l4120lft.jsp`
- 3: `https://www.tamilvu.org/slet/l4130/l4130lft.jsp`
- 4: `https://www.tamilvu.org/slet/l4140/l4140lft.jsp`
- 5: `https://www.tamilvu.org/slet/l4150/l4150lft.jsp`
- 6: `https://www.tamilvu.org/slet/l4160/l4160lft.jsp`
- 7: `https://www.tamilvu.org/slet/l4170/l4170lft.jsp`
- 8: `https://www.tamilvu.org/slet/l4180/l4180lft.jsp`

## Failure Rules

- Empty HTTP bodies fail fast.
- Raw snapshots are saved before parsing.
- Parser failures are recorded in `ingestion_summary.json`; successful rows are still
  written.
- Missing commentary URL becomes a commentary row with `missing_commentary_url`.
- Broad crawling must remain allowlisted to Thirumurai 1-8 sources only.
