# Site Reconnaissance Notes

Date: 2026-06-06

## Observed Entry Structure

The library catalog page is a Tamil/English literature index containing hundreds of internal links. It groups content by literary type and source collection:

- சொல்வடைவு and Tamil number references
- இலக்கணம்
- சங்க இலக்கியம்
- பதினெண் கீழ்க்கணக்கு
- காப்பியங்கள்
- சமய இலக்கியங்கள்
- சிற்றிலக்கியங்கள்
- நெறி நூல்கள்
- சித்தர் இலக்கியம்
- twentieth-century poetry/prose
- நாட்டுடைமை நூல்கள்
- dictionaries, lexicons, and encyclopedic collections

The catalog page is a modern TamilVU wrapper. Individual entries often expose a `Legacy Page` link to older content under `/library/...`.

## Observed Page Families

### Modern Drupal Wrapper

Example:

- `/ta/library-l4100-html-l4100cor-135660`

Useful fields:

- title
- breadcrumb/category
- tags
- view count
- last updated timestamp
- legacy page link

### Legacy Static HTML

Example:

- `/library/l4100/html/l4100cor.htm`
- `/library/l4100/html/l4100ind.htm`
- `/library/l41F0/html/l41F0ind.htm`

Traits:

- mostly UTF-8 HTML
- table-based layout
- relative links across sibling book folders
- image references under `/library/.../images`
- important navigation links embedded in table cells

### Legacy Frames

Example:

- `/library/l1100/html/l1100ind.htm`

Traits:

- `frameset` with a left navigation frame and right content frame
- left frame can point to `/slet/.../*.jsp`
- right frame can point to legacy HTML or Drupal node content

### SLET/JSP Tree Menus

Example:

- `/slet/l1100/l1100lft.jsp`

Traits:

- large nested `<ul>` navigation trees
- links to `../../node/<id>?format=simple`
- semantic categories such as மரங்கள், மலர்கள், தானியம், விலங்குகள், பறவைகள்
- useful for extracting topic/entity associations, not only poems

### Drupal Simple Nodes

Example pattern:

- `/node/<id>?format=simple`
- `/ta/library-...?...format=simple`

Expected role:

- cleaner content nodes reachable from SLET menus
- should be snapshotted and parsed separately from full Drupal wrapper pages

## Implications For Scraper Design

- Use a URL frontier with page type classification, not a single recursive crawler.
- Preserve raw HTML because extraction rules will vary by family.
- Parse frame definitions and enqueue frame `src` values.
- Parse JSP tree menus as structured table-of-contents records.
- Extract modern wrapper metadata and link it to legacy content.
- Normalize relative URLs carefully because legacy folders cross-link heavily.
- Keep image/table assets as first-class source artifacts for manuscripts, scans, page ornaments, and title images.

