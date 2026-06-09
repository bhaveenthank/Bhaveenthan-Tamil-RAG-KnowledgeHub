# Semantic Retrieval Benchmark Report

## Summary

- Status: `EVALUATED`
- Queries evaluated: `42`
- Recall@1: `0.5238`
- Recall@3: `0.6190`
- Recall@5: `0.6905`
- Recall@10: `0.7381`
- MRR: `0.5827`
- Exact match@1: `0.5238`
- Failed queries: `11`

## Query-Level Results

| Query ID | Type | Pass | Top Record | Top Chunk | RR |
| --- | --- | --- | --- | --- | ---: |
| `exact_song_no_1470` | exact_lookup | `True` | `thevaram_02_1664_1470` | `thevaram_02_1664_1470_verse_plus_commentary` | 1.000 |
| `exact_hymn_id_1664` | exact_lookup | `True` | `thevaram_02_1664_1479` | `thevaram_02_1664_1479_verse_plus_commentary` | 1.000 |
| `known_hymn_title_thiruppoontharai` | exact_title | `False` | `thevaram_02_1775_2685` | `thevaram_02_1775_2685_verse_plus_commentary` | 0.000 |
| `metadata_author_sambandar` | metadata | `True` | `thevaram_02_1737_2273` | `thevaram_02_1737_2273_verse_plus_commentary` | 1.000 |
| `metadata_irandaam_thirumurai` | metadata | `True` | `thevaram_02_1737_2273` | `thevaram_02_1737_2273_verse_plus_commentary` | 1.000 |
| `metadata_pann_indhalam` | metadata | `True` | `thevaram_02_1668_1523` | `thevaram_02_1668_1523_verse_plus_commentary` | 1.000 |
| `keyword_arul` | keyword | `True` | `thevaram_02_1767_2597` | `thevaram_02_1767_2597_verse_plus_commentary` | 0.250 |
| `keyword_sivan` | keyword | `False` | `thevaram_02_1688_1740` | `thevaram_02_1688_1740_verse_plus_commentary` | 0.000 |
| `keyword_sivaperuman` | keyword | `False` | `thevaram_02_1740_2310` | `thevaram_02_1740_2310_verse_plus_commentary` | 0.000 |
| `keyword_thiruppoontharai` | keyword | `False` | `thevaram_02_1737_2273` | `thevaram_02_1737_2273_verse_plus_commentary` | 0.000 |
| `commentary_with_pozhppurai` | commentary | `True` | `thevaram_02_1737_2273` | `thevaram_02_1737_2273_verse_plus_commentary` | 1.000 |
| `commentary_with_kurippurai` | commentary | `True` | `thevaram_02_1737_2273` | `thevaram_02_1737_2273_verse_plus_commentary` | 1.000 |
| `commentary_partial` | commentary | `True` | `thevaram_02_1742_2325` | `thevaram_02_1742_2325_verse_plus_commentary` | 1.000 |
| `commentary_missing_pozhppurai` | commentary | `False` | `thevaram_02_1737_2273` | `thevaram_02_1737_2273_verse_plus_commentary` | 0.000 |
| `commentary_missing_kurippurai` | commentary | `False` | `thevaram_02_1737_2273` | `thevaram_02_1737_2273_verse_plus_commentary` | 0.000 |
| `mixed_author_arul` | mixed | `True` | `thevaram_02_1775_2685` | `thevaram_02_1775_2685_verse_plus_commentary` | 0.250 |
| `mixed_title_commentary` | mixed | `True` | `thevaram_02_1664_1479` | `thevaram_02_1664_1479_verse_plus_commentary` | 0.111 |
| `mixed_thirumurai_song` | mixed | `True` | `thevaram_02_1664_1470` | `thevaram_02_1664_1470_verse_plus_commentary` | 1.000 |
| `sample_hymn_1702` | exact_lookup | `True` | `thevaram_02_1702_1891` | `thevaram_02_1702_1891_verse_plus_commentary` | 1.000 |
| `sample_hymn_1711` | exact_lookup | `True` | `thevaram_02_1711_1987` | `thevaram_02_1711_1987_verse_plus_commentary` | 1.000 |
| `sample_hymn_1748` | exact_lookup | `True` | `thevaram_02_1748_2396` | `thevaram_02_1748_2396_verse_plus_commentary` | 1.000 |
| `sample_hymn_1785` | exact_lookup | `True` | `thevaram_02_1785_2795` | `thevaram_02_1785_2795_verse_plus_commentary` | 1.000 |
| `keyword_ae51c91b` | keyword | `False` | `thevaram_02_1775_2684` | `thevaram_02_1775_2684_verse_plus_commentary` | 0.000 |
| `keyword_7411594e` | keyword | `False` | `thevaram_02_1687_1727` | `thevaram_02_1687_1727_verse_plus_commentary` | 0.000 |
| `keyword_e8067692` | keyword | `False` | `thevaram_02_1688_1740` | `thevaram_02_1688_1740_verse_plus_commentary` | 0.000 |
| `keyword_f2ac554e` | keyword | `False` | `thevaram_02_1687_1727` | `thevaram_02_1687_1727_verse_plus_commentary` | 0.000 |
| `keyword_6b461d75` | keyword | `True` | `thevaram_02_1785_2795` | `thevaram_02_1785_2795_verse_plus_commentary` | 0.500 |
| `keyword_5f0f2f51` | keyword | `True` | `thevaram_02_1684_1694` | `thevaram_02_1684_1694_verse_plus_commentary` | 0.333 |
| `keyword_484bb676` | keyword | `True` | `thevaram_02_1775_2684` | `thevaram_02_1775_2684_verse_plus_commentary` | 0.333 |
| `keyword_ed6fa7da` | keyword | `True` | `thevaram_02_1687_1727` | `thevaram_02_1687_1727_verse_plus_commentary` | 0.111 |
| `keyword_5c3b23bb` | keyword | `True` | `thevaram_02_1687_1727` | `thevaram_02_1687_1727_verse_plus_commentary` | 0.250 |
| `keyword_e48daa8f` | keyword | `False` | `thevaram_02_1688_1740` | `thevaram_02_1688_1740_verse_plus_commentary` | 0.000 |
| `keyword_a78a34b0` | keyword | `True` | `thevaram_02_1767_2597` | `thevaram_02_1767_2597_verse_plus_commentary` | 1.000 |
| `keyword_4ef6099d` | keyword | `True` | `thevaram_02_1775_2684` | `thevaram_02_1775_2684_verse_plus_commentary` | 0.333 |
| `deterministic_record_thevaram_02_1668_1521` | manual_spot_check | `True` | `thevaram_02_1668_1521` | `thevaram_02_1668_1521_verse_plus_commentary` | 1.000 |
| `deterministic_record_thevaram_02_1683_1679` | manual_spot_check | `True` | `thevaram_02_1683_1679` | `thevaram_02_1683_1679_verse_plus_commentary` | 1.000 |
| `deterministic_record_thevaram_02_1684_1698` | manual_spot_check | `True` | `thevaram_02_1684_1698` | `thevaram_02_1684_1698_verse_plus_commentary` | 1.000 |
| `deterministic_record_thevaram_02_1690_1755` | manual_spot_check | `True` | `thevaram_02_1690_1755` | `thevaram_02_1690_1755_verse_plus_commentary` | 1.000 |
| `deterministic_record_thevaram_02_1705_1927` | manual_spot_check | `True` | `thevaram_02_1705_1927` | `thevaram_02_1705_1927_verse_plus_commentary` | 1.000 |
| `deterministic_record_thevaram_02_1710_1971` | manual_spot_check | `True` | `thevaram_02_1710_1971` | `thevaram_02_1710_1971_verse_plus_commentary` | 1.000 |
| `deterministic_record_thevaram_02_1715_2033` | manual_spot_check | `True` | `thevaram_02_1715_2033` | `thevaram_02_1715_2033_verse_plus_commentary` | 1.000 |
| `deterministic_record_thevaram_02_1783_2779` | manual_spot_check | `True` | `thevaram_02_1783_2779` | `thevaram_02_1783_2779_verse_plus_commentary` | 1.000 |

