# SaanruGraph Phase 3 Annotation Guideline

Dataset version: `saanrugraph-thevaram-1-7-gold-annotation-v1`

## Goal

Create a trusted gold set for Paadal to Pozhippurai linking evaluation. The human label is the authority. The model confidence and prior label are shown only to help sampling diagnostics; do not copy them blindly.

## What To Annotate

For each row, compare `source_text` from the Paadal with `target_text` from the Pozhippurai. Use `full_paadal_text` and `full_pozhippurai` as context.

## Allowed Link Labels

- `link`
- `partial_link`
- `no_link`
- `unsure`

Use:

- `link` when the target span directly explains the source span.
- `partial_link` when the target explains part of the source span or is too broad but still contains the explanation.
- `no_link` when the target is unrelated, only shares an entity, or explains a different phrase.
- `unsure` when a Tamil literary/scholarly judgment is needed.

## Allowed Relation Labels

- `glosses_word`
- `explains_phrase`
- `explains_line`
- `interprets_image`
- `describes_entity`
- `theological_explanation`

Relation definitions:

- `glosses_word`: explains a single word or lexical form.
- `explains_phrase`: explains a phrase shorter than a full line.
- `explains_line`: explains the whole paadal line.
- `interprets_image`: explains poetic imagery, symbol, iconography, or metaphorical image.
- `describes_entity`: explains a deity, place, body part, object, person, or named entity.
- `theological_explanation`: explains grace, karma, liberation, devotion, worship, doctrine, or spiritual result.

## Exact Span Correction

If `target_text` is too broad or slightly wrong, fill:

- `exact_pozhippurai_span_reviewed`
- `corrected_target_start_char` if easy
- `corrected_target_end_char` if easy

If exact character offsets are hard, the exact text span alone is enough for Phase 3.

## Double Annotation

The file `gold_double_annotation_subset_100.csv` should be independently labeled by two people if possible. Fill `annotator1_label` and `annotator2_label`; agreement can then be calculated.

## Important Rules

- Do not mark empty Pozhippurai rows as linker errors. They are true missing-commentary coverage cases.
- A shared word or shared entity alone is not enough for `link`.
- A valid explanation may be in reverse order compared with the Paadal.
- Single-token spans can be valid, especially deity/object/theology words.
- Prefer `partial_link` over `link` when the target span is too broad.
