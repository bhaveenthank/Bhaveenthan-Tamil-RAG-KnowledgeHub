# Unified Thirumurai Corpus Schema

## Contract

The normalized format is UTF-8 JSONL with one literary verse record per line. Schema version: `unified-thirumurai-v1`.

```json
{
  "schema_version": "unified-thirumurai-v1",
  "record_id": "thevaram_02_1664_1470",
  "corpus_id": "thirumurai_02",
  "thirumurai_no": 2,
  "collection": "Thirumurai",
  "canonical_title": "Irandaam Thirumurai",
  "author": "Tirugnanasambandar",
  "nayanmar": "Tirugnanasambandar",
  "hymn_id": "1664",
  "pathigam_id": "1664",
  "song_no": "1470",
  "verse_no": "1",
  "title": "2.1 திருப்பூந்தராய் - வினா உரை - இந்தளம்",
  "place": "திருப்பூந்தராய்",
  "deity": "Siva",
  "verse_text": "...",
  "pozhppurai": "...",
  "kurippurai": "...",
  "source_url": "https://www.tamilvu.org/...",
  "commentary_url": "https://www.tamilvu.org/...",
  "metadata": {}
}
```

## Required Fields

The following fields must exist and have the declared type:

| Field | Type | Rule |
| --- | --- | --- |
| `schema_version` | string | Must identify the unified contract. |
| `record_id` | string | Stable and unique across normalized records. |
| `corpus_id` | string | Registry ID, namespaced by Thirumurai. |
| `thirumurai_no` | integer | Integer from 1 through 12. |
| `collection` | string | Canonical broad collection; currently `Thirumurai`. |
| `canonical_title` | string | Normalized title of the registered corpus. |
| `author` | string | Normalized primary author for the record. |
| `nayanmar` | string | Normalized Nayanmar identity where applicable. |
| `hymn_id` | string | Source-preserved hymn identifier. |
| `pathigam_id` | string | Stable pathigam identifier; may equal `hymn_id`. |
| `song_no` | string | Source-preserved song identifier. |
| `verse_no` | string | Verse order within its literary parent. |
| `title` | string | Source-preserved hymn or literary-unit title. |
| `place` | string | Place when available; empty is allowed for future works. |
| `deity` | string | Normalized principal deity or subject. |
| `verse_text` | string | Required source verse text. |
| `pozhppurai` | string | Commentary field; empty only when unavailable. |
| `kurippurai` | string | Commentary field; empty only when unavailable. |
| `source_url` | string | Exact source page URL. |
| `commentary_url` | string | Exact commentary URL when available. |
| `metadata` | object | Source-specific and versioned metadata. |

## Derived Fields

`corpus_id`, normalized `author`, `nayanmar`, `collection`, `canonical_title`, `deity`, and `schema_version` are derived during normalization. Derivation must never overwrite source text or identifiers.

For Irandaam Thirumurai:

- `record_id`, `canonical_id`, `source_record_id`, and `verse_id` are preserved from v1.1.
- `pathigam_id` maps to the existing `hymn_id`.
- `verse_no` maps to `verse_index_in_hymn`.
- `source_url` maps to the hymn URL.
- `commentary_url` remains the exact TamilVU commentary endpoint.

## Optional Values

The fields themselves are present in every record, but these values may be empty:

- `place`, when a work has no place association.
- `pozhppurai` or `kurippurai`, when the audited source lacks that section.
- `commentary_url`, for source families without a distinct commentary endpoint.

An empty required-value exception must be reported by corpus validation or explicitly allowed by the source-family contract.

## Metadata Object

The initial metadata object preserves:

- source and source site
- source and enriched corpus versions
- source record, canonical, and verse IDs
- original author and collection labels
- work, pann, and hymn note
- citation text
- commentary availability
- extraction status

Retrieval-only arrays such as tokens and keyword candidates are intentionally excluded.

## Future Enhancements

Future versioned metadata may include:

- normalized deity aliases and epithets
- place authority IDs and alternate names
- Tamil literary synonym concepts
- imagery and motif labels
- simile and metaphor annotations
- mythic events
- meter and pann authority records
- annotation method, confidence, reviewer, and version

These are enrichments, not replacements for the original verse and commentary.
