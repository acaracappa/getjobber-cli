# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
