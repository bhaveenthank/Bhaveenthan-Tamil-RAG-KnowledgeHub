# Book Registry Schema

## Purpose

The book registry sits between website categories and extracted corpus records. It records what a source work is, where it lives, which formats exist, which parser should handle it, and whether ingestion is legally and technically ready.

## Proposed Record

```json
{
  "book_id": "sangam_purananuru_tvu",
  "category_id": "sangam_literature",
  "collection_id": "ettuthokai",
  "work_id": "purananuru",
  "title_tamil": "புறநானூறு",
  "title_english": "Purananuru",
  "alternate_titles": [],
  "authors": [],
  "editors": [],
  "commentators": [],
  "period": "Sangam",
  "genre": "classical_poetry",
  "language": "ta",
  "source_urls": [],
  "source_format": "html",
  "text_availability": "full|partial|none|unknown",
  "commentary_availability": "full|partial|none|unknown",
  "image_availability": false,
  "pdf_availability": false,
  "image_urls": [],
  "pdf_urls": [],
  "parser_family": "verse_parser",
  "source_page_family": "unknown",
  "rights_status": "unknown|public_domain|permission_required|external_reference",
  "rights_notes": "",
  "ingestion_status": "discovered|inspected|pilot_ready|pilot_ingested|complete|deferred|failed",
  "validation_status": "not_validated|pilot_valid|valid|partial|invalid",
  "collection_family": "sangam",
  "source_metadata": {},
  "notes": ""
}
```

## Identity

- `book_id` is deterministic and source-scoped.
- `category_id` must exist in the website category registry.
- `collection_id` groups related works where the source exposes a meaningful collection.
- `work_id` is the normalized literary work identity and may be shared by multiple editions.
- Source URLs and source-format metadata distinguish editions without losing the normalized work link.

## Availability

Text, commentary, image, and PDF availability are independent. An image book must not be marked text-complete simply because page images exist. OCR output, when later approved, is a derived artifact with its own method, confidence, and validation state.

## Rights And Policy

`rights_status` and `rights_notes` record only evidence available from the source or project review. The registry must not infer public-domain status from age or category name alone. External-library entries require independent robots, terms, and rights review.

## Workflow States

1. `discovered`: catalog entry recorded.
2. `inspected`: page family and content units documented.
3. `pilot_ready`: bounded allowlist and parser acceptance criteria approved.
4. `pilot_ingested`: pilot artifacts exist.
5. `complete`: approved scope extracted and audited.
6. `deferred` or `failed`: reason recorded.

Validation state remains separate from ingestion state so a downloaded work cannot appear production-ready before quality review.
