# கலைக்களஞ்சியங்கள் Pilot Fixtures

- Category ID: `encyclopedias`
- Parser family: `dictionary_parser`
- Planned fixture type: `mixed`
- Target fixture count: `3`
- Risk level: `high`
- Source status: `metadata_only_unconfirmed`

## Expected Structure

Headword article with sections, references, author/editor metadata, cross-links, tables, and possible images.

## Required Fixture Coverage

1. article index or navigation
2. plain text article
3. article with references, table, or media

## Collection Rule

Add only a tiny, allowlisted, source-attributed fixture after source inspection is
explicitly approved. Do not place full books, full category exports, credentials,
copyright-restricted bulk text, or generated corpus outputs in this directory.

## Notes

The current dictionary-parser assignment may need a dedicated encyclopedia adapter after fixtures expose mixed article and media structure.
