# Dynamic Content Discovery

This phase investigates how TamilVU loads hymn, poem, and commentary content for the Thirumurai pages. It is still inspection only; it is not the pilot scraper.

Target page:

`https://www.tamilvu.org/ta/library-l4100-html-l4120001-135793`

## What We Know From Manual Inspection

Manual browser inspection of the second Thirumurai page shows:

- The page lists many பதிகம் / hymn entries.
- Clicking a hymn entry such as "திருப்பூந்தராய் - வினா உரை - இந்தளம்" does not appear to navigate to a completely separate browser page.
- Poem content appears on the same page, usually on the right side of the hymn list.
- The example hymn has around 11 poems/verses.
- Each poem has around 4 lines.
- Each poem has an "உரை" icon/link.
- The "உரை" control reveals commentary such as:
  - பொழிப்புரை
  - குறிப்புரை

## What The Static Inspector Found

The allowlist-only static inspector fetched:

`https://www.tamilvu.org/ta/library-l4100-html-l4120001-135793`

Static findings:

- The fetched wrapper page contains internal links and page metadata.
- It did not detect the visible poem text or "உரை" commentary controls in the initial wrapper HTML.
- The wrapper includes iframe-related scripts and iframe elements.
- The left iframe points to a SLET/JSP endpoint:
  - `/slet/l4120/l4120lft.jsp`
- The right iframe points to a simple-render content endpoint:
  - `https://www.tamilvu.org/ta/library-l4100-html-l4120003-135795?renderframe=simple`
- A legacy page link is present:
  - `/library/l4100/html/l4120001.htm`

## Main Uncertainty

Before building a pilot scraper, we need to determine whether hymn/poem/commentary content is:

1. Hidden in the fetched wrapper HTML and revealed by CSS/JavaScript.
2. Loaded through iframe/frame endpoints.
3. Loaded through JavaScript event handlers from the left navigation frame.
4. Loaded from a separate legacy HTML endpoint.
5. Loaded from a Drupal/simple-render endpoint such as `?renderframe=simple`.
6. Loaded by AJAX after clicking a hymn or "உரை" control.

The current evidence leans toward iframe/frame endpoints, but we need direct evidence from the static HTML and frame source pages before using browser automation.

## Evidence Needed Before Pilot Scraper

Collect the following evidence using `src/inspector/discover_dynamic_content.py`:

- script tags and referenced JavaScript files
- iframe/frame `src` values
- inline `onclick` handlers
- `href="javascript:..."` links
- nearby URLs or path fragments around known hymn names such as "திருப்பூந்தராய்"
- presence or absence of Tamil keywords:
  - திருப்பூந்தராய்
  - உரை
  - பொழிப்புரை
  - குறிப்புரை
- hidden DOM nodes:
  - `hidden`
  - `display:none`
  - `visibility:hidden`
  - `aria-hidden=true`
- IDs/classes that look like content panels:
  - `content`
  - `panel`
  - `frame`
  - `iframe`
  - `right`
  - `left`
  - `tab`
  - `urai`
- first 10 candidate hymn/navigation entries and their `href`/`onclick` attributes.

## Expected Next Decision

After this phase, choose one of these paths:

- If iframe endpoints contain the hymn list and content URLs, build a static endpoint inspector for those specific frame URLs.
- If hidden HTML contains the poems/commentary, build a DOM extractor.
- If JavaScript handlers reveal deterministic URLs, parse those handlers.
- If only real browser interaction exposes content, then introduce Playwright in a later, explicitly scoped phase.

