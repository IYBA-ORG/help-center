# Hosting, repository policy, and first release

Use this runbook to publish the help center at `help.iyba.org`. Complete local
verification and the initial GitHub push first, then activate repository rules
and configure Cloudflare. Deployment is disabled until the repository variable
`DEPLOYMENTS_ENABLED` is explicitly set to `true`.

The initial publication must put the trusted commit checker on `main` before
contributors open PRs. Skip bootstrap commands if that initial commit has
already been pushed; do not repeat one-time setup blindly.

Commands below run from the **help-center repository root**. The original local
checkout is `/Users/vercryger/Code/FoundationalTeam/IYBA/help-center`.
Estimates are not deadlines; network and provider timing vary. Under an agent
execution policy limiting operations to 60 seconds, run longer operations
yourself or explicitly authorize their exact commands and waiting. CI and
provider jobs run asynchronously; use the linked dashboards or one-shot status
commands instead of polling.

## 1. Verify the source locally

Requires Python 3.11+. Installation normally takes 1–3 minutes:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
git config core.hooksPath .githooks
python -m unittest discover -s tests -p 'test_*.py'
python scripts/validate-content.py
zensical build --strict
```

Success: tests, validation, and the strict build exit zero; `site/index.html`,
`site/iyba/index.html`, `site/yachtbroker/index.html`, and
`site/boatdox/index.html` exist. First build budget: 1–2 minutes.

```bash
python -m http.server 8000 --bind 127.0.0.1 --directory site
```

The server stays running until Ctrl-C. Open `http://127.0.0.1:8000/` to inspect
the actual built output. Allow about five minutes to verify
the three cards, all product tabs/sidebars, mobile navigation, light/dark mode,
and search results across all products. For search, try “membership”, “vessel”,
and “deal” and follow results. Stop the server before continuing.

## 2. Bootstrap the empty repository

After local verification, leave `DEPLOYMENTS_ENABLED` unset or set to `false`:

```bash
git add .
git commit -m 'feat: establish help center foundation and documentation structure'
git push -u origin main
```

Expected: push may take 1–2 minutes; GitHub validation may take 2–5 minutes
afterward. The push starts `Validate`; the `Deploy` workflow's production job
is skipped because deployment has not been enabled. Cloudflare configuration
is not required for this push.

