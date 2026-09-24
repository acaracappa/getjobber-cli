# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Client write commands work again.** `clients create`, `clients update` and
  `clients archive` are rebuilt against the current schema and no longer gated.
  The old versions could not have worked: they sent `email`/`phoneNumber`
  strings where `ClientCreateInput` takes `emails`/`phones` lists of objects,
  and called `clientUpdate`, which does not exist.
- `docs/write-redesign.md` records the full v1.0 → current mapping for every
  write command, verified by introspecting the live schema.
- **Quote and invoice write commands work again.** `quotes create` and
  `invoices create` are rebuilt against the inputs the schema now requires:
  both need line items, quotes need a property, and invoices need due details
  and a tax calculation method. Line items are given as
  `--line-item name[:quantity[:unit_price]]`, repeated.
- **Job write commands work again.** `jobs create`, `jobs update` and
  `jobs close` are rebuilt and no longer gated. `jobs create` resolves the
  client's property automatically when there is exactly one, and refuses to
  guess when there are several.

### Changed
- **`clients delete` is now `clients archive`.** Jobber has no client deletion;
  the only mutation is `clientArchive`, and it is reversible. A command named
  `delete` that archives is a trap.
- **`clients update` reads before it writes.** `clientEdit` has no way to *set*
  an email or phone — they are added, or edited by their own id. Updating a
  contact method now looks up the existing one and edits it, instead of adding
  a duplicate. A name-only update skips the lookup.

- **`jobs complete` is now `jobs close`.** `jobComplete` no longer exists.
  `jobClose` requires `--incomplete-visits`, which has no default because
  `DESTROY_ALL` deletes visit records; choosing it prompts unless `--force`.
- **`jobs update --status` is gone.** `JobEditInput` has no status field; job
  status changes through closing and reopening, not editing.
- **Job commands no longer turn a cancelled confirmation into a failure.** Every
  handler in `job_commands` caught its own `typer.Exit`, so declining a prompt
  exited 1 and printed "Unexpected error: 0".

- **`invoices send` is now `invoices mark-sent`.** `invoiceSend` no longer
  exists, and `invoiceMarkAsSent` only flags the record — nothing in the current
  API emails an invoice to a client. The command says so before acting.
- **Every command module now re-raises `typer.Exit`.** `job_commands`,
  `query_commands`, `config_commands` and `auth_commands` caught their own exit,
  so declining a confirmation exited 1 and printed "Unexpected error: 0".

### Removed
- **`quotes send` and `quotes approve`.** Jobber's API exposes no mutation that
  can send or approve anything — searching all 109 mutations for
  send/approve/deliver/email/message/submit returns nothing. These cannot be
  rebuilt; use the Jobber web app. Tests pin the removal so they are not
  reintroduced.
- **The write-command gate.** `utils/gating.py` and every `@write_command_pending`
  decorator are gone: no write command is gated any more.

## [1.2.1] — 2026-09-23

### Fixed
- **1.2.0 shipped with no working commands.** `query_commands` imports `click`,
  which was never declared as a dependency. Typer 0.26+ does not depend on
  click, so an ordinary `pip install getjobber-cli` had no click, the command
  imports raised `ImportError`, and `register_commands()` swallowed it — leaving
  a CLI that answered `--version` and `--help` with an exit code of 0 and not a
  single command registered. `click>=8.0` is now a declared dependency.
- **`register_commands()` no longer hides import failures.** It caught
  `ImportError` and passed, a leftover from when the command modules did not yet
  exist. That is what turned a missing dependency into a silently empty CLI; it
  now raises with a message naming the failed import.

### Added
- A packaging test that parses every import in `src/` and asserts each
  third-party module is a declared runtime dependency. It fails against 1.2.0.
- An `install` CI job that builds the wheel and installs it **without** dev
  extras, then checks all nine top-level commands are present. The existing
  matrix installs `.[dev]`, where `black` supplies click transitively — which is
  precisely why this passed CI and broke on PyPI.

## [1.2.0] — 2026-09-23

### Fixed
- **`query --interactive` no longer crashes.** The command called
  `typer.edit()`, which Typer has never exported and which raises
  `AttributeError` on Typer 0.27. It now uses `click.edit()`, the function
  it was always meant to wrap. The interactive path had no test coverage,
  which is why the break went unnoticed.
- **A missing access token now reports "not authenticated."** Commands passed
  the result of `get_access_token()` straight to `GraphQLClient` without
  checking for `None`, so a token cleared between the authentication check
  and the read surfaced as an unrelated downstream error instead of a prompt
  to log in.

- **`--version` no longer reports a stale number.** `APP_VERSION` was a
  hard-coded copy in `constants.py` that drifted from `pyproject.toml`; it is now
  read from installed package metadata, with a test asserting the two agree.

### Changed
- **Access tokens now refresh automatically.** `get_access_token()` exchanges the
  stored refresh token for a new one when the current token has expired, so
  commands no longer fail with `Not authenticated` an hour after login. The
  README had advertised this behaviour since 1.0.0 without it existing; it now
  exists. `auth refresh` remains for renewing on demand and shares the same
  implementation, and `auth status` distinguishes an expired-but-recoverable
  token from being signed out entirely.
- **Documentation corrected: the credential file fallback is not encrypted.** The
  README, the privacy notice and the 1.0.0 changelog entry all described the
  `~/.getjobber/credentials.enc` fallback as encrypted. It never has been — the
  file holds plain JSON and is protected only by `0600` permissions. No code
  behaviour changed here; the documentation was wrong, and a reader could have
  accepted the fallback believing their tokens were encrypted at rest.