## Failed Queries

- `known_hymn_title_thiruppoontharai` top=`thevaram_02_1775_2685` missing_records=`['thevaram_02_1664_1470', 'thevaram_02_1664_1471', 'thevaram_02_1664_1472', 'thevaram_02_1664_1473', 'thevaram_02_1664_1474', 'thevaram_02_1664_1475', 'thevaram_02_1664_1476', 'thevaram_02_1664_1477', 'thevaram_02_1664_1478', 'thevaram_02_1664_1479']` missing_chunks=`['thevaram_02_1664_1470_kurippurai_only', 'thevaram_02_1664_1470_metadata_context', 'thevaram_02_1664_1470_pozhppurai_only', 'thevaram_02_1664_1470_verse_only', 'thevaram_02_1664_1470_verse_plus_commentary', 'thevaram_02_1664_1471_kurippurai_only', 'thevaram_02_1664_1471_metadata_context', 'thevaram_02_1664_1471_pozhppurai_only', 'thevaram_02_1664_1471_verse_only', 'thevaram_02_1664_1471_verse_plus_commentary']`
- `keyword_sivan` top=`thevaram_02_1688_1740` missing_records=`['thevaram_02_1666_1498', 'thevaram_02_1671_1555', 'thevaram_02_1674_1580', 'thevaram_02_1674_1583', 'thevaram_02_1674_1587', 'thevaram_02_1676_1607', 'thevaram_02_1679_1642', 'thevaram_02_1680_1652', 'thevaram_02_1682_1671', 'thevaram_02_1688_1732']` missing_chunks=`['thevaram_02_1666_1498_kurippurai_only', 'thevaram_02_1666_1498_metadata_context', 'thevaram_02_1666_1498_pozhppurai_only', 'thevaram_02_1666_1498_verse_only', 'thevaram_02_1666_1498_verse_plus_commentary', 'thevaram_02_1671_1555_kurippurai_only', 'thevaram_02_1671_1555_metadata_context', 'thevaram_02_1671_1555_pozhppurai_only', 'thevaram_02_1671_1555_verse_only', 'thevaram_02_1671_1555_verse_plus_commentary']`
- `keyword_sivaperuman` top=`thevaram_02_1740_2310` missing_records=`['thevaram_02_1664_1477', 'thevaram_02_1668_1521', 'thevaram_02_1669_1524', 'thevaram_02_1669_1527', 'thevaram_02_1671_1557', 'thevaram_02_1674_1588', 'thevaram_02_1675_1591', 'thevaram_02_1682_1669', 'thevaram_02_1682_1670', 'thevaram_02_1682_1673']` missing_chunks=`['thevaram_02_1664_1477_kurippurai_only', 'thevaram_02_1664_1477_metadata_context', 'thevaram_02_1664_1477_pozhppurai_only', 'thevaram_02_1664_1477_verse_only', 'thevaram_02_1664_1477_verse_plus_commentary', 'thevaram_02_1668_1521_kurippurai_only', 'thevaram_02_1668_1521_metadata_context', 'thevaram_02_1668_1521_pozhppurai_only', 'thevaram_02_1668_1521_verse_only', 'thevaram_02_1668_1521_verse_plus_commentary']`
- `keyword_thiruppoontharai` top=`thevaram_02_1737_2273` missing_records=`['thevaram_02_1664_1470', 'thevaram_02_1664_1471', 'thevaram_02_1664_1472', 'thevaram_02_1664_1473', 'thevaram_02_1664_1474', 'thevaram_02_1664_1475', 'thevaram_02_1664_1476', 'thevaram_02_1664_1477', 'thevaram_02_1664_1478', 'thevaram_02_1664_1479']` missing_chunks=`['thevaram_02_1664_1470_kurippurai_only', 'thevaram_02_1664_1470_metadata_context', 'thevaram_02_1664_1470_pozhppurai_only', 'thevaram_02_1664_1470_verse_only', 'thevaram_02_1664_1470_verse_plus_commentary', 'thevaram_02_1664_1471_kurippurai_only', 'thevaram_02_1664_1471_metadata_context', 'thevaram_02_1664_1471_pozhppurai_only', 'thevaram_02_1664_1471_verse_only', 'thevaram_02_1664_1471_verse_plus_commentary']`
- `commentary_missing_pozhppurai` top=`thevaram_02_1737_2273` missing_records=`['thevaram_02_1704_1914', 'thevaram_02_1717_2053', 'thevaram_02_1720_2082', 'thevaram_02_1742_2325']` missing_chunks=`['thevaram_02_1704_1914_kurippurai_only', 'thevaram_02_1704_1914_metadata_context', 'thevaram_02_1704_1914_verse_only', 'thevaram_02_1704_1914_verse_plus_commentary', 'thevaram_02_1717_2053_kurippurai_only', 'thevaram_02_1717_2053_metadata_context', 'thevaram_02_1717_2053_verse_only', 'thevaram_02_1717_2053_verse_plus_commentary', 'thevaram_02_1720_2082_kurippurai_only', 'thevaram_02_1720_2082_metadata_context']`
- `commentary_missing_kurippurai` top=`thevaram_02_1737_2273` missing_records=`['thevaram_02_1721_2097', 'thevaram_02_1759_2517', 'thevaram_02_1776_2701']` missing_chunks=`['thevaram_02_1721_2097_metadata_context', 'thevaram_02_1721_2097_pozhppurai_only', 'thevaram_02_1721_2097_verse_only', 'thevaram_02_1721_2097_verse_plus_commentary', 'thevaram_02_1759_2517_metadata_context', 'thevaram_02_1759_2517_pozhppurai_only', 'thevaram_02_1759_2517_verse_only', 'thevaram_02_1759_2517_verse_plus_commentary', 'thevaram_02_1776_2701_metadata_context', 'thevaram_02_1776_2701_pozhppurai_only']`
- `keyword_ae51c91b` top=`thevaram_02_1775_2684` missing_records=`['thevaram_02_1666_1493', 'thevaram_02_1666_1495', 'thevaram_02_1669_1528', 'thevaram_02_1669_1529', 'thevaram_02_1669_1532', 'thevaram_02_1670_1537', 'thevaram_02_1671_1547', 'thevaram_02_1673_1574', 'thevaram_02_1675_1591', 'thevaram_02_1678_1624']` missing_chunks=`['thevaram_02_1666_1493_kurippurai_only', 'thevaram_02_1666_1493_metadata_context', 'thevaram_02_1666_1493_pozhppurai_only', 'thevaram_02_1666_1493_verse_only', 'thevaram_02_1666_1493_verse_plus_commentary', 'thevaram_02_1666_1495_kurippurai_only', 'thevaram_02_1666_1495_metadata_context', 'thevaram_02_1666_1495_pozhppurai_only', 'thevaram_02_1666_1495_verse_only', 'thevaram_02_1666_1495_verse_plus_commentary']`
- `keyword_7411594e` top=`thevaram_02_1687_1727` missing_records=`['thevaram_02_1664_1474', 'thevaram_02_1666_1497', 'thevaram_02_1669_1524', 'thevaram_02_1672_1561', 'thevaram_02_1673_1578', 'thevaram_02_1675_1595', 'thevaram_02_1676_1601', 'thevaram_02_1678_1623', 'thevaram_02_1680_1645', 'thevaram_02_1681_1658']` missing_chunks=`['thevaram_02_1664_1474_kurippurai_only', 'thevaram_02_1664_1474_metadata_context', 'thevaram_02_1664_1474_pozhppurai_only', 'thevaram_02_1664_1474_verse_only', 'thevaram_02_1664_1474_verse_plus_commentary', 'thevaram_02_1666_1497_kurippurai_only', 'thevaram_02_1666_1497_metadata_context', 'thevaram_02_1666_1497_pozhppurai_only', 'thevaram_02_1666_1497_verse_only', 'thevaram_02_1666_1497_verse_plus_commentary']`
- `keyword_e8067692` top=`thevaram_02_1688_1740` missing_records=`['thevaram_02_1667_1507', 'thevaram_02_1669_1526', 'thevaram_02_1669_1529', 'thevaram_02_1674_1580', 'thevaram_02_1674_1582', 'thevaram_02_1675_1598', 'thevaram_02_1679_1639', 'thevaram_02_1694_1801', 'thevaram_02_1699_1861', 'thevaram_02_1700_1871']` missing_chunks=`['thevaram_02_1667_1507_kurippurai_only', 'thevaram_02_1667_1507_metadata_context', 'thevaram_02_1667_1507_pozhppurai_only', 'thevaram_02_1667_1507_verse_only', 'thevaram_02_1667_1507_verse_plus_commentary', 'thevaram_02_1669_1526_kurippurai_only', 'thevaram_02_1669_1526_metadata_context', 'thevaram_02_1669_1526_pozhppurai_only', 'thevaram_02_1669_1526_verse_only', 'thevaram_02_1669_1526_verse_plus_commentary']`
- `keyword_f2ac554e` top=`thevaram_02_1687_1727` missing_records=`['thevaram_02_1664_1470', 'thevaram_02_1664_1473', 'thevaram_02_1669_1526', 'thevaram_02_1669_1531', 'thevaram_02_1670_1541', 'thevaram_02_1674_1583', 'thevaram_02_1677_1612', 'thevaram_02_1678_1624', 'thevaram_02_1678_1628', 'thevaram_02_1681_1657']` missing_chunks=`['thevaram_02_1664_1470_kurippurai_only', 'thevaram_02_1664_1470_metadata_context', 'thevaram_02_1664_1470_pozhppurai_only', 'thevaram_02_1664_1470_verse_only', 'thevaram_02_1664_1470_verse_plus_commentary', 'thevaram_02_1664_1473_kurippurai_only', 'thevaram_02_1664_1473_metadata_context', 'thevaram_02_1664_1473_pozhppurai_only', 'thevaram_02_1664_1473_verse_only', 'thevaram_02_1664_1473_verse_plus_commentary']`
- `keyword_e48daa8f` top=`thevaram_02_1688_1740` missing_records=`['thevaram_02_1665_1490', 'thevaram_02_1668_1519', 'thevaram_02_1669_1533', 'thevaram_02_1673_1573', 'thevaram_02_1673_1575', 'thevaram_02_1673_1578', 'thevaram_02_1681_1663', 'thevaram_02_1682_1674', 'thevaram_02_1683_1680', 'thevaram_02_1691_1771']` missing_chunks=`['thevaram_02_1665_1490_kurippurai_only', 'thevaram_02_1665_1490_metadata_context', 'thevaram_02_1665_1490_pozhppurai_only', 'thevaram_02_1665_1490_verse_only', 'thevaram_02_1665_1490_verse_plus_commentary', 'thevaram_02_1668_1519_kurippurai_only', 'thevaram_02_1668_1519_metadata_context', 'thevaram_02_1668_1519_pozhppurai_only', 'thevaram_02_1668_1519_verse_only', 'thevaram_02_1668_1519_verse_plus_commentary']`

## Notes

Semantic retrieval searches only local `verse_plus_commentary` vectors in this phase. Hybrid retrieval remains pending.