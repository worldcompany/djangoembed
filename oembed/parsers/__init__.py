from oembed.constants import OEMBED_TEXT_PARSER, OEMBED_HTML_PARSER
from oembed.utils import load_class


text_parser = load_class(OEMBED_TEXT_PARSER)
html_parser = load_class(OEMBED_HTML_PARSER)
