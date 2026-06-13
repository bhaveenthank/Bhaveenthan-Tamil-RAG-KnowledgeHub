from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

DEFAULT_OUTPUT = Path("data/processed/eval/literary_analysis_questions.jsonl")
DEFAULT_REPORT = Path("reports/question-taxonomy-report.md")

CATEGORIES = (
    "A. Basic lookup",
    "B. Verse identification",
    "C. Word occurrence",
    "D. Synonym expansion",
    "E. Deity and epithet",
    "F. Simile and metaphor",
    "G. Poet/Nayanmar comparison",
    "H. Cross-hymn and cross-corpus",
    "I. Failure diagnosis",
)
DIFFICULTIES = {"easy", "medium", "hard"}
EVALUATION_METHODS = {
    "exact_match",
    "citation_match",
    "list_recall",
    "aggregation_check",
    "manual_review",
}
REQUIREMENT_FIELDS = {
    "retrieval",
    "citation",
    "aggregation",
    "synonym_expansion",
    "cross_corpus",
    "llm_generation",
}
REQUIRED_FIELDS = {
    "question_id",
    "question_tamil",
    "question_english_gloss",
    "category",
    "expected_answer_type",
    "requires",
    "difficulty",
    "evaluation_method",
    "notes",
}


def item(
    tamil: str,
    gloss: str,
    answer_type: str,
    difficulty: str,
    evaluation_method: str,
    notes: str,
    *,
    aggregation: bool = False,
    synonym_expansion: bool = False,
    cross_corpus: bool = False,
    llm_generation: bool = False,
) -> dict[str, Any]:
    return {
        "question_tamil": tamil,
        "question_english_gloss": gloss,
        "expected_answer_type": answer_type,
        "requires": {
            "retrieval": True,
            "citation": True,
            "aggregation": aggregation,
            "synonym_expansion": synonym_expansion,
            "cross_corpus": cross_corpus,
            "llm_generation": llm_generation,
        },
        "difficulty": difficulty,
        "evaluation_method": evaluation_method,
        "notes": notes,
    }


