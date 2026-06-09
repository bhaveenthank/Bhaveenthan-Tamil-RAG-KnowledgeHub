#!/usr/bin/env bash
set -euo pipefail

: "${TVU_GCP_PROJECT:?Set TVU_GCP_PROJECT first}"
: "${TVU_GCP_REGION:=asia-south1}"
: "${TVU_GCP_BUCKET:?Set TVU_GCP_BUCKET first, e.g. gs://tvu-corpus-yourname}"

gcloud config set project "$TVU_GCP_PROJECT"
gcloud config set run/region "$TVU_GCP_REGION"
gcloud config set artifacts/location "$TVU_GCP_REGION"

gcloud services enable \
  run.googleapis.com \
  storage.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com

if ! gcloud storage buckets describe "$TVU_GCP_BUCKET" >/dev/null 2>&1; then
  gcloud storage buckets create "$TVU_GCP_BUCKET" \
    --location="$TVU_GCP_REGION" \
    --uniform-bucket-level-access
fi

tmp_keep="$(mktemp)"
trap 'rm -f "$tmp_keep"' EXIT

gcloud storage cp "$tmp_keep" "$TVU_GCP_BUCKET/raw/.keep"
gcloud storage cp "$tmp_keep" "$TVU_GCP_BUCKET/processed/.keep"
gcloud storage cp "$tmp_keep" "$TVU_GCP_BUCKET/reports/.keep"
gcloud storage cp "$tmp_keep" "$TVU_GCP_BUCKET/indexes/.keep"

echo "GCP bootstrap complete for $TVU_GCP_PROJECT in $TVU_GCP_REGION"
