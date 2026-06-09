# Hymn Endpoint Inspection

This phase inspects one selected hymn endpoint. It is still inspection only; it is not a full scraper.

Target hymn:

- Title: `திருப்பூந்தராய் - வினா உரை - இந்தளம்`
- URL: `https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1664`

## Current Evidence Chain

The modern TamilVU wrapper page:

`https://www.tamilvu.org/ta/library-l4100-html-l4120001-135793`

is only a frame container. It does not contain direct hymn entries, poem text, or உரை/commentary content in its static HTML.

The wrapper exposes a left iframe:

`https://www.tamilvu.org/slet/l4120/l4120lft.jsp`

The left iframe contains hymn/navigation links. The first discovered hymn link is:

`https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1664`

## Aim

Inspect the selected hymn endpoint and determine whether it contains:

- poem/verse text
- verse numbers
- உரை links or commentary controls
- பொழிப்புரை / குறிப்புரை content
- hidden commentary content
- forms, scripts, or iframes
- stable URL parameters such as `subid`

## Evidence Needed Before Pilot Scraper

The one-hymn inspection should answer:

- Are poems represented as table rows, paragraphs, divs, or another layout?
- Are verse numbers explicit in text or markup?
- Are poem line breaks preserved in the HTML?
- Are உரை/commentary controls normal links, image links, JavaScript handlers, or hidden blocks?
- Is commentary already present in the endpoint HTML or loaded from another URL?
- Is `subid=1664` a stable identifier for this hymn/pathigam?

## Expected Next Decision

After this phase:

- If the hymn endpoint contains poem text and உரை links, design a one-hymn parser contract.
- If உரை links point to separate endpoints, inspect one commentary endpoint.
- If commentary is hidden in the same HTML, design same-page extraction.
- If content is still not present statically, only then consider browser automation.