- **Jobber GraphQL API version bumped from `2025-04-16` to `2026-05-12`.** The
  old pin was six versions behind and close to the end of its 18-month
  accessibility window (around 2026-10-16), after which Jobber silently upgrades
  requests to the oldest supported version. Every documented change between the
  two versions is additive — six new enum values, nothing removed or retyped —
  so no query or mutation in this CLI is affected. The README had also claimed
  the old pin was "the latest active version as of 2026-07-23", which was untrue
  even then. The version now lives in `constants.py` as `API_VERSION` instead of
  a string literal in the transport setup, so future bumps are a one-line
  change.
- All runtime and development dependencies upgraded; `cryptography` and
  `anyio` moved to versions that close four Dependabot security advisories.
  Both are transitive and unexercised by this CLI, so no behaviour changes.
- Dependency floors in `pyproject.toml` raised to the versions actually
  supported and tested. The previous floors spanned several major releases
  and were never exercised.
- `typer[all]` is now plain `typer`; Typer no longer defines an `all` extra.
- The authenticated-client helper, previously copy-pasted into all five
  command modules, now lives once in `getjobber_cli.api.client` as
  `get_authenticated_client()`.

- **The write redesign moves from v1.2.0 to v1.3.0.** This release takes the
  1.2.0 number because automatic token refresh is new functionality rather than
  a fix. The gating message and README now name v1.3.0, so the version users are
  told to wait for stays accurate.

### Added
- `black --check` and `mypy` run as blocking CI checks alongside the test
  matrix, so formatting and typing cannot drift again.
- Dependabot configuration for monthly grouped dependency and GitHub Actions
  updates.

## [1.1.1] — 2026-07-23

### Fixed
- **Query-cost throttling now raises `RateLimitError`.** Jobber's query-cost
  limiter returns a GraphQL error with `extensions.code: THROTTLED` rather than
  an HTTP 429; these responses previously surfaced as a generic `GraphQLError`.

### Changed
- README now states the pinned Jobber GraphQL API version (`2025-04-16`),
  verified as the latest active version against Jobber's changelog as of
  2026-07-23.
- `uv.lock` is now committed for reproducible development installs.

## [1.1.0] — 2026-07-01

Schema refresh for Jobber's current GraphQL API. The read path was rebuilt
against the live schema (verified via introspection) and tested against a real
account; the write path is temporarily gated pending a redesign.

### Fixed
- **Read commands modernized to the current schema.** Rewrote all query
  selections in `api/queries.py`:
  - Money now read from `amounts { total, subtotal, paymentsTotal, invoiceBalance, ... }`
    instead of the removed `totalAmount` / `amountPaid` / `balance` scalars.
  - Status fields are the typed enums `invoiceStatus` / `quoteStatus` / `jobStatus`,
    and list filters use `InvoiceStatusTypeEnum` / `QuoteStatusTypeEnum` / `JobStatusTypeEnum`.
  - Single-record lookups take `EncodedId!` (was `ID!`).
  - Line items read `totalPrice` (was `total`) under a `nodes { ... }` connection;
    invoice→jobs and client `tags` / `phones` updated to their current connection shapes.
  - Client phone reads `phone` (was `phoneNumber`).
- `invoices list --unpaid` now filters client-side by outstanding balance (the old
  `status: "UNPAID"` value is not a valid enum).

### Changed
- **Write commands temporarily disabled** (`clients create/update/delete`,
  `jobs create/update/complete`, `quotes create/send/approve`,
  `invoices create/send`). Jobber's current schema reworked the write surface:
  `invoiceSend` / `quoteSend` / `quoteApprove` / `jobComplete` no longer exist, and
  the create mutations require nested inputs (`dueDetails`, `tax`, `lineItems`,
  `propertyId`) the commands don't yet collect. These now exit with a clear message
  instead of a cryptic GraphQL error, pending the write redesign (1.2.0).

### Added
- Schema-shape guard tests (`tests/api/test_queries_schema.py`) to prevent
  regressions to removed fields.

## [1.0.0] — 2026-06-04

### Added
- Initial public 1.0.0 release.
- OAuth 2.0 authentication flow with browser-based code exchange, and a stored refresh token renewed on demand via `auth refresh`. (This entry originally said "automatic refresh"; refresh has always been manual. Corrected in [Unreleased].)
- Client, job, quote, invoice management commands (CRUD + send/approve/complete).
- Raw GraphQL query execution.
- Multiple output formats: table, JSON, CSV, YAML.
- OS-level keychain integration for secure token storage (macOS Keychain, Windows Credential Manager, Linux Secret Service), with a permissions-protected file fallback. (This entry originally said "encrypted file fallback"; the fallback has never been encrypted. Corrected in [Unreleased].)
- `typing_extensions` declared as an explicit runtime dependency.

### Changed
- Package metadata: dual-author attribution (Anthony Vincent Caracappa, DC Tree Cutting and Land Service).
- Project URLs: Homepage → dctreecutting.com, Author → github.com/acaracappa, Sponsor → dctreecutting.com.
- Development Status classifier upgraded from Alpha to Production/Stable.
- README: added project context section, maintainer attribution, fixed placeholder URLs.

[1.2.1]: https://github.com/acaracappa/getjobber-cli/releases/tag/v1.2.1
[1.2.0]: https://github.com/acaracappa/getjobber-cli/releases/tag/v1.2.0
[1.1.1]: https://github.com/acaracappa/getjobber-cli/releases/tag/v1.1.1
[1.1.0]: https://github.com/acaracappa/getjobber-cli/releases/tag/v1.1.0
[1.0.0]: https://github.com/acaracappa/getjobber-cli/releases/tag/v1.0.0
