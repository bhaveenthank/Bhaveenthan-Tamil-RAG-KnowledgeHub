# Future Knowledge Extraction Targets

No extraction is implemented in this phase. The following targets define future
evidence-bearing annotation work.

| Target | Registry Link | Required Evidence | Main Risk |
| --- | --- | --- | --- |
| deity names | Deity, Entity | exact text span and canonical deity ID | name may be common noun or context-dependent |
| author names | Author | source metadata or explicit text span | variant names and honorifics |
| place names | Place, Entity | text span, source place field, or title evidence | sacred-place aliases and historical names |
| epithets | Deity, Literary Device | epithet span and described deity relation | synonym/attribute/epithet boundary |
| metaphors | Literary Device, Theme, Entity | source and target spans with interpretation | contextual and scholarly disagreement |
| similes | Literary Device, Entity | comparison spans and cue evidence | implicit comparisons without fixed markers |
| themes | Theme | passage-level evidence and review rationale | overly broad or anachronistic labels |
| imagery | Motif, Entity | image-bearing span and normalized concept | literal object versus poetic image |
| motifs | Motif, Theme | repeated pattern with multiple cited occurrences | recurrence threshold and variant forms |
| relationships | all registries | typed source/target IDs and evidence span | false links caused by ambiguous aliases |

## Annotation Requirements

Every future annotation should preserve `record_id`, field, surface form, offsets,
knowledge ID, relation type, method, confidence, review status, and source URL. Automatic
methods must be evaluated against a manually reviewed Tamil sample before corpus-wide use.

## Deferred Work

This phase does not tokenize the corpus, scan terms, infer entities, classify literary
devices, count occurrences, or modify existing records.
