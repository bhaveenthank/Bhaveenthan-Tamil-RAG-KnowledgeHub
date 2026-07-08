# Normalizer Project

Owns conversion from extracted records into stable normalized corpus records.

## Inputs

- extracted records from parser releases or pilots
- corpus/category registries

## Outputs

- normalized corpus JSONL
- validation reports
- readiness audits

Normalization may derive canonical IDs and citations, but must not overwrite source text or provenance.

## Thevaram 1-8 Relational Tables

Use `corpus.normalize_thevaram_tables` after the parsed Thevaram tables have been
manually reviewed and strengthened. It writes a separate five-table output under
`data/processed/thevaram_normalized/`; it does not modify raw snapshots or the
supervisor-reviewed parsed tables under `data/processed/thevaram/`.

```bash
python3 -m corpus.normalize_thevaram_tables \
  --input-root data/processed/thevaram \
  --output-root data/processed/thevaram_normalized \
  --report reports/thevaram-normalization-report.md
```

The normalizer preserves existing `\n` line boundaries, because those line breaks are
program-friendly structure for poem lines and future span alignment. It only
canonicalizes Unicode, removes unsafe invisible/control characters, collapses repeated
spaces inside each line, trims line edges, refreshes `tokenized_paadal`, and rebuilds
`text_spans` with offsets against the normalized text.
