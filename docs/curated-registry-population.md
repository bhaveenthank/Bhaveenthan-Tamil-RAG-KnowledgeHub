# Curated Registry Population

## Why Curated Knowledge Is Needed

Tamil literary analytics cannot safely equate every similar-looking word or infer every
deity, author, motif, or literary device from string matching. A small curated authority
set provides stable identities and reviewed starter vocabulary for evaluation before any
automatic process is introduced.

## Why Automatic Extraction Is Premature

Classical Tamil is highly contextual. A term may be a literal object, divine attribute,
epithet, metaphor, place, or ordinary noun depending on the passage. The current corpus has
no reviewed annotation sample against which automatic extraction quality could be
measured. Automating first would create unquantified errors and weak ground truth.

## Curated Seed Scope

This phase manually curates:

- three synonym concepts: moon, sun, and ocean
- three deity identities: Siva, Murugan, and Vishnu
- three Tevaram author identities
- three imagery motifs: moon, fire, and river
- three literary devices: simile, metaphor, and epithet

Each record has a deterministic ID and `status=curated_seed`. These records are authority
seeds, not claims that a form occurs in any particular corpus record.

## Evaluation Role

The curated seeds can become:

- expected canonical IDs for entity-linking tests
- approved lexical forms for synonym-expansion evaluation
- positive vocabulary for manually annotated motif and device fixtures
- normalization targets for author and deity metadata
- stable expected outputs for future extraction validation

Evaluation must still use exact corpus evidence and negative examples. Registry membership
alone is not a valid occurrence annotation.

## Future Query Expansion

A later query-expansion phase may resolve a user term to a concept ID and expand only to
approved forms. It must preserve the original query, expose which forms were added, handle
ambiguous aliases, and benchmark precision as well as recall. This phase does not implement
that behavior.

## Quality Boundary

The seeds are intentionally small and manually curated, but they are not yet a
publication-ready scholarly authority. Future expansion needs cited lexical sources,
reviewer metadata, ambiguity notes, version history, evidence annotations, and Tamil
researcher review.
