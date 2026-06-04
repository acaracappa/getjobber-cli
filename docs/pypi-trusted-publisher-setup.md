# PyPI Trusted Publisher Setup Checklist

This is a one-time manual checklist for Anthony to configure PyPI Trusted Publisher
(OIDC) for `getjobber-cli`. After this is configured, the GitHub Actions release
workflow (`.github/workflows/release.yml`) can publish to PyPI on tag push without
needing a long-lived API token.

---

## 1. PyPI account prerequisites

- [ ] Create a PyPI account at <https://pypi.org/account/register/> if you don't
      already have one.
- [ ] Verify the account email address (PyPI will email a confirmation link).
- [ ] Enable two-factor authentication on the account
      (<https://pypi.org/manage/account/two-factor/>). This is required to use
      Trusted Publishers and to upload via API token.
- [ ] (Recommended) Also create an account on TestPyPI
      (<https://test.pypi.org/account/register/>) with the same precautions —
      we'll dry-run there first.

---

## 2. Dry-run upload to TestPyPI (recommended)

This proves the build is well-formed and the rendered metadata page looks right
without burning the real PyPI project name.

- [ ] From the repo root, build distributions locally:
      ```
      python -m build
      ```
      You should see `dist/getjobber_cli-1.0.0.tar.gz` and
      `dist/getjobber_cli-1.0.0-py3-none-any.whl`.
- [ ] Create a TestPyPI API token at
      <https://test.pypi.org/manage/account/token/> (scope: "Entire account"
      since the project doesn't exist there yet).
- [ ] Upload to TestPyPI:
      ```
      python -m pip install --upgrade twine
      python -m twine upload --repository testpypi dist/*
      ```
- [ ] Visit <https://test.pypi.org/project/getjobber-cli/> and verify:
      - Description renders correctly (README markdown).
      - Author block shows both Anthony Vincent Caracappa and DC Tree Cutting
        and Land Service.
      - Project URLs (Homepage, Repository, Author, Sponsor, Documentation,
        Issues) are all present and correct.
      - Classifiers include "Development Status :: 5 - Production/Stable".
- [ ] (Optional) Try installing from TestPyPI in a clean venv:
      ```
      python -m venv /tmp/tpv && source /tmp/tpv/bin/activate
      pip install --index-url https://test.pypi.org/simple/ \
        --extra-index-url https://pypi.org/simple/ \
        getjobber-cli==1.0.0
      getjobber-cli --help
      ```

---

## 3. Reserve the `getjobber-cli` project name on real PyPI

You have two options for the very first upload. Trusted Publisher requires the
project to already exist on PyPI before you can configure it from the project
settings page — UNLESS you use the newer "pending publisher" feature, which lets
you pre-register before the project exists.

### Option A — Bootstrap with a one-time API token (simple, well-trodden)

- [ ] Create an API token at <https://pypi.org/manage/account/token/>
      with scope "Entire account" (since the project doesn't exist yet).
      Save the token somewhere safe; it is shown only once.
- [ ] Locally upload v1.0.0 to real PyPI using that token:
      ```
      python -m twine upload dist/* \
        --username __token__ \
        --password pypi-<the-token>
      ```
- [ ] Verify the project page renders correctly at
      <https://pypi.org/project/getjobber-cli/>.
- [ ] After upload, go to step 4 to configure Trusted Publisher. Then
      **revoke the bootstrap API token** at
      <https://pypi.org/manage/account/token/> so it can never be reused.

### Option B — Use a "pending" Trusted Publisher (newer feature, no token)

- [ ] Go to <https://pypi.org/manage/account/publishing/> and scroll to
      "Add a new pending publisher".
- [ ] Fill in:
      - PyPI Project Name: `getjobber-cli`
      - Owner: `acaracappa`
      - Repository name: `getjobber-cli`
      - Workflow name: `release.yml`
      - Environment name: leave blank (or `pypi` — see step 4)
- [ ] Click "Add". PyPI now trusts the workflow to create the project on its
      first successful publish.
- [ ] Skip step 4 sub-step "Add a new publisher" — pending publishers are
      automatically promoted on first upload.

> Pick **one** option. Option A is more conservative; Option B is fewer steps
> if you trust the GitHub Actions flow on the first try.

---

## 4. Configure Trusted Publisher on the PyPI project

(Skip this section if you used Option B above — pending publishers auto-promote.)

- [ ] Go to <https://pypi.org/project/getjobber-cli/>.
- [ ] Click "Manage" → "Publishing" in the left sidebar.
      Direct link: <https://pypi.org/manage/project/getjobber-cli/settings/publishing/>
- [ ] Under "Trusted publisher management", click **"Add a new publisher"**.
- [ ] Choose **GitHub** as the publisher.
- [ ] Fill in the form:
      - **PyPI Project Name**: `getjobber-cli` (pre-filled)
      - **Owner**: `acaracappa`
      - **Repository name**: `getjobber-cli`
      - **Workflow name**: `release.yml`
      - **Environment name**: leave blank for the simplest setup, OR use
        `pypi` if you want to add a GitHub deployment-environment gate
        (requires also creating an environment named `pypi` under
        repo Settings → Environments and matching `environment: pypi`
        in `release.yml`).
- [ ] Click "Add". You should see the new publisher listed.

---

## 5. Verify the workflow OIDC permissions

The `.github/workflows/release.yml` file must request the `id-token: write`
permission so GitHub will mint the OIDC token PyPI verifies. The relevant block
is:

```yaml
jobs:
  build-and-publish:
    runs-on: ubuntu-latest

    permissions:
      id-token: write
      contents: read
```

- [ ] Confirm that block is present in `.github/workflows/release.yml` on the
      `main` branch (or whichever branch the tag is created from).
- [ ] Confirm the workflow filename on disk is exactly `release.yml` — it must
      match what you typed in the Trusted Publisher form. Renaming this file
      later requires updating the publisher on PyPI.

---

## 6. First trusted-publisher release dry-run

Once steps 1–5 are done and v1.0.0 is on PyPI (either via Option A above or
about to be created via Option B):

- [ ] Cut and push the v1.0.0 git tag (this is the trigger for `release.yml`):
      ```
      git tag -a v1.0.0 -m "v1.0.0 — initial public release"
      git push origin v1.0.0
      ```
      > If you used Option A, the tag still triggers `release.yml`, but the
      > upload will fail with "file already exists" because v1.0.0 is already
      > on PyPI. That's fine — the next release (v1.0.1, v1.1.0, etc.) will be
      > the first one to actually exercise the trusted-publisher path.
- [ ] Watch the GitHub Actions run at
      <https://github.com/acaracappa/getjobber-cli/actions>.
- [ ] Confirm the "Publish to PyPI" step succeeds without any token in the
      logs (you should see OIDC token exchange happening).

---

## 7. Aftercare

- [ ] If you used Option A: **revoke** the one-time PyPI API token at
      <https://pypi.org/manage/account/token/>.
- [ ] Save a copy of this checklist as proof-of-setup for future maintainers.
- [ ] For every future release, the flow is just:
      1. Bump version in `pyproject.toml`.
      2. Update `CHANGELOG.md`.
      3. Commit, tag `vX.Y.Z`, push tag.
      4. GitHub Actions builds and publishes automatically — no secrets to
         rotate, no tokens to manage.
