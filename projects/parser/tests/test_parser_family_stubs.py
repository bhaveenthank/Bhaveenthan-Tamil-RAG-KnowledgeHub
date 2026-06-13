from parsers.base_parser import BaseParser, ParseContext, parser_for_family


FAMILIES = {
    "verse_parser": "verse",
    "prose_parser": "prose_section",
    "grammar_parser": "grammar_rule",
    "dictionary_parser": "dictionary_entry",
    "table_parser": "dictionary_entry",
    "image_metadata_parser": "manuscript_image",
    "mixed_parser": "prose_section",
    "external_link_registry": "external_reference",
}


def context(family: str) -> ParseContext:
    return ParseContext(
        category_id="sample",
        category_tamil="மாதிரி",
        parser_family=family,
        book_id="book_1",
        work_id="work_1",
        pilot_id="pilot_test",
    )


def test_parser_stubs_share_interface_and_schema() -> None:
    for family, record_type in FAMILIES.items():
        parser = parser_for_family(family)
        records = parser.parse(
            {
                "record_id": "native_1",
                "title": "தமிழ் மாதிரி",
                "content_text": "தமிழ் உள்ளடக்கம்",
                "source_url": "https://www.tamilvu.org/example",
            },
            context(family),
        )

        assert isinstance(parser, BaseParser)
        assert records[0]["schema_version"] == "website-corpus-v2"
        assert records[0]["record_type"] == record_type
        assert records[0]["parser_family"] == family


def test_parser_output_is_deterministic() -> None:
    parser = parser_for_family("grammar_parser")
    source = {
        "record_id": "rule_1",
        "content_text": "எழுத்து விதி",
        "source_url": "https://www.tamilvu.org/grammar/rule_1",
    }

    first = parser.parse(source, context("grammar_parser"))
    second = parser.parse(source, context("grammar_parser"))

    assert first == second
    assert first[0]["record_id"].startswith("tvu_sample_")


def test_verse_parser_preserves_commentary_separation() -> None:
    record = parser_for_family("verse_parser").parse(
        {
            "record_id": "verse_1",
            "verse_text": "பாடல் வரி",
            "pozhppurai": "பொழிப்புரை",
            "kurippurai": "குறிப்புரை",
            "source_url": "https://www.tamilvu.org/verse/1",
        },
        context("verse_parser"),
    )[0]

    assert record["content_text"] == "பாடல் வரி"
    assert record["verse_text"] == "பாடல் வரி"
    assert record["pozhppurai"] == "பொழிப்புரை"
    assert record["kurippurai"] == "குறிப்புரை"
    assert "பொழிப்புரை" in record["commentary_text"]
