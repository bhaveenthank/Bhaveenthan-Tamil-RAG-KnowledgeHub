# Thevaram Manual QA Samples

- Table root: `data/processed/thevaram`
- Sample count: `20`

## Corpus Counts

- `thirumurai_books`: `8`
- `paadal_thogupugal`: `841`
- `paadalgal`: `9012`
- `commentaries`: `9012`
- `text_spans`: `64073`

## Commentary Status

- `partial_commentary`: `1641`
- `success`: `7371`

## Automated Audit Snapshot

- `minor`: `553`
- `failed_commentary_has_text`: `553`

## What To Check In Each Sample

- Thirumurai number and author are plausible.
- Thogupu title, thalam, and pann are split correctly.
- `global_song_no`, `source_song_no`, `local_song_no`, and `verse_index_in_thogupu` make sense.
- Paadal text has meaningful line breaks and no UI/header/footer text.
- Commentary status matches available `kurippurai` / `pozhppurai` text.
- Source URL points to TamilVU and can be cited.

## 20 Row QA Samples

### Sample 1: `thirumurai_01_paadal_1`

- Thirumurai: `1`
- Thogupu: `thirumurai_01_thogupu_1529`
- Title: திருப்பிரமபுரம் - நட்டபாடை
- Thalam: திருப்பிரமபுரம்
- Pann: நட்டபாடை
- Song numbers: global `1`, source `1`, local `1`, index `1`
- Commentary status: `success`
- Span count: `6`
- Source: https://www.tamilvu.org/slet/l4110/l4110son.jsp?subid=1529

Paadal:

> தோடு உடைய செவியன், விடை ஏறி, ஓர் தூ வெண்மதி சூடி, / காடு உடைய சுடலைப் பொடி பூசி, என் உள்ளம் கவர் கள்வன்- / ஏடு உடைய மலரான் முனைநாள் பணிந்து ஏத்த, அருள்செய்த, / பீடு உடைய பிரமாபுரம் மேவிய, பெம்மான்-இவன் அன்றே!

Commentary sample:

> தோடுடையசெவியன் என்பது முதலாக உள்ளங்கவர்ந்த கள்வனுடைய சிறப்பியல்புகள் தெரிவிக்கப்பெறுகின்றன. பிள்ளையாருடைய அழுகைக் குரல் சென்று பரந்து திருமுலைப்பால் அருளச் செய்தது திருச்செவியாதலின் அதனை முதற்கண் தெரிவிக்கிறார். உலகுய...

### Sample 2: `thirumurai_01_paadal_1469`

- Thirumurai: `1`
- Thogupu: `thirumurai_01_thogupu_1663`
- Title: திருத்தருமபுரம் - யாழ்மூரி
- Thalam: திருத்தருமபுரம்
- Pann: யாழ்மூரி
- Song numbers: global `1469`, source `1469`, local `1469`, index `11`
- Commentary status: `success`
- Span count: `11`
- Source: https://www.tamilvu.org/slet/l4110/l4110son.jsp?subid=1663

Paadal:

> “பொன் நெடு நல் மணி மாளிகை சூழ் விழவம் மலீ / பொரூஉ புனல் திரூஉ அமர் புகலி” என்று உலகில் / தன்னொடு நேர் பிற இல் பதி ஞானசம்பந்தனது / செந்தமிழ்த் தடங்கல்-தருமபுரம்பதியைப் / பின் நெடுவார் சடையில் பிறையும் அரவும் உடையவன் / பிணைதுணை கழல்கள் பேணுதல் உரியார், / இன் ...

Commentary sample:

> ஞானசம்பந்தப் பெருமான் செந்தமிழால் திருத் தருமபுரப் பதியில் எழுந்தருளியிருக்கின்ற இறைவன் கழல்களைப் பேணுதல் உரியார் நல்லுலகம் எய்துவர்; போகம் பெறுவர்; இடரும் பிணியும் எய்தப்பெறார் என்கின்றது. விழவம் மலீ - விழாக்கள் நிறை...

