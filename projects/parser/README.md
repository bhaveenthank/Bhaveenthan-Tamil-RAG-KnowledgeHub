# Parser Project

Owns extraction of structured records from raw TamilVU snapshots and bounded source fixtures.

## Inputs

- raw snapshots from the crawler
- approved local fixtures for parser-family pilots

## Outputs

- extracted JSONL records
- parser warnings, extraction reports, and source provenance
- normalized Thevaram table artifacts for approved Thirumurai expansion slices

Parser output must preserve source URLs, literary hierarchy, and source order.

## Commands

```bash
tvu-build-thevaram-tables --thirumurai 1-4,8 --resume
tvu-build-thevaram-tables --thirumurai 1 --limit-thogupugal 1 --limit-paadalgal-per-thogupu 1 --resume --execute
```

See `docs/thevaram-1-8-schema-and-ingestion.md` for the table schema, live probe
status, and full scrape guardrails.
