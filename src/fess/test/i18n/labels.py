"""Fess UI label lookup.

Loads `fess_label.properties` (English fallback) and
`fess_label_<lang>.properties` (language-specific), then provides
a `get(key)` lookup with the precedence:

    lang-specific -> base -> default -> KeyError
"""

from fess.test.i18n.bundle import PropertiesBundle


class LabelStrings(PropertiesBundle):
    def __init__(self, lang: str, label_dir: str):
        super().__init__("fess_label", lang, label_dir)