### Sample 3: `thirumurai_02_paadal_1470`

- Thirumurai: `2`
- Thogupu: `thirumurai_02_thogupu_1664`
- Title: திருப்பூந்தராய் - வினா உரை - இந்தளம்
- Thalam: திருப்பூந்தராய்
- Pann: இந்தளம்
- Song numbers: global `1470`, source `1470`, local `1470`, index `1`
- Commentary status: `success`
- Span count: `7`
- Source: https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1664

Paadal:

> செந்நெல் அம் கழனிப் பழனத்து / அயலே செழும் / புன்னை வெண் கிழியில் பவளம் புரை பூந்தராய் / துன்னி, நல் இமையோர் முடி தோய் கழலீர்! சொலீர் / பின்னுசெஞ்சடையில் பிறை பாம்புஉடன் வைத்ததே?

Commentary sample:

> திருஞான சம்பந்த மூர்த்தி நாயனார் இத்திருப்பதிகம் முதலாக நான்கு பதிகத்தில், சிவபெருமானை முன்னிலையிற் பெற்று, வினாவுதலும் விடைகூறியருள வேண்டுதலும் அமையப் பாடியிருத்தல்பற்றி, இவற்றை ‘வினாவுரை’ என்றனர். இத் தலைப்புடைய பிற...

### Sample 4: `thirumurai_02_paadal_2800`

- Thirumurai: `2`
- Thogupu: `thirumurai_02_thogupu_1785`
- Title: திருப்புகலி - செவ்வழி
- Thalam: திருப்புகலி
- Pann: செவ்வழி
- Song numbers: global `2800`, source `2800`, local `2800`, index `10`
- Commentary status: `success`
- Span count: `6`
- Source: https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1785

Paadal:

> எய்த ஒண்ணா இறைவன் உறைகின்ற புகலியை, / கைதவம் இல்லாக் கவுணியன் ஞானசம்பந்தன் சீர் / செய்த பத்தும்(ம்) இவை செப்ப வல்லார், சிவலோகத்தில் / எய்தி, நல்ல இமையோர்கள் ஏத்த, இருப்பார்களே.

Commentary sample:

> எய்த ஒண்ணா இறைவன்-பாசஞானத்தாலும் பசுஞானத்தாலுூம பார்ப்பரிய பரம்பரன்! (சித்தியார் சூ.9) “ இமையோர் கூட்டம் எய்துமாறு அறியாத எந்தர்” (திருவாசகம். திருச்சதகம். 25) உறைகின்ற-திருக்கோயில்கொண்டு (கடல் கொண்ட கடை நாளிலும்) அடி...

### Sample 5: `thirumurai_03_paadal_2801`

- Thirumurai: `3`
- Thogupu: `thirumurai_03_thogupu_1786`
- Title: கோயில் - காந்தாரபஞ்சமம்
- Thalam: கோயில்
- Pann: காந்தாரபஞ்சமம்
- Song numbers: global `2801`, source `2801`, local `2801`, index `1`
- Commentary status: `success`
- Span count: `9`
- Source: https://www.tamilvu.org/slet/l4130/l4130son.jsp?subid=1786

Paadal:

> ஆடினாய், நறுநெய்யொடு, பால், தயிர்! அந்தணர் பிரியாத / சிற்றம்பலம் / நாடினாய், இடமா! நறுங்கொன்றை நயந்தவனே! / பாடினாய், மறையோடு பல்கீதமும்! பல்சடைப் பனி கால் கதிர் / வெண்திங்கள் / சூடினாய்! அருளாய், சுருங்க எம தொல்வினையே! / 1

Commentary sample:

> எல்லாத் தலங்களுள்ளும் ஓர் ஆண்டிற்குள் ஆறு நாள் அபிடேக விசேடமுடைய தம் சிதம்பரமேயாதலின் “ஆடினாய்” என்பது திருநடனத்தையும் கருதிய தொடக்கம் உடையதாகி நின்றது. தில்லைவாழ் அந்தணருள் நடராசப்பிரானாரும் ஒருவராதலின், பிரியாமை பிர...

