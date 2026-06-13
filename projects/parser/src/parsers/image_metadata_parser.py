from .base_parser import BaseParser


class ImageMetadataParser(BaseParser):
    parser_family = "image_metadata_parser"
    record_type = "manuscript_image"

    # TODO: preserve folio labels, captions, dimensions, rights, and OCR provenance.
