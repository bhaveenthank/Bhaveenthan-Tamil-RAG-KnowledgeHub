# A Semantic Ontology for Thevaram Literary Analysis: Modeling Deities, Sacred Places, Iconography, Nature Imagery, and Commentary Evidence

## Abstract

Classical Tamil literary question answering requires more than passage retrieval. A user may ask which hymns invoke Shiva through specific epithets, which sacred places are associated with particular imagery, how commentary explains mythological references, or where nature images function as iconographic evidence. Such questions require a semantic layer that preserves textual evidence while modeling deities, sacred places, epithets, objects, natural imagery, theological concepts, music, and relations. This paper presents a corpus-driven ontology and annotation framework for Thevaram literary analysis. The ontology defines 25 entity types, 29 relation types, 14 attributes, and a 20-item mythological event canon. A deterministic annotation pass over the Thevaram 1-8 normalized corpus produced 624 registry rows, 823 aliases, 107761 entity mentions, 4491 relationship records, and 30710 cross-type overlap records. Validation checks found zero invalid bounds, zero span text mismatches, and zero duplicate mention identifiers. We position the ontology as a review-aware semantic evidence layer for future citation-grounded Tamil literary retrieval and question answering, while explicitly distinguishing it from a final expert-validated scholarly ontology.

## 1. Introduction

The first step in building useful computational tools for Tamil literature is to create reliable corpora. The next step is to make those corpora semantically usable. A verse-level corpus can support search for exact words and citations, but many literary questions require more structure. For example, a reader may ask: Which hymns refer to Shiva through iconographic signs? Which sacred places are associated with rivers or flowers? Which verses mention Vishnu or Brahma in relation to Shiva? Which commentary passages explain a mythological event? These questions cannot be answered safely by raw keyword search alone.

This paper presents a semantic ontology and annotation framework for Thevaram literary analysis. It builds on a normalized Thevaram 1-8 corpus and introduces a structured vocabulary for agents, sacred places, objects, nature imagery, body imagery, mythological events, theological concepts, devotional acts, musical metadata, and textual works. The goal is not to replace expert reading. The goal is to create a typed, citation-grounded evidence layer that helps retrieval systems, annotation workflows, and future question-answering systems know what kind of evidence they are using.

The core claim is that Tamil literary AI needs explicit semantic modeling before it can make trustworthy analytical claims. Top-k retrieval may find relevant passages, but it does not by itself know whether a phrase is a deity, epithet, temple, flower, weapon, event, or theological concept. Nor does it know whether a term is used literally, iconographically, or through commentary. An ontology can make these distinctions explicit and reviewable.

The contributions of this paper are:

1. A Thevaram ontology v1 with 25 entity types, 29 relation types, 14 attributes, and a mythological event canon.
2. A migration model from a broad six-type earlier annotation layer to a finer literary ontology.
3. A deterministic annotation layer over Thevaram 1-8 with 107761 mentions and explicit review statuses.
4. A discussion of how ontology-grounded evidence supports future Tamil literary retrieval, corpus analysis, and citation-grounded QA.

## 2. Why Thevaram Needs a Semantic Layer

Thevaram is rich in devotional address, mythological reference, sacred geography, iconographic description, nature imagery, musical tradition, and commentary. A computational system that treats every text span as plain text cannot distinguish these functions. The word form alone is often insufficient. Some terms require word-sense disambiguation; some expressions refer to a deity through a body part or object; some nature images also function as sacred iconography.

For Tamil poets and language lovers, the ontology can support searches for imagery and phrases. For researchers, it can support source-traceable evidence tables and comparison across hymns. For students, it can help separate poem evidence from commentary explanation. For a future RAG system, it can prevent a generated answer from hiding whether its evidence came from verse text, commentary, metadata, entity annotation, or inferred relationships.

The ontology therefore has three design goals:

- make literary evidence typed,
- keep evidence linked to exact corpus records and offsets,
- and preserve uncertainty through review statuses.

## 3. Ontology Design

The Thevaram ontology v1 is a corpus-driven draft ontology. It defines 25 entity types organized across major branches: agents, places, objects and nature, events and concepts, and literary or musical metadata.

| Branch | Entity types |
| --- | --- |
| Agent | `DEITY`, `MANIFESTATION`, `DIVINE_EPITHET`, `MYTH_FIGURE`, `SAINT`, `PERSON`, `REL_GROUP` |
| Place | `SACRED_PLACE`, `REGION`, `MYTHIC_PLACE`, `RIVER`, `MOUNTAIN` |
| Object / nature / body | `SACRED_OBJECT`, `FLORA`, `FAUNA`, `CELESTIAL`, `BODY_PART` |
| Event / concept / practice | `MYTH_EVENT`, `THEO_CONCEPT`, `COSMO_CONCEPT`, `DEVOTIONAL_ACT`, `RITUAL` |
| Literary / music / text | `PAN`, `INSTRUMENT`, `TEXT_WORK` |

