# Sangam Literature Pilot Ingestion

## Why Natrinai

Natrinai is the first non-devotional poetry pilot because it tests whether the existing
verse parser family can preserve a different literary hierarchy without forcing Sangam
poems into hymn fields. It also contributes direct value for poet, thinai, situation, and
classical-language analysis.

The pilot uses exactly three allowlisted TamilVU pages:

1. the Natrinai wrapper page;
2. its left navigation frame;
3. the first ten-poem endpoint, retained as a compact fixture excerpt of poems 1-3.

No additional poem group or commentary page was fetched.

## Difference From Thirumurai

Thirumurai records are organized by devotional work, author, hymn/pathigam, sacred place,
pann, verse, and prose commentary. Natrinai is an anthology organized by poem number and
thinai; its closing colophon supplies a dramatic situation and poet. The two traditions
therefore share line-preserving verse content but require different literary identity
fields.

Proving both through one parser family matters for cross-corpus analysis. It allows future
research to compare imagery, motifs, authors, places, situations, themes, and word usage
without erasing the source tradition's own hierarchy. Place extraction and thematic
classification are deliberately deferred because the pilot source does not label them as
separate fields.

## Observed Structure

The wrapper is an iframe container. The navigation frame links to content groups such as
`1-10` using `l1210son.jsp?subid=3362`. Within the content response, each poem has:

- a numbered heading and explicit thinai;
- ordered verse lines;
- an `உரை` link with `book_id` and `song_no`;
- a final colophon combining situation text and poet.

The parser splits the colophon only at its final source separator. It does not infer a
modernized thurai category or alter the poem text.

## Unified Schema Mapping

| Source Element | Unified Schema v2 |
| --- | --- |
| Natrinai | `work_id=natrinai` |
| Ettuthokai | `book_id=ettuthokai` |
| Poem number | `poem_no`, `verse_no`, `song_no` |
| Thinai heading | `thinai` |
| Verse lines | `verse_text`, `content_text` |
| Situation text | `thurai` |
| Full closing text | `colophon` |
| Poet | `author` |
| Poem group URL | `source_url` |
| Urai endpoint | `commentary_url` |

Records use `record_type=verse`, `parser_family=verse_parser`, and deterministic
SHA-256-derived IDs.

## Parser Risks

- Natrinai pages group multiple poems inside legacy, imperfect HTML.
- Colophon separators and poet attribution may vary.
- Some poems may omit or alter thinai, poet, or commentary links.
- Commentary structure is not inspected in this phase.
- Other Sangam works may use a related but non-identical template.

This pilot validates only the committed three-poem fixture and does not authorize an
anthology or category scrape.
