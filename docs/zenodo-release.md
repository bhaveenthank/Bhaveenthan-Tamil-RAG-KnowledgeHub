# Optional Zenodo Release Plan

Zenodo is not required for the current JCDL submission because the public GitHub
repository is the primary resource. Use this plan later only when creating a
frozen DOI-backed archive.

## Intended Record

Title:

`Tamil Literary KnowledgeHub: Thevaram 1-8 Corpus Resource and Tools`

Resource type:

`Dataset`

Creators:

- Kajanikanth, Bhaveenthan; University of Peradeniya
- Thayasivam, Uthayasanker; University of Moratuwa

Recommended first DOI package:

Use either a rights-safe Thevaram 1-8 package or the stricter audited subset:

- Full resource documentation and code from the public GitHub repository.
- Audited subset package: `data/releases/irandaam-thirumurai-v1/`.

Metadata source:

`data/releases/irandaam-thirumurai-v1/zenodo_metadata.json`

## Files To Upload

If uploading the existing audited subset, upload the release directory contents,
not the full repository working tree:

- `irandaam_thirumurai.jsonl`
- `schema.json`
- `corpus_manifest.json`
- `corpus_checksum.sha256`
- `CORPUS_SUMMARY.md`
- `RELEASE_NOTES.md`
- `corpus_card.md`
- `DATASHEET.md`
- `RIGHTS_AND_ACCESS.md`
- `USAGE.md`
- `corpus-audit-report.md`
- `corpus-coverage-report.md`
- `manual-audit-sample.md`
- `schema-validation-report.md`

## DOI Workflow

Zenodo supports creating an upload through the web UI or REST API. The REST API
requires a personal access token with `deposit:write`; publishing also requires
`deposit:actions`. Do not commit or paste the token into this repository.

Recommended safe sequence:

1. Create a Zenodo draft upload.
2. Reserve a DOI, but do not publish yet.
3. Add the reserved DOI to `RIGHTS_AND_ACCESS.md`, `CITATION.cff`, and the paper.
4. Upload the files listed above.
5. Preview the record.
6. Publish only after rights/access language is final.

Repository helper:

```bash
export ZENODO_ACCESS_TOKEN="..."
python3 scripts/zenodo_upload_release.py --dry-run
python3 scripts/zenodo_upload_release.py
```

The helper creates a draft and reserves a DOI. It does not publish unless
`--publish` is passed.

## Rights Decision Before Publishing

If explicit TamilVU full-text redistribution permission is confirmed, publish the
full release files as open files.

If permission is not confirmed, publish one of these safer variants:

- metadata, schema, checksums, reports, and a small permitted sample as open files;
- full files as restricted files with access conditions; or
- repository code plus reconstruction scripts, with source URLs and attribution.