QUESTION_GROUPS: dict[str, list[dict[str, Any]]] = {
    "A. Basic lookup": [
        item("திருப்பூந்தராய் பதிகத்தைப் பாடியவர் யார்?", "Who composed the Tiruppoontharaai hymn?", "single_metadata_value", "easy", "exact_match", "Tests author lookup."),
        item("திருப்பூந்தராய் பதிகம் எந்தத் திருமுறையில் உள்ளது?", "Which Thirumurai contains the Tiruppoontharaai hymn?", "single_metadata_value", "easy", "exact_match", "Tests work hierarchy lookup."),
        item("திருப்பூந்தராய் பதிகத்தின் hymn ID என்ன?", "What is the hymn ID of Tiruppoontharaai?", "identifier", "easy", "exact_match", "Tests stable hymn identifier lookup."),
        item("1470 என்ற song number எந்தப் பதிகத்தைச் சேர்ந்தது?", "Which hymn contains song number 1470?", "hymn_reference", "easy", "citation_match", "Tests song-to-hymn mapping."),
        item("இரண்டாம் திருமுறையின் ஆசிரியர் யார்?", "Who is the author of the Second Thirumurai?", "single_metadata_value", "easy", "exact_match", "Tests normalized author metadata."),
        item("திருப்பூந்தராய் பதிகத்தின் பண் என்ன?", "What is the pann of the Tiruppoontharaai hymn?", "single_metadata_value", "easy", "exact_match", "Tests musical-mode metadata."),
        item("திருவலஞ்சுழி பதிகத்தின் தலப்பெயர் என்ன?", "What is the place name of the Tiruvalanchuzhi hymn?", "single_metadata_value", "easy", "citation_match", "Tests hymn location metadata."),
        item("ஒரு பாடலுக்கான பொழிப்புரை கிடைக்கிறதா?", "Is a prose explanation available for this verse?", "boolean_with_citation", "easy", "citation_match", "Tests commentary availability."),
        item("ஒரு பாடலுக்கான குறிப்புரை கிடைக்கிறதா?", "Is an explanatory note available for this verse?", "boolean_with_citation", "easy", "citation_match", "Tests commentary field availability."),
        item("திருப்பூந்தராய் பதிகத்தில் எத்தனை பாடல்கள் உள்ளன?", "How many verses are in the Tiruppoontharaai hymn?", "count", "medium", "aggregation_check", "Requires within-hymn counting.", aggregation=True),
        item("1479 என்ற song number-இன் source URL என்ன?", "What is the source URL for song number 1479?", "source_url", "easy", "exact_match", "Tests provenance lookup."),
        item("திருப்பூந்தராய் பதிகத்தின் முழுத் தலைப்பு என்ன?", "What is the full title of the Tiruppoontharaai hymn?", "title", "easy", "citation_match", "Tests title preservation."),
    ],
    "B. Verse identification": [
        item("இந்தப் பாடல் வரி எந்தப் பதிகத்தில் வருகிறது: 'பூந்தராய்'?", "Which hymn contains the line or phrase 'Poontharaai'?", "hymn_and_verse_reference", "easy", "citation_match", "Tests exact Tamil phrase retrieval."),
        item("'வினா உரை' என்று தலைப்பில் வரும் பதிகத்தை அடையாளம் காண்க.", "Identify the hymn whose title contains 'vina urai'.", "hymn_reference", "easy", "citation_match", "Tests title phrase matching."),
        item("'இந்தளம்' பண் கொண்ட பதிகங்களை கண்டறிக.", "Find hymns set in the Indhalam pann.", "hymn_list", "medium", "list_recall", "Tests metadata-filtered retrieval.", aggregation=True),
        item("கொடுக்கப்பட்ட ஒரு தேவார வரியிலிருந்து song number-ஐ கண்டறிக.", "Identify the song number from a supplied Thevaram line.", "identifier", "medium", "citation_match", "Requires verse-level exact matching."),
        item("கொடுக்கப்பட்ட பாடல் வரியிலிருந்து பதிகத் தலைப்பைக் கண்டறிக.", "Identify the hymn title from a supplied verse line.", "hymn_reference", "medium", "citation_match", "Tests verse-to-parent mapping."),
        item("கொடுக்கப்பட்ட பாடல் வரியைப் பாடிய சம்பந்தரை அடையாளம் காண்க.", "Identify Sambandar as the poet of a supplied verse.", "author_with_citation", "medium", "citation_match", "Tests verse-to-author provenance."),
        item("'திருத் தெளிச்சேரி' எனும் சொற்றொடர் எந்தப் பதிகத் தலைப்பில் உள்ளது?", "Which hymn title contains 'Tirut Telichcheri'?", "hymn_reference", "easy", "citation_match", "Tests place-title retrieval."),
        item("ஒரு பொழிப்புரைத் துணுக்கிலிருந்து அதற்குரிய பாடலை கண்டறிக.", "Find the verse associated with a prose-commentary excerpt.", "verse_reference", "hard", "citation_match", "Tests commentary-to-verse retrieval."),
        item("ஒரு குறிப்புரைத் துணுக்கிலிருந்து hymn ID-ஐ கண்டறிக.", "Find the hymn ID from an explanatory-note excerpt.", "identifier", "hard", "citation_match", "Tests note-to-parent tracing."),
        item("இரண்டு ஒத்த பாடல் வரிகளில் சரியான மூலப் பாடலை வேறுபடுத்துக.", "Disambiguate the correct source verse between two similar lines.", "disambiguated_reference", "hard", "manual_review", "Tests precise source grounding."),
        item("ஒரு பாடலின் முதல் வரியைக் கொண்டு அதன் முழுப் பாடலை மீட்டெடுக்குக.", "Retrieve a full verse from its first line.", "verse_text", "medium", "citation_match", "Tests line-to-verse retrieval."),
        item("ஒரு பாடலின் இறுதி வரியைக் கொண்டு அதன் பதிகத்தை அடையாளம் காண்க.", "Identify a hymn from the final line of a verse.", "hymn_reference", "hard", "citation_match", "Tests retrieval when the query is not the opening line."),
    ],
    "C. Word occurrence": [
        item("எந்த எந்த பாடல்களில் 'சந்திரன்' குறிப்பிடப்பட்டுள்ளது?", "Which verses mention 'chandran'?", "verse_list", "medium", "list_recall", "Requires corpus-wide occurrence counting.", aggregation=True),
        item("எந்த பாடல்களில் 'நிலவு' என்ற சொல் வருகிறது?", "Which verses contain the word 'nilavu'?", "verse_list", "medium", "list_recall", "Exact word occurrence query.", aggregation=True),
        item("எந்த பாடல்களில் 'மதி' என்ற சொல் வருகிறது?", "Which verses contain the word 'madhi'?", "verse_list", "medium", "list_recall", "Exact word occurrence query.", aggregation=True),
        item("எந்த பாடல்களில் 'திங்கள்' என்ற சொல் வருகிறது?", "Which verses contain the word 'thingal'?", "verse_list", "medium", "list_recall", "Exact word occurrence query.", aggregation=True),
        item("'அருள்' என்ற சொல் அதிகம் வரும் பதிகங்கள் எவை?", "Which hymns use the word 'arul' most often?", "ranked_hymn_list", "hard", "aggregation_check", "Requires frequency aggregation.", aggregation=True),
        item("'சடை' என்ற சொல் வரும் பாடல்களையும் எண்ணிக்கையையும் தருக.", "List verses containing 'sadai' and give the count.", "verse_list_and_count", "hard", "aggregation_check", "Requires occurrence list and count.", aggregation=True),
        item("'கங்கை' என்ற சொல் பொழிப்புரையில் வரும் இடங்கள் எவை?", "Where does 'Gangai' occur in prose commentary?", "commentary_occurrence_list", "hard", "list_recall", "Restricts search to pozhppurai.", aggregation=True),
        item("'உமை' என்ற சொல் குறிப்புரையில் வரும் இடங்கள் எவை?", "Where does 'Umai' occur in explanatory notes?", "commentary_occurrence_list", "hard", "list_recall", "Restricts search to kurippurai.", aggregation=True),
        item("ஒரே பாடலில் 'மதி' மற்றும் 'சடை' இரண்டும் வரும் இடங்கள் எவை?", "Which verses contain both 'madhi' and 'sadai'?", "verse_list", "hard", "list_recall", "Requires boolean term intersection.", aggregation=True),
        item("'திரு' என்று தொடங்கும் தலப்பெயர்கள் எத்தனை?", "How many place names begin with 'Tiru'?", "count_and_list", "medium", "aggregation_check", "Requires normalized place metadata.", aggregation=True),
        item("ஒவ்வொரு பதிகத்திலும் 'சிவன்' வரும் எண்ணிக்கையைத் தருக.", "Give the count of 'Sivan' occurrences in each hymn.", "grouped_counts", "hard", "aggregation_check", "Requires per-hymn aggregation.", aggregation=True),
        item("பாடல் உரையிலும் பொழிப்புரையிலும் ஒரே சொல் வரும் பதிவுகளை கண்டறிக.", "Find records where the same target word appears in verse and prose commentary.", "record_list", "hard", "aggregation_check", "Requires field-aware occurrence comparison.", aggregation=True),
    ],
    "D. Synonym expansion": [
        item("சந்திரனுக்கான தமிழ் இலக்கிய ஒத்த சொற்கள் எவை?", "What are the Tamil literary synonyms for the moon?", "synonym_list", "medium", "manual_review", "Requires a curated literary synonym lexicon.", synonym_expansion=True),
        item("நிலவு, மதி, திங்கள் ஆகிய சொற்கள் வரும் பாடல்களை ஒன்றாகத் தருக.", "List together verses containing nilavu, madhi, or thingal.", "expanded_verse_list", "hard", "list_recall", "Requires synonym-expanded retrieval.", aggregation=True, synonym_expansion=True),
        item("சிவனை குறிக்கும் ஒத்த பெயர்களை வைத்து பாடல்களைத் தேடுக.", "Search verses using synonymous names for Siva.", "expanded_verse_list", "hard", "list_recall", "Requires deity-name lexicon.", aggregation=True, synonym_expansion=True),
        item("உமைக்கான மாற்றுப் பெயர்கள் வரும் பாடல்கள் எவை?", "Which verses contain alternative names for Uma?", "expanded_verse_list", "hard", "list_recall", "Requires goddess-name expansion.", aggregation=True, synonym_expansion=True),
        item("கடல் என்பதற்கான இலக்கிய மாற்றுச் சொற்கள் என்ன?", "What are literary alternatives for the word sea?", "synonym_list", "medium", "manual_review", "Lexicon answer needs scholarly review.", synonym_expansion=True),
        item("மலர் என்ற கருத்தைக் குறிக்கும் ஒத்த சொற்கள் வரும் பாடல்கள் எவை?", "Which verses contain synonyms expressing the concept of flower?", "expanded_verse_list", "hard", "list_recall", "Requires concept and morphology-aware expansion.", aggregation=True, synonym_expansion=True),
        item("ஒளி என்பதற்கான ஒத்த சொற்களை விரிவாக்கி பாடல்களை கண்டறிக.", "Expand synonyms for light and find matching verses.", "expanded_verse_list", "hard", "list_recall", "Requires literary synonym expansion.", aggregation=True, synonym_expansion=True),
        item("இறைவன் என்ற சொல்லுக்கு இணையான அடைமொழிகள் எவை?", "Which epithets are equivalent to 'iraivan'?", "synonym_and_epithet_list", "hard", "manual_review", "Boundary between synonym and epithet needs curation.", synonym_expansion=True),
        item("அன்பு, காதல், நேசம் சார்ந்த சொற்கள் வரும் பாடல்களைத் தொகுக்குக.", "Collect verses containing terms related to love and affection.", "semantic_field_list", "hard", "manual_review", "Requires a semantic-field lexicon.", aggregation=True, synonym_expansion=True),
        item("ஒரே சந்திரக் கருத்து வெவ்வேறு சொற்களால் வரும் பாடல்களை ஒப்பிடுக.", "Compare verses that express the moon using different words.", "comparative_evidence_set", "hard", "manual_review", "Requires synonym expansion plus comparison.", aggregation=True, synonym_expansion=True, llm_generation=True),
    ],
    "E. Deity and epithet": [
        item("சிவனை குறிக்கும் அடைமொழிகள் எவை?", "What epithets refer to Siva?", "epithet_list", "hard", "manual_review", "Requires entity and epithet extraction.", aggregation=True),
        item("'சடையன்' என சிவன் அழைக்கப்படும் பாடல்கள் எவை?", "Which verses call Siva 'Sadaiyan'?", "verse_list", "medium", "list_recall", "Tests exact epithet retrieval.", aggregation=True),
        item("கங்கை அணிந்தவனாக சிவன் வர்ணிக்கப்படும் பாடல்கள் எவை?", "Which verses describe Siva as wearing the Ganges?", "verse_list", "hard", "manual_review", "Requires deity-description interpretation.", aggregation=True, llm_generation=True),
        item("பிறை அணிந்தவனாக சிவன் வரும் பாடல்கள் எவை?", "Which verses portray Siva as wearing the crescent moon?", "verse_list", "hard", "list_recall", "Requires phrase and epithet matching.", aggregation=True),
        item("உமையுடன் சிவன் குறிப்பிடப்படும் பாடல்கள் எவை?", "Which verses mention Siva together with Uma?", "verse_list", "medium", "list_recall", "Requires deity co-occurrence.", aggregation=True),
        item("சிவனின் உருவ அடையாளங்கள் என்னென்ன?", "What physical attributes of Siva are described?", "attribute_list_with_evidence", "hard", "manual_review", "Requires corpus-wide entity attribute extraction.", aggregation=True, llm_generation=True),
        item("எந்த அடைமொழி அதிகமான பாடல்களில் வருகிறது?", "Which epithet occurs in the most verses?", "ranked_epithet", "hard", "aggregation_check", "Requires normalized epithet counts.", aggregation=True),
        item("ஒரே பாடலில் சிவனுக்குப் பல அடைமொழிகள் வரும் இடங்கள் எவை?", "Which verses use multiple epithets for Siva?", "verse_list_with_epithets", "hard", "manual_review", "Requires multi-label epithet extraction.", aggregation=True),
        item("பொழிப்புரையில் விளக்கப்படும் சிவன் அடைமொழிகள் எவை?", "Which Siva epithets are explained in the prose commentary?", "commentary_grounded_epithet_list", "hard", "manual_review", "Requires verse-commentary alignment.", aggregation=True),
        item("குறிப்புரையில் புராணச் செய்தியுடன் இணைக்கப்படும் இறை அடையாளங்கள் எவை?", "Which divine attributes are linked to mythology in the notes?", "attribute_and_myth_list", "hard", "manual_review", "Requires interpretation of notes.", aggregation=True, llm_generation=True),
        item("தலத்தோடு தொடர்புடைய இறை அடைமொழிகள் எவை?", "Which divine epithets are associated with a place?", "place_epithet_pairs", "hard", "manual_review", "Requires place and epithet entities.", aggregation=True),
        item("சிவன் தவிர குறிப்பிடப்படும் பிற தெய்வங்கள் எவை?", "Which deities other than Siva are mentioned?", "deity_list_with_citations", "hard", "list_recall", "Requires deity entity recognition.", aggregation=True),
    ],
    "F. Simile and metaphor": [
        item("சந்திரன் எந்த இடங்களில் உவமையாக பயன்படுத்தப்பட்டுள்ளது?", "Where is the moon used as a simile?", "verse_list_with_device", "hard", "manual_review", "Requires literary-device annotation.", aggregation=True, llm_generation=True),
        item("மலர் உவமை வரும் பாடல்கள் எவை?", "Which verses use flower imagery as a simile?", "verse_list_with_device", "hard", "manual_review", "Requires imagery and simile detection.", aggregation=True, llm_generation=True),
        item("கடல் உருவகமாக வரும் பாடல்கள் எவை?", "Which verses use the sea metaphorically?", "verse_list_with_device", "hard", "manual_review", "Requires metaphor interpretation.", aggregation=True, llm_generation=True),
        item("ஒளி சிவனுக்கான உருவகமாக பயன்படுத்தப்படும் இடங்கள் எவை?", "Where is light used as a metaphor for Siva?", "verse_list_with_device", "hard", "manual_review", "Requires deity-linked metaphor detection.", aggregation=True, llm_generation=True),
        item("எந்த இயற்கைக் கூறுகள் இறைவனை வர்ணிக்கப் பயன்படுத்தப்படுகின்றன?", "Which natural elements are used to describe the deity?", "imagery_inventory", "hard", "manual_review", "Requires corpus-wide imagery extraction.", aggregation=True, llm_generation=True),
        item("ஒரே பதிகத்தில் மீண்டும் வரும் உவமைகள் எவை?", "Which similes recur within the same hymn?", "repeated_device_list", "hard", "manual_review", "Requires within-hymn comparison.", aggregation=True, llm_generation=True),
        item("பொழிப்புரை எந்த உவமைகளை வெளிப்படையாக விளக்குகிறது?", "Which similes are explicitly explained by the prose commentary?", "commentary_grounded_device_list", "hard", "manual_review", "Requires commentary-aware device detection.", aggregation=True, llm_generation=True),
        item("குறிப்புரை உருவகத்திற்கான புராணப் பின்னணியைத் தருகிறதா?", "Does the note provide mythic background for a metaphor?", "evidence_based_boolean", "hard", "manual_review", "Requires close reading of verse and note.", llm_generation=True),
        item("சந்திரன் உவமையா அல்லது சிவனின் அடையாளமா என்பதை வேறுபடுத்துக.", "Distinguish whether the moon is a simile or an attribute of Siva.", "literary_device_classification", "hard", "manual_review", "Requires contextual literary classification.", llm_generation=True),
        item("எந்த உருவகம் அதிகமான பதிகங்களில் மீள்கிறது?", "Which metaphor recurs across the most hymns?", "ranked_device", "hard", "aggregation_check", "Requires normalized device aggregation.", aggregation=True, llm_generation=True),
        item("ஒரே கருத்துக்கு பயன்படுத்தப்பட்ட வேறுபட்ட உவமைகளை ஒப்பிடுக.", "Compare different similes used for the same concept.", "comparative_analysis", "hard", "manual_review", "Requires grouped evidence and interpretation.", aggregation=True, llm_generation=True),
        item("உவமை இல்லாமல் நேரடி வர்ணனை வரும் பாடல்களை அடையாளம் காண்க.", "Identify verses that use direct description rather than simile.", "verse_classification_list", "hard", "manual_review", "Requires negative literary-device classification.", aggregation=True, llm_generation=True),
    ],
    "G. Poet/Nayanmar comparison": [
        item("சம்பந்தர் எந்த அடைமொழிகளை அதிகம் பயன்படுத்துகிறார்?", "Which epithets does Sambandar use most?", "ranked_epithet_list", "hard", "aggregation_check", "Single-author baseline aggregation.", aggregation=True),
        item("சம்பந்தரின் பதிகங்களில் சந்திரக் காட்சிகள் எவ்வளவு வருகின்றன?", "How often does lunar imagery occur in Sambandar's hymns?", "count_with_evidence", "hard", "aggregation_check", "Requires imagery annotation and counting.", aggregation=True, synonym_expansion=True),
        item("சம்பந்தரும் அப்பரும் சிவனை வர்ணிக்கும் முறையை ஒப்பிடுக.", "Compare how Sambandar and Appar describe Siva.", "cross_author_comparison", "hard", "manual_review", "Requires another normalized author corpus.", aggregation=True, cross_corpus=True, llm_generation=True),
        item("எந்த நாயன்மார் சந்திரனை அதிகமாக உவமையாக பயன்படுத்துகிறார்?", "Which Nayanmar uses the moon most often as a simile?", "ranked_author", "hard", "aggregation_check", "Requires multiple Nayanmar corpora and device annotations.", aggregation=True, synonym_expansion=True, cross_corpus=True),
        item("எந்த பாடகர் சிவனை அதிகமான அடைமொழிகளால் பாடுகிறார்?", "Which poet uses the greatest variety of epithets for Siva?", "ranked_author", "hard", "aggregation_check", "Requires normalized cross-author epithet counts.", aggregation=True, cross_corpus=True),
        item("சம்பந்தர் மற்றும் சுந்தரர் பயன்படுத்தும் தல வர்ணனைகளை ஒப்பிடுக.", "Compare place descriptions used by Sambandar and Sundarar.", "cross_author_comparison", "hard", "manual_review", "Requires multi-corpus place metadata.", aggregation=True, cross_corpus=True, llm_generation=True),
        item("அப்பர் மற்றும் சம்பந்தர் பொழிப்புரைகளில் விளக்கப்படும் கருத்து வேறுபாடுகள் எவை?", "What conceptual differences appear in commentary for Appar and Sambandar?", "cross_author_commentary_comparison", "hard", "manual_review", "Requires commentary normalization across corpora.", aggregation=True, cross_corpus=True, llm_generation=True),
        item("ஒவ்வொரு நாயன்மாரின் பாடல்களில் அதிகம் வரும் தெய்வ அடையாளம் எது?", "Which divine attribute is most frequent for each Nayanmar?", "grouped_ranked_attributes", "hard", "aggregation_check", "Requires multi-author aggregation.", aggregation=True, cross_corpus=True),
        item("பண் பயன்பாட்டில் நாயன்மார்களுக்கிடையிலான வேறுபாடு என்ன?", "How does pann usage differ between Nayanmars?", "cross_author_distribution", "hard", "aggregation_check", "Requires normalized pann metadata.", aggregation=True, cross_corpus=True),
        item("ஒரே தலத்தைப் பாடிய நாயன்மார்களின் வர்ணனைகளை ஒப்பிடுக.", "Compare descriptions by Nayanmars who sang about the same place.", "cross_author_place_comparison", "hard", "manual_review", "Requires normalized place identity and multiple corpora.", aggregation=True, cross_corpus=True, llm_generation=True),
    ],
    "H. Cross-hymn and cross-corpus": [
        item("எந்த பதிகங்களில் ஒரே imagery மீண்டும் வருகிறது?", "Which hymns repeat the same imagery?", "cross_hymn_clusters", "hard", "manual_review", "Requires imagery normalization across hymns.", aggregation=True, llm_generation=True),
        item("ஒரே தெய்வம் பல பதிகங்களில் எவ்வாறு வேறுபட்டு வர்ணிக்கப்படுகிறது?", "How is the same deity described differently across hymns?", "cross_hymn_comparison", "hard", "manual_review", "Requires grouped evidence and analysis.", aggregation=True, llm_generation=True),
        item("இரண்டாம் திருமுறையில் ஒரே தலத்தைச் சேர்ந்த பதிகங்கள் எவை?", "Which Second Thirumurai hymns concern the same place?", "grouped_hymn_list", "hard", "aggregation_check", "Requires normalized place grouping.", aggregation=True),
        item("வேறுபட்ட பண்களில் ஒரே கருத்து எவ்வாறு பாடப்படுகிறது?", "How is one theme expressed in different pann settings?", "cross_hymn_comparison", "hard", "manual_review", "Requires pann and theme annotations.", aggregation=True, llm_generation=True),
        item("தேவாரத்திலும் திருப்புகழிலும் சந்திர imagery-ஐ ஒப்பிடுக.", "Compare lunar imagery in Thevaram and Tiruppugazh.", "cross_corpus_comparison", "hard", "manual_review", "Requires an approved Tiruppugazh corpus.", aggregation=True, synonym_expansion=True, cross_corpus=True, llm_generation=True),
        item("இரண்டாம் மற்றும் மூன்றாம் திருமுறைகளில் சிவன் அடைமொழிகளை ஒப்பிடுக.", "Compare Siva epithets in the Second and Third Thirumurai.", "cross_corpus_comparison", "hard", "aggregation_check", "Requires another audited Thirumurai.", aggregation=True, cross_corpus=True),
        item("பல திருமுறைகளில் மீண்டும் வரும் பாடல் சொற்றொடர்கள் எவை?", "Which phrases recur across multiple Thirumurai?", "cross_corpus_phrase_list", "hard", "list_recall", "Requires cross-corpus phrase indexing.", aggregation=True, cross_corpus=True),
        item("ஒரே புராண நிகழ்வு பல பதிகங்களில் எவ்வாறு சொல்லப்படுகிறது?", "How is one mythic event narrated across hymns?", "cross_hymn_comparison", "hard", "manual_review", "Requires event normalization and interpretation.", aggregation=True, llm_generation=True),
        item("வேறு திருமுறைகளின் பொழிப்புரை பாணியை ஒப்பிடுக.", "Compare prose-commentary styles across Thirumurai.", "cross_corpus_commentary_comparison", "hard", "manual_review", "Requires normalized commentary corpora.", aggregation=True, cross_corpus=True, llm_generation=True),
        item("ஒரே song number வேறு தொகுப்புகளில் மோதுகிறதா?", "Does the same song number collide across collections?", "identifier_collision_report", "hard", "aggregation_check", "Requires namespaced cross-corpus identifiers.", aggregation=True, cross_corpus=True),
        item("தேவாரம் மற்றும் சங்க இலக்கியத்தில் கடல் உருவகத்தை ஒப்பிடுக.", "Compare sea metaphors in Thevaram and Sangam literature.", "cross_corpus_comparison", "hard", "manual_review", "Requires a normalized Sangam corpus.", aggregation=True, cross_corpus=True, llm_generation=True),
        item("பல corpus-களில் ஒரே தலப்பெயர் எவ்வாறு இணைக்கப்படுகிறது?", "How is the same place name linked across corpora?", "cross_corpus_entity_links", "hard", "manual_review", "Requires entity resolution across corpora.", aggregation=True, cross_corpus=True),
    ],
    "I. Failure diagnosis": [
        item("எதிர்பார்த்த பாடல் கிடைக்கவில்லை; மூலத் தரவு இல்லையா என்பதைச் சரிபார்க்கவும்.", "A verse was not found; check whether source data is missing.", "diagnostic_classification", "medium", "manual_review", "Distinguishes source absence from retrieval failure."),
        item("பாடல் உள்ளது ஆனால் பொழிப்புரை இல்லை; இது source missing பிரச்சினையா?", "The verse exists but pozhppurai is absent; is this source missing?", "diagnostic_classification", "medium", "manual_review", "Uses raw-source audit evidence."),
        item("மூல HTML-ல் உரை உள்ளது ஆனால் record-ல் இல்லை; காரணம் parser issue-ஆ?", "Commentary exists in source HTML but not the record; is it a parser issue?", "diagnostic_classification", "hard", "manual_review", "Requires source-versus-record comparison."),
        item("lexical retrieval கண்டுபிடித்த பதிவை semantic retrieval ஏன் தவறவிட்டது?", "Why did semantic retrieval miss a record found lexically?", "retrieval_diagnosis", "hard", "manual_review", "Uses retrieval diagnostics, not answer generation."),
        item("சரியான பதிவு top-10-ல் உள்ளது ஆனால் rank 1-ல் இல்லை; இது ranking issue-ஆ?", "The correct record is in top ten but not rank one; is this a ranking issue?", "retrieval_diagnosis", "hard", "manual_review", "Tests ranking failure classification."),
        item("கேள்விக்கு corpus-wide count தேவை; context builder மட்டும் ஏன் போதாது?", "Why is the context builder insufficient for a corpus-wide count?", "architecture_diagnosis", "hard", "manual_review", "Identifies missing analysis-layer capability.", aggregation=True),
        item("ஒத்த சொல் கேள்வி தோல்வியடைந்தது; synonym lexicon இல்லாமையே காரணமா?", "Did a synonym query fail because no synonym lexicon exists?", "architecture_diagnosis", "hard", "manual_review", "Identifies lexicon dependency.", synonym_expansion=True),
        item("வேறு நாயன்மாரை ஒப்பிட முடியவில்லை; இது missing corpus அல்லது metadata normalization பிரச்சினையா?", "A Nayanmar comparison failed; is the cause missing corpus or metadata normalization?", "architecture_diagnosis", "hard", "manual_review", "Separates corpus coverage from normalization.", aggregation=True, cross_corpus=True),
    ],
}