The ontology also defines 29 relation types. These include iconographic relations such as `wears`, `holds`, `rides`, and `smeared_with`; divine relations such as `consort_of`, `parent_of`, and `manifestation_of`; linking relations such as `refers_to`; event relations such as `agent_of` and `patient_of`; place relations such as `enshrined_at` and `located_in`; and literary relations such as `composed_by` and `set_in_pan`.

This relation model matters because many Thevaram expressions are not isolated named entities. For example, in the opening phrase "தோடு உடைய செவியன், விடை ஏறி, ஓர் தூ வெண்மதி சூடி", the phrase "தோடு உடைய செவியன்" functions as a divine epithet, while "தோடு", "விடை", and "வெண்மதி" also carry object, animal, and celestial imagery. A flat entity model loses the relation between the deity and the iconographic signs.

## 4. Migration from an Earlier Annotation Layer

The ontology supersedes an earlier six-type annotation layer. That earlier layer was useful as a seed, but it was too broad for literary analysis. In particular, `NATURE` mixed animals, flowers, rivers, mountains, and celestial objects. `ACTION` treated event-like phrases as entities, even though mythological events are better modeled as event anchors with participants and instruments.

The v1 migration stance is:

- convert `ACTION` to canonical `MYTH_EVENT` anchors,
- split `NATURE` into `FLORA`, `FAUNA`, `RIVER`, `MOUNTAIN`, and `CELESTIAL`,
- narrow `SACRED_OBJECT` to artefacts and substances,
- move role semantics into relations,
- add `DIVINE_EPITHET`, `SACRED_PLACE`, `SAINT`, `REL_GROUP`, `PAN`, and `TEXT_WORK`,
- and queue ambiguous lexemes such as `பதி`, `பசு`, `மெய்`, and `மால்` for word-sense review.

This migration is important because a literary ontology must distinguish surface occurrence from interpretive role. The same term may be a body part, an epithet component, an iconographic anchor, or a theological concept depending on context.

## 5. Annotation Pipeline

The annotation layer uses a deterministic seed-lexicon approach. It loads registry entries and aliases, scans normalized Thevaram fields, records offsets against the normalized corpus, suppresses same-type nested overlaps, and keeps cross-type overlaps where poetic imagery legitimately supports more than one category. Each mention receives a review status such as `auto_accepted`, `context_supported`, `needs_context_review`, or `ambiguous_review`.

The v3 annotation pass produced:

| Metric | Count |
| --- | ---: |
| Entity registry rows | 624 |
| Entity aliases | 823 |
| Seed terms loaded | 823 |
| Entity mentions | 107761 |
| Entity relationships | 4491 |
| Cross-type overlap records | 30710 |
| Suppressed same-type overlapping candidates | 12578 |

Validation checks found zero invalid bounds, zero span text mismatches, and zero duplicate mention identifiers. This is important because even if the interpretation needs further review, the technical integrity of the offsets and mention IDs is a prerequisite for future review.

## 6. Annotation Results

The largest mention categories were nature, body parts, sacred objects, deities, theological concepts, temples, and weapons.

| Entity type | Mentions |
| --- | ---: |
| `NATURE` | 23831 |
| `BODY_PART` | 17304 |
| `SACRED_OBJECT` | 16191 |
| `DEITY` | 13847 |
| `THEOLOGICAL_CONCEPT` | 11238 |
| `TEMPLE` | 4036 |
| `WEAPON` | 3772 |
| `ICONOGRAPHIC_FEATURE` | 2373 |
| `SACRED_RIVER` | 2303 |
| `RELATIONSHIP` | 2000 |

Mentions occur across both poem and commentary layers:

| Field | Mentions |
| --- | ---: |
| `commentaries.kurippurai` | 39618 |
| `commentaries.pozhppurai` | 37803 |
| `paadalgal.paadal_text` | 30340 |

The review statuses show why this should be described as review-aware annotation rather than final gold annotation.

| Review status | Mentions |
| --- | ---: |
| `auto_accepted` | 73627 |
| `context_supported` | 20582 |
| `needs_context_review` | 11376 |
| `ambiguous_review` | 2176 |

These numbers are useful because they separate stronger evidence from uncertain evidence. A future QA system should treat an auto-accepted temple mention differently from an ambiguous theological term requiring context review.

## 7. Relationship Layer

