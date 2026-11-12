## What changed

Describe the customer task or maintenance problem and the resulting behavior.

## Verification

Describe the product evidence, content checks, and build results. If a check was
not run, explain why and give the command needed to run it.

## Checklist

- [ ] Every non-merge commit and this PR title follow the Conventional Commits policy in CONTRIBUTING.md.
- [ ] Product instructions match the current interface and were verified by a product reviewer.
- [ ] New pages use lowercase kebab-case paths and are included in `zensical.toml` navigation.
- [ ] Internal links resolve; images have descriptive alternative text.
- [ ] Screenshots and files contain no credentials, customer data, or private information.
- [ ] `python3 scripts/validate-content.py` and `zensical build --strict` pass, or limitations are recorded above.

For structural changes without product instructions or screenshots, mark the
corresponding checks as not applicable in the verification notes.
