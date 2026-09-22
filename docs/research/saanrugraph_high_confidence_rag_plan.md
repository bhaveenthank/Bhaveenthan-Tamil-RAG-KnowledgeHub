# SaanruGraph High-Confidence RAG Plan

Dataset version: `saanrugraph-high-confidence-rag-v1`

## Decision

Use only high-confidence Paadal to Pozhippurai links for the time-limited RAG paper path.
This supports a precision-first claim: the chatbot answers only when it has a high-confidence evidence path.

## Core Counts

- High-confidence evidence paths: `7154`
- RAG corpus records: `7154`
- Golden QA questions: `120`
- Questions per main capability: `20`

## Capabilities

| Capability | Relation | Evidence paths | QA questions |
| --- | --- | ---: | ---: |
| Word meaning from Pozhippurai | `glosses_word` | 176 | 20 |
| Phrase explanation | `explains_phrase` | 1,441 | 20 |
| Line-level explanation | `explains_line` | 34 | 20 |
| Poetic image and iconography interpretation | `interprets_image` | 2,157 | 20 |
| Entity, deity, object, and place description | `describes_entity` | 1,657 | 20 |
| Devotional or theological explanation | `theological_explanation` | 1,689 | 20 |

## Phase 4 RAG Corpus

The trusted retrieval base is written locally as:

- `data/processed/saanrugraph_rag/high_confidence_rag_corpus.jsonl`
- `data/processed/saanrugraph_rag/high_confidence_rag_corpus.csv`

Each record is one high-confidence evidence path with `Paadal span`, `Pozhippurai explanation`, `Full Paadal`, and `Evidence path` in a single ready-to-index `chunk_text` field.

## What This Lets You Claim

- The system can answer with exact Paadal and Pozhippurai evidence paths.
- The first evaluation can focus on high-precision grounded retrieval and answer citation.
- Medium/low confidence linker hardening becomes future work, not a blocker for the paper.

## What You Should Not Claim Yet

- Do not claim full-corpus coverage.
- Do not claim all Paadal spans are linked.
- Do not claim final RAG accuracy until the 120-question benchmark is run.

## Recommended Scores To Report

- Retrieval Recall@5
- Evidence Path Recall
- Answer correctness
- Citation precision
- Citation recall
- Unsupported answer rate
