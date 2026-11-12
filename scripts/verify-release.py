#!/usr/bin/env python3
"""Allow deployment only for the latest published stable release on main."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote


TAG = re.compile(r"v(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\Z")
SHA = re.compile(r"[0-9a-fA-F]{40}(?:[0-9a-fA-F]{24})?\Z")
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


def validate_release(
    tag: str,
    release: dict,
    latest: dict,
    local_sha: str,
    remote_sha: str,
    on_main: bool,
    expected_sha: str | None = None,
) -> str:
    """Validate observed metadata and refs without making external calls."""
    if not TAG.fullmatch(tag):
        raise ValueError("release tag must use stable vMAJOR.MINOR.PATCH syntax")
    for name, metadata in (("requested", release), ("latest", latest)):
        if metadata.get("draft") is not False or metadata.get("prerelease") is not False:
            raise ValueError(f"{name} release must be stable and published, not a draft or prerelease")
        published = metadata.get("published_at")
        if not isinstance(published, str) or not published.strip():
            raise ValueError(f"{name} release has not been published")
        if type(metadata.get("id")) is not int or metadata["id"] <= 0:
            raise ValueError(f"{name} release is missing a valid release ID")
        if metadata.get("tag_name") != tag:
            raise ValueError(f"{name} release does not match the requested tag")
    if release["id"] != latest["id"]:
        raise ValueError("requested release is no longer GitHub's latest stable release")
    if not all(isinstance(sha, str) and SHA.fullmatch(sha) for sha in (local_sha, remote_sha)):
        raise ValueError("release tag must resolve to full local and remote commit SHAs")
    if local_sha.lower() != remote_sha.lower():
        raise ValueError("release tag moved: local and remote commit SHAs differ")
    if expected_sha is not None:
        if not SHA.fullmatch(expected_sha) or expected_sha.lower() != local_sha.lower():
            raise ValueError("release commit differs from the commit used to build the artifact")
    if not on_main:
        raise ValueError("release commit is not an ancestor of origin/main")
    return local_sha.lower()


def gh_api(endpoint: str) -> dict:
    result = subprocess.run(
        ["gh", "api", endpoint], check=True, capture_output=True, text=True, timeout=15
    )
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise ValueError("GitHub returned an unexpected API response")
    return payload


def git_state(tag: str) -> tuple[str, bool]:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--end-of-options", f"refs/tags/{tag}^{{commit}}"],
        check=True, capture_output=True, text=True, timeout=5,
    )
    sha = result.stdout.strip()
    if not SHA.fullmatch(sha):
        raise ValueError("local release tag did not resolve to a full commit SHA")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", sha, "origin/main"],
        capture_output=True, text=True, timeout=5,
    )
    if ancestry.returncode not in (0, 1):
        raise ValueError("cannot compare release commit with origin/main; fetch complete history")
    return sha, ancestry.returncode == 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="published stable release tag, such as v1.0.0")
    parser.add_argument("--expected-sha", help="previously verified commit used to build the artifact")
    args = parser.parse_args(argv)
    try:
        if not TAG.fullmatch(args.tag):
            raise ValueError("release tag must use stable vMAJOR.MINOR.PATCH syntax")
        repository = os.environ.get("GITHUB_REPOSITORY", "")
        if not REPOSITORY.fullmatch(repository):
            raise ValueError("GITHUB_REPOSITORY must identify owner/repository")
        if not os.environ.get("GH_TOKEN"):
            raise ValueError("GH_TOKEN is required to verify the published release")
        encoded_tag = quote(args.tag, safe="")
        endpoint = f"repos/{repository}"
        release = gh_api(f"{endpoint}/releases/tags/{encoded_tag}")
        latest = gh_api(f"{endpoint}/releases/latest")
        remote = gh_api(f"{endpoint}/commits/{encoded_tag}")
        local_sha, on_main = git_state(args.tag)
        sha = validate_release(
            args.tag, release, latest, local_sha, remote.get("sha"), on_main, args.expected_sha
        )
        output_path = os.environ.get("GITHUB_OUTPUT")
        if output_path:
            with Path(output_path).open("a", encoding="utf-8") as output:
                output.write(f"sha={sha}\n")
        print(f"Verified published release {args.tag} at {sha}.")
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"Release verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
