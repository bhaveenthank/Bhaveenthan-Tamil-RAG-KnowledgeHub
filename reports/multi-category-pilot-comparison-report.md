# Multi-Category Pilot Comparison Report

This table compares only bounded pilot readiness. A planned row does not imply that source
content has been fetched or approved.

| Category | Parser Family | Records | Missing Fields | URL Coverage | Content Type | Extraction Risks | Next Expansion |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
| இலக்கணம் | `grammar_parser` | 0 | Not tested | Not tested | Pending inspected sample | HTML hierarchy unknown | Source inspection required |
| சங்க இலக்கியம் | `verse_parser` | 0 | Not tested | Not tested | Pending inspected sample | HTML hierarchy unknown | Source inspection required |
| சைவம் | `verse_parser` | 10 | 0 | 100.0% | Validated verse/commentary seed | Existing source family only | Framework verified |
| இருபதாம் நூற்றாண்டு இலக்கியங்கள் உரைநடைகள் | `prose_parser` | 0 | Not tested | Not tested | Pending inspected sample | HTML hierarchy unknown | Source inspection required |
| அகராதிகள் | `dictionary_parser` | 0 | Not tested | Not tested | Pending inspected sample | HTML hierarchy unknown | Source inspection required |
| கலைக்களஞ்சியங்கள் | `dictionary_parser` | 0 | Not tested | Not tested | Pending inspected sample | HTML hierarchy unknown | Source inspection required |

## Finding

The shared contract works for the existing Saivam verse/commentary seed. Grammar, Sangam,
prose, dictionary, and encyclopedia pilots still require source inspection and local
fixtures before ingestion. This is the principal risk and the intended control point.
