# Entity Extraction Report

## Summary

- Supported entity types: `deity, author, place, work`
- Expected entities: `7`
- Extracted entities: `6`
- True positives: `6`
- False positives: `0`
- False negatives: `1`
- Precision: `1.0000`
- Recall: `0.8571`
- F1: `0.9231`
- Exact match: `0.8571`
- Entity extraction pilot performed: `true`
- Corpus-wide extraction performed: `false`
- Scraping performed: `false`
- LLM calls: `0`

## Error Analysis

### False Negatives

| Record | Label | Text | Span |
| --- | --- | --- | --- |
| `gold_entities_001` | `deity` | பிரமன் | 19-25 |

### False Positives

| Record | Label | Text | Span |
| --- | --- | --- | --- |
| none | none | none | none |

## Future Improvements

- Add missing deity authority seeds after human review.
- Add more negative and ambiguous examples before broad extraction.
- Add spelling and orthographic variant handling only after fixture coverage improves.
