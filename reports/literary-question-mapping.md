# Literary Question Mapping

## Purpose

This map identifies the structured knowledge and deterministic operations needed before
future RAG can answer analytical Tamil literary questions completely and with citations.

| Question | Required Registries | Required Engine Capability | Evidence Requirement |
| --- | --- | --- | --- |
| எந்த hymns-இல் சந்திரன் மற்றும் அதன் ஒத்த சொற்கள் வருகின்றன? | Synonym, Entity, Work | synonym expansion, exhaustive occurrence scan | every matched span, record ID, hymn, source URL |
| எந்த நாயன்மார் சந்திரனை அதிகமாக பயன்படுத்துகிறார்? | Author, Synonym, Entity, Work | author grouping and frequency aggregation | normalized author, lunar form, count, cited records |
| சிவனுக்கான அடைமொழிகள் என்ன? | Deity, Entity, Literary Device | epithet relation inventory | epithet span, deity link, verse/commentary evidence |
| எந்த கடவுளுக்கு அதிக உவமைகள் உள்ளன? | Deity, Literary Device, Entity | device classification and grouped distinct counts | reviewed simile annotation and deity relation |
| எந்த இலக்கியங்களில் குறிப்பிட்ட உருவகங்கள் அதிகம் காணப்படுகின்றன? | Work, Motif, Literary Device, Theme | cross-work aggregation and coverage control | metaphor evidence grouped by complete work scope |
| எந்த ஆசிரியர்கள் ஒரே கருப்பொருளைப் பகிர்கின்றனர்? | Author, Work, Theme, Motif | author-theme comparison | reviewed theme evidence in each cited work |
| ஒரே தலத்தைப் பாடிய ஆசிரியர்களின் வர்ணனைகளை ஒப்பிடுக | Place, Author, Work, Motif | entity resolution and cross-author comparison | shared place ID and cited descriptive passages |
| சந்திரன் உவமையா அல்லது சிவனின் அடையாளமா? | Entity, Deity, Literary Device, Motif | contextual relation classification | exact span, surrounding text, reviewed relation type |

## Pipeline Mapping

1. Query resolver identifies registry concepts and aliases.
2. Analytical retrieval finds all linked annotations within an explicit corpus scope.
3. Aggregation groups by author, deity, work, place, motif, or device.
4. Citation grounding returns exact records and source URLs.
5. Future answer generation may explain the deterministic result but may not invent counts.

## Current Status

Registry foundations exist, but extraction, annotation, aggregation, and answer generation
do not. These questions remain future evaluation targets.
