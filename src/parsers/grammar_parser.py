from .base_parser import BaseParser


class GrammarParser(BaseParser):
    parser_family = "grammar_parser"
    record_type = "grammar_rule"

    # TODO: separate sutra/rule text, explanation, examples, exceptions, and commentator.
