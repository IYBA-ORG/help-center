#!/usr/bin/env python3
"""Enforce the repository's Conventional Commits subject policy (stdlib only)."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


TYPES = "feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert"
SUBJECT = re.compile(
    rf"^(?:{TYPES})(?:\([a-z0-9]+(?:-[a-z0-9]+)*\))?!?: \S[^\r\n]*$"
)
SHA = re.compile(r"[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?\Z")
MAX_LENGTH = 100


def validate_subject(subject: str) -> list[str]:
    """Return every applicable subject error; do not exempt merge/bot commits."""
    errors = []
    if not SUBJECT.fullmatch(subject):
        errors.append("expected type(scope): description; scope is optional and kebab-case")
    if len(subject) > MAX_LENGTH:
        errors.append(f"subject exceeds {MAX_LENGTH} characters")
    if subject != subject.strip():
        errors.append("subject must not have leading or trailing whitespace")
    if any(ord(character) < 32 or ord(character) == 127 for character in subject):
        errors.append("subject must not contain control characters")
    return errors


def git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout


def resolve_commit(repo: Path, revision: str) -> str:
    if not revision or revision.startswith("-"):
        raise ValueError("revision must be a nonempty Git revision, not an option")
    return git(repo, "rev-parse", "--verify", "--end-of-options", revision + "^{commit}").strip()


def range_subjects(repo: Path, revision_range: str) -> list[tuple[str, str]]:
    if revision_range.count("..") != 1 or "..." in revision_range:
        raise ValueError("range must be BASE..HEAD")
    base, head = revision_range.split("..")
    base_sha = resolve_commit(repo, base)
    head_sha = resolve_commit(repo, head)
    output = git(repo, "log", "--format=%H%x00%s", f"{base_sha}..{head_sha}", "--")
    commits = [tuple(line.split("\0", 1)) for line in output.splitlines()]
    if not commits:
        raise ValueError("commit range is empty; refusing to report an unchecked range as valid")
    return commits


def event_subjects(repo: Path, event_file: Path) -> list[tuple[str, str]]:
    event = json.loads(event_file.read_text(encoding="utf-8"))
    pull_request = event["pull_request"]
    title = pull_request["title"]
    if not isinstance(title, str):
        raise ValueError("pull request title must be text")
    base = pull_request["base"]["sha"]
    head = pull_request["head"]["sha"]
    if not all(isinstance(value, str) and SHA.fullmatch(value) for value in (base, head)):
        raise ValueError("pull request base and head must be full commit SHAs")
    return [("pull request title", title), *range_subjects(repo, f"{base}..{head}")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="Git checkout to inspect")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--message-file", type=Path, help="commit-msg hook message file")
    source.add_argument("--range", dest="revision_range", help="inspect every commit in BASE..HEAD")
    source.add_argument("--event-file", type=Path, help="GitHub pull_request event JSON")
    source.add_argument("--title", help="validate one subject or PR title")
    args = parser.parse_args(argv)

    try:
        if args.message_file is not None:
            lines = args.message_file.read_text(encoding="utf-8").splitlines()
            subjects = [("commit message", lines[0] if lines else "")]
        elif args.revision_range is not None:
            subjects = range_subjects(args.repo, args.revision_range)
        elif args.event_file is not None:
            subjects = event_subjects(args.repo, args.event_file)
        else:
            subjects = [("subject", args.title)]
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"Cannot validate commits: {error}", file=sys.stderr)
        return 1

    failed = False
    for label, subject in subjects:
        errors = validate_subject(subject)
        if errors:
            failed = True
            # JSON quoting keeps untrusted titles from injecting terminal control characters.
            print(f"Invalid {label}: {json.dumps(subject, ensure_ascii=True)}", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
    if failed:
        print("See CONTRIBUTING.md. Example: docs(boatdox): add deal overview", file=sys.stderr)
        return 1
    print(f"Conventional Commits: {len(subjects)} subject(s) passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
