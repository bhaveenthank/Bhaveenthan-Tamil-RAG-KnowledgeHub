# Multi-Thirumurai Corpus Expansion

## Why A Single Corpus Is Not Enough

Irandaam Thirumurai supports reliable lookup, retrieval, citation, and limited within-corpus analysis. It cannot answer questions that compare Sambandar with Appar or Sundarar, measure motifs across all Thirumurai, or identify how an epithet changes between authors. Those claims need complete, consistently described evidence from more than one corpus.

The expansion framework therefore comes before additional scraping. It establishes the identities, metadata contract, validation rules, and registry states that every later corpus must satisfy.

## Shared Schema

All twelve Thirumurai are registered under deterministic IDs such as `thirumurai_02`. Each normalized verse record uses the same top-level fields for corpus, author, Nayanmar, hymn/pathigam, song, verse, place, deity, commentary, and provenance.

Source-specific fields remain in `metadata`. This accommodates structural differences such as:

- Tevaram pathigams in Thirumurai 1-7.
- Tiruvacakam and Tirukkovaiyar in Thirumurai 8.
- Multi-author works in Thirumurai 9 and 11.
- Tirumantiram's different literary organization in Thirumurai 10.
- Periyapuranam's narrative structure in Thirumurai 12.

The shared contract does not force those works into a false Tevaram hierarchy. Instead, future source adapters map their native units to stable corpus, work, section, and verse identities.

## Preparation For Future Scraping

The registry is a planning and readiness artifact, not a crawl queue. A corpus may move to `available` only after:

1. Source inspection identifies its page families and unit hierarchy.
2. A small allowlisted pilot verifies extraction.
3. Representative sampling confirms parser assumptions.
4. Full extraction passes schema, coverage, and source audits.
5. The resulting corpus is frozen and normalized without modifying earlier releases.

No new TamilVU content is fetched in this phase.

## Comparison And Aggregation

Normalized author and Nayanmar fields make author comparison explicit. Stable `corpus_id`, `hymn_id`, `song_no`, and `record_id` values prevent identifier collisions when multiple Thirumurai are combined.

Corpus-wide analytical operations can later group or count by:

- corpus and Thirumurai
- author or Nayanmar
- place and deity
- pann and work
- hymn/pathigam and verse
- commentary availability
- future normalized epithet, imagery, motif, and literary-device annotations

This analysis path must scan the complete eligible corpus. It must not treat top-k RAG contexts as exhaustive evidence.

## Synonyms, Motifs, And Literary Entities

The unified schema supplies stable records to which future enrichments can attach. A Tamil literary synonym lexicon can expand concepts such as moon into source-preserving variants. Entity and motif annotations can identify deities, epithets, places, natural imagery, similes, and mythic events.

These enrichments should be versioned separately from source text. Automated labels must retain confidence and method metadata, while scholarly corrections remain auditable.

## Current Result

- Twelve Thirumurai are registered under the broader website-wide corpus architecture.
- Irandaam Thirumurai remains fully `available`.
- Fourth Thirumurai is `available` with `pilot_verified` status for a bounded five-hymn sample, not a complete corpus.
- Both available artifacts are normalized into the shared schema.
- Frozen v1 and retrieval-ready v1.1 remain unchanged.
- Scraping, embedding generation, vector indexing, and answer generation remain outside this phase.
