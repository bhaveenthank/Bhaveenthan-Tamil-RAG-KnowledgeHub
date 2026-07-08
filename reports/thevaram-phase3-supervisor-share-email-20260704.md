Subject: Thevaram Paadal-Pozhippurai Linking v3 - BigQuery Tables and Review Viewer

Dear Sir,

I am sharing the current progress of the Thevaram Paadal-Pozhippurai linking work.

We have completed a v3 linker pass over the available Thevaram 1-8 corpus. This version
uses the earlier v2 linker outputs together with focused manual QA corrections and
split-link examples.

Current v3 output summary:

- Total v3 link/coverage rows: 48,951
- Positive training links: 11,126
- High confidence: 914
- Medium confidence: 10,309
- Low confidence: 30,859
- No-link rows: 6,869
- Manual review pack: 194 rows

BigQuery dataset:

https://console.cloud.google.com/bigquery?project=tvu-corpus-e22051-260606&p=tvu-corpus-e22051-260606&d=thevaram_pozhippurai_phase3_20260704&page=dataset

Important tables:

- links_v3_full: full v3 Paadal-Pozhippurai link table
- links_v2_full: full v2 table for comparison
- v3_manual_review_pack: rows prioritized for next manual review
- phase3_clean_decision_table: focused Phase 3 QA decision table
- phase3_corrected_usable: corrected usable QA/split examples
- v3_summary: one-row summary metadata

HTML review viewer:

https://storage.cloud.google.com/tvu-ppl-phase3-share-e22051-20260704/paadal_pozhippurai_v3_review_viewer.html

The viewer shows each candidate link together with:

- the paadal phrase/line
- the full paadal containing that phrase
- the proposed pozhppurai span
- the full pozhppurai for that paadal
- kurippurai
- confidence, score, relationship type, and diagnostic notes

Access has been granted to rtuthaya@cse.mrt.ac.lk for the BigQuery dataset and the
reviewer file.

Please note that this is not claimed as final scholarly gold yet. The v3 output is a
strengthened review/training layer, and the remaining low-confidence/manual-review rows
still need checking.

Best regards,
Bhaveenthan
