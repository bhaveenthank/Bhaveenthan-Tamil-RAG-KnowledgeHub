# Controlled Fourth Thirumurai Pilot Expansion

## Purpose

The Irandaam Thirumurai pipeline proves one complete Sambandar corpus and one TamilVU page family. Before approving three or four additional Thirumurai, the project needs evidence that ingestion, normalization, validation, and audit work for another author without weakening existing artifacts.

This phase selects exactly one additional corpus and deliberately limits ingestion to five hymns.

## Selected Pilot

The pilot is **Naangaam Thirumurai (Fourth Thirumurai)** by **Tirunavukkarasar/Appar**.

It was selected because:

- it introduces a second Nayanmar for future author comparison;
- it remains within Tevaram, keeping the literary hierarchy reasonably comparable;
- TamilVU exposes static SLET hymn and commentary pages that can be fetched without browser automation;
- it tests meaningful parser variation before attempting structurally different works such as Tirumantiram or Periyapuranam.

## Fixed Scope

- Navigation endpoint: `https://www.tamilvu.org/slet/l4140/l4140lft.jsp`
- Discovered hymn links: 113 at inspection time.
- Pilot selection: first five deterministic navigation entries.
- The CLI cannot silently expand to the remaining hymns.
- Raw snapshots are stored under `data/raw/pilot/thirumurai_04/`.
- Pilot records are stored under `data/processed/pilot/`.
- Existing Irandaam Thirumurai files are never used as output paths.

The registry marks this corpus `available` with `verification_status = pilot_verified` only after validation passes. This means the pipeline adapter is proven for the bounded sample; it does not mean the Fourth Thirumurai corpus is complete.

## Parser Differences

TamilVU's Fourth Thirumurai navigation page is under `l4140`, while hymn links use the legacy filename `l4130son.jsp`. Hymn pages use `l4140uri.jsp` commentary endpoints with `book_id=112` and `head_id=62`.

Other observed differences:

- song numbers restart within each hymn;
- verse tables contain additional nested heading tables;
- commentary includes `பொ-ரை`, `பொருள்`, `விளக்கம்`, and `குறிப்பு` sections;
- commentary can be substantially longer than Second Thirumurai commentary.

The pilot uses a source-specific adapter around shared snapshot, URL, title, statistics, schema, and validation functions. It does not modify the proven Second Thirumurai parser.

## Normalization

Pilot records map to `unified-thirumurai-v1` with:

- `corpus_id = thirumurai_04`
- `thirumurai_no = 4`
- normalized author and Nayanmar `Tirunavukkarasar`
- deterministic record IDs namespaced by corpus, hymn, and song
- source-preserved hymn and commentary URLs
- source commentary mapped into `pozhppurai` and `kurippurai`

## Expansion Decision

This pilot prepares the next decision; it does not approve bulk extraction. Before a full Fourth Thirumurai run, the project should review:

- parser coverage across first, middle, and last hymns;
- commentary label variation;
- hymn-local song numbering;
- duplicate verse behavior;
- author, place, pann, and source metadata;
- rate limits and expected request volume.

Only after that review should a separately authorized full-corpus extraction be considered.
