# IYBA Help Center

A public documentation portal for IYBA, YachtBroker, and BoatDox, built with
[Zensical](https://zensical.org/docs/) and intended for `https://help.iyba.org/`.
All content builds into static files; no application server, database, or
customer login is required. Global search uses Zensical's built-in client-side
engine.

## Implementation status

Phases 1 and 2 are implemented in source: homepage, branding, responsive theme
with light/dark modes, global and product navigation, all proposed category and
article paths, support resources, templates, content validation, and CI/CD.
The 35 product article placeholders deliberately contain no unverified steps.

Infrastructure setup is separate from the source implementation. A live portal
requires active GitHub rules, a Cloudflare Pages project, production secrets,
and DNS/TLS configuration. Follow [deployment setup](maintenance/deployment.md)
after local verification and the initial push. The production job is skipped
until the repository variable `DEPLOYMENTS_ENABLED` is explicitly set to `true`;
validation runs independently. Checked-in rules and workflows must be activated
in GitHub before they enforce remote policy or publish content.

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

Every commit and PR title **must follow Conventional Commits**. Start with
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
| `scripts/` and `tests/` | Content and commit validation |
| `.githooks/` | Local commit-message enforcement |
| `.github/workflows/` | PR validation, commit checks, production deployment |
| `.github/rulesets/main.json` | Required review/check policy to apply in GitHub |
| `maintenance/` | Hosting and asset maintenance instructions; not published |

## Short checks

These checks use only the Python standard library and normally take seconds:

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/validate-content.py
```

After installation, use `zensical build --strict` to verify the actual renderer
and link anchors. CI runs the same checks and retains the generated website as
an artifact for seven days. Production deployment repeats validation before
uploading `site/` to Cloudflare Pages.

## Publishing and status

Follow [maintenance/deployment.md](maintenance/deployment.md) in order: verify
locally, push the initial source, activate GitHub rules, configure Cloudflare,
then enable deployment and attach the domain. The initial push validates the
site while production deployment stays disabled. Once hosting is configured and
the repository variable `DEPLOYMENTS_ENABLED` is `true`, reviewed merges deploy
automatically.

Set that variable to `false` to prevent future deployment jobs from starting;
this does not cancel an in-progress job or remove the published site. View
[GitHub Actions](https://github.com/IYBA-ORG/help-center/actions) or run this
one-shot status command; no polling is required:

```bash
gh run list --repo IYBA-ORG/help-center --limit 5
```

Phase 3 will add verified workflows and screenshots. Phase 4 will complete
production usability, search, deployment, and rollback verification with product
owners.