### Sample 6: `thirumurai_03_paadal_4158`

- Thirumurai: `3`
- Thogupu: `thirumurai_03_thogupu_1911`
- Title: திருவிடைவாய்
- Thalam: திருவிடைவாய்
- Pann: 
- Song numbers: global `4158`, source `4158`, local `4158`, index `11`
- Commentary status: `partial_commentary`
- Span count: `6`
- Source: https://www.tamilvu.org/slet/l4130/l4130son.jsp?subid=1911

Paadal:

> ஆறும் மதியும் பொதி வேணியன் ஊர் ஆம் / மாறு இல் பெருஞ் செல்வம் மலி விடைவாயை, / நாறும் பொழில் காழியர் ஞானசம்பந்தன் / கூறும் தமிழ் வல்லவர், குற்றம் அற்றோரே. / 11

Commentary sample:

> கங்கை, பிறை ஆகியவற்றைச் சூடிய சடைமுடியை உடைய சிவபெருமானது ஊராகிய செல்வம் நிறைந்த திருவிடைவாயை, பொழில் சூழ்ந்த காழியில் தோன்றிய ஞானசம்பந்தன் போற்றிப் பரவிய இத்தமிழ் மாலையை ஓதி வழிபட வல்லவர் குற்றமற்றவராவர். திருஞானசம்ப...

### Sample 7: `thirumurai_04_paadal_1`

- Thirumurai: `4`
- Thogupu: `thirumurai_04_thogupu_1912`
- Title: திருஅதிகைவீரட்டானம் - கொல்லி
- Thalam: திருஅதிகைவீரட்டானம்
- Pann: கொல்லி
- Song numbers: global `1`, source `1`, local `1`, index `1`
- Commentary status: `partial_commentary`
- Span count: `5`
- Source: https://www.tamilvu.org/slet/l4140/l4130son.jsp?subid=1912

Paadal:

> கூற்று ஆயின ஆறு விலக்ககிலீர்-கொடுமைபல செய்தன நான் அறியேன்; / ஏற்றாய்! அடிக்கே இரவும் பகலும் பிரியாது வணங்குவன், எப்பொழுதும்; / தோற்றாது என் வயிற்றின் அகம்படியே குடரோடு துடக்கி முடக்கியிட, / ஆற்றேன், அடியேன்:-அதிகைக் கெடில வீரட்டானத்து உறை அம்மானே!

Commentary sample:

> கெடில ஆற்றின் வடகரையில்விளங்கும் திருவதிகை என்னும் வீரட்டானத் திருப்பதியில் உகந்தெழுந்தருளியிருக்கும் தலைவனே! யான் இப்பிறப்பில் என் அறிவு அறியப் பல கொடுஞ் செயல்களைச் செய்தேனாக எனக்குத் தோன்றவில்லை. அவ்வாறாகச் சூலைநோய்...

### Sample 8: `thirumurai_04_paadal_1070`

- Thirumurai: `4`
- Thogupu: `thirumurai_04_thogupu_2024`
- Title: தனி - திருவிருத்தம்
- Thalam: தனி
- Pann: திருவிருத்தம்
- Song numbers: global `1070`, source `1070`, local `1070`, index `11`
- Commentary status: `success`
- Span count: `6`
- Source: https://www.tamilvu.org/slet/l4140/l4130son.jsp?subid=2024

Paadal:

> மேலும் அறிந்திலன், நான்முகன் மேல் சென்று; கீழ் இடந்து / மாலும் அறிந்திலன்; மால் உற்றதே; வழிபாடு செய்யும் / பாலன் மிசைச் சென்று பாசம் விசிறி மறிந்த சிந்தைக் / காலன் அறிந்தான், அறிதற்கு அரியான் கழல் அடியே!

Commentary sample:

