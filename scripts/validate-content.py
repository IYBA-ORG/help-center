#!/usr/bin/env python3
"""Validate the help center's source structure without third-party dependencies.

Supports ordinary Markdown inline/reference links and HTML href/src attributes.
Fenced code and inline code are ignored. Zensical's strict build is responsible
for rendered Markdown semantics and heading-anchor validation.
"""

from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
import tomllib
from urllib.parse import unquote, urlsplit


REQUIRED_PAGES = (
    "index.md",
    "iyba/index.md",
    "yachtbroker/index.md",
    "boatdox/index.md",
    "support/index.md",
    "support/contact.md",
)
REQUIRED_FEATURES = {
    "navigation.tabs",
    "navigation.sections",
    "navigation.indexes",
    "navigation.top",
    "navigation.tracking",
    "search.highlight",
}
KEBAB = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
DESTINATION = r"(?:<([^>\n]+)>|([^\s<>]+))"
REFERENCE_DEFINITION = re.compile(r"^ {0,3}\[([^]\n]+)\]:\s*" + DESTINATION, re.M)
INLINE_LINK = re.compile(
    r"!?\[[^]\n]*\]\(\s*(?:<([^>\n]+)>|((?:[^\s()<>]|\([^()\n]*\))+))"
    r"(?:\s+[\"'][^\n]*?[\"'])?\s*\)"
)
REFERENCE_USE = re.compile(r"!?\[([^]\n]+)\]\[([^]\n]*)\]")


def prose_only(text: str) -> str:
    """Remove fenced code while preserving line boundaries."""
    result = []
    fence = None
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence is None and match:
            fence = match.group(1)
            result.append("")
        elif fence is not None:
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence):
                fence = None
            result.append("")
        else:
            result.append(line)
    return re.sub(r"(`+)[^`\n]*?\1", "", "\n".join(result))


