# IYBA Help Center

A public documentation portal for IYBA, YachtBroker, and BoatDox, built with
[Zensical](https://zensical.org/docs/) and hosted on GitHub Pages. The default
address is [iyba-org.github.io/help-center](https://iyba-org.github.io/help-center/).
All content builds into static files; no application server, database, or
customer login is required. Global search uses Zensical's built-in client-side
engine.

## Implementation status

Phases 1 and 2 are implemented in source: homepage, branding, responsive theme
with light/dark modes, global and product navigation, all proposed category and
article paths, support resources, templates, content validation, and CI/CD.
The 35 product article placeholders deliberately contain no unverified steps.

GitHub Pages and repository permissions must be configured before the first
release. Follow [deployment setup](maintenance/deployment.md) to activate Pages,
required checks, and Release Please. A normal push or merge does not deploy the
website: publication requires a stable GitHub release.

## Quick start

Run from the repository root with Python 3.11+:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
git config core.hooksPath .githooks
python scripts/validate-content.py
zensical serve
```

Dependency installation is usually 1–3 minutes; the preview runs until Ctrl-C.
Open the URL printed by Zensical. To produce portable static output, run
`zensical build --strict`; success produces `site/index.html` and product pages.
Python is used for building and validation, not by visitors to the published site.

Every non-merge commit and PR title **must follow Conventional Commits**. Merge
commits are ignored. Start with
[CONTRIBUTING.md](CONTRIBUTING.md) for the exact policy, examples, hooks, article
standards, and review process.

## Repository map

| Path | Purpose |
| --- | --- |
| `docs/index.md` | Product directory homepage |
| `docs/{iyba,yachtbroker,boatdox}/` | Product landings, category indexes, article placeholders |
| `docs/support/` | Shared support and product resources |
| `docs/assets/` | Shared and product branding/media |
| `zensical.toml` | Site metadata, explicit navigation, theme, strict link validation |
| `templates/` | Article, category, and FAQ templates; not published |
| `scripts/` and `tests/` | Content, commit, and release validation |
| `.githooks/` | Local commit-message enforcement |
| `.github/workflows/` | PR validation, Release Please, and release-only Pages deployment |
| `.github/rulesets/main.json` | Required review/check policy to apply in GitHub |
| `release-please-config.json` | Release strategy and changelog sections |
| `.release-please-manifest.json`, `version.txt`, `CHANGELOG.md` | Release Please's version and release history |
| `maintenance/` | Hosting and asset maintenance instructions; not published |

## Short checks

These checks use only the Python standard library and normally take seconds:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/validate-content.py
```

After installation, use `zensical build --strict` to verify the actual renderer
and link anchors. CI runs the same checks and retains the generated website as
an artifact for seven days. Release deployment validates and builds the released
commit before uploading `site/` to GitHub Pages.

## Releases and publishing

1. Merge reviewed content or code changes into `main`.
2. Release Please creates or updates a release PR containing the version and
   changelog changes. Ordinary merges leave the published site unchanged.
3. Review the release PR, approve its workflows if GitHub requests it, and pass
   the required checks. Keep the bot's PR as a single commit.
4. Use **Rebase and merge**. Release Please publishes the stable `vX.Y.Z` release;
   only then does the Pages deployment run.

The initial release is `v1.0.0`. Later documentation-only changes are eligible
for patch releases. Draft releases, prereleases, tag-only pushes, and outdated
release reruns cannot publish the site. The workflows use the built-in
`GITHUB_TOKEN`; no personal access token or external hosting credentials are
required. See the [runbook](maintenance/deployment.md) for setup, recovery,
and optional `help.iyba.org` DNS configuration.

View [GitHub Actions](https://github.com/IYBA-ORG/help-center/actions) or use
these one-shot status commands instead of watching or polling jobs:

```bash
gh run list --repo IYBA-ORG/help-center --limit 5
gh release list --repo IYBA-ORG/help-center --limit 5
```

Phase 3 will add verified workflows and screenshots. Phase 4 will complete
production usability, search, deployment, and rollback verification with product
owners.
