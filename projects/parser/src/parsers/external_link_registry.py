from .base_parser import BaseParser


class ExternalLinkRegistryParser(BaseParser):
    parser_family = "external_link_registry"
    record_type = "external_reference"

    # TODO: add institution, rights, robots, scope, and approval metadata before any crawl.
