# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- OAuth 2.0 authentication flow with browser-based code exchange and automatic refresh.
- Client, job, quote, invoice management commands (CRUD + send/approve/complete).
- Raw GraphQL query execution.
- Multiple output formats: table, JSON, CSV, YAML.
- OS-level keychain integration for secure token storage (macOS Keychain, Windows Credential Manager, Linux Secret Service), with encrypted file fallback.
- `typing_extensions` declared as an explicit runtime dependency.

### Changed
- Package metadata: dual-author attribution (Anthony Vincent Caracappa, DC Tree Cutting and Land Service).
- Project URLs: Homepage → dctreecutting.com, Author → github.com/acaracappa, Sponsor → dctreecutting.com.
- Development Status classifier upgraded from Alpha to Production/Stable.
- README: added project context section, maintainer attribution, fixed placeholder URLs.

[1.0.0]: https://github.com/acaracappa/getjobber-cli/releases/tag/v1.0.0
