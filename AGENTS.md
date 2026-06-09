# AGENTS.md

## Project Mission

Build a practical Tamil literary corpus pipeline for a future RAG chat agent serving Tamil poets, researchers, and language lovers.

The first source is Tamil Virtual Academy/TamilVU library content. Preserve provenance, respect crawling limits, and keep raw snapshots so extraction can improve without repeatedly fetching the site.

## Working Agreements

- Do not run broad scraping unless the user explicitly approves the phase and scope.
- Prefer small pilot allowlists before expanding a crawl.
- Keep raw source, processed corpus, reports, and indexes separated.
- Treat Tamil text quality as a first-class requirement: preserve Unicode, source order, headings, commentary, and citation paths.
- Keep cloud work cost-aware. Prefer Cloud Run Jobs and Cloud Storage before always-on services.
- Never commit credentials, API keys, service account JSON, or local `.env` files.
- When changing crawler behavior, update tests and docs together.

## Commands

- Run tests: `python3 -m pytest`
- Inspect config: `PYTHONPATH=src python3 -m tvu_scraper inspect-config configs/tamilvu.yaml`
- Bootstrap GCP after sourcing private config: `source ~/.config/tvu-corpus/secrets.zsh && scripts/gcp-bootstrap.sh`

## Role Skills

Use the repo skills in `.agents/skills` when the task matches a role:

- `$TVU_Architect`: architecture, crawl phases, corpus schema, storage, cloud design, cost guardrails.
- `$TVU_Developer`: implementation of crawler, extractors, storage adapters, CLI, and indexes.
- `$TVU_Tester`: test strategy, fixtures, extraction QA, regression checks, and acceptance criteria.
- `$TVU_Security_Analyser`: scraping ethics, secrets, GCP IAM, dependency risk, and data handling.
- `$TVU_User`: Tamil poet/researcher perspective, retrieval use cases, UX expectations, answer quality.

Use subagents only when the user explicitly asks for parallel agents or when they explicitly name multiple role agents for one task.

## Review Guidelines

- Flag any code path that can crawl too broadly, ignore rate limits, overwrite raw snapshots, or drop source URLs.
- Flag any secret leakage, committed credentials, over-broad IAM, or unnecessary public bucket access.
- Flag tests that rely on live TamilVU pages when a fixture would be safer.
- Flag extraction changes that flatten useful hierarchy such as work, section, poem, verse, commentary, or glossary category.