def build_questions() -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    for category in CATEGORIES:
        for specification in QUESTION_GROUPS[category]:
            record = {"question_id": f"q_{len(questions) + 1:03d}", **specification}
            record["category"] = category
            questions.append(record)
    return questions


def validate_questions(questions: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if len(questions) != 100:
        errors.append(f"expected exactly 100 questions, found {len(questions)}")

    expected_ids = [f"q_{index:03d}" for index in range(1, len(questions) + 1)]
    actual_ids = [question.get("question_id") for question in questions]
    if actual_ids != expected_ids:
        errors.append("question IDs are not deterministic and sequential")

    missing_categories = set(CATEGORIES) - {question.get("category") for question in questions}
    if missing_categories:
        errors.append(f"missing categories: {sorted(missing_categories)}")

    for index, question in enumerate(questions, start=1):
        missing_fields = REQUIRED_FIELDS - question.keys()
        if missing_fields:
            errors.append(f"q_{index:03d}: missing fields {sorted(missing_fields)}")
            continue
        text_fields = REQUIRED_FIELDS - {"requires"}
        if not all(isinstance(question[field], str) and question[field].strip() for field in text_fields):
            errors.append(f"q_{index:03d}: required text fields must be non-empty strings")
        if question["category"] not in CATEGORIES:
            errors.append(f"q_{index:03d}: invalid category")
        if question["difficulty"] not in DIFFICULTIES:
            errors.append(f"q_{index:03d}: invalid difficulty")
        if question["evaluation_method"] not in EVALUATION_METHODS:
            errors.append(f"q_{index:03d}: invalid evaluation method")
        requirements = question["requires"]
        if not isinstance(requirements, dict) or set(requirements) != REQUIREMENT_FIELDS:
            errors.append(f"q_{index:03d}: malformed requires object")
        elif any(not isinstance(value, bool) for value in requirements.values()):
            errors.append(f"q_{index:03d}: requirement flags must be booleans")
        elif not requirements["retrieval"] or not requirements["citation"]:
            errors.append(f"q_{index:03d}: retrieval and citation must be required")
    return errors


def summarize(questions: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts = Counter(question["category"] for question in questions)
    difficulty_counts = Counter(question["difficulty"] for question in questions)
    requirement_counts = {
        field: sum(question["requires"][field] for question in questions)
        for field in sorted(REQUIREMENT_FIELDS)
    }
    ordinary_rag = sum(
        not question["requires"]["aggregation"]
        and not question["requires"]["synonym_expansion"]
        and not question["requires"]["cross_corpus"]
        and not question["requires"]["llm_generation"]
        for question in questions
    )
    return {
        "total_questions": len(questions),
        "category_counts": dict(category_counts),
        "difficulty_counts": dict(sorted(difficulty_counts.items())),
        "requirement_counts": requirement_counts,
        "ordinary_rag_questions": ordinary_rag,
    }


def render_report(summary: dict[str, Any]) -> str:
    category_rows = "\n".join(
        f"| {category} | {summary['category_counts'].get(category, 0)} |" for category in CATEGORIES
    )
    difficulty_rows = "\n".join(
        f"| {difficulty.title()} | {count} |"
        for difficulty, count in summary["difficulty_counts"].items()
    )
    requirements = summary["requirement_counts"]
    return f"""# Tamil Literary RAG Question Taxonomy Report

## Summary

- Total questions: `{summary["total_questions"]}`
- Ordinary RAG questions: `{summary["ordinary_rag_questions"]}`
- Corpus-wide aggregation questions: `{requirements["aggregation"]}`
- Synonym expansion questions: `{requirements["synonym_expansion"]}`
- Cross-corpus questions: `{requirements["cross_corpus"]}`
- Questions marked for future LLM generation: `{requirements["llm_generation"]}`

## Category Distribution

| Category | Questions |
| --- | ---: |
{category_rows}

## Difficulty Distribution

| Difficulty | Questions |
| --- | ---: |
{difficulty_rows}

## Architecture Implications

- Current RAG context builder can answer lookup/retrieval questions.
- Analytical questions require an additional corpus analysis layer.
- Synonym-based questions require a Tamil literary synonym lexicon.
- Cross-Nayanmar comparison requires multi-corpus metadata normalization.
- Parser quality must be audited before scaling to 3-4 more Thirumurai.
- Citation grounding remains mandatory for lookup, lists, counts, and future generated explanations.
- Literary-device questions need curated annotations or a separately evaluated analysis pipeline; retrieval scores alone do not prove a simile or metaphor.

## Scope Decision

This phase defines and validates the evaluation space only. It makes no LLM calls, performs no scraping, and does not alter corpus, embedding, or vector-index artifacts.
"""


def write_jsonl(path: Path, questions: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(
        json.dumps(question, ensure_ascii=False, sort_keys=True) + "\n" for question in questions
    )
    path.write_text(content, encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build and validate the Tamil literary question taxonomy.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the existing output file without regenerating it.",
    )
    args = parser.parse_args(argv)

    questions = load_jsonl(args.output) if args.validate_only else build_questions()
    errors = validate_questions(questions)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    if not args.validate_only:
        write_jsonl(args.output, questions)
    summary = summarize(questions)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(summary), encoding="utf-8")

    print(f"Questions: {summary['total_questions']}")
    print(f"Ordinary RAG: {summary['ordinary_rag_questions']}")
    print(f"Aggregation: {summary['requirement_counts']['aggregation']}")
    print(f"Synonym expansion: {summary['requirement_counts']['synonym_expansion']}")
    print(f"Cross-corpus: {summary['requirement_counts']['cross_corpus']}")
    print(f"Dataset: {args.output}")
    print(f"Report: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
