from tvu_scraper.text import normalize_tamil_text, tamil_ratio


def test_normalize_tamil_text_collapses_spaces() -> None:
    assert normalize_tamil_text(" திருப்புகழ்   \n\n  முருகா ") == "திருப்புகழ்\nமுருகா"


def test_tamil_ratio() -> None:
    assert tamil_ratio("திருப்புகழ் Muruga") >= 0.5
