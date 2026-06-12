# Aggregation Engine Report

## Summary

The aggregation engine groups occurrence evidence into counts, rankings, and distributions. It performs no scraping, extraction, answer generation, or LLM calls.

## Example Rankings

### சந்திரன்

- Matched terms: `சந்திரன், நிலா, மதி, திங்கள், நிலவு`
- Total occurrences: `686`
- Unique records: `298`
- Unique works: `2`
- Unique authors: `2`

| Rank | Group | Occurrences | Percentage | Unique Records |
| ---: | --- | ---: | ---: | ---: |
| 1 | `thirumurai_02` | 635 | 92.57% | 277 |
| 2 | `thirumurai_04` | 47 | 6.85% | 20 |
| 3 | `saivam` | 4 | 0.58% | 1 |

### சிவன்

- Matched terms: `சிவன், சிவபெருமான், ஈசன், மகாதேவன்`
- Total occurrences: `209`
- Unique records: `156`
- Unique works: `3`
- Unique authors: `2`

| Rank | Group | Occurrences | Percentage | Unique Records |
| ---: | --- | ---: | ---: | ---: |
| 1 | `thirumurai_02` | 196 | 93.78% | 149 |
| 2 | `saivam` | 6 | 2.87% | 2 |
| 3 | `thirumurai_04` | 5 | 2.39% | 4 |
| 4 | `dictionaries` | 2 | 0.96% | 1 |

### அப்பர்

- Matched terms: `அப்பர், திருநாவுக்கரசர், நாவுக்கரசர்`
- Total occurrences: `38`
- Unique records: `22`
- Unique works: `2`
- Unique authors: `2`

| Rank | Group | Occurrences | Percentage | Unique Records |
| ---: | --- | ---: | ---: | ---: |
| 1 | `thirumurai_02` | 19 | 50.00% | 17 |
| 2 | `saivam` | 12 | 31.58% | 2 |
| 3 | `thirumurai_04` | 7 | 18.42% | 3 |

### உவமை

- Matched terms: `உவமை, போல், போன்ற, ஒத்த`
- Total occurrences: `454`
- Unique records: `273`
- Unique works: `2`
- Unique authors: `2`

| Rank | Group | Occurrences | Percentage | Unique Records |
| ---: | --- | ---: | ---: | ---: |
| 1 | `thirumurai_02` | 371 | 81.72% | 246 |
| 2 | `thirumurai_04` | 53 | 11.67% | 22 |
| 3 | `saivam` | 30 | 6.61% | 5 |

## Limitations

- Counts are literal occurrence counts from the Phase 24 evidence index.
- Expanded concept counts depend on the current curated registry seed terms.
- This is aggregation infrastructure, not interpretive literary reasoning.
- Future analytical retrieval should cite the underlying occurrence rows for every statistic.
