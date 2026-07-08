# Thevaram Paadal-Pozhippurai Linker v4 Supervisor Share

Generated: 2026-07-05

## Main File

- `thevaram_pozhippurai_links_v4_full_supervisor_table.csv` contains all 49,019 span-level link records.

## Important Columns

- `paadal_id`, `global_song_no`, `thogupu_title`, `thirumurai_no`: source paadal identity.
- `source_text`: paadal line/phrase/span proposed by the linker.
- `target_field`: whether the target is `pozhppurai` or `kurippurai`.
- `target_text`: linked commentary span.
- `score`, `confidence`, `relationship_type`: linker decision data.
- `changed_bucket`: whether the row came from v4 gold seed, focused QA rule, baseline similarity, split/gold overlap, or no-link coverage.
- `manual_review_required`: whether the row should be reviewed before use as positive training data.
- `diagnostic_note`: why the linker categorized the row this way.

## Statistical Analysis

- `thevaram-pozhppurai-link-v4-statistical-analysis.md` explains why high/medium/low/no-link statuses occur.
- Supporting CSVs provide the breakdowns by confidence, source shape, entities, token overlap, and Thirumurai.
