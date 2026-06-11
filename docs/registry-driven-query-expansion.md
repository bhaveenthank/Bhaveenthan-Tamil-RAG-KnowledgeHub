# Registry-Driven Query Expansion

## Purpose

Query expansion adds reviewed equivalent terms to a user's query before retrieval. It
helps a query such as `அப்பர் பாடல்கள்` also search the canonical author name
`திருநாவுக்கரசர்`, and helps a moon query cover `சந்திரன்`, `நிலா`, `மதி`, `திங்கள்`,
and `நிலவு`.

The registry is the knowledge source. The expander is only the retrieval technique that
applies that knowledge. Keeping these responsibilities separate makes every added term
reviewable and prevents retrieval code from accumulating untraceable hard-coded aliases.

## Supported Registries

The deterministic expander reads five curated files under `data/knowledge/`:

- `synonyms.json`: canonical concepts, synonyms, and variant forms
- `authors.json`: canonical author names and aliases
- `deities.json`: canonical deity names and aliases
- `motifs.json`: motif names and reviewed example patterns
- `literary_devices.json`: device names and recognition cues

A query may match one, several, or none of these registries. No match leaves the query
unchanged. Matches and applied rules are returned with the expanded query so later
retrieval diagnostics can explain exactly why each term was added.

## Retrieval Integration

Expansion is opt-in. `build_context.py --expand-query` expands the query immediately
before the existing hybrid retriever runs. The context package preserves:

- the original user query;
- the exact retrieval query;
- matched registries;
- deterministic expansion rules;
- the ordinary citation-ready retrieval contexts.

Without `--expand-query`, the existing context path and query text are unchanged.

## Analytical Value

Registry expansion is groundwork for author-name normalization, deity alias lookup,
imagery and motif discovery, literary-device search, and future cross-corpus analysis.
It can improve recall where a source uses a canonical name while a researcher uses an
alias, or where related literary terms express the same reviewed concept.

## Limitations

The seed registries are deliberately small. They do not yet model Tamil inflection,
sandhi, historical spellings, contextual ambiguity, or negative senses. Motif patterns
and literary-device cues are retrieval hints, not proof that a record contains that
motif or device. The evaluation therefore reports a deterministic corpus-evidence proxy
and does not claim human relevance judgment.

This phase performs no scraping, extraction, aggregation, answer generation, embedding
generation, or index rebuilding.
