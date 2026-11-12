#!/usr/bin/env python3
"""Set the canonical build URL from GitHub Pages configuration."""

import argparse
import json
from pathlib import Path
import re
import tomllib
from urllib.parse import urlsplit


def configure(text: str, url: str) -> str:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https" or not parsed.hostname
        or parsed.username or parsed.password or parsed.query or parsed.fragment
        or any(character.isspace() for character in url)
    ):
        raise ValueError("Pages URL must be an absolute HTTPS URL without credentials, query, or fragment")
    url = url.rstrip("/") + "/"
    original = tomllib.loads(text)
    pattern = r'(?m)^site_url\s*=\s*[^\n]+$'
    updated, count = re.subn(pattern, lambda _: "site_url = " + json.dumps(url), text)
    if count != 1:
        raise ValueError("Expected exactly one site_url setting")
    expected = {**original, "project": {**original["project"], "site_url": url}}
    if tomllib.loads(updated) != expected:
        raise ValueError("Only project.site_url may change")
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url")
    parser.add_argument("--config", type=Path, default=Path("zensical.toml"))
    args = parser.parse_args()
    try:
        updated = configure(args.config.read_text(encoding="utf-8"), args.url)
        args.config.write_text(updated, encoding="utf-8")
    except (ValueError, KeyError, OSError) as error:
        parser.exit(1, f"Cannot configure Pages URL: {error}\n")


if __name__ == "__main__":
    main()
