"""Fess user-message lookup (validation/error text rendered by <la:errors>).

Loads `fess_message.properties` (English fallback) and
`fess_message_<lang>.properties`, with the same precedence as labels:

    lang-specific -> base -> default -> KeyError

Separate from LabelStrings because Fess keeps the two families in separate
files: a label names a UI element, a message is text Fess shows the user in
response to something. `scripts/extract_labels.sh` already copies both
families out of the Fess image, so no extraction change is needed.
"""

from fess.test.i18n.bundle import PropertiesBundle


class MessageStrings(PropertiesBundle):
    def __init__(self, lang: str, label_dir: str):
        super().__init__("fess_message", lang, label_dir)
