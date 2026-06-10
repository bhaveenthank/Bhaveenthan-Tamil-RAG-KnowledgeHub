# Unified Website Corpus Schema v2

## Design

Schema v2 supports heterogeneous TamilVU materials while preserving the complete Thirumurai identity surface. It uses a common provenance envelope plus record-type-specific fields. Empty non-applicable fields are allowed; required fields depend on `record_type`.

## Common Record

```json
{
  "schema_version": "website-corpus-v2",
  "record_id": "stable-source-scoped-id",
  "record_type": "verse",
  "category_id": "saivam",
  "collection_id": "thirumurai",
  "book_id": "panniru_thirumurai",
  "work_id": "thevaram_thirumurai_02",
  "corpus_id": "thirumurai_02",
  "title": "",
  "author": "",
  "language": "ta",
  "genre": "",
  "period": "",
  "section_id": "",
  "chapter_id": "",
  "page_no": "",
  "content_text": "",
  "commentary_text": "",
  "source_url": "",
  "commentary_url": "",
  "image_url": "",
  "pdf_url": "",
  "source_metadata": {}
}
```

## Supported Record Types

| Record Type | Required Content Fields | Typical Structure |
| --- | --- | --- |
| `verse` | `verse_text`, `content_text` | poem/hymn verse and optional commentary |
| `hymn` | `hymn_id`, `title` | pathigam/hymn-level metadata and summary |
| `prose_section` | `content_text`, section or chapter identity | paragraph/section/page |
| `grammar_rule` | `content_text`, rule identity | sutra/rule, explanation, examples |
| `dictionary_entry` | `entry_headword`, `content_text` | headword, senses, labels, examples |
| `encyclopedia_entry` | `entry_headword`, `content_text` | article, references, media |
| `manuscript_image` | `image_url` or `pdf_url` | folio/page metadata and optional transcription |
| `external_reference` | `source_url`, `title` | external institution/library reference |

## Generalized Fields

- `category_id`: website category registry identity.
- `collection_id`: collection family within a category.
- `book_id`: source edition/book registry identity.
- `work_id`: normalized literary or reference work.
- `record_type`: content-unit contract.
- `section_id`, `chapter_id`, `page_no`: source hierarchy.
- `entry_headword`: dictionary, nigandu, encyclopedia, terminology, or index headword.
- `transliteration`: source-provided or derived romanized form, with method in metadata.
- `language`: primary content language; additional languages belong in metadata.
- `genre`, `period`: normalized labels with original values preserved.
- `content_text`: record's principal searchable text.
- `commentary_text`: generalized commentary/explanation.
- `image_url`, `pdf_url`: exact source asset URLs.
- `source_metadata`: source hierarchy, hashes, parser, warnings, rights notes, and type-specific data.

## Preserved Thirumurai Fields

Schema v2 retains:

- `corpus_id`
- `thirumurai_no`
- `author`
- `nayanmar`
- `hymn_id`
- `pathigam_id`
- `song_no`
- `verse_no`
- `verse_text`
- `pozhppurai`
- `kurippurai`
- `source_url`
- `commentary_url`

For Thirumurai verse records, `content_text` equals the normalized verse text and `commentary_text` combines available commentary without deleting the separate fields.

## Type-Specific Fields

### Poetry And Hymns

`poet`, `meter`, `pann`, `thinai`, `thurai`, `place`, `deity`, stanza/line order, and commentary fields may be carried in `source_metadata` until promoted by a later schema version.

### Grammar

Rule number, sutra text, explanation, examples, exception, source chapter, and commentator must remain separable.

### Dictionary And Encyclopedia

Headword, homonym number, sense order, part of speech, definition, example, etymology, cross-reference, and domain label must remain structured.

### Manuscript And Image

Asset URL, folio/page label, dimensions, caption, collection, script, condition, rights note, and optional transcription/OCR confidence must remain traceable to the image.

## Validation Principles

- Every record has a stable ID, category, book/work identity, record type, and exact source URL.
- Required fields are selected by record type.
- Source text and derived text are distinguishable.
- Hierarchy and source order are preserved.
- Empty optional fields do not become invented metadata.
- OCR, transliteration, entities, and literary annotations carry method/version/confidence metadata.
- Existing frozen Thirumurai artifacts are not rewritten in place.
