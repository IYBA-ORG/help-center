# GitHub Pages, repository policy, and releases

The default public address is `https://iyba-org.github.io/help-center/`.
Publishing uses GitHub Pages and Release Please. Ordinary merges update the
pending release PR; they do not deploy the site. A published stable GitHub
release is required before deployment can run.

Commands below run from the **help-center repository root**:

```bash
cd /Users/vercryger/Code/FoundationalTeam/IYBA/help-center
```

The initial source must already be on `main` before activating the ruleset or
opening PRs, because commit validation uses the policy from the target branch.
Check existing settings before repeating one-time setup. These instructions
describe the required configuration; checked-in files alone do not prove the
remote settings have been applied.

Estimates are not deadlines. Under the 60-second execution policy, run longer
commands yourself or explicitly authorize the specific command and waiting.
Do not watch or poll CI or provider jobs; use their URLs and one-shot status
commands. Creating or merging a release PR is a separate publication decision.

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

Success: tests, content validation, and the strict build exit zero, and
`site/index.html` plus the product pages exist. The first build can take
1–2 minutes. Python is only a build and validation dependency.

For a browser preview of the generated files:

```bash
python -m http.server 8000 --bind 127.0.0.1 --directory site
```

Open `http://127.0.0.1:8000/`. Allow about five minutes to check product cards,
sidebars, mobile navigation, light/dark modes, and search for “membership”,
“vessel”, and “deal”. Follow the search results. The server runs until Ctrl-C.
Check the hosted build again after release, since its `/help-center/` base path
differs from a root-level local preview.

## 2. Activate mandatory Conventional Commits and reviews

Configure rebase-only merging so the commit subjects checked by CI are preserved:

```bash
gh api --method PATCH repos/IYBA-ORG/help-center \
  -F allow_squash_merge=false \
  -F allow_merge_commit=false \
  -F allow_rebase_merge=true
```

Two rulesets separate required checks from review approval. The main ruleset
requires a pull request, resolved review conversations, both checks, and linear
history, with no bypass actors. The review ruleset requires one approving review
and grants `Vercryger` (GitHub user ID `3949146`) a bypass for pull requests only.
This bypass does not allow direct pushes or bypass required checks.

For a new repository, create the review ruleset first, then the main ruleset:

```bash
gh api --method POST repos/IYBA-ORG/help-center/rulesets \
  -H 'X-GitHub-Api-Version: 2026-03-10' \
  --input .github/rulesets/main-reviews.json

gh api --method POST repos/IYBA-ORG/help-center/rulesets \
  --input .github/rulesets/main.json
```

These configuration calls normally take seconds. Do not repeatedly POST the
rulesets; update existing rulesets by ID with `PUT` instead. When migrating an
existing combined ruleset, create the review ruleset before setting the main
ruleset's approval count to zero. Both active rulesets target `main`; together
they preserve review requirements for other contributors, prevent deletion and
force pushes, require linear history, and require **Content and build** plus
**Conventional commits** from GitHub Actions.

The active repository ruleset IDs are `27153910` (main protections) and
`27156701` (review approval).

To use the approval bypass, `Vercryger` opens the PR merge controls and chooses
to bypass the review requirement. Both required checks must pass and review
conversations must be resolved.