> தி.8 திருவாசகம் 3:- 50; 4:- 1-10; நான்முகன் அன்னப் புள்ளுருக்கொண்டு மேற்சென்று பறந்து தேடியலைந்து மேலும் அறிந்திலன். மாலும் பன்றியுருக்கொண்டு கீழிடந்து கீழும் அறிந்திலன். மேலும் என்றதால் கீழும் என வருவித்துரைக்கப்பட்ட...

### Sample 9: `thirumurai_05_paadal_1071`

- Thirumurai: `5`
- Thogupu: `thirumurai_05_thogupu_2025`
- Title: கோயில் - திருக்குறுந்தொகை
- Thalam: கோயில்
- Pann: திருக்குறுந்தொகை
- Song numbers: global `1071`, source `1071`, local `1071`, index `1`
- Commentary status: `success`
- Span count: `7`
- Source: https://www.tamilvu.org/slet/l4150/l4150son.jsp?subid=2025

Paadal:

> அன்னம் பாலிக்கும் தில்லைச் சிற்றம்பலம் / பொன்னம் பாலிக்கும்; / மேலும், இப் பூமிசை / என் நம்பு ஆலிக்கும் ஆறு கண்டு, இன்பு உற / இன்னம் பாலிக்குமோ, இப் பிறவியே?

Commentary sample:

> அன்னம் - வீட்டின்பம். "பாதகமே சோறு பற்றினவா தோணோக்கம்" என்னும் திருவாசகத்தில் சோறு என்பது பேரின்பம் என்னும் பொருள் பயத்தல் காண்க. கடவுளை அன்னம் (அமுதம்) என்னும் சொல்லால் குறித்தலுமுண்டு. தான் இறவாதுநின்று பிறர் இறப்பை...

### Sample 10: `thirumurai_05_paadal_2085`

- Thirumurai: `5`
- Thogupu: `thirumurai_05_thogupu_2110`
- Title: பொது - ஆதிபுராணத் திருக்குறுந்தொகை
- Thalam: பொது
- Pann: ஆதிபுராணத் திருக்குறுந்தொகை
- Song numbers: global `2085`, source `2085`, local `2085`, index `10`
- Commentary status: `success`
- Span count: `6`
- Source: https://www.tamilvu.org/slet/l4150/l4150son.jsp?subid=2110

Paadal:

> அரக்கன் வல் அரட்டு ஆங்கு ஒழித்து, ஆர் அருள் / பெருக்கச் செய்த பிரான் பெருந்தன்மையை / அருத்தி செய்து அறியப் பெறுகின்றிலர்- / கருத்து இலாக் கயக்கவணத்தோர்களே.

Commentary sample:

> அரட்டு - துட்டச்செயல். அருத்தி - அன்பு. கயவக் கணம் - கீழ்மக்கட்கூட்டம்.

### Sample 11: `thirumurai_06_paadal_1`

- Thirumurai: `6`
- Thogupu: `thirumurai_06_thogupu_2111`
- Title: கோயில் - பெரிய திருத்தாண்டகம்
- Thalam: கோயில்
- Pann: பெரிய திருத்தாண்டகம்
- Song numbers: global `1`, source `1`, local `1`, index `1`
- Commentary status: `success`
- Span count: `10`
- Source: https://www.tamilvu.org/slet/l4160/l4160son.jsp?subid=2111

Paadal:

> அரியானை, அந்தணர் தம் சிந்தை யானை, / அருமறையின் அகத்தானை, அணுவை, யார்க்கும் / தெரியாத தத்துவனை, தேனை, பாலை, திகழ் ஒளியை, / தேவர்கள்தம் கோனை, மற்றைக் / கரியானை, நான்முகனை, கனலை, காற்றை, / கனைகடலை, குலவரையை, கலந்து நின்ற / பெரியானை, பெரும்பற்றப்புலியூரானை,-பேச...

Commentary sample:

