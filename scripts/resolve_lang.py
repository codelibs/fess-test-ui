#!/usr/bin/env python3
"""Host-side language resolver.

Mirrors fess.test.i18n.select_language without importing it (the package
has a transitive jproperties dependency that the host may not have).
Reads TEST_LANG and TEST_LANG_SEED from the environment, prints the
resolved Fess locale to stdout.

Used by run_test.sh to:
  1. Pass an explicit lang into the container (instead of 'random')
  2. Export TEST_LANG_RESOLVED to $GITHUB_ENV for CI artifact naming
"""
import os
import random
import sys

SUPPORTED_LANGS = [
    "de", "en", "es", "fr", "hi", "id", "it", "ja", "ko",
    "nl", "pl", "pt_BR", "ru", "tr", "zh_CN", "zh_TW",
]


def main() -> int:
    env_value = (os.environ.get("TEST_LANG", "") or "").strip() or None
    seed_str = (os.environ.get("TEST_LANG_SEED", "") or "").strip()
    seed = int(seed_str) if seed_str else None

    if env_value in (None, "", "random"):
        rng = random.Random(seed) if seed is not None else random
        resolved = rng.choice(SUPPORTED_LANGS)
    elif env_value not in SUPPORTED_LANGS:
        print(
            f"ERROR: unsupported TEST_LANG={env_value!r}; "
            f"must be one of {SUPPORTED_LANGS} or 'random'",
            file=sys.stderr,
        )
        return 2
    else:
        resolved = env_value

    print(resolved)
    return 0


if __name__ == "__main__":
    sys.exit(main())
