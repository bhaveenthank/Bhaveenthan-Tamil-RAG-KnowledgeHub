# Hybrid Retrieval Benchmark Report

## Summary

- Status: `EVALUATED`
- Lexical weight: `0.6500`
- Semantic weight: `0.3500`
- Queries evaluated: `42`
- Recall@1: `1.0000`
- Recall@3: `1.0000`
- Recall@5: `1.0000`
- Recall@10: `1.0000`
- MRR: `1.0000`
- Exact match@1: `1.0000`
- Failed queries: `0`

## Ablation Table

| Setting | Lexical Weight | Semantic Weight | Recall@1 | Recall@3 | Recall@5 | Recall@10 | MRR | Failed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| lexical-heavy | 0.80 | 0.20 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 |
| balanced | 0.50 | 0.50 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0 |
| semantic-heavy | 0.30 | 0.70 | 0.8810 | 0.9048 | 0.9048 | 0.9048 | 0.8929 | 4 |

- Best ablation: `lexical-heavy`

## Query-Level Results

| Query ID | Type | Pass | Top Record | Top Chunk | RR |
| --- | --- | --- | --- | --- | ---: |
| `exact_song_no_1470` | exact_lookup | `True` | `thevaram_02_1664_1470` | `thevaram_02_1664_1470_verse_plus_commentary` | 1.000 |
| `exact_hymn_id_1664` | exact_lookup | `True` | `thevaram_02_1664_1479` | `thevaram_02_1664_1479_verse_plus_commentary` | 1.000 |
| `known_hymn_title_thiruppoontharai` | exact_title | `True` | `thevaram_02_1664_1470` | `thevaram_02_1664_1470_verse_plus_commentary` | 1.000 |
| `metadata_author_sambandar` | metadata | `True` | `thevaram_02_1665_1489` | `thevaram_02_1665_1489_verse_plus_commentary` | 1.000 |
| `metadata_irandaam_thirumurai` | metadata | `True` | `thevaram_02_1664_1470` | `thevaram_02_1664_1470_verse_plus_commentary` | 1.000 |
| `metadata_pann_indhalam` | metadata | `True` | `thevaram_02_1664_1478` | `thevaram_02_1664_1478_verse_plus_commentary` | 1.000 |
| `keyword_arul` | keyword | `True` | `thevaram_02_1785_2795` | `thevaram_02_1785_2795_verse_plus_commentary` | 1.000 |
| `keyword_sivan` | keyword | `True` | `thevaram_02_1779_2731` | `thevaram_02_1779_2731_metadata_context` | 1.000 |
| `keyword_sivaperuman` | keyword | `True` | `thevaram_02_1706_1937` | `thevaram_02_1706_1937_verse_plus_commentary` | 1.000 |
| `keyword_thiruppoontharai` | keyword | `True` | `thevaram_02_1664_1470` | `thevaram_02_1664_1470_verse_plus_commentary` | 1.000 |
| `commentary_with_pozhppurai` | commentary | `True` | `thevaram_02_1664_1470` | `thevaram_02_1664_1470_verse_plus_commentary` | 1.000 |
| `commentary_with_kurippurai` | commentary | `True` | `thevaram_02_1664_1470` | `thevaram_02_1664_1470_verse_plus_commentary` | 1.000 |
| `commentary_partial` | commentary | `True` | `thevaram_02_1742_2325` | `thevaram_02_1742_2325_verse_plus_commentary` | 1.000 |
| `commentary_missing_pozhppurai` | commentary | `True` | `thevaram_02_1704_1914` | `thevaram_02_1704_1914_verse_plus_commentary` | 1.000 |
| `commentary_missing_kurippurai` | commentary | `True` | `thevaram_02_1721_2097` | `thevaram_02_1721_2097_verse_plus_commentary` | 1.000 |
| `mixed_author_arul` | mixed | `True` | `thevaram_02_1759_2516` | `thevaram_02_1759_2516_verse_plus_commentary` | 1.000 |
| `mixed_title_commentary` | mixed | `True` | `thevaram_02_1664_1476` | `thevaram_02_1664_1476_verse_plus_commentary` | 1.000 |
| `mixed_thirumurai_song` | mixed | `True` | `thevaram_02_1664_1470` | `thevaram_02_1664_1470_verse_plus_commentary` | 1.000 |
| `sample_hymn_1702` | exact_lookup | `True` | `thevaram_02_1702_1891` | `thevaram_02_1702_1891_verse_plus_commentary` | 1.000 |
| `sample_hymn_1711` | exact_lookup | `True` | `thevaram_02_1711_1987` | `thevaram_02_1711_1987_verse_plus_commentary` | 1.000 |
| `sample_hymn_1748` | exact_lookup | `True` | `thevaram_02_1748_2396` | `thevaram_02_1748_2396_verse_plus_commentary` | 1.000 |
| `sample_hymn_1785` | exact_lookup | `True` | `thevaram_02_1785_2795` | `thevaram_02_1785_2795_verse_plus_commentary` | 1.000 |
| `keyword_ae51c91b` | keyword | `True` | `thevaram_02_1669_1529` | `thevaram_02_1669_1529_verse_plus_commentary` | 1.000 |
| `keyword_7411594e` | keyword | `True` | `thevaram_02_1746_2368` | `thevaram_02_1746_2368_metadata_context` | 1.000 |
| `keyword_e8067692` | keyword | `True` | `thevaram_02_1669_1529` | `thevaram_02_1669_1529_verse_plus_commentary` | 1.000 |
| `keyword_f2ac554e` | keyword | `True` | `thevaram_02_1708_1955` | `thevaram_02_1708_1955_metadata_context` | 1.000 |
| `keyword_6b461d75` | keyword | `True` | `thevaram_02_1705_1919` | `thevaram_02_1705_1919_metadata_context` | 1.000 |
| `keyword_5f0f2f51` | keyword | `True` | `thevaram_02_1733_2233` | `thevaram_02_1733_2233_metadata_context` | 1.000 |
| `keyword_484bb676` | keyword | `True` | `thevaram_02_1670_1543` | `thevaram_02_1670_1543_metadata_context` | 1.000 |
| `keyword_ed6fa7da` | keyword | `True` | `thevaram_02_1696_1825` | `thevaram_02_1696_1825_verse_plus_commentary` | 1.000 |
| `keyword_5c3b23bb` | keyword | `True` | `thevaram_02_1733_2222` | `thevaram_02_1733_2222_pozhppurai_only` | 1.000 |
| `keyword_e48daa8f` | keyword | `True` | `thevaram_02_1771_2645` | `thevaram_02_1771_2645_metadata_context` | 1.000 |
| `keyword_a78a34b0` | keyword | `True` | `thevaram_02_1767_2597` | `thevaram_02_1767_2597_verse_plus_commentary` | 1.000 |
| `keyword_4ef6099d` | keyword | `True` | `thevaram_02_1740_2307` | `thevaram_02_1740_2307_pozhppurai_only` | 1.000 |
| `deterministic_record_thevaram_02_1668_1521` | manual_spot_check | `True` | `thevaram_02_1668_1521` | `thevaram_02_1668_1521_verse_plus_commentary` | 1.000 |
| `deterministic_record_thevaram_02_1683_1679` | manual_spot_check | `True` | `thevaram_02_1683_1679` | `thevaram_02_1683_1679_verse_plus_commentary` | 1.000 |
| `deterministic_record_thevaram_02_1684_1698` | manual_spot_check | `True` | `thevaram_02_1684_1698` | `thevaram_02_1684_1698_verse_plus_commentary` | 1.000 |
| `deterministic_record_thevaram_02_1690_1755` | manual_spot_check | `True` | `thevaram_02_1690_1755` | `thevaram_02_1690_1755_verse_plus_commentary` | 1.000 |
| `deterministic_record_thevaram_02_1705_1927` | manual_spot_check | `True` | `thevaram_02_1705_1927` | `thevaram_02_1705_1927_verse_plus_commentary` | 1.000 |
| `deterministic_record_thevaram_02_1710_1971` | manual_spot_check | `True` | `thevaram_02_1710_1971` | `thevaram_02_1710_1971_verse_plus_commentary` | 1.000 |
| `deterministic_record_thevaram_02_1715_2033` | manual_spot_check | `True` | `thevaram_02_1715_2033` | `thevaram_02_1715_2033_verse_plus_commentary` | 1.000 |
| `deterministic_record_thevaram_02_1783_2779` | manual_spot_check | `True` | `thevaram_02_1783_2779` | `thevaram_02_1783_2779_verse_plus_commentary` | 1.000 |

## Failed Queries

- None

## Notes

Hybrid retrieval combines lexical exactness with semantic recall. These benchmark results should guide the retrieval mode used before any RAG answer generation is built.