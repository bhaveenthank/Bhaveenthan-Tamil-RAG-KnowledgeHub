from .base_parser import BaseParser


class TableParser(BaseParser):
    parser_family = "table_parser"
    record_type = "dictionary_entry"

    # TODO: preserve table headers, row/column identity, language, and domain labels.
