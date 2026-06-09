# iframe Endpoint Inspection

This phase inspects the frame endpoints discovered inside the Thirumurai wrapper page. It is still inspection only; it is not a full scraper and does not recursively crawl.

Wrapper page:

`https://www.tamilvu.org/ta/library-l4100-html-l4120001-135793`

## Why The Wrapper Page Alone Is Insufficient

The wrapper page does not contain direct hymn entries or உரை/commentary content in its static HTML. Static dynamic-content discovery found:

- `திருப்பூந்தராய்`: 0 matches
- `உரை`: 0 matches
- `பொழிப்புரை`: 0 matches
- `குறிப்புரை`: 0 matches
- no direct hymn/navigation candidates

However, the wrapper contains iframe endpoints. This means the visible browser experience is likely assembled from frame content rather than from the wrapper HTML itself.

## Discovered iframe Endpoints

Left/navigation frame:

`https://www.tamilvu.org/slet/l4120/l4120lft.jsp`

Main/content frame:

`https://www.tamilvu.org/ta/library-l4100-html-l4120003-135795?renderframe=simple`

## Hypothesis

- The left frame likely contains hymn/navigation links for the selected Thirumurai.
- The main frame likely contains a default hymn/poem/commentary content page or a placeholder that updates when the left navigation frame is clicked.

## Evidence Needed Before Pilot Scraper

Before building a pilot scraper, inspect both frame endpoints for:

- page title
- Tamil text length
- internal TamilVU links and link text
- `href` values
- `onclick` handlers
- nested frame/iframe tags
- forms and form actions
- script sources
- Tamil keyword matches:
  - திருப்பூந்தராய்
  - உரை
  - பொழிப்புரை
  - குறிப்புரை
  - இந்தளம்
- possible content-bearing elements:
  - table rows
  - divs
  - anchors
  - elements with Tamil-heavy text

## Expected Next Decision

After this phase:

- If the left frame contains deterministic hymn links, use those links as the next allowlist for a pilot endpoint inspection.
- If the right frame contains poem/commentary text, design a static extractor for that frame.
- If the frames still hide content behind JavaScript handlers, inspect the handler URLs or JavaScript source next.
- Use Playwright/Selenium only after static frame endpoint evidence is insufficient.

