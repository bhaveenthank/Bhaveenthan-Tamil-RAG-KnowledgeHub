# Dictionary Pilot Ingestion

## Why Dictionary First

The Tamil–Tamil dictionary pilot is the first non-Thirumurai content type because a
dictionary entry has a smaller, clearer boundary than prose chapters, grammar commentary,
Sangam colophons, or encyclopedia articles. The selected work is the typed
*Tamil - Tamil Agaramuthali* by M. Shanmugampillai.

Exactly three pages were allowlisted:

1. the dictionary work landing page;
2. the alphabet navigation page;
3. one exact entry response, `x=1&y=1`.

No category crawl or range download was performed.

## Difference From Verse Content

A verse record preserves poetic line order, hymn hierarchy, author, place, pann, and
commentary. A dictionary record instead centers on a headword and its definition. Meaning
order, grammatical labels, examples, etymology, and cross-references matter more than
stanza or hymn structure.

The observed entry endpoint uses a table with the headings:

- `சொல்`
- `அருஞ்சொற்பொருள்`

The source does not provide a dedicated part-of-speech column in the sampled entry. The
parser therefore leaves `part_of_speech` empty rather than inventing it.

## Literary Value

Dictionary support provides a future authority layer for:

- Tamil-first word explanations;
- synonym and near-synonym expansion;
- rare-word analysis in classical poetry;
- comparison of literary usage against lexical meanings;
- transparent citations for lexical claims.

The current definition remains intact as source text. Splitting semicolon-delimited senses
is deferred until more entry variants prove a reliable rule.

## Schema Mapping

| Source Element | Unified Schema v2 |
| --- | --- |
| Dictionary work | `book_id`, `work_id`, `source_metadata.source_work` |
| சொல் | `entry_headword`, `title` |
| அருஞ்சொற்பொருள் | `definition`, `content_text` |
| Explicit grammatical label | `part_of_speech` |
| Entry endpoint | `source_url` |
| Fixture provenance | `source_metadata` |

Every record has `record_type=dictionary_entry`,
`parser_family=dictionary_parser`, and a SHA-256-derived deterministic ID.

## Parser Challenges

- navigation pages and entry tables share one source family;
- range endpoints may contain many rows and are prohibited in this pilot;
- part of speech may be embedded in prose rather than labeled;
- semicolons may separate senses, grammatical functions, or related meanings;
- other TamilVU dictionaries may use different tables or scripts.

This pilot validates only the observed two-column table and does not authorize expansion.
