"""Java .properties file loader and label lookup.

Loads `fess_label.properties` (English fallback) and
`fess_label_<lang>.properties` (language-specific), then provides
a `get(key)` lookup with the precedence:

    lang-specific -> base -> default -> KeyError
"""

from pathlib import Path
from typing import Optional

from jproperties import Properties


class LabelStrings:
    def __init__(self, lang: str, label_dir: str):
        self._lang = lang
        base_path = Path(label_dir) / "fess_label.properties"
        lang_path = Path(label_dir) / f"fess_label_{lang}.properties"

        if not base_path.is_file():
            raise FileNotFoundError(
                f"Base label file not found: {base_path}")
        if not lang_path.is_file():
            raise FileNotFoundError(
                f"Language label file not found: {lang_path}")

        self._base = self._load(base_path)
        self._lang_map = self._load(lang_path)

    @staticmethod
    def _load(path: Path) -> dict:
        props = Properties()
        with open(path, "rb") as f:
            props.load(f, encoding="utf-8")
        return {key: props[key].data for key in props}

    def get(self, key: str, default: Optional[str] = None) -> str:
        if key in self._lang_map:
            return self._lang_map[key]
        if key in self._base:
            return self._base[key]
        if default is not None:
            return default
        raise KeyError(
            f"Label key not found in lang={self._lang} or base: {key}")

    def sizes(self) -> dict:
        return {"lang": len(self._lang_map), "base": len(self._base)}
