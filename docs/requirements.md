# TamilVU Corpus Requirements

## Product Goal

Create a trustworthy Tamil literary knowledge store for a smart Tamil chat agent. The agent should help Tamil poets, researchers, students, and Tamil language lovers search, cite, compare, and understand classical and modern Tamil literary material.

## Initial Source

- Seed catalog: `https://www.tamilvu.org/ta/library-libcontnt-273141`
- Important content families:
  - modern TamilVU catalog/wrapper pages
  - legacy static HTML under `/library/`
  - frame-based books
  - SLET/JSP tree menus under `/slet/`
  - Drupal simple nodes using `?format=simple`

## Non-Goals For Early Phases

- Do not build the chat UI yet.
- Do not scrape the whole website until pilot extraction quality is reviewed.
- Do not start with Kubernetes or always-on vector infrastructure.
- Do not do OCR unless a later phase explicitly includes image-only works.

## Functional Requirements

- Discover links from the seed catalog and classify page types.
- Fetch raw source snapshots with URL, headers, status, hash, timestamp, and parent URL.
- Parse frames and enqueue frame sources.
- Extract normalized Tamil text while preserving useful structure.
- Capture metadata: work, section, title, author/commentary author when available, source path, source URL, and parser confidence.
- Save extraction warnings and QA reports.
- Produce records suitable for lexical search and vector indexing.
- Keep a dry-run mode and crawl allowlists for pilot work.

## Quality Requirements

- All extracted records must have a source URL.
- Raw snapshots must be immutable by content hash.
- Tamil Unicode normalization should default to NFC.
- Extraction should preserve hierarchy before chunking.
- Tests should use local fixtures for parser behavior.
- Live network tests should be opt-in.

## Security And Cost Requirements

- No secrets in Git.
- Store local project defaults in `~/.config/tvu-corpus/secrets.zsh`.
- Store production secrets in Google Secret Manager.
- Prefer least-privilege service accounts.
- Use budget alerts before running cloud jobs.
- Rate-limit crawling and obey site policy/robots before expansion.

## First Pilot Acceptance Criteria

- 5-20 allowlisted URLs fetched into `gs://tvu-corpus-e22051-260606/raw/`.
- Processed JSONL records written under `processed/`.
- QA report lists page type, source URL, extracted Tamil character count, warnings, and parser confidence.
- Manual inspection confirms Thevaram/Thiruppugazh/Sangam samples preserve headings and poem/commentary boundaries.
- Tests pass locally with `python3 -m pytest`.

