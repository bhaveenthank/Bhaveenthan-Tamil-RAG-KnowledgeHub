# Irandaam Thirumurai Corpus Builder

This phase generalizes the one-hymn pilot into a controlled corpus builder for **Irandaam Thirumurai only**.

It is not a full TamilVU scraper.

## Scope

Input navigation source:

`https://www.tamilvu.org/slet/l4120/l4120lft.jsp`

Earlier frame inspection counted 124 internal links. The strict corpus-builder filter looks only for valid hymn endpoints and the current dry-run discovered 122 `l4120son.jsp?subid=...` hymn/pathigam links like:

`https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1664`

The builder extracts only hymn links matching `l4120son.jsp?subid=...`.

## What The Builder Extracts

For each selected hymn, the builder:

- fetches the hymn endpoint
- extracts the hymn/pathigam title
- extracts verse/song text
- extracts all `உரை` commentary URLs from `window.open(...)` controls
- fetches each commentary endpoint
- extracts `பொழிப்புரை` / `பொ-ரை`
- extracts `குறிப்புரை` / `கு-ரை`
- writes one JSONL record per verse/song

The normalized records include literary metadata, source URLs, source parameters, text statistics, and extraction metadata.

## Output Files

Raw HTML snapshots:

- `data/raw/corpus/irandaam_thirumurai/navigation/`
- `data/raw/corpus/irandaam_thirumurai/hymns/`
- `data/raw/corpus/irandaam_thirumurai/commentary/`

Processed outputs:

- `data/processed/corpus/irandaam_thirumurai.jsonl`
- `data/processed/corpus/irandaam_thirumurai/hymns/hymn_{subid}.jsonl`

QA report:

- `reports/irandaam-thirumurai-corpus-report.md`

## Safety Behavior

The builder remains deliberately slow and bounded:

- `--delay 2.0` is the default delay between network requests.
- `--limit N` processes only the first `N` hymn links.
- `--dry-run` fetches/reads only the left frame and prints discovered hymn links.
- `--resume` reuses already saved raw snapshots where possible.
- `--output-dir` can redirect all raw, processed, and report files under another base directory.

Do not run the full 122 strict hymn endpoints until we explicitly review the limited run output.

## Validation Checks

The QA report includes:

- total valid hymn links discovered
- total hymns attempted
- total hymns successful
- total verse records written
- missing verse text count
- missing commentary URL count
- missing `pozhppurai` count
- missing `kurippurai` count
- duplicate `song_no` detection
- duplicate source/commentary URL detection
- per-hymn success/failure summary

Missing commentary fields are warnings. Missing verse text and duplicate identifiers are validation errors.

## Known Assumptions

- `subid` identifies the hymn/pathigam.
- `song_no` identifies the verse/song across this Thirumurai.
- Commentary URLs expose stable `song_no`, `book_id`, `head_id`, and `sub_id` parameters.
- The hymn pages use the same table layout observed in the one-hymn pilot.
- Commentary pages remain statically extractable with `requests` + BeautifulSoup.
- TamilVU label variants include both full and abbreviated commentary labels.

## Difference From The One-Hymn Pilot

The one-hymn pilot starts from a known hymn URL and expects 10 commentary pages for `subid=1664`.

This builder starts from the Irandaam Thirumurai left frame, discovers the hymn URLs, and can process a controlled number of hymns. It writes a single corpus JSONL file plus per-hymn JSONL files, and it validates corpus-wide duplicate IDs and missing fields.

The builder reuses the pilot parser functions for hymn pages, commentary URLs, commentary splitting, Tamil text normalization, and source parameter extraction.
