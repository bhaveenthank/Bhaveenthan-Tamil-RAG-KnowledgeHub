# Knowledge Registry Schemas

All registry files use this envelope:

```json
{
  "registry_name": "entities",
  "schema_version": "knowledge-registry-v1",
  "status": "foundation_seed_only",
  "records": []
}
```

Seed records are illustrative and unreviewed. Population phases must add source,
reviewer, version, and evidence metadata before analytical use.

## Entity Registry

```json
{
  "entity_id": "",
  "entity_type": "",
  "canonical_name": "",
  "aliases": [],
  "description": ""
}
```

## Synonym Registry

```json
{
  "concept_id": "",
  "canonical_term": "",
  "synonyms": [],
  "variant_forms": []
}
```

## Motif Registry

```json
{
  "motif_id": "",
  "motif_name": "",
  "description": "",
  "example_patterns": []
}
```

## Author Registry

```json
{
  "author_id": "",
  "canonical_name": "",
  "aliases": [],
  "period": "",
  "works": []
}
```

## Deity Registry

Required fields: `deity_id`, `canonical_name`, `aliases`, `tradition`, `description`.
Epithets remain separate reviewed relationships rather than being treated automatically
as synonyms.

## Place Registry

Required fields: `place_id`, `canonical_name`, `aliases`, `place_type`, `description`.
Future records may link historical names and geographic identifiers.

## Work Registry

Required fields: `work_id`, `canonical_title`, `aliases`, `authors`, `period`, `genre`.
Edition and source-page identity remain in corpus provenance, not in the work authority.

## Theme Registry

Required fields: `theme_id`, `theme_name`, `description`, `related_concepts`.

## Literary Device Registry

Required fields: `device_id`, `device_name`, `description`, `recognition_cues`.
Recognition cues are review aids, not sufficient evidence for automatic classification.

## Future Evidence Contract

Extraction phases should create annotations separate from these registries:

```json
{
  "annotation_id": "ann_...",
  "knowledge_id": "entity_moon",
  "record_id": "tvu_...",
  "field": "verse_text",
  "surface_form": "மதி",
  "start_offset": 0,
  "end_offset": 3,
  "relation_type": "mentions",
  "method": "manual|rule|model",
  "confidence": 1.0,
  "review_status": "unreviewed|accepted|rejected",
  "source_url": ""
}
```
