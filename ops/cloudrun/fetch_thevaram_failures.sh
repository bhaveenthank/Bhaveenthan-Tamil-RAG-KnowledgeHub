#!/usr/bin/env bash
set -euo pipefail

: "${TVU_GCS_BUCKET:?Set TVU_GCS_BUCKET to a gs:// bucket}"

cd /app
mkdir -p data/processed/thevaram data/raw/corpus/thevaram

if [[ ! -f data/processed/thevaram/ingestion_summary.json ]]; then
  if [[ -f ops/cloudrun/input/ingestion_summary.json ]]; then
    cp ops/cloudrun/input/ingestion_summary.json data/processed/thevaram/ingestion_summary.json
  else
    echo "Missing ingestion_summary.json input" >&2
    exit 1
  fi
fi

args=(
  --fetch-failures
  --failure-kind "${TVU_FAILURE_KIND}"
  --timeout "${TVU_FETCH_TIMEOUT}"
  --delay "${TVU_FETCH_DELAY}"
  --progress-every "${TVU_PROGRESS_EVERY}"
  --compact-summary
)

if [[ -n "${TVU_FAILURE_CORPUS:-}" ]]; then
  args+=(--failure-corpus "${TVU_FAILURE_CORPUS}")
fi
if [[ -n "${TVU_FAILURE_LIMIT:-}" ]]; then
  args+=(--failure-limit "${TVU_FAILURE_LIMIT}")
fi
if [[ -n "${TVU_FAILURE_OFFSET:-}" ]]; then
  args+=(--failure-offset "${TVU_FAILURE_OFFSET}")
fi

set +e
python3 -m scraper.thevaram_corpus "${args[@]}"
fetch_status=$?
set -e

if [[ -f data/processed/thevaram/failure_fetch_summary.json ]]; then
  gcloud storage cp data/processed/thevaram/failure_fetch_summary.json \
    "${TVU_GCS_BUCKET}/processed/thevaram/failure_fetch_summary.json"
fi

if find data/raw/corpus/thevaram -type f | grep -q .; then
  gcloud storage cp --recursive data/raw/corpus/thevaram "${TVU_GCS_BUCKET}/raw/corpus/"
else
  echo "No raw snapshots were fetched; skipping raw upload."
fi

echo "Fetch command exit status: ${fetch_status}"
exit 0
