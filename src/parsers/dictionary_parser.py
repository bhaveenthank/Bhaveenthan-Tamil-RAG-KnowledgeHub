from .base_parser import BaseParser


class DictionaryParser(BaseParser):
    parser_family = "dictionary_parser"
    record_type = "dictionary_entry"

    # TODO: separate headword, homonym, sense, part of speech, examples, and cross-references.
