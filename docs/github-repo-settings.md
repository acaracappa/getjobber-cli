# GitHub repo settings checklist

A manual checklist for repository-level settings that can't be set from code.
Apply these from the GitHub UI at
<https://github.com/acaracappa/getjobber-cli/settings>.

## Repo "About" sidebar

Go to the repo homepage and click the gear icon next to **About** (top right).

**Description** (under 350 chars):

> A portable Python CLI for the Jobber GraphQL API — originally built by
> DC Tree Cutting and Land Service for internal field-service automation.

**Website**:

```
https://dctreecutting.com
```

**Topics** (add each as a separate tag — lowercase, hyphenated):

- `python`
- `cli`
- `jobber`
- `getjobber`
- `field-service`
- `fsm`
- `oauth`
- `graphql`
- `crm`
- `automation`

Leave **Releases**, **Packages**, and **Deployments** checkboxes enabled in the
About panel so they show up in the sidebar once those features are used.

## Social preview image

Go to **Settings → General → Social preview → Edit**.

**Specs**:

- 1280 × 640 px (GitHub's recommended size)
- PNG or JPG
- Under 1 MB

**Suggested content** (for a designer to mock up — do not auto-generate):

- `getjobber-cli` wordmark, prominent
- Subtitle: "by DC Tree Cutting and Land Service"
- Small visual hint that this is a Jobber API client (e.g., a terminal prompt
  glyph plus the Jobber name or logo, used per Jobber's brand guidelines)
- DC Tree Cutting brand colors / typography for consistency with
  dctreecutting.com

Upload the finished image via **Settings → General → Social preview → Edit**.

## Other repo settings worth applying

### Features (Settings → General → Features)

- **Issues**: Enabled (used for bug reports and feature requests, linked from
  README and CONTRIBUTING.md)
- **Discussions**: Enable if Anthony wants a community Q&A / ideas surface.
  Optional — fine to leave off if Issues is enough.
- **Wikis**: Leave disabled. Documentation lives in `README.md`, `docs/`, and
  `CONTRIBUTING.md`.
- **Projects**: Optional. Enable if used for release planning.
- **Sponsorships**: Optional. Can be enabled later if a `FUNDING.yml` is added.

### Pull Requests (Settings → General → Pull Requests)

- **Allow merge commits**: Optional
- **Allow squash merging**: Enabled (recommended default)
- **Allow rebase merging**: Optional
- **Automatically delete head branches**: Enabled (keeps the branch list clean)

### Branch protection on `main`

Go to **Settings → Branches → Add branch ruleset** (or **Add rule** under
classic branch protection rules) and apply to `main`:

- **Require a pull request before merging**
  - Require approvals: 1 (or 0 if Anthony is the sole maintainer and prefers
    self-merging from a PR for the audit trail)
  - Dismiss stale approvals when new commits are pushed: enabled
- **Require status checks to pass before merging**
  - Require branches to be up to date before merging: enabled
  - Required status checks: add the `test.yml` workflow job(s) once Group B's
    CI is merged and has run at least once (the check name only appears in the
    selector after its first run)
- **Require conversation resolution before merging**: enabled
- **Block force pushes**: enabled
- **Restrict deletions**: enabled

### Security (Settings → Code security and analysis)

- **Dependency graph**: Enabled (default on public repos)
- **Dependabot alerts**: Enabled
- **Dependabot security updates**: Enabled
- **Secret scanning**: Enabled (default on public repos)
- **Secret scanning push protection**: Enabled

### Actions (Settings → Actions → General)

- **Actions permissions**: Allow `acaracappa`, and select non-`acaracappa`,
  actions and reusable workflows — or "Allow all actions and reusable
  workflows" if that's simpler. Group B's CI may pull in third-party actions
  (e.g., `actions/checkout`, `actions/setup-python`) that need to be allowed.
- **Workflow permissions**: Read repository contents permission (default).
  Grant write only if a workflow needs it (e.g., a future release workflow).

### Pages (optional)

Not required for v1.0. Enable later if project documentation moves off the
README.