class HTMLLinks(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.targets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name in {"href", "src"} and value is not None:
                self.targets.append(value)


def normalize_reference(label: str) -> str:
    return " ".join(label.split()).casefold()


def link_targets(text: str) -> tuple[list[str], list[str]]:
    """Return local/external targets and explicit undefined reference labels."""
    text = prose_only(text)
    definitions = {
        normalize_reference(match.group(1)): match.group(2) or match.group(3)
        for match in REFERENCE_DEFINITION.finditer(text)
    }
    targets = list(definitions.values())
    text = REFERENCE_DEFINITION.sub("", text)
    targets.extend(match.group(1) or match.group(2) for match in INLINE_LINK.finditer(text))
    undefined = []
    for match in REFERENCE_USE.finditer(text):
        label = normalize_reference(match.group(2) or match.group(1))
        if label not in definitions:
            undefined.append(label)
    # A shortcut is only a link when it has a matching definition. Otherwise it
    # is valid plain text (for example, a checklist or a bracketed UI label).
    for match in re.finditer(r"!?\[([^]\n]+)\](?![\[(])", text):
        label = normalize_reference(match.group(1))
        if label in definitions:
            targets.append(definitions[label])
    parser = HTMLLinks()
    parser.feed(text)
    targets.extend(parser.targets)
    return targets, undefined


def local_target(docs: Path, source: Path, target: str) -> Path | None:
    """Resolve an internal URL and reject targets outside the public docs tree."""
    target = target.strip()
    if not target:
        raise ValueError("empty link target")
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        if parsed.scheme not in {"", "https", "http", "mailto", "tel"}:
            raise ValueError(f"unsupported link scheme: {parsed.scheme}")
        return None
    path = unquote(parsed.path)
    if not path:
        return None  # The strict build validates fragments against rendered IDs.
    if "\\" in path:
        raise ValueError("use forward slashes in links")
    resolved = ((docs / path.lstrip("/")) if path.startswith("/") else source.parent / path).resolve()
    if not resolved.is_relative_to(docs):
        raise ValueError("link escapes the docs directory")
    if resolved.is_dir() or (not resolved.suffix and not resolved.exists()):
        resolved /= "index.md"
    return resolved


def navigation_paths(value: object, errors: list[str]) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result = []
        for item in value:
            result.extend(navigation_paths(item, errors))
        return result
    if isinstance(value, dict):
        if len(value) != 1:
            errors.append("Each navigation entry must have exactly one label")
        result = []
        for label, item in value.items():
            if not label.strip():
                errors.append("Navigation labels must not be empty")
            result.extend(navigation_paths(item, errors))
        return result
    errors.append("Navigation entries must be Markdown paths, lists, or labeled entries")
    return []


def validate(root: Path) -> list[str]:
    root = root.resolve()
    docs = (root / "docs").resolve()
    errors: list[str] = []
    if not docs.is_relative_to(root):
        return ["The docs directory must remain inside the repository"]
    try:
        config = tomllib.loads((root / "zensical.toml").read_text(encoding="utf-8"))
        project = config.get("project", {})
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return [f"Cannot read zensical.toml: {exc}"]
    if not isinstance(project, dict):
        return ["zensical.toml must define a [project] table"]
    for field in ("site_name", "site_url", "site_description"):
        if not isinstance(project.get(field), str) or not project[field].strip():
            errors.append(f"project.{field} must be a nonempty string")
    if isinstance(project.get("site_url"), str) and not project["site_url"].startswith("https://"):
        errors.append("project.site_url must use HTTPS")
    if project.get("docs_dir", "docs") != "docs":
        errors.append("project.docs_dir must be docs")
    theme = project.get("theme", {})
    if not isinstance(theme, dict):
        errors.append("project.theme must be a table")
        theme = {}
    if theme.get("language") != "en":
        errors.append("project.theme.language must be en")
    features = theme.get("features", [])
    if not isinstance(features, list) or not all(isinstance(item, str) for item in features):
        errors.append("project.theme.features must be a list of strings")
        features = []
    for feature in sorted(REQUIRED_FEATURES - set(features)):
        errors.append(f"Missing theme feature: {feature}")
    plugins = project.get("plugins", {})
    if isinstance(plugins, dict) and isinstance(plugins.get("search"), dict):
        if plugins["search"].get("enabled") is False:
            errors.append("Built-in search must remain enabled")
    extra_css = project.get("extra_css", [])
    if not isinstance(extra_css, list) or not all(isinstance(item, str) for item in extra_css):
        errors.append("project.extra_css must be a list of asset paths")
        extra_css = []
    for asset in [theme.get("logo"), theme.get("favicon"), *extra_css]:
        if asset and isinstance(asset, str):
            try:
                resolved = local_target(docs, docs / "index.md", asset)
                if resolved is not None and not resolved.is_file():
                    errors.append(f"Configured asset does not exist: {asset}")
            except ValueError as exc:
                errors.append(f"Invalid configured asset {asset!r}: {exc}")
    try:
        requirements = (root / "requirements.txt").read_text(encoding="utf-8")
        pins = [line.split("#", 1)[0].strip() for line in requirements.splitlines()]
        pins = [line for line in pins if re.match(r"zensical\b", line, re.I)]
        if len(pins) != 1 or not re.fullmatch(r"zensical==\d+\.\d+\.\d+", pins[0]):
            errors.append("requirements.txt must pin one exact Zensical release: zensical==X.Y.Z")
    except OSError as exc:
        errors.append(f"Cannot read requirements.txt: {exc}")
    for required in REQUIRED_PAGES:
        if not (docs / required).is_file():
            errors.append(f"Required page is missing: docs/{required}")
    nav = project.get("nav")
    if not isinstance(nav, list) or not nav:
        errors.append("project.nav must be a nonempty explicit navigation list")
        nav = []
    paths = navigation_paths(nav, errors)
    normalized_nav = []
    for path in paths:
        parsed = urlsplit(path)
        if parsed.scheme or parsed.netloc or path.startswith("/") or "\\" in path or parsed.query or parsed.fragment:
            errors.append(f"Navigation must use relative Markdown paths: {path}")
            continue
        candidate = (docs / unquote(path)).resolve()
        if not candidate.is_relative_to(docs) or candidate.suffix != ".md":
            errors.append(f"Invalid navigation path: {path}")
            continue
        normalized_nav.append(candidate)
        if not candidate.is_file():
            errors.append(f"Navigation page does not exist: {path}")
    for path, count in Counter(normalized_nav).items():
        if count > 1:
            errors.append(f"Page appears {count} times in navigation: {path.relative_to(docs)}")
    for page in sorted(docs.rglob("*.md")):
        relative = page.relative_to(docs)
        if not page.resolve().is_relative_to(docs):
            errors.append(f"Page escapes docs through a symlink: {relative}")
            continue
        if any(not KEBAB.fullmatch(part) for part in [*relative.parts[:-1], page.stem]):
            errors.append(f"Use lowercase kebab-case for Markdown paths: {relative}")
        if page.resolve() not in normalized_nav:
            errors.append(f"Page is missing from explicit navigation: {relative}")
        text = page.read_text(encoding="utf-8")
        front = re.match(r"\A---\s*\n(.*?)\n---[ \t]*(?:\n|$)", text, re.S)
        if not front:
            errors.append(f"{relative}: add YAML front matter with title and description")
            body = text
        else:
            for field in ("title", "description"):
                value = re.search(rf"^{field}:[ \t]*(.+)$", front.group(1), re.M)
                if not value or value.group(1).strip() in {"''", '""', "|", ">", "null", "~"} or value.group(1).lstrip().startswith("#"):
                    errors.append(f"{relative}: {field} must be a nonempty single-line YAML scalar")
            body = text[front.end():]
        if len(re.findall(r"^#\s+\S", prose_only(body), re.M)) != 1:
            errors.append(f"{relative}: include exactly one level-one Markdown heading")
        targets, undefined = link_targets(body)
        for label in undefined:
            errors.append(f"{relative}: undefined link reference [{label}]")
        for target in dict.fromkeys(targets):
            try:
                resolved = local_target(docs, page, target)
                if resolved is not None and not resolved.is_file():
                    errors.append(f"{relative}: missing internal target {target!r}")
            except ValueError as exc:
                errors.append(f"{relative}: invalid link {target!r}: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root)
    if errors:
        print("Content validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Content validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
