# Contributing to the IYBA Help Center

**Conventional Commits are required for every commit and every pull request
title.** This applies to documentation, code, assets, automation, dependency
updates, and reverts. The automated check rejects nonconforming messages.

## Commit and pull request policy

Use [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/):

```text
type(optional-scope): concise description
```

- Allowed types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`,
  `build`, `ci`, `chore`, and `revert`.
- A scope is optional. If present, use lowercase kebab-case, for example
  `iyba`, `yachtbroker`, `boatdox`, `support`, or `deployment`.
- Use exactly one space after the colon and a nonempty description.
- Keep the entire first line at 100 characters or fewer, with no leading or
  trailing whitespace. Use an imperative description such as “add” or “correct”.
- Mark breaking changes with `!` before the colon and/or explain them in a
  `BREAKING CHANGE:` footer. Bodies and footers may span additional lines.
- Automatic merge messages, default `Revert "..."` messages, and bot commits
  have no exemption. Use a conventional `revert: ...` subject for a revert.

Examples:

```text
docs(boatdox): add verified signing instructions
fix(navigation): restore membership guide link
ci: validate documentation before deployment
feat(yachtbroker)!: reorganize listing guides
revert: restore previous support navigation
```

`Update docs`, `WIP`, and `Fixed typo` are invalid commit subjects and PR titles.
Use `docs: correct membership terminology` instead.

Enable the local hook once per clone (Python 3.11+ is required):

```bash
git config core.hooksPath .githooks
```

The `commit-msg` hook checks messages before the commit is created. A local hook
can be bypassed, so it is not the authoritative enforcement mechanism. The
**Conventional commits** CI job checks the PR title and **every commit added by
the PR**, using the checker from the target branch. Editing the PR title reruns
the check. Renaming only the PR does not repair invalid commits.

Check a title or branch locally:

```bash
python3 scripts/validate-commits.py --title 'docs(iyba): update membership guide'
python3 scripts/validate-commits.py --range origin/main..HEAD
```

For the most recent unpushed commit, use `git commit --amend` to correct its
message. Coordinate changes to shared history with its contributors.
When updating a feature branch from `main`, rebase it; a generated merge commit
would fail the same subject check.

Use **Rebase and merge** so the checked commit subjects are preserved on `main`.
Squash merging is disabled because its final subject can be edited after CI;
merge commits are disabled because their generated messages break this policy.
Repository maintainers must activate the
[main ruleset](.github/rulesets/main.json) and configure rebase-only merging as
described in [deployment setup](maintenance/deployment.md). Until that remote
setup is applied, CI reports failures but GitHub does not necessarily block a
merge. The ruleset requires both checks and one approving review.

## Local setup

Use Python 3.11 or newer. Run these commands from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
git config core.hooksPath .githooks
```

Installation can take 1–3 minutes. The pinned Zensical release is intentional;
upgrade it in a separate reviewed change. No Node dependency is required to
author or build the documentation locally.

## Add or update an article

1. Create a short-lived branch from current `main`.
2. Choose the appropriate product and category under `docs/`.
3. Copy [the article template](templates/article.md) into that category, or use
   the [category](templates/category.md) or [FAQ](templates/faq.md) template.
4. Replace every template instruction with verified, customer-facing content.
5. Add the page to the explicit `nav` in `zensical.toml` and its category index.
6. Validate and preview the change, then open a pull request with a conventional
   title and describe how the product behavior was verified.
7. Obtain a product-knowledgeable review and pass both required checks before
   merging. A merge to `main` updates the pending release; it does not deploy.
   Publication happens only after a stable GitHub release is made.

During phases 1 and 2, article pages intentionally say **Guide in preparation**.
They reserve the proposed structure and URLs; they do not establish that the
described feature exists. Replace a placeholder only after checking the actual
product and obtaining review. Phase 3 owns verified instructions/screenshots.

## Release workflow

Release Please reads Conventional Commits on `main` and creates or updates a
release PR, normally titled `chore(main): release 1.0.0`. It maintains
`version.txt`, `.release-please-manifest.json`, and `CHANGELOG.md`. The initial
release is `v1.0.0`; subsequent documentation-only changes can produce patch
releases, features produce minor releases, and breaking changes produce major
releases.

Review the generated changelog and version, obtain the required approval, and
use **Rebase and merge** when the checks pass. Keep the release PR as the bot's
single commit: let Release Please refresh it when `main` advances, rather than
adding manual commits or merging `main` into that branch. Correct content in an
ordinary PR first so the bot includes the correction in the release.

The workflow uses `GITHUB_TOKEN`. GitHub may show an **Approve workflows to run**
banner on the bot's PR; a contributor with write access must approve those runs
before the required checks can complete. Do not bypass the checks. A successful
release PR merge lets Release Please publish a stable GitHub release and then
deploy its tagged commit to Pages. Drafts and prereleases do not deploy. See
[deployment setup](maintenance/deployment.md) for the release and recovery steps.

## Content and file conventions

- Write for customers. Use short sentences and the current product's UI labels.
- Use lowercase kebab-case for all published filenames and directories, such as
  `docs/boatdox/deals/creating-a-deal.md`.
- Include `title` and `description` front matter and exactly one `#` heading.
  Use the product name in article titles to distinguish global search results.
- Instructional articles use: Before You Begin, Steps, Expected Result,
  Troubleshooting, and Related Articles. Explain prerequisites and permissions.
- Keep product documentation under `docs/iyba/`, `docs/yachtbroker/`, or
  `docs/boatdox/`; shared support belongs under `docs/support/`.
- Link to other pages using relative `.md` paths. Keep URLs stable; plan
  redirects with a maintainer before moving or renaming published articles.
- Keep templates and internal maintenance instructions **outside `docs/`**.
  Everything in `docs/` can be published. Hiding a page from navigation or
  search does not make it private.
- Avoid custom JavaScript, theme overrides, and new dependencies unless needed
  for a reviewed requirement.

## Screenshots, logos, and media

Store product images in `docs/assets/<product>/` and shared branding in
`docs/assets/branding/`. Use descriptive kebab-case names, meaningful alternative
text, and optimized PNG or WebP files. Capture the current product UI with sample
data; remove personal information, tokens, confidential documents, and internal
URLs. Keep images below 1 MB where practical and do not commit large video files.
Embed videos only from an approved provider. See [asset provenance](maintenance/assets.md)
before replacing existing logos.

## Validation and preview

Fast structural checks (normally under a few seconds):

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/validate-content.py
```

Build and run an interactive local preview after installing dependencies:

```bash
source .venv/bin/activate
zensical build --strict
zensical serve
```

The first build can take 1–2 minutes; `serve` runs until stopped with Ctrl-C.
Open the local URL printed by Zensical. Check the homepage cards, each product's
sidebar, light/dark modes, narrow-screen navigation, and global search. Search
for “membership”, “vessel”, and “deal”, and follow each result. The build should
exit successfully with no invalid local links or anchors and produce `site/index.html`.

The content validator checks structure, metadata, paths, navigation coverage,
and local file targets without contacting external sites. The strict Zensical
build supplies Markdown rendering and anchor validation. Reviewers still verify
external links and real product behavior; automated checks cannot do that.

## Review expectations

The PR template records product verification, screenshots, links, and checks.
At least one reviewer must verify the customer-facing behavior. Do not publish
credentials, customer records, internal engineering instructions, or unverified
product steps. Pull request CI has read-only repository permissions. Release
creation and Pages deployment receive their required permissions only in their
respective jobs; no personal access token or external hosting secret is needed.
Never commit credentials to this repository.
