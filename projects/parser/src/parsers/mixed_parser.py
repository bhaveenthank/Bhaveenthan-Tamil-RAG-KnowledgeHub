from .base_parser import BaseParser


class MixedParser(BaseParser):
    parser_family = "mixed_parser"
    record_type = "prose_section"

    # TODO: dispatch inspected source units without flattening verse/prose/media hierarchy.