> அரியான் - புறப்பொருளை அறியும் கருவியறிவினாலும், தன்னையறியும் உயிரறிவினாலும் அறிய வாராதவன். 'அந்தணர்' என்றது, ஈண்டுத் தில்லைவாழ் அந்தணரை. 'அந்தணர்தம் சிந்தை யானை' என்றது, அரியானாகிய அவன், எளியனாய்நிற்கும் முறைமையை அருள...

### Sample 12: `thirumurai_06_paadal_981`

- Thirumurai: `6`
- Thogupu: `thirumurai_06_thogupu_2209`
- Title: திருப்புகலூர் - திருத்தாண்டகம்
- Thalam: திருப்புகலூர்
- Pann: திருத்தாண்டகம்
- Song numbers: global `981`, source `981`, local `981`, index `10`
- Commentary status: `success`
- Span count: `10`
- Source: https://www.tamilvu.org/slet/l4160/l4160son.jsp?subid=2209

Paadal:

> ஒருவரையும் அல்லாது உணராது, உள்ளம்; / உணர்ச்சித் தடுமாற்றத்துள்ளே நின்ற / இருவரையும் மூவரையும் என்மேல் ஏவி, இல்லாத / தரவு அறுத்தாய்க்கு இல்லேன்; ஏலக் / கருவரை சூழ் கானல் இலங்கை வேந்தன் கடுந் தேர் / மீது ஓடாமைக் காலால் செற்ற / பொரு வரையாய்! உன் அடிக்கே போதுகி...

Commentary sample:

> "ஒருவனை" என்பதில் ஐ, முன்னிலை விகுதி; அன், சாரியை. தடுமாற்றத்து - கலக்கத்தையுடைய; என்றது, 'கலக்கத்தைச் செய்கின்ற' என்றபடி. 'தடுமாற்றத்து இருவரையும் மூவரையும்' என இயையும். "உள்ளே நின்ற" என்றது, 'புலனாகாது அருவாய் நின்ற...

### Sample 13: `thirumurai_07_paadal_440`

- Thirumurai: `7`
- Thogupu: `thirumurai_07_thogupu_2211`
- Title: திருப்பரங்குன்றம் - இந்தளம்
- Thalam: திருப்பரங்குன்றம்
- Pann: இந்தளம்
- Song numbers: global `440`, source `440`, local `1`, index `1`
- Commentary status: `partial_commentary`
- Span count: `7`
- Source: https://www.tamilvu.org/slet/l4170/l4170son.jsp?subid=2211

Paadal:

> கோத்திட்டையும் கோவலும் கோவில் கொண்டீர்; உம்மைக் கொண்டு உழல்கின்றது ஓர், / கொல்லைச் சில்லை, / சே, திட்டுக் குத்தித் தெருவே திரியும்; சில் பூதமும் நீரும் திசை திசையன; / சோத்திட்டு விண்ணோர் பலரும் தொழ, நும் அரைக் கோவணத்தோடு ஒரு தோல் புடை / சூழ்ந்து, / ஆர்த்திட...

Commentary sample:

> இறைவரே, நீர், பெரிய மலையையும், சுரத்தையும் கோயிலாகக் கொண்டுள்ளீர். உம்மைச் சுமந்து கொண்டு திரிகின்ற முல்லை நிலத்து இளைய ஓர் எருது. மண்மேடுகளைத் தன் கொம்பால் குத்தித் தெருவில் துள்ளித் திரியும். சில பூதங்களும், அவற்றின...

### Sample 14: `thirumurai_07_paadal_1284`

- Thirumurai: `7`
- Thogupu: `thirumurai_07_thogupu_2309`
- Title: திருநொடித்தான்மலை - பஞ்சமம்
- Thalam: திருநொடித்தான்மலை
- Pann: பஞ்சமம்
- Song numbers: global `1284`, source `1284`, local `10`, index `10`
- Commentary status: `success`
- Span count: `6`
- Source: https://www.tamilvu.org/slet/l4170/l4170son.jsp?subid=2309

Paadal:

