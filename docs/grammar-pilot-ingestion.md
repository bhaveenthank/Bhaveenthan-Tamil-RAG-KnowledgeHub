# Grammar Pilot Ingestion

## Why Grammar Next

The readiness audit identified grammar as the highest-information next pilot. Saivam and
Sangam proved two poetry hierarchies, while dictionaries proved a lexical record. Grammar
adds a genuinely new structure: a numbered rule or sutra inside a chapter and section,
with explanation, examples, exceptions, and commentary potentially attached.

The selected work is *நன்னூல் - காண்டிகையுரை*. Exactly three TamilVU pages were
allowlisted:

1. the Nannul wrapper page;
2. its left navigation frame;
3. the `எழுத்து இயல்` endpoint containing rules 56 and 57.

No other section or commentary endpoint was fetched.

## Difference From Verse And Dictionary Content

Verse records preserve literary line order, poem or hymn identity, author, and literary
metadata. Dictionary records center on a headword and definition. Grammar records center
on a normative rule and its structural context. Rule text must remain separate from later
explanation, examples, exceptions, and commentator prose.

The sampled rules are metrical in form, but they are classified as `grammar_rule`, not
literary verse. This distinction is essential for accurate retrieval and citation.

## Observed Source Structure

The wrapper is an iframe container. The navigation hierarchy is:

`எழுத்ததிகாரம் → எழுத்தியல் → எழுத்து இயல்`

The content endpoint is `l0900son.jsp?subid=212`. It contains numbered rules, preserved
line breaks, and JavaScript `உரை` controls with stable `song_no`, `book_id`, and `head_id`
parameters.

## Unified Schema Mapping

| Source Element | Unified Schema v2 |
| --- | --- |
| Nannul work | `book_id`, `work_id`, `source_metadata.source_work` |
| எழுத்ததிகாரம் | `chapter_id` |
| எழுத்தியல் | `section_id` |
| Rule number | `rule_no` |
| Sutra/rule text | `rule_text`, `content_text` |
| Commentary text | `explanation_text` |
| Rule endpoint | `source_url` |
| Urai endpoint | `commentary_url` |
| Fixture provenance | `source_metadata` |

`explanation_text` is empty in this pilot because fetching commentary would exceed the
three-page ceiling. The source URL is retained and the absence is explicitly documented.

## Parser Challenges

- legacy table markup may vary across sections;
- rule text can resemble poetry but must retain grammar semantics;
- commentary, examples, and exceptions may use different labels or endpoints;
- commentator identity may depend on the selected edition or commentary work;
- Tolkappiyam and other grammar works may have deeper hierarchy;
- cross-rule references need structured links rather than flattened prose.

## Linguistic Value

Structured grammar records will later support Tamil-first rule lookup, comparison between
prescriptive grammar and literary usage, grammatical classification of cited examples,
and research across grammar traditions. This bounded pilot establishes the record contract;
it does not claim linguistic coverage of Nannul or TamilVU grammar collections.
