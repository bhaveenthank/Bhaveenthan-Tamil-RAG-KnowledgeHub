# Analytical Retrieval Report

## Supported Intents

- `term_occurrence`
- `group_by_author`
- `group_by_work`
- `group_by_category`
- `group_by_record_type`
- `compare_sources`
- `unsupported`

## Example Structured Outputs

### எந்த ஆசிரியர் சந்திரன் தொடர்பான சொற்களை அதிகம் பயன்படுத்துகிறார்?

- Intent: `group_by_author`
- Term: `சந்திரன்`
- Expanded: `true`
- Group by: `author`
- Total occurrences: `686`
- Top result: `Tirugnanasambandar` with `635` occurrences

### எந்த corpus-இல் சிவன் அதிகமாக குறிப்பிடப்படுகிறார்?

- Intent: `group_by_category`
- Term: `சிவன்`
- Expanded: `true`
- Group by: `category`
- Total occurrences: `209`
- Top result: `thirumurai_02` with `196` occurrences

### உவமை எந்த works-இல் அதிகம் வருகிறது?

- Intent: `group_by_work`
- Term: `உவமை`
- Expanded: `true`
- Group by: `work`
- Total occurrences: `454`
- Top result: `Panniru Thirumurai` with `424` occurrences

### அப்பர் தொடர்பான குறிப்புகள் எந்த record types-இல் வருகின்றன?

- Intent: `group_by_record_type`
- Term: `அப்பர்`
- Expanded: `true`
- Group by: `record_type`
- Total occurrences: `38`
- Top result: `unified-thirumurai-v1` with `26` occurrences

## Limitations

- Classification is deterministic and rule-based.
- Outputs are structured analytics, not fluent final answers.
- Counts depend on literal occurrence evidence and curated expansion seeds.
- No LLM call, scraping, cloud job, embedding regeneration, or vector rebuild is performed.

## Next Steps

Phase 27 can add answer composition after every statistic is traceable to evidence samples and citations.
