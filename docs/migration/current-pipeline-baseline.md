# Current Pipeline Baseline

Baseline tag: `pre-reorg-2026-06-13`

Baseline commit: `45aa50a Add entity extraction pilot`

Branch used for migration: `codex/reorg-migration`

## Mature Corpus

Irandaam Thirumurai v1 is the only frozen production-like corpus release.

- Release path: `data/releases/irandaam-thirumurai-v1/`
- Records: `1331`
- Hymns: `122`
- Successful records: `1324`
- Partial commentary records: `7`
- Missing verse text: `0`
- Schema violations: `0`

The release files must not be edited in place.

## Pilot Corpora

- `thirumurai_04`: `51` records from `5` selected hymns.
- `dictionaries`: `1` pilot record.
- `grammar`: `2` pilot records.
- `saivam`: `10` pilot records.
- `sangam_literature`: `3` pilot records.
- `twentieth_century_prose`: `2` pilot records.

## Retrieval Artifacts

- Enriched Irandaam Thirumurai records: `1331`
- Retrieval chunks: `6648`
- Embeddings: `1331`
- Vector metadata rows: `1331`
- Occurrence index rows: `7000`

## Reproducibility Rule

Any migration work should preserve the ability to reproduce the current pipeline outputs
from the frozen release and local raw snapshots. If a new artifact contract is introduced,
it should point back to this baseline or a later explicit release.
