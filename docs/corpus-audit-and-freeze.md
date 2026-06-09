# Corpus Audit And Freeze Decision

This phase evaluates whether the completed Irandaam Thirumurai corpus candidate is ready to freeze as `Irandaam Thirumurai Corpus v1`.

It is an audit-only phase. It does not scrape, repair, regenerate records, build embeddings, use a vector database, use GCP, or move toward RAG.

## Audit Objectives

- Verify that the processed JSONL corpus is structurally valid.
- Confirm that the 7 `partial_commentary` records are understood and classified.
- Check corpus integrity: identifiers, source URLs, missing text, metadata, Tamil text quality, and suspicious lengths.
- Validate schema consistency across every record.
- Estimate extraction coverage by comparing sampled raw hymn HTML against extracted records.
- Produce a freeze recommendation: `FREEZE_READY` or `REPAIR_REQUIRED`.

## Audit Methodology

The audit reads:

- `data/processed/corpus/irandaam_thirumurai.jsonl`
- raw hymn snapshots under `data/raw/corpus/irandaam_thirumurai/hymns/`
- raw commentary snapshots under `data/raw/corpus/irandaam_thirumurai/commentary/`

It generates:

- `reports/corpus-audit-report.md`
- `reports/schema-validation-report.md`
- `reports/corpus-coverage-report.md`
- `reports/manual-audit-sample.md`
- `corpus_manifest.json`
- `docs/corpus-freeze-v1.md`

## Corpus Freeze Criteria

The corpus is considered freeze-ready when:

- all records pass schema validation
- all required identifiers and source URLs are present
- no duplicate `song_no` values exist
- no duplicate commentary source URLs exist
- no verse text is missing
- sampled source-vs-extracted coverage is 100%
- partial commentary records are explicitly classified and accepted as known limitations

Missing commentary prose may still be acceptable for v1 if the source HTML itself appears to omit that section. It is not acceptable if the source contains the section and the parser missed it.

## Classification System

Partial commentary records are classified as:

- `SOURCE_MISSING`: the saved TamilVU source HTML does not contain the expected commentary section label.
- `PARSER_LIMITATION`: the source appears to contain the section, but the parser did not extract it.
- `CORRUPT_HTML`: the saved raw snapshot is malformed or not recognizable as HTML.
- `UNKNOWN`: automated evidence is insufficient; manual review is required.

## Known Risks

- TamilVU legacy pages may contain inconsistent punctuation, labels, or typographic variants.
- A commentary section can be genuinely absent in source HTML.
- Some fields such as `hymn_note` and `pann` are inferred from link-title conventions and may need later human curation.
- Audit coverage compares a representative sample, not every raw hymn page, against source HTML.

## Limitations

- The audit does not repair records.
- The audit does not fetch missing pages.
- The audit does not verify every verse manually against TamilVU.
- The audit does not decide literary correctness of commentary prose.
- Freeze recommendation still requires human acceptance of known limitations.
