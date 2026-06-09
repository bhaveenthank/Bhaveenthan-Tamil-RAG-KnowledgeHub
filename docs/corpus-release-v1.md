# Irandaam Thirumurai Corpus v1 Release

This document finalizes the audited corpus candidate as:

`Irandaam Thirumurai Corpus v1`

The release is packaged under:

`data/releases/irandaam-thirumurai-v1/`

## Release Inputs

- Corpus JSONL: `data/processed/corpus/irandaam_thirumurai.jsonl`
- Manifest: `corpus_manifest.json`
- Audit report: `reports/corpus-audit-report.md`
- Coverage report: `reports/corpus-coverage-report.md`
- Schema validation report: `reports/schema-validation-report.md`

## Release Criteria

The corpus was released because the audit found:

- `122` hymns
- `1331` verse records
- `0` schema violations
- `0` failed hymns
- `0` duplicate `song_no` values
- `0` missing verse text records
- `100%` sampled coverage
- `7` partial commentary records, all classified as `SOURCE_MISSING`
- no verified parser bugs

## Release Contents

- `irandaam_thirumurai.jsonl`
- `corpus_manifest.json`
- `schema.json`
- `corpus-audit-report.md`
- `corpus-coverage-report.md`
- `schema-validation-report.md`
- `manual-audit-sample.md`
- `RELEASE_NOTES.md`
- `corpus_card.md`
- `corpus_checksum.sha256`

## Freeze Statement

The released files are intended to represent the v1 frozen corpus for Irandaam Thirumurai extraction work.

Do not modify the release corpus contents in place. Any future changes should be made through a separate repair or v2 release phase.
