# Usage: Thevaram 1-8 Corpus Resource

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

## Inspect The Normalized Corpus Summary

```bash
python3 -m json.tool data/processed/thevaram_normalized/normalization_summary.json
```

## Verify Checksums

```bash
shasum -a 256 -c data/releases/thevaram-1-8-v1/corpus_checksum.sha256
```

## Small Usage Example

Print the first three paadal records with source URLs:

```bash
python3 - <<'PY'
import json
from pathlib import Path

path = Path("data/processed/thevaram_normalized/paadalgal.jsonl")
with path.open(encoding="utf-8") as handle:
    for index, line in enumerate(handle, start=1):
        record = json.loads(line)
        print(record["paadal_id"], record.get("source_url", ""))
        print(record["paadal_text"].splitlines()[0])
        print()
        if index == 3:
            break
PY
```

## Schema

The package schema is:

`data/releases/thevaram-1-8-v1/schema.json`

The canonical shared schema is:

`shared/tvu-schemas/schemas/thevaram_relational_tables.schema.json`

