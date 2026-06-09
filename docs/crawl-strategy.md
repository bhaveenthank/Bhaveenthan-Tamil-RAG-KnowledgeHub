# TamilVU Crawl Strategy

This project should not begin with a broad crawler. TamilVU content requires a two-part strategy:

1. Link-following crawling for normal page transitions.
2. Same-page/inline content extraction for pages where selecting a hymn reveals content without navigating to a new URL.

## Why Link-Following Is Not Enough

Manual inspection found that the path:

`நூல்கள் -> சமய இலக்கியங்கள் -> சைவம் -> பன்னிரு திருமுறைகள் -> இரண்டாம் திருமுறை`

eventually reaches:

`https://www.tamilvu.org/ta/library-l4100-html-l4120001-135793`

On that page, hymn/pathigam entries such as "திருப்பூந்தராய் - வினா உரை - இந்தளம்" may display poem content on the same page, to the right side of the list. If a crawler only follows `href` links, it may capture the hymn list but miss the selected poem and commentary content.

## Required Inspection Before Scraping

For each observed page family, inspect:

- internal TamilVU links and link text
- URL pattern and legacy page references
- frame sources when present
- inline buttons/icons/links containing "உரை"
- scripts or attributes that may load content dynamically
- hidden or same-page content containers
- Tamil text length and rough content density

## Crawl Phases

### Phase A: Manual Allowlist Inspection

Use `src/inspector/site_inspector.py` against only the known URLs from manual inspection.

Output:

- raw HTML snapshots under `data/raw/inspection/`
- markdown report under `reports/site-inspection-report.md`

No recursion. No full-site crawl.

### Phase B: Page-Type Classifier

Use inspection results to refine page types:

- main library/category page
- subcategory page
- collection index page
- thirumurai index page
- hymn list/content page
- inline poem/commentary content

### Phase C: Pilot Extractor

Implement a small extractor for one allowlisted Thirumurai page:

- detect hymn entries
- detect selected/inline poem blocks
- detect "உரை" controls
- map commentary back to poem/verse records

### Phase D: Controlled Pilot Crawl

Only after Phase C:

- fetch 5-20 approved URLs
- keep rate limit and low concurrency
- save raw snapshots before parsing
- generate QA report
- manually review Tamil text fidelity

## Politeness Rules

- Use a clear User-Agent.
- Use a delay between requests.
- Retry only a small number of times.
- Respect robots/site policy before expansion.
- Keep crawl scope allowlisted until extraction quality is proven.

## Inspector Command

```bash
python3 src/inspector/site_inspector.py --dry-run
python3 src/inspector/site_inspector.py --delay 2.0
python3 src/inspector/site_inspector.py --url https://www.tamilvu.org/ta/library-l4100-html-l4120001-135793 --delay 2.0
```

