# Setup And Reuse

## Install

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

For package-specific development, install the needed project package:

```bash
python3 -m pip install -e shared/tvu-common
python3 -m pip install -e shared/tvu-schemas
python3 -m pip install -e projects/retrieval
```

## Verify Checksums

```bash
cd data/releases/irandaam-thirumurai-v1
shasum -a 256 -c corpus_checksum.sha256
```

## Validate The Release

From the repository root:

```bash
python3 scripts/validate-artifact.py data/releases/irandaam-thirumurai-v1/corpus_manifest.json
```

## Small Usage Example

Print the first three records with their source URLs:

```bash
python3 - <<'PY'
import json
from pathlib import Path

path = Path("data/releases/irandaam-thirumurai-v1/irandaam_thirumurai.jsonl")
with path.open(encoding="utf-8") as handle:
    for index, line in enumerate(handle, start=1):
        record = json.loads(line)
        print(record["song_no"], record["hymn_url"])
        print(record["verse_text"].splitlines()[0])
        print()
        if index == 3:
            break
PY
```

## Build Retrieval Artifacts

```bash
python3 -m enrichment.build_retrieval_ready_corpus \
  --input data/releases/irandaam-thirumurai-v1/irandaam_thirumurai.jsonl \
  --output-enriched data/processed/enriched/irandaam_thirumurai_enriched.jsonl \
  --output-chunks data/processed/chunks/irandaam_thirumurai_chunks.jsonl \
  --output-lexical-index data/processed/indexes/irandaam_thirumurai_lexical_index.json \
  --output-golden-queries data/processed/eval/golden_queries.jsonl \
  --report reports/retrieval-readiness-report.md
```

Generated `data/processed` artifacts are intentionally not part of the release.
