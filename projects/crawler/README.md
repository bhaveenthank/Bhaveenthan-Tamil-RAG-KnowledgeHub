# Crawler Project

Owns TamilVU URL inspection, classification, safe fetching, and raw snapshot capture.

## Inputs

- `configs/tamilvu.yaml`
- explicit allowlists or approved frontier manifests

## Outputs

- raw HTML/assets under `data/raw/...`
- crawl and inspection reports under `reports/...`
- raw snapshot manifests matching `raw_snapshot.schema.json`

This project must not perform broad crawling unless a crawl phase and scope are explicitly approved.
