# Website Parser Strategy Matrix

This matrix is an architectural hypothesis based on category purpose and known TamilVU page families. Every selected pilot still requires static site inspection before ingestion.

| Category | Expected Structure | Parser | Difficulty | Required Metadata | Likely Risks | Early Pilot | OCR / Media | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| சொல்லடைவு | Headword/index rows linked to works or pages | `dictionary_parser` | Medium | headword, work, occurrence, source | ambiguous token boundaries, tables | Later | No | Planned |
| தமிழ் எண் சுவடி | Manuscript images and descriptive metadata | `image_metadata_parser` | High | manuscript, folio, script, image URL, rights | image-only text, OCR quality | No | Yes | Deferred |
| இலக்கணம் | Work/chapter/sutra/rule/example/commentary | `grammar_parser` | High | rule ID, chapter, author, example, commentary | flattened rules and examples | Yes | Maybe | Pilot candidate |
| சங்க இலக்கியம் | Anthology/work/poem/poet/thinai/commentary | `verse_parser` | High | poem no., poet, thinai, work, commentary | variant numbering, attribution | Yes | No | Pilot candidate |
| பதினெண் கீழ்க்கணக்கு | Work/chapter/verse/commentary | `verse_parser` | Medium | work, verse no., author, chapter | work-specific numbering | Later | No | High priority |
| காப்பியங்கள் | Canto/chapter/verse/prose/commentary | `mixed_parser` | High | canto, section, speaker, verse/prose type | very long pages, mixed units | Later | Maybe | Planned |
| சமய இலக்கியங்கள் | Parent category with heterogeneous works | `mixed_parser` | High | tradition, work, author, unit type | false uniformity | No | Maybe | Plan children |
| சைவம் | Work/hymn/verse/commentary | `verse_parser` | Medium | work, author, hymn, song, place, pann | multiple SLET variants | Proven subset | No | Pilot family |
| வைணவம் | Work/pasuram/author/commentary | `verse_parser` | High | work, Alvar, pasuram, section, commentary | different hierarchy and terms | Later | No | High priority |
| கிறித்துவம் | Poetry, prose, translations, chapters | `mixed_parser` | High | author, edition, genre, language | mixed formats and rights | Later | Maybe | Planned |
| இசுலாம் | Poetry, prose, biography, translation | `mixed_parser` | High | author, work, genre, language | transliteration and mixed formats | Later | Maybe | Planned |
| சிற்றிலக்கியங்கள் | Work/form/section/verse | `verse_parser` | Medium | literary form, meter, author, verse | heterogeneous minor forms | Later | No | High priority |
| நெறி நூல்கள் | Aphorism/verse/chapter/prose explanation | `mixed_parser` | Medium | chapter, maxim, author, commentary | unit-boundary ambiguity | Later | No | Planned |
| சித்தர் இலக்கியம் | Poet/work/song/verse | `verse_parser` | Medium | Siddhar, work, song no., terminology | author variants, specialist terms | Later | No | Planned |
| இருபதாம் நூற்றாண்டு இலக்கியங்கள் கவிதைகள் | Book/poem/stanza/page | `verse_parser` | Medium | author, edition, poem, period, rights | copyright and typography | Later | Maybe | Planned |
| இருபதாம் நூற்றாண்டு இலக்கியங்கள் உரைநடைகள் | Book/chapter/section/paragraph/page | `prose_parser` | Medium | author, chapter, page, period, rights | long pages, footnotes | Yes | Maybe | Pilot candidate |
| நாட்டுப்புற இலக்கியங்கள் | Genre/region/song/story/variant | `mixed_parser` | High | region, genre, performer/source, variant | oral variants and weak attribution | Later | Maybe | Planned |
| சிறுவர் இலக்கியங்கள் | Story/poem/chapter/illustration | `mixed_parser` | Medium | author, age, unit type, image | illustration-text alignment, rights | Later | Yes | Planned |
| ரோமன் வடிவம் | Romanized work/section/text | `mixed_parser` | Medium | transliteration scheme, source work, language | alignment with Tamil text | Later | No | Planned |
| அகராதிகள் | Headword/sense/label/example/reference | `dictionary_parser` | High | headword, sense order, POS, example, page | typography and multi-column pages | Yes | Maybe | Pilot candidate |
| நிகண்டுகள் | Semantic group/headword/synonyms/verse | `dictionary_parser` | High | group, headword, synonym, source line | poetic lexicon structures | Later | Maybe | High priority |
| பிற மொழியில் தமிழ் நூல்கள் | Translation/edition/chapter/text | `mixed_parser` | High | source/target language, translator, edition | alignment and rights | No | Maybe | Deferred |
| கலைக்களஞ்சியங்கள் | Headword/article/cross-reference/media | `dictionary_parser` | Medium | headword, article, editor, references | long entries and embedded media | Optional | Maybe | Pilot candidate |
| கலைச்சொல் தொகுப்புகள் | Domain tables and bilingual terms | `table_parser` | Medium | term, language, domain, definition, columns | merged cells and encoding | Later | Maybe | Planned |
| சுவடிக்காட்சியகம் | Item/folio/image/caption | `image_metadata_parser` | High | item ID, folio, script, image, rights | OCR, image access, incomplete metadata | No | Yes | Deferred |
| பண்பாட்டுக் காட்சியகம் | Object/topic/article/image/caption | `image_metadata_parser` | Medium | object/topic, place, period, image, caption | media licensing and sparse text | Optional | Yes | Pilot candidate |
| நாட்டுடைமை நூல்கள் | Parent category across typed/image works | `mixed_parser` | High | rights evidence, author, title, format | mixed formats and duplicate editions | No | Yes | Plan children |
| நாட்டுடைமையாக்கப்பட்ட தமிழறிஞர்களின் நூல்கள் உருப்பட வடிவில் | Book/page image/PDF | `image_metadata_parser` | High | scholar, title, page, image/PDF, rights | OCR quality and large assets | No | Yes | Deferred |
| நாட்டுடைமையாக்கப்பட்ட தமிழறிஞர்களின் நூல்கள் தட்டச்சு வடிவில் | Book/chapter/paragraph/page | `prose_parser` | Medium | scholar, title, chapter, page, rights | edition duplicates, long pages | Later | No | High priority |
| உருப்பட நூல்கள் | Book/page image/PDF | `image_metadata_parser` | High | title, author, page, asset URL, rights | image-only content and storage | No | Yes | Deferred |
| தமிழக வரலாறு, கலைப் பண்பாடு, இலக்கியம் தொடர்பான நூல்கள் | Book/chapter/section/page/images | `prose_parser` | Medium | subject, period, place, bibliography, page | footnotes, tables, images | Later | Maybe | Planned |
| பிற நூலக இணையத் தளங்கள் | Institution/title/URL/scope | `external_link_registry` | Low locally | institution, URL, scope, policy date | external terms and link rot | No | No | Registry only |

## Parser Acceptance Rule

A parser family becomes reusable only after at least one representative pilot preserves hierarchy, source URLs, Tamil Unicode, record order, commentary/media boundaries, and local fixture tests. Category membership alone never authorizes recursive crawling.
