# Query Expansion Evaluation Report

## Summary

- Queries tested: `4`
- Queries expanded: `4`
- Retrieval result sets changed: `4`
- Improved: `3`
- Degraded: `0`
- Neutral: `1`

Assessment uses a deterministic corpus-evidence proxy: the first rank and count of top-k records containing curated expansion terms. It is not a substitute for Tamil researcher relevance judgments.

## Query Results

| Query | Registries | Expanded Query | Changed | Baseline Hits | Expanded Hits | Assessment |
| --- | --- | --- | --- | ---: | ---: | --- |
| அப்பர் பாடல்கள் | authors | அப்பர் திருநாவுக்கரசர் நாவுக்கரசர் பாடல்கள் | yes | 0 | 0 | neutral |
| சந்திரன் வரும் பாடல்கள் | synonyms | சந்திரன் நிலா மதி திங்கள் நிலவு வரும் பாடல்கள் | yes | 1 | 5 | improved |
| சிவன் பற்றிய பாடல்கள் | deities | சிவன் சிவபெருமான் ஈசன் மகாதேவன் பற்றிய பாடல்கள் | yes | 3 | 5 | improved |
| உவமை உள்ள பாடல்கள் | literary_devices | உவமை போல் போன்ற ஒத்த உள்ள பாடல்கள் | yes | 3 | 4 | improved |

## Known Limitations

- The curated registries are intentionally small and do not cover inflected or sandhi forms.
- Expansion can increase lexical recall while also introducing broad aliases or imagery cues.
- The current corpus is Irandaam Thirumurai; an Appar query cannot be fully evaluated against an author corpus that is not indexed.
- Human relevance labels are still required before treating these outcomes as retrieval quality metrics.
