from .base_parser import BaseParser


class VerseParser(BaseParser):
    parser_family = "verse_parser"
    record_type = "verse"

    # TODO: add source-specific stanza, meter, poet, thinai, and commentary boundaries.
