# Occurrence Search Report

## Summary

- Indexed records: `1400`
- Indexed field entries: `7000`
- Indexed fields: `author, commentary_text, content_text, definition, kurippurai, pozhppurai, rule_text, title, verse_text`
- Scraping performed: `false`
- LLM calls: `0`

## Corpus Coverage

| Corpus | Indexed field entries |
| --- | ---: |
| `dictionaries` | 3 |
| `grammar` | 8 |
| `sangam_literature` | 12 |
| `thirumurai_02` | 6648 |
| `thirumurai_04` | 323 |
| `twentieth_century_prose` | 6 |

## Field Coverage

| Field | Indexed entries |
| --- | ---: |
| `author` | 1399 |
| `commentary_text` | 10 |
| `content_text` | 18 |
| `definition` | 1 |
| `kurippurai` | 1388 |
| `pozhppurai` | 1387 |
| `rule_text` | 2 |
| `title` | 1400 |
| `verse_text` | 1395 |

## Example Searches

```bash
python3 src/analytics/search_occurrences.py --term "சந்திரன்"
python3 src/analytics/search_occurrences.py --term "சந்திரன்" --expand-query
```

Expanded search uses the curated query expander. For `சந்திரன்`, it searches the canonical
term plus reviewed synonym and variant forms from `data/knowledge/synonyms.json`.

| Query | Expanded terms | Occurrences |
| --- | --- | ---: |
| `சந்திரன்` | `சந்திரன், நிலா, மதி, திங்கள், நிலவு` | 686 |
| `சிவன்` | `சிவன், சிவபெருமான், ஈசன், மகாதேவன்` | 209 |
| `அப்பர்` | `அப்பர், திருநாவுக்கரசர், நாவுக்கரசர்` | 38 |
| `உவமை` | `உவமை, போல், போன்ற, ஒத்த` | 454 |

## Limitations

- Matching is literal substring matching; inflection, sandhi, and morphology are not yet handled.
- This layer returns evidence occurrences only. It does not aggregate counts into literary claims.
- Source text quality is limited to the currently normalized local corpora and pilot fixtures.
- Motif and literary-device terms are search cues, not automatic annotations.

## Recommendation

Use this occurrence index as the foundation for Phase 25 aggregation and statistics.
Aggregation should consume these evidence rows rather than re-reading source corpora.
