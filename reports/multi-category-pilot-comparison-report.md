# Multi-Category Pilot Comparison Report

This table compares only bounded pilot readiness. A planned row does not imply that source
content has been fetched or approved.

| Category | Parser Family | Records | Missing Fields | URL Coverage | Content Type | Extraction Risks | Next Expansion |
| --- | --- | ---: | --- | ---: | --- | --- | --- |
| இலக்கணம் | `grammar_parser` | 2 | 0 | 100.0% | Validated prior pilot | Bounded pilot evidence only | Framework verified |
| சங்க இலக்கியம் | `verse_parser` | 3 | 0 | 100.0% | Validated prior pilot | Bounded pilot evidence only | Framework verified |
| சைவம் | `verse_parser` | 10 | 0 | 100.0% | Validated prior pilot | Bounded pilot evidence only | Framework verified |
| இருபதாம் நூற்றாண்டு இலக்கியங்கள் உரைநடைகள் | `prose_parser` | 2 | 0 | 100.0% | Validated structural prose paragraphs | Three-page fixture evidence only | Framework verified |
| அகராதிகள் | `dictionary_parser` | 1 | 0 | 100.0% | Validated prior pilot | Bounded pilot evidence only | Framework verified |
| கலைக்களஞ்சியங்கள் | `dictionary_parser` | 0 | Not tested | Not tested | Pending inspected sample | HTML hierarchy unknown | Source inspection required |

## Finding

The shared contract works for bounded Saivam, Sangam, dictionary, grammar, and structural
prose evidence. Encyclopedia ingestion still requires source inspection and local fixtures.
Permissioned source-text fixtures remain required before prose corpus expansion.