The current relationship output contains 4491 relationship records. Most are corpus co-occurrence edges, while a smaller number are curated ontology relations.

| Relationship type | Count |
| --- | ---: |
| `co_occurs_in_paadal` | 4474 |
| `performed_by` | 6 |
| `associated_with` | 3 |
| `consort_of` | 2 |
| `defeats` | 2 |
| `epithet_of` | 1 |
| `manifestation_of` | 1 |
| `weapon_of` | 1 |
| `worn_or_held_by` | 1 |

This distribution shows that the relation layer is still early. Co-occurrence is useful for discovery and candidate generation, but scholarly claims need curated or reviewed relations. The ontology provides the relation vocabulary; future work must populate it with stronger evidence.

## 8. Pilot Evaluation and Readiness

A small entity extraction pilot covered deity, author, place, and work entities. It reported precision 1.0000, recall 0.8571, F1 0.9231, and exact match 0.8571 over seven expected entities. The false negative was `பிரமன்`. This is encouraging, but it is a pilot rather than a corpus-wide gold evaluation.

Annotation readiness was measured at 59.8/100 overall. Entity annotation readiness was 72.0, deity annotation 68.0, author annotation 66.0, motif annotation 62.0, epithet annotation 58.0, simile annotation 56.0, metaphor annotation 50.0, and relationship annotation 46.0. These numbers indicate that the framework is ready for controlled annotation expansion but not yet ready for automated literary claims about motifs, metaphors, or relationships.

## 9. Use Cases for Tamil Literary QA

The ontology supports several future question types:

- Which hymns invoke Shiva using a particular epithet?
- Which sacred places are associated with river, flower, or mountain imagery?
- Which commentary passages explain references to Brahma, Vishnu, Yama, or Ravana?
- Which verses combine body imagery and iconographic objects?
- Which hymns mention a deity in verse text versus commentary?
- Which paadalgal can support evidence-grounded answers about sacred places or theological concepts?

Without the ontology, these questions are reduced to brittle keyword search. With the ontology, a system can return typed evidence with source fields and review statuses.

## 10. Limitations

The current ontology and annotation layer have important limitations.

First, the ontology is draft v1, not a final scholarly authority. It should be reviewed by Tamil literary and Saiva studies experts.

Second, deterministic annotation is not interpretation. It can identify surface mentions and candidate entities, but it cannot reliably resolve every metaphor, simile, theological usage, or ambiguous word sense.

Third, relation extraction remains early. Most current relationship records are co-occurrence edges, not curated semantic relations.

Fourth, inter-annotator agreement has not yet been measured. A publishable gold annotation layer should include at least two reviewers and a documented adjudication process.

Fifth, the current v3 annotation labels still include legacy categories such as `NATURE`, `TEMPLE`, and `WEAPON`; the v1 ontology defines the cleaner target model for migration.

## 11. Future Work

The next phase should create a stronger gold set. Recommended steps are:

1. Select 100-200 representative mentions across verse, pozhppurai, and kurippurai.
2. Have two Tamil-literate reviewers annotate entity type, span, link target, and confidence.
3. Measure inter-annotator agreement.
4. Add negative and ambiguous examples for deity, epithet, simile, metaphor, and relationship cases.
5. Evaluate whether ontology-based query expansion improves retrieval for deity, temple, epithet, and imagery questions.
6. Convert high-confidence co-occurrence edges into reviewed semantic relations only when evidence supports them.

## 12. Conclusion

This paper presented a semantic ontology and annotation framework for Thevaram literary analysis. The ontology defines 25 entity types, 29 relation types, 14 attributes, and a mythological event canon. A deterministic annotation pass over Thevaram 1-8 produced 107761 entity mentions and 4491 relationship records, with technical validation showing zero invalid bounds, zero span mismatches, and zero duplicate mention identifiers.

The main contribution is not a claim that Thevaram interpretation has been automated. The contribution is a typed, review-aware semantic evidence layer that can support future Tamil literary retrieval, annotation, and citation-grounded question answering. By making entities, relations, uncertainty, and source fields explicit, the ontology helps move from raw text search toward trustworthy computational literary analysis.

## References and Resource Notes

- Tamil Virtual Academy/TamilVU source material: https://www.tamilvu.org/
- Ontology file: `data/knowledge/ontology/thevaram_ontology_v1.json`
- Relation file: `data/knowledge/ontology/thevaram_relations_v1.json`
- Annotation output: `data/processed/thevaram_entity_annotations_v3/`
- Main reports: `reports/thevaram-ontology-v1-validation-report.md`, `reports/thevaram-entity-annotation-v3-report.md`, `reports/annotation-readiness-report.md`, `reports/entity-extraction-report.md`