> ஊழிதொறு ஊழி முற்றும்(ம்) உயர் பொன் நொடித்தான்மலையை, / சூழ் இசை இன் கரும்பின் சுவை நாவல ஊரன் சொன்ன, / ஏழ் இசை இன் தமிழால் இசைந்து ஏத்திய பத்தினையும், / ஆழி-கடல்(ல்) அரையா! அஞ்சையப்பர்க்கு அறிவிப்பதே!

Commentary sample:

> 'திருக்கயிலை மலை, உலகமெல்லாம் அழிகின்ற ஒவ்வோர் ஊழியிலும் ஓங்கி உயர்வது' என்பது, இத்திருப்பாடலில் குறிக்கப்பட்டிருத்தல் அறியத்தக்கது. "நாவல்" என்ற அகரம் சாரியை. "அறிவிப்பது" என்பது, தொழிற்பெயர். அதன்பின், 'வேண்டும்' என...

### Sample 15: `thirumurai_08_paadal_1`

- Thirumurai: `8`
- Thogupu: `thirumurai_08_thogupu_2310`
- Title: சிவபுராணம்
- Thalam: சிவபுராணம்
- Pann: 
- Song numbers: global `1`, source `1`, local `நமச்சிவாய`, index `1`
- Commentary status: `partial_commentary`
- Span count: `5`
- Source: https://www.tamilvu.org/slet/l4180/l4180son.jsp?subid=2310

Paadal:

> நமச்சிவாய வாஅழ்க! நாதன் தாள் வாழ்க! / இமைப் பொழுதும் என் நெஞ்சில் நீங்காதான் தாள் வாழ்க! / கோகழி ஆண்ட குருமணி தன் தாள் வாழ்க! / ஆகமம் ஆகிநின்று அண்ணிப்பான் தாள் வாழ்க! / ஏகன், அநேகன், இறைவன், அடி வாழ்க!

### Sample 16: `thirumurai_08_paadal_782`

- Thirumurai: `8`
- Thogupu: `thirumurai_08_thogupu_2369`
- Title: அச்சோப் பதிகம்
- Thalam: அச்சோப் பதிகம்
- Pann: 
- Song numbers: global `782`, source `782`, local `செம்மை`, index `9`
- Commentary status: `partial_commentary`
- Span count: `4`
- Source: https://www.tamilvu.org/slet/l4180/l4180son.jsp?subid=2369

Paadal:

> செம்மை நலம் அறியாத சிதடரொடும் திரிவேனை, / மும்மை மலம் அறுவித்து, முதல் ஆய முதல்வன் தான் / நம்மையும் ஓர் பொருள் ஆக்கி, நாய் சிவிகை ஏற்றுவித்த / அம்மை எனக்கு அருளிய ஆறு, ஆர் பெறுவார்? அச்சோவே!

### Sample 17: `thirumurai_01_paadal_475`

- Thirumurai: `1`
- Thogupu: `thirumurai_01_thogupu_1572`
- Title: திருப்பாச்சிலாச்சிராமம் - தக்கராகம்
- Thalam: திருப்பாச்சிலாச்சிராமம்
- Pann: தக்கராகம்
- Song numbers: global `475`, source `475`, local `475`, index `6`
- Commentary status: `partial_commentary`
- Span count: `4`
- Source: https://www.tamilvu.org/slet/l4110/l4110son.jsp?subid=1572

Paadal:

> நீறு மெய் பூசி, நிறை சடை தாழ, நெற்றிக்கண்ணால் உற்று நோக்கி, / ஆறுஅது சூடி, ஆடு அரவு ஆட்டி, ஐவிரல் கோவண ஆடை / பால் தரு மேனியர்; தத்தர்; பாச்சிலாச்சிராமத்து உறைகின்ற / ஏறு அது ஏறியர்; ஏழையை வாட இடர் செய்வதோ இவர் ஈடே?

### Sample 18: `thirumurai_01_paadal_950`

