# Extraction Schemas

## Common Candidate Envelope

All extraction candidate files use a small deterministic envelope:

```json
{
  "registry_name": "entities_candidates",
  "schema_version": "extraction-candidate-v1",
  "status": "framework_placeholder_only",
  "automatic_extraction_performed": false,
  "records": []
}
```

Candidate records are not accepted knowledge. They become registry entries only after
evidence validation and human review.

## Common Candidate Fields

| Field | Required | Description |
| --- | --- | --- |
| `candidate_id` | yes | Deterministic candidate identifier. |
| `candidate_type` | yes | Extraction family, such as `entity`, `motif`, or `simile`. |
| `surface_form` | optional | Exact text observed in evidence. |
| `canonical_form` | optional | Normalized target if known. |
| `source_record_id` | yes | Corpus record identifier, or `placeholder_only` in this phase. |
| `source_field` | optional | Field containing evidence, such as `verse_text`. |
| `source_url` | optional | Source URL for traceability. |
| `evidence_text` | optional | Short evidence span. |
| `confidence` | yes | Numeric confidence. Placeholder examples use `0.0`. |
| `status` | yes | `placeholder_seed`, `candidate`, `reviewed`, or `rejected`. |
| `review_notes` | optional | Human review comments. |

## Entity Candidate

```json
{
  "candidate_id": "entity_candidate_example_001",
  "candidate_type": "entity",
  "entity_type": "deity",
  "surface_form": "சிவன்",
  "canonical_form": "சிவன்",
  "aliases": ["சிவபெருமான்"],
  "source_record_id": "placeholder_only",
  "confidence": 0.0,
  "status": "placeholder_seed"
}
```

## Motif And Theme Candidates

Motif and theme candidates must distinguish literal words from analytical labels. For
example, a verse containing `நிலா` may support a moon-imagery candidate, but that
candidate should still preserve the exact word and evidence span.

## Epithet Candidate

Epithet candidates link descriptive names to a target entity only when evidence supports
the relationship.

```json
{
  "candidate_id": "epithet_candidate_example_001",
  "candidate_type": "epithet",
  "epithet": "சடையன்",
  "target_entity": "சிவன்",
  "source_record_id": "placeholder_only",
  "confidence": 0.0,
  "status": "placeholder_seed"
}
```

## Simile Candidate

Simile candidates should capture the comparison marker, subject, object, and evidence
span. Marker detection alone is insufficient for acceptance.

## Metaphor Candidate

Metaphor candidates require source-domain and target-domain fields. They should stay as
candidates until reviewed because figurative interpretation is high-risk.

## Relationship Candidate

Relationship candidates connect other candidates or registry records. They must be
traceable to exact corpus evidence before promotion.
