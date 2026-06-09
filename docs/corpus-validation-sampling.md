# Corpus Validation Sampling Phase

This phase checks whether the Irandaam Thirumurai extraction assumptions hold beyond the first three pilot hymns.

It does not run the full 122-hymn corpus extraction.

## Goal

Before expanding the corpus builder, sample hymns from the beginning, middle, and end of the discovered Irandaam Thirumurai hymn list and verify that:

- hymn pages keep the expected poem table structure
- `உரை` commentary links remain discoverable
- commentary pages still use supported labels and punctuation variants
- verse counts are within the expected Thevaram range
- source identifiers remain stable

## Script

`src/validation/sample_hymn_validator.py`

Default navigation source:

`https://www.tamilvu.org/slet/l4120/l4120lft.jsp`

Default output report:

`reports/corpus-validation-sampling-report.md`

Raw validation snapshots are saved under:

`data/raw/validation/corpus_sampling/`

## Sampling Strategy

The validator discovers valid hymn links matching `l4120son.jsp?subid=...`, then samples:

- first 5 hymns
- middle 5 hymns
- last 5 hymns

Duplicates are removed if the discovered list is small. For the current Irandaam Thirumurai left frame, this should sample 15 hymns from the 122 strict hymn endpoints.

## Per-Hymn Checks

For each sampled hymn, the validator records:

- `hymn_id`
- hymn title
- verse count
- commentary count
- missing verse text count
- missing `pozhppurai` count
- missing `kurippurai` count
- extraction success/failure
- parsing anomalies

## Anomaly Detection

The validator flags:

- different HTML structure, such as missing poem markers or no parsed verse records
- missing commentary links
- different commentary labels or punctuation variants, represented by parser warnings
- duplicate `song_no`
- unusual verse count outside the current expected range of 8 to 12
- unexpected hymn or commentary URL patterns

## Summary Metrics

The report includes:

- sampled hymns
- successful hymns
- failed hymns
- average verses per hymn
- average commentary coverage

## Execution Policy

Run this validator before the full Irandaam Thirumurai extraction:

```bash
python3 src/validation/sample_hymn_validator.py
```

The validator uses `requests` + BeautifulSoup only, reuses saved raw snapshots by default, and does not use GCP or browser automation.