- Thirumurai: `1`
- Thogupu: `thirumurai_01_thogupu_1616`
- Title: திருஆப்பனூர் - குறிஞ்சி
- Thalam: திருஆப்பனூர்
- Pann: குறிஞ்சி
- Song numbers: global `950`, source `950`, local `950`, index `3`
- Commentary status: `success`
- Span count: `7`
- Source: https://www.tamilvu.org/slet/l4110/l4110son.jsp?subid=1616

Paadal:

> முருகு விரி குழலார் மனம் கொள் அநங்கனை முன் / பெரிதும் முனிந்து உகந்தான், பெருமான், பெருங்காட்டின் / அரவம் அணிந்தானை, அணி ஆப்பனூரானைப் / பரவும் மனம் உடையார் வினை / பற்று அறுப்பாரே.

Commentary sample:

> முருகு விரி குழலாள் - மணம் வீசும் கூந்தலையுடைய பெண்கள். அநங்கன் - மன்மதன்.

### Sample 19: `thirumurai_01_paadal_1424`

- Thirumurai: `1`
- Thogupu: `thirumurai_01_thogupu_1659`
- Title: திருவீழிமிழலை - மேகராகக்குறிஞ்சி
- Thalam: திருவீழிமிழலை
- Pann: மேகராகக்குறிஞ்சி
- Song numbers: global `1424`, source `1424`, local `1424`, index `9`
- Commentary status: `success`
- Span count: `11`
- Source: https://www.tamilvu.org/slet/l4110/l4110son.jsp?subid=1659

Paadal:

> செந்தளிர் மா மலரோனும் திருமாலும், / ஏனமொடு அன்னம் ஆகி, / அந்தம் அடி காணாதே, அவர் ஏத்த, வெளிப்பட்டோன் அமரும் / கோயில் / புந்தியின் நால்மறைவழியே புல் பரப்பி, நெய் சமிதை கையில் / கொண்டு, / வெந்தழலின் வேட்டு, உலகில் மிக அளிப்போர் சேரும் ஊர் / மிழலை / ஆமே.

Commentary sample:

> அயனும் மாலும், அன்னமும் ஏனமுமாகித் தேடியறிய முடியாது வணங்க வெளிபட்ட இறைவன்கோயில், வேதவிதிப்படி தருப்பையைப்பரப்பி, நெய் சமித்து இவைகளைக்கொண்டு வேள்வி செய்து, உலகைக்காக்கும் அந்தணர் வாழும் மிழலையாம் என்கின்றது. அந்தம் -...

### Sample 20: `thirumurai_02_paadal_1898`

- Thirumurai: `2`
- Thogupu: `thirumurai_02_thogupu_1703`
- Title: திருப்பிரமபுரம் - சீகாமரம்
- Thalam: திருப்பிரமபுரம்
- Pann: சீகாமரம்
- Song numbers: global `1898`, source `1898`, local `1898`, index `4`
- Commentary status: `success`
- Span count: `8`
- Source: https://www.tamilvu.org/slet/l4120/l4120son.jsp?subid=1703

Paadal:

> சாம் நாள் இன்றி(ம்), மனமே! சங்கைதனைத் / தவிர்ப்பிக்கும் / கோன் ஆளும் திருவடிக்கே கொழு மலர் தூவு! / எத்தனையும் / தேன் ஆளும் பொழில் பிரமபுரத்து உறையும் தீவணனை, / நா, நாளும் நன்நியமம் செய்து, சீர் நவின்று ஏத்தே!

Commentary sample:

> சாம்நாள் இன்றி, இகரத்தைச்சுட்டாக்குதல் பொருந்தாது. சங்கை-சாகும் நாள் உண்டோ இன்றோ என்னும் சந்தேகம். தவிர்ப்பிக்கும்-தவிரப்போக்கும். கோன்-தலைவன் (சிவபிரான்) மேல் ‘திருவடியே’ என்றும் இங்கு, ‘திருவடிக்கே’ என்றும் அருளியதை...


## Source Numbering Anomalies For Manual Review

### Thirumurai 7 source song `1020`

