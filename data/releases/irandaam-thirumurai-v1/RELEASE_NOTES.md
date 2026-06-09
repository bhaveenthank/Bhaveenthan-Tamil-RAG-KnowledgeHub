# Irandaam Thirumurai Corpus v1 Release Notes

## Version

- Corpus name: `Irandaam Thirumurai Corpus`
- Version: `v1`
- Candidate manifest version: `candidate-v1`
- Schema version: `irandaam-thirumurai-jsonl-v0.1`
- Extractor version: `irandaam_thirumurai_builder:0.1`
- Source: TamilVU

## Corpus Statistics

- Hymns: `122`
- Verse records: `1331`
- Extraction status `success`: `1324`
- Extraction status `partial_commentary`: `7`
- Missing verse text: `0`
- Missing commentary URLs: `0`
- Missing `pozhppurai`: `4`
- Missing `kurippurai`: `3`
- Duplicate `song_no`: `0`
- Duplicate commentary URLs: `0`
- Sampled coverage: `100%`

## Extraction Methodology

The corpus was built from the Irandaam Thirumurai TamilVU left-frame navigation endpoint:

`https://www.tamilvu.org/slet/l4120/l4120lft.jsp`

The builder extracted valid hymn links matching `l4120son.jsp?subid=...`, fetched each hymn page, extracted verse text and `உரை` commentary URLs, then fetched static commentary pages with `requests` and parsed them with BeautifulSoup.

The extraction preserved raw source snapshots separately and wrote one JSONL record per verse/song.

## Known Limitations

- Seven records have partial commentary because the corresponding source HTML appears to omit either `pozhppurai` or `kurippurai`.
- These seven records are preserved with `partial_commentary` status and were classified as `SOURCE_MISSING` during audit.
- Link-title metadata such as `hymn_location`, `hymn_note`, and `pann` is parsed from TamilVU navigation labels and may require later scholarly curation.
- This release covers Irandaam Thirumurai only.

## Source Attribution

Source pages are from Tamil Virtual Academy / TamilVU:

`https://www.tamilvu.org/`

Each record includes its hymn URL and commentary URL for provenance.

## Release Integrity

Checksums are recorded in:

`corpus_checksum.sha256`

Do not edit release files in place. Future corrections should become a separate repair phase or v2 release.
