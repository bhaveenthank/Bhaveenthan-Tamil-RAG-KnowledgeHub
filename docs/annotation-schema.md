# Annotation Schema

## Annotation File Envelope

```json
{
  "annotation_set": "entities_gold",
  "schema_version": "annotation-gold-v1",
  "status": "manual_gold_seed",
  "automatic_extraction_performed": false,
  "records": []
}
```

## Record Schema

```json
{
  "record_id": "gold_entity_001",
  "source_record_id": "local_record_id",
  "source_file": "data/processed/...",
  "source_url": "https://...",
  "text": "சிவன் , திருமால் , பிரமன்",
  "annotations": []
}
```

## Span Annotation Schema

```json
{
  "annotation_id": "ann_001",
  "type": "entity",
  "label": "deity",
  "text": "சிவன்",
  "start": 0,
  "end": 5,
  "review_status": "manual_gold_seed"
}
```

The substring `record.text[start:end]` must equal `annotation.text`.

## Relationship Annotation Schema

```json
{
  "annotation_id": "rel_001",
  "type": "relationship",
  "source": "ann_entity_001",
  "target": "ann_epithet_001",
  "relationship_type": "deity_has_epithet",
  "review_status": "manual_gold_seed"
}
```

Relationship `source` and `target` values must refer to annotation IDs in the same record.

## Required Annotation Types

- `entity`
- `deity`
- `author`
- `place`
- `work`
- `motif`
- `theme`
- `epithet`
- `simile`
- `metaphor`
- `relationship`

## Phase Boundary

These files are manual gold fixtures. They are not extraction output and do not populate
the curated knowledge registries.