- `thirumurai_07_paadal_1020` local `7` index `7`: மணி கெழு செவ்வாய், வெண்நகை, கரிய வார்குழல், மா மயில் சாயல், / அணி கெழு கொங்கை, அம் கயல் கண்ணார் அரு நடம் ஆடல் அறாத / திணி பொழில் தழுவு திரு முல்லை வாயில் செல...
- `thirumurai_07_paadal_1020_2278_8` local `8` index `8`: நம்பனே! அன்று வெண்ணெய் நல்லூரில் நாயினேன் தன்னை ஆட்கொண்ட / சம்புவே! உம்பரார் தொழுது ஏத்தும் தடங்கடல் நஞ்சு உண்ட கண்டா! / செம்பொன் மாளிகை சூழ் திரு முல்லை வாய...

### Thirumurai 7 source song `1025`

- `thirumurai_07_paadal_1025` local `2` index `2`: மண்ணின் மேல் மயங்கிக் கிடப்பேனை வலிய வந்து என்னை ஆண்டுகொண்டானே! / கண் இலேன்; உடம்பில்(ல்) அடு நோயால் கருத்து அழிந்து, உனக்கே பொறை ஆனேன்; / தெண் நிலா எறிக்கும...
- `thirumurai_07_paadal_1025_2279_3` local `3` index `3`: ஒப்பு இலாமுலையாள் ஒருபாகா! உத்தமா! மத்தம் ஆர் தரு சடையாய்! / முப்புரங்களைத் தீ வளைத்து அங்கே மூவருக்கு அருள் செய்ய வல்லானே! / செப்ப ஆல் நிழல் கீழ் இருந்து அர...

### Thirumurai 7 source song `1034`

- `thirumurai_07_paadal_1034` local `2` index `2`: சிகரத்து இடை இள வெண்பிறை வைத்தான் இடம், தெரியில் / முகரத்து இடை முத்தின்(ன்) ஒளி பவளத்திரள், ஓதம், / தகரத்து இடை தாழைத்திரள் ஞாழல்-திரள் நீழல், / மகரத்தொடு ச...
- `thirumurai_07_paadal_1034_2280_3` local `3` index `3`: அங்கங்களும் மறை நான்கு உடன் விரித்தான் இடம் அறிந்தோம் / தெங்கங்களும் நெடும் பெண்ணையும் பழம் வீழ் மணல் படப்பை, / சங்கங்களும் இலங்கு இப்பியும் வலம்புரிகளும் இட...

### Thirumurai 7 source song `1037`

- `thirumurai_07_paadal_1037` local `6` index `6`: அடல் விடையினன், மழுவாளினன், அலரால் அணி கொன்றைப் / படரும் சடைமுடி உடையவர்க்கு இடம் ஆவது பரவைக்- / கடல் இடை இடை கழி அருகினில் கடி நாறு தண் கைதை / மடல் இடை இடை ...
- `thirumurai_07_paadal_1037_2280_7` local `7` index `7`: முளை வளர் இளமதி உடையவன், முன் செய்த வல்வினைகள்- / களை களைந்து எனை ஆளல்(ல்) உறு கண்டன், இடம் செந்நெல் / வளை விளைவயல் கயல் பாய்தரு குண, வார் மணல், கடல் வாய் / ...

### Thirumurai 7 source song `1042`

- `thirumurai_07_paadal_1042` local `2` index `2`: புரம் அவை எரிதர வளைந்த வில்லினன், அவன்; / மர உரி புலி அதள் அரைமிசை மருவினன்; / அர உரி இரந்தவன், இரந்து உண விரும்பி நின்று; / இரவு எரி ஆடி தன் இடம் வலம்புரமே.
- `thirumurai_07_paadal_1042_2281_3` local `3` index `3`: நீறு அணி மேனியன், நெருப்பு உமிழ் அரவினன், / கூறு அணி கொடுமழு ஏந்தி(ய) ஒர் கையினன், / ஆறு அணி அவிர்சடை அழல் வளர் மழலை வெள்- / ஏறு அணி அடிகள் தம் இடம் வலம்புரமே.
