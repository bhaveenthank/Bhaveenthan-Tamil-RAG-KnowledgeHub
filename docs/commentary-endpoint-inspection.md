# Commentary Endpoint Inspection

This phase inspects one selected commentary endpoint. It is not a scraper and does not recursively crawl.

## Current Evidence Chain

The selected hymn endpoint:

`https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1664`

contains the poem/verse text for:

`திருப்பூந்தராய் - வினா உரை - இந்தளம்`

It has 10 `உரை` controls. These controls are `javascript:void(0)` links that call `window.open(...)`.

The discovered commentary URL pattern is:

`l4120uri.jsp?song_no={song_no}&book_id=110&head_id=60&sub_id={sub_id}`

For the first verse/commentary:

`https://www.tamilvu.org/slet/l4120/l4120uri.jsp?song_no=1470&book_id=110&head_id=60&sub_id=1664`

## Goal

Inspect one commentary page and determine whether it contains:

- பொழிப்புரை
- குறிப்புரை
- verse text repetition
- prose explanation
- links, scripts, forms, or frames
- stable metadata through URL parameters:
  - `song_no`
  - `book_id`
  - `head_id`
  - `sub_id`

## Evidence Needed Before Pilot Scraper

The commentary endpoint inspection should answer:

- Is commentary visible in the fetched HTML?
- Are commentary sections labelled with stable Tamil labels such as பொழிப்புரை and குறிப்புரை?
- Is the verse text repeated in the commentary page?
- Are prose explanation blocks extractable by static HTML parsing?
- Does the page require JavaScript, frames, or forms to reveal commentary?
- Are URL parameters enough to connect commentary back to hymn and verse?

## Expected Next Decision

After this phase:

- If the commentary page is statically extractable, define the first parser contract for one hymn plus one commentary page.
- If commentary labels are visible but layout is table-heavy, preserve table row/cell structure in the parser contract.
- If commentary requires another endpoint or dynamic action, inspect only that next endpoint before building a scraper.

