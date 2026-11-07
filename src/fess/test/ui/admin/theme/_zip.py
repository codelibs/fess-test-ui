"""Build theme ZIP archives in memory, so the tests need no fixture files."""
import io
import zipfile
from typing import Dict, Optional


def manifest(name: str, display_name: str = "E2E Theme", version: str = "1.0.0") -> str:
    # minFessVersion is left out: the archive must install on every Fess
    # line the theme screen exists on.
    return (
        "apiVersion: fess.codelibs.org/v1\n"
        "kind: StaticTheme\n"
        f"name: {name}\n"
        f'displayName: "{display_name}"\n'
        f'version: "{version}"\n'
        "entry: index.html\n"
        "spaFallback: true\n"
        "type: static\n"
    )


def theme_zip(name: str, marker: str, files: Optional[Dict[str, str]] = None,
              with_manifest: bool = True) -> bytes:
    """A minimal theme: theme.yml plus an index.html that carries `marker`."""
    entries = {"index.html": f"<!DOCTYPE html><html><head><title>{marker}</title></head>"
                             f"<body><p>{marker}</p></body></html>"}
    if with_manifest:
        entries["theme.yml"] = manifest(name)
    entries.update(files or {})
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, text in entries.items():
            zf.writestr(path, text)
    return buf.getvalue()
