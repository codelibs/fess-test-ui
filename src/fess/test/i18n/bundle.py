"""Java .properties bundle loader shared by the label and message catalogs.

Fess ships two parallel families of localized strings, both extracted into
the same directory by `scripts/extract_labels.sh`:

    fess_label.properties   / fess_label_<lang>.properties     -- UI labels
    fess_message.properties / fess_message_<lang>.properties    -- messages

They differ only in filename prefix, so both are loaded through this class.
Lookup precedence is:

    lang-specific -> base -> default -> KeyError
"""

from pathlib import Path
from typing import Optional

from jproperties import Properties


class PropertiesBundle:
    """A base + language-specific pair of Java .properties files."""

    def __init__(self, prefix: str, lang: str, label_dir: str):
        self._prefix = prefix
        self._lang = lang
        base_path = Path(label_dir) / f"{prefix}.properties"
        lang_path = Path(label_dir) / f"{prefix}_{lang}.properties"

        if not base_path.is_file():
            raise FileNotFoundError(
                f"Base {prefix} file not found: {base_path}")
        if not lang_path.is_file():
            raise FileNotFoundError(
                f"Language {prefix} file not found: {lang_path}")

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
            f"{self._prefix} key not found in lang={self._lang} or base: {key}")

    def sizes(self) -> dict:
        return {"lang": len(self._lang_map), "base": len(self._base)}
