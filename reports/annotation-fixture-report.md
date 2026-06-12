# Annotation Fixture Report

## Summary

- Annotation files: `8`
- Records: `24`
- Annotations: `39`
- Validation: `VALID`
- Automatic extraction performed: `false`
- Scraping performed: `false`
- LLM calls: `0`

## Counts By File

| File | Records | Annotations | Errors |
| --- | ---: | ---: | ---: |
| `entities_gold.json` | 3 | 7 | 0 |
| `deities_gold.json` | 3 | 5 | 0 |
| `authors_gold.json` | 3 | 3 | 0 |
| `motifs_gold.json` | 3 | 6 | 0 |
| `epithets_gold.json` | 3 | 3 | 0 |
| `similes_gold.json` | 3 | 3 | 0 |
| `metaphors_gold.json` | 3 | 3 | 0 |
| `relationships_gold.json` | 3 | 9 | 0 |

## Counts By Annotation Type

| Type | Count |
| --- | ---: |
| `author` | 4 |
| `deity` | 5 |
| `entity` | 10 |
| `epithet` | 4 |
| `metaphor` | 3 |
| `motif` | 7 |
| `relationship` | 3 |
| `simile` | 3 |

## Coverage

The fixtures cover entity, deity, author, motif, epithet, simile, metaphor, and
relationship examples. Place and work appear inside entity and relationship fixtures.

## Limitations

- The fixture set is intentionally small.
- It is manually curated and not a corpus-wide annotation release.
- It has no inter-annotator agreement measurement yet.
- Metaphor and relationship examples are seed examples for schema testing.

## Future Expansion Recommendations

Add positive, negative, and ambiguous examples for each extraction target before building
automatic extractors.
