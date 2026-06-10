from .base_parser import BaseParser


class ProseParser(BaseParser):
    parser_family = "prose_parser"
    record_type = "prose_section"

    # TODO: add chapter, section, paragraph, page, footnote, and edition extraction.