View [Actions](https://github.com/IYBA-ORG/help-center/actions) and use this
one-shot status command when needed:

```bash
gh run list --repo IYBA-ORG/help-center --limit 5
```

Success: the commit is present on GitHub `main`, `Validate` completes
successfully, and the production deployment job is skipped. These results
establish the source and CI; they do not mean a public website is deployed.

## 3. Activate mandatory Conventional Commits and reviews

Configure rebase-only merging so the exact commit subjects validated by CI
reach `main`. Squash merging allows editing a new subject after CI and is
therefore disabled, as are generated merge commits:

```bash
gh api --method PATCH repos/IYBA-ORG/help-center \
  -F allow_squash_merge=false \
  -F allow_merge_commit=false \
  -F allow_rebase_merge=true
```

Create the checked-in main ruleset **after the bootstrap push**:

```bash
gh api --method POST repos/IYBA-ORG/help-center/rulesets \
  --input .github/rulesets/main.json
```

These are one-time configuration calls, normally seconds. Do not repeatedly
POST the ruleset: subsequent updates use PUT with its returned ID. Success:
the active ruleset targets `main`, has no bypass actors, prevents deletion and
force pushes, requires linear history and one approving review, and requires
**Content and build** plus **Conventional commits** from GitHub Actions.
Confirm in [repository rules](https://github.com/IYBA-ORG/help-center/settings/rules).

Check activation without watching a job:

```bash
gh api repos/IYBA-ORG/help-center/rules/branches/main
```

The `Conventional commits` PR workflow checks both the PR title and all new
commit subjects. It executes the validator from the base branch, so modifying
the checker inside a PR cannot make that same PR evade validation. Local hooks
provide immediate feedback but are not the merge gate. See
[CONTRIBUTING.md](../CONTRIBUTING.md) for the exact message policy.

Use a short-lived PR to verify both required status checks appear; an invalid
title or commit should block merging. Correct it before merging. Administrators
can change repository settings, so maintain ownership of the ruleset as part of
normal repository administration.

## 4. Create the Cloudflare Pages project

Use a **Direct Upload** Pages project with production branch `main`; GitHub
Actions owns the build and upload. Do not also connect Cloudflare Git builds,
which would create a second deployment path. Static build output is `site/`.

With Node 22.12+ and access to the intended Cloudflare account, run:

```bash
npx --yes wrangler@4.161.0 login
npx --yes wrangler@4.161.0 pages project create iyba-help-center --production-branch main
```

Login is interactive and project creation may take 1–3 minutes including the
first CLI download. Success: Cloudflare lists a Pages project named
`iyba-help-center` with production branch `main`. If using an existing project
or the name is unavailable, use its actual name in the GitHub variable below.
This step creates the destination; it does not upload the site.

Create an API token restricted to the intended account with **Account →
Cloudflare Pages → Edit** permission. Obtain the account ID from Cloudflare.
Do not put the token in a command argument, file, commit, or chat. See the
[Cloudflare CI deployment guide](https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/).

## 5. Configure the GitHub production environment

Create the `production` environment in
[repository environments](https://github.com/IYBA-ORG/help-center/settings/environments).
Allow deployments only from `main`. Add these environment secrets using the
GitHub UI or these interactive, hidden-input commands:

```bash
gh secret set CLOUDFLARE_API_TOKEN --env production --repo IYBA-ORG/help-center
gh secret set CLOUDFLARE_ACCOUNT_ID --env production --repo IYBA-ORG/help-center
gh variable set CLOUDFLARE_PAGES_PROJECT --body iyba-help-center --repo IYBA-ORG/help-center
```

Success: both secret **names** appear in the environment and the repository
variable matches the Pages project name. No secret value should be printed.
Configure these before enabling production deployment. These interactive
configuration steps normally take a few minutes.

## 6. Enable and run the first production deployment

Set the switch as a **repository variable**, not an environment variable. The
job condition evaluates before the production environment is loaded, so an
environment-level switch would not enable the job.

After the Pages project, production secrets, and project variable are ready:

```bash
gh variable set DEPLOYMENTS_ENABLED --body true --repo IYBA-ORG/help-center
gh workflow run deploy.yml --ref main --repo IYBA-ORG/help-center
```

Enabling the variable does not deploy by itself; the manual workflow dispatch
starts the first release. Expected duration: 2–5 minutes. View
[Actions](https://github.com/IYBA-ORG/help-center/actions) or run the one-shot
status command from step 2. Do not watch or poll the job.

Success: `Deploy` completes successfully and the project’s actual `pages.dev`
URL serves the generated portal. Save that hostname for DNS setup. Check product
navigation, direct article URLs, and search on this hosted build before attaching
the custom domain.

## 7. Attach the custom domain and DNS

In Cloudflare Pages, open the project, choose **Custom domains**, and add
`help.iyba.org`. Associate the hostname with the Pages project **before** creating
its DNS record. At the existing DNS provider, set a CNAME for `help` to the
project's actual `<project>.pages.dev` hostname returned by Cloudflare. If the
zone is already in Cloudflare, use the record it creates for the project.

Do not replace an existing `help` record without confirming its current use.
Cloudflare provisions TLS after domain validation. DNS/certificate propagation
can take minutes to hours; check later in the dashboard rather than polling.
See [Cloudflare custom-domain setup](https://developers.cloudflare.com/pages/configuration/custom-domains/).

Success: the domain is active, `https://help.iyba.org/` shows the portal with a
valid certificate, and HTTP redirects to HTTPS. Check direct article URLs,
global search, and that an unknown route returns the generated 404 page.
The canonical URL is already set in `zensical.toml`.

## Releases and rollback

While `DEPLOYMENTS_ENABLED` is `true`, merging an approved PR into `main`
starts production deployment. It checks
required hosting configuration, installs pinned Zensical, runs validation and
tests, builds with `--strict`, and uploads only the static `site/` directory with
pinned Wrangler. Pull requests never receive deployment secrets. PR builds
retain static artifacts for review; automatic hosted PR previews are not set up.

To redeploy the current main branch after correcting hosting configuration:

```bash
gh workflow run deploy.yml --ref main --repo IYBA-ORG/help-center
```

Expected duration: 2–5 minutes. Check the Actions URL or the one-shot status
command above. Success is the completed deployment and the correct content at
the production URL.

To prevent future deployment jobs from starting:

```bash
gh variable set DEPLOYMENTS_ENABLED --body false --repo IYBA-ORG/help-center
```

This switch does **not** cancel a job already in progress and does not remove the
currently published site. If a deployment is already running and must stop,
cancel that specific run in GitHub Actions. To resume releases, set the variable
back to `true`; dispatch `deploy.yml` to publish the current `main` immediately.

For an urgent rollback, select a previously successful production deployment in
Cloudflare Pages and choose rollback. Then create a reviewed revert PR to make
`main` match the intended release; use a `revert: ...` commit and PR title. A
later merge would otherwise redeploy the content you rolled back. No database
restore is involved. Test rollback with the hosting owner during phase 4.

## Launch checklist

- [ ] Install the pinned generator and pass a strict build.
- [ ] Verify desktop/mobile layout, light/dark mode, and global search.
- [ ] Publish the initial main branch, confirm validation success, and confirm deployment is skipped.
- [ ] Apply rebase-only settings and the active required-check ruleset.
- [ ] Configure Pages, environment secrets, and the project variable.
- [ ] Set the repository deployment switch to `true` and verify the first hosted release.
- [ ] Attach `help.iyba.org` and confirm DNS, TLS, and HTTPS redirect.
- [ ] Verify a rejected nonconventional PR and a successful reviewed release.

Mark these complete only after observing the corresponding result.