Verify in [repository rules](https://github.com/IYBA-ORG/help-center/settings/rules)
or inspect the effective rules once:

```bash
gh api repos/IYBA-ORG/help-center/rules/branches/main
```

The PR checks validate both the title and every new commit subject. Release
Please's generated `chore(main): release ...` subject follows the same policy;
the bot has no exemption. See [CONTRIBUTING.md](../CONTRIBUTING.md).

## 3. Enable GitHub Pages

Open [Settings → Pages](https://github.com/IYBA-ORG/help-center/settings/pages).
Under **Build and deployment**, set **Source** to **GitHub Actions**. Do not
choose branch-based publishing: the release workflow uploads the built site.

In [Settings → Environments](https://github.com/IYBA-ORG/help-center/settings/environments),
create or open `github-pages`. Set **Deployment branches and tags** to
**Selected branches and tags**, then add these two separate policies:

| Ref type | Pattern | Purpose |
| --- | --- | --- |
| Branch | `main` | Release Please's deployment in the same workflow run |
| Tag | `v*` | Deployment triggered by a published release event |

Use separate branch and tag entries; a branch rule does not grant tag access.
Do not select “Protected branches only”, which would block the tag path. No
environment secret is needed. See GitHub's
[environment configuration](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
and [Pages workflow requirements](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

Setup normally takes a few minutes. Success: Pages shows GitHub Actions as its
source and `github-pages` allows the two expected ref patterns. There may be no
live website until the first release deploys.

## 4. Allow Release Please to open pull requests

In [Settings → Actions → General](https://github.com/IYBA-ORG/help-center/settings/actions),
under **Workflow permissions**, enable **Allow GitHub Actions to create and
approve pull requests**. The organization may need to permit this setting first.
The workflow itself grants write permissions only to its release-management job;
it does not approve its own release PR.

Release Please uses the built-in `GITHUB_TOKEN`; no personal access token or
additional secret is required. When GitHub shows **Approve workflows to run**
on a bot-created or updated release PR, a user with write access must approve
the runs so the required checks can execute. This is separate from approving the
PR's changes. See GitHub's
[workflow trigger behavior](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow).

The release configuration uses the `simple` strategy, maintains `version.txt`
and `CHANGELOG.md`, and initially has an empty version manifest. `0.0.0` in
`version.txt` is the pre-release baseline, not a published release. The first
release PR targets `1.0.0`. Visible documentation changelog entries make
documentation-only changes eligible for patch releases after that.

## 5. Publish the first release

Once the workflows are on `main` and the settings above are ready:

1. Merge reviewed changes into `main`. The push runs validation and Release
   Please, which creates or refreshes a PR such as `chore(main): release 1.0.0`.
2. Open the release PR. Review the version, changelog, and included changes.
   If GitHub requests workflow approval, choose **Approve workflows to run**.
3. Wait outside a restricted agent session for **Content and build** and
   **Conventional commits** to pass. Obtain the required approving review.
4. Keep the bot PR as one commit and choose **Rebase and merge**. If it is behind
   `main`, let Release Please refresh it; do not add a merge commit or manual
   commits to the release branch.
5. The resulting push lets Release Please publish tag `v1.0.0` and its GitHub
   release. The successful release-creation output then calls the Pages workflow.

Each automation run generally takes 2–5 minutes. Follow
[Actions](https://github.com/IYBA-ORG/help-center/actions),
[pull requests](https://github.com/IYBA-ORG/help-center/pulls), and
[releases](https://github.com/IYBA-ORG/help-center/releases), or inspect once:

```bash
gh run list --repo IYBA-ORG/help-center --limit 5
gh pr list --repo IYBA-ORG/help-center --base main
gh release list --repo IYBA-ORG/help-center --limit 5
```

Success: a stable `v1.0.0` release exists, its deployment succeeds, and
`https://iyba-org.github.io/help-center/` serves the portal. Verify product
navigation, direct article URLs, images, and search on the hosted site.
Do not infer deployment success from a successful merge or release creation.

## What can deploy

The normal path calls the reusable Pages workflow only when Release Please
reports that it has created a release. This is intentional: a release created
with `GITHUB_TOKEN` does not trigger a second workflow through the release event.
The same-run call handles that case without another credential.

The Pages workflow also handles **published** release events for stable releases
created by a maintainer. Both entry paths verify the published release, resolve
the tag's exact commit, and check that it belongs to `main` history. Only the
GitHub-designated latest stable release may deploy. The tag and release are
checked again before publishing so a stale rerun cannot replace a newer release.

Ordinary pushes, tag-only pushes, drafts, and prereleases do not deploy. There
is no manual dispatch that publishes arbitrary `main` content. The build uses
the released commit rather than whatever happens to be at the tip of `main`.
GitHub Pages' configured base URL is applied during the deployment build, so
the default project path and an optional custom domain use the correct URLs.

## Recovery and rollback

If setup prevents deployment after a release was published, correct the setting
and rerun the failed deployment job for that **same latest release** from the
Actions UI. The release guard still applies. For a failed Release Please run
that did not finish creating its release, correct its permissions and rerun that
failed job. Do not watch or poll either run; check its result later.

For a content rollback, open a reviewed revert PR with a conventional subject
such as `revert: restore previous support navigation`. Merge it, then review and
merge the next Release Please PR. This produces a new version containing the
reverted content. Do not move published tags or rerun an old release to roll
back. No database restore is involved.

## Optional: use help.iyba.org

The GitHub Pages address works without a custom domain. If adding `help.iyba.org`,
confirm domain ownership and the current use of the `help` DNS record first.
Verify the domain in the organization’s GitHub Pages settings where available.

Add `help.iyba.org` under the repository's **Settings → Pages → Custom domain**
before changing DNS. At the existing DNS provider, create the record:

| Type | Name | Target |
| --- | --- | --- |
| CNAME | `help` | `iyba-org.github.io` |

The target is the hostname only, with no protocol or `/help-center` path. This
custom-workflow deployment does not require a committed `CNAME` file. Follow
[GitHub's custom-domain instructions](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site).

After propagation and certificate provisioning, enable **Enforce HTTPS** in
Pages settings. DNS and HTTPS availability can take up to 24 hours; check later
rather than polling. Update the source `site_url` to `https://help.iyba.org/` in
a reviewed change and release it so local builds reflect the chosen domain too.
Deployment already derives its canonical URL from the Pages configuration.

Success: `https://help.iyba.org/` serves the released site with a valid certificate,
HTTP redirects to HTTPS, and direct article links and search work.

## Launch checklist

- [ ] Install dependencies and pass tests, content validation, and a strict build.
- [ ] Verify desktop/mobile layout, light/dark mode, and global search.
- [ ] Apply rebase-only settings and the active required-check ruleset.
- [ ] Enable GitHub Actions publishing in Pages and configure `github-pages` ref policies.
- [ ] Permit Release Please to create PRs and approve bot workflow runs when requested.
- [ ] Review and merge the first release PR; verify the stable release and hosted site.
- [ ] If desired, configure the custom domain, DNS, and HTTPS.

Mark these complete only after observing the corresponding result.
