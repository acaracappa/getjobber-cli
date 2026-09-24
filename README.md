# getjobber-cli

[![PyPI version](https://img.shields.io/pypi/v/getjobber-cli.svg)](https://pypi.org/project/getjobber-cli/) [![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE) [![Python versions](https://img.shields.io/pypi/pyversions/getjobber-cli.svg)](https://pypi.org/project/getjobber-cli/) [![CI](https://github.com/acaracappa/getjobber-cli/actions/workflows/test.yml/badge.svg)](https://github.com/acaracappa/getjobber-cli/actions/workflows/test.yml)

Built and maintained by [DC Tree Cutting](https://dctreecutting.com), an Eastern North Carolina tree service.

A portable, Python-based CLI tool that provides terminal access to the GetJobber CRM GraphQL API.

## Table of Contents

- [⚠️ Important](#-important)
- [Features](#features)
- [About this tool](#about-this-tool)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command Reference](#command-reference)
- [Output Formats](#output-formats)
- [Configuration](#configuration)
- [Token Storage](#token-storage)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Maintainer](#maintainer)
- [License](#license)
- [Contributing](#contributing)
- [Support](#support)
- [Acknowledgments](#acknowledgments)

## ⚠️ Important

**Please read our [Privacy Policy and Terms of Use](PRIVACY_AND_TERMS.md) before using this tool.**

This tool is provided as-is with no warranties. You use it at your own risk. We collect no data and assume no liability for any impact to your GetJobber account.

### Write commands

All write commands work again, rebuilt against Jobber's current schema. Three
were renamed and two were removed, because the API no longer does what their
old names promised:

| Old command | Now | Why |
|---|---|---|
| `clients delete` | `clients archive` | Jobber has no client deletion; archiving is reversible |
| `jobs complete` | `jobs close` | `jobComplete` is gone; `jobClose` needs an `--incomplete-visits` decision |
| `invoices send` | `invoices mark-sent` | `invoiceMarkAsSent` flags the record; **it does not email anyone** |
| `quotes send` | *removed* | no mutation in the API can send a quote |
| `quotes approve` | *removed* | no mutation in the API can approve a quote |

`jobs create` and `quotes create` need a property, which is resolved from the
client automatically when the client has exactly one and reported when it has
several. `quotes create` and `invoices create` need at least one `--line-item`,
given as `name[:quantity[:unit_price]]`.

See [docs/write-redesign.md](docs/write-redesign.md) for the full mapping.

## Features

- **OAuth 2.0 Authentication** - Secure browser-based authentication with automatic token refresh
- **Client Management** - Full support: list, retrieve, search, create, update, archive
- **Job Management** - Full support: list, retrieve, create, update, close
- **Quote Management** - List, retrieve, and create quotes
- **Invoice Management** - List, retrieve, create, and mark invoices as sent
- **Raw GraphQL Queries** - Execute custom GraphQL queries directly
- **Multiple Output Formats** - Table, JSON, CSV, and YAML output formats
- **Secure Token Storage** - OS-level keychain integration (macOS Keychain, Windows Credential Manager, Linux Secret Service)

## About this tool

`getjobber-cli` was originally built by [DC Tree Cutting and Land Service](https://dctreecutting.com) — an Eastern North Carolina tree service operating from Rocky Mount and Goldsboro across nine counties — to automate internal workflows on top of the Jobber field-service platform. It is released as open source under the MIT License for any Jobber customer or developer who wants terminal access to the Jobber GraphQL API.

## Requirements

- Python 3.10 or higher
- GetJobber account with OAuth app credentials

Targets Jobber GraphQL API version `2026-05-12`, sent via the
`X-JOBBER-GRAPHQL-VERSION` header and defined once as `API_VERSION` in
`src/getjobber_cli/constants.py`.

`2026-05-12` was Jobber's latest active version when checked against
[Jobber's changelog](https://developer.getjobber.com/docs/changelog/) on
2026-09-23. Jobber supports a version for a minimum of 12 months and keeps it
accessible for up to 18 months from its release date, after which requests are
silently upgraded to the oldest supported version — so this pin is worth
re-checking periodically, and the changelog is the place to do it.

## Installation

### From Source

```bash
# Clone the repository (or navigate to the project directory)
cd getjobber-cli

# Install in development mode
pip install -e .
```

### Via pip

```bash
pip install getjobber-cli
```

## Quick Start

### 1. Set up OAuth Credentials

First, you need to create an OAuth app in your GetJobber account:

1. Log in to your GetJobber account at https://app.getjobber.com
2. Navigate to **Settings → Developer Center**
3. Click "Create New App"
4. Fill in app details:
   - **App Name**: "getjobber-cli" (or your preferred name)
   - **Redirect URI**: `http://localhost:8888/callback`
   - **Scopes**: Select the scopes you need (clients:read, clients:write, jobs:read, etc.)
5. Click "Create App" and copy your Client ID and Client Secret

### 2. Configure the CLI

```bash
# Set your OAuth credentials
getjobber-cli config set client_id YOUR_CLIENT_ID
getjobber-cli config set client_secret YOUR_CLIENT_SECRET

# Verify configuration
getjobber-cli config list
```

### 3. Authenticate

```bash
# Start OAuth login flow (will open browser)
getjobber-cli login

# Check authentication status
getjobber-cli auth status
```

### 4. Start Using

```bash
# List all clients
getjobber-cli clients list

# Get client details
getjobber-cli clients get CLIENT_ID

# Search clients
getjobber-cli clients search "company name"

# List jobs
getjobber-cli jobs list

# Execute a raw GraphQL query
getjobber-cli query '{ clients(first: 5) { nodes { id firstName lastName } } }'
```

## Command Reference

### Authentication Commands

```bash
# Login with OAuth
getjobber-cli login

# Logout
getjobber-cli logout

# Check authentication status
getjobber-cli auth status

# Manually refresh token
getjobber-cli auth refresh
```

### Client Commands

```bash
# List clients
getjobber-cli clients list
getjobber-cli clients list --limit=50 --format=json

# Get client details
getjobber-cli clients get CLIENT_ID

# Create client (interactive)
getjobber-cli clients create

# Create client (with flags)
getjobber-cli clients create \
  --first-name="John" \
  --last-name="Doe" \
  --email="john@example.com" \
  --phone="555-1234"

# Update client
getjobber-cli clients update CLIENT_ID --email="newemail@example.com"

# Search clients
getjobber-cli clients search "company name"

# Archive client (Jobber has no delete; archiving is reversible in the web app)
getjobber-cli clients archive CLIENT_ID
```

### Job Commands

```bash
# List jobs
getjobber-cli jobs list
getjobber-cli jobs list --status=active

# Get job details
getjobber-cli jobs get JOB_ID

# Create job (property resolved from the client when it has only one)
getjobber-cli jobs create --client-id=CLIENT_ID --title="Lawn Maintenance"

# Update job
getjobber-cli jobs update JOB_ID --title="Updated Title"

# Close job (--incomplete-visits is required; DESTROY_ALL deletes visits)
getjobber-cli jobs close JOB_ID --incomplete-visits=COMPLETE_PAST_DESTROY_FUTURE
```

### Quote Commands

```bash
# List quotes
getjobber-cli quotes list
getjobber-cli quotes list --status=draft

# Get quote details
getjobber-cli quotes get QUOTE_ID

# Create quote (at least one --line-item required)
getjobber-cli quotes create --client-id=CLIENT_ID --title="Tree removal" \
  --line-item="Removal:1:850" --line-item="Haul away:1:150"

```

### Invoice Commands

```bash
# List invoices
getjobber-cli invoices list
getjobber-cli invoices list --unpaid

# Get invoice details
getjobber-cli invoices get INVOICE_ID

# Create invoice (--client-id and at least one --line-item are required)
getjobber-cli invoices create --client-id=CLIENT_ID --subject="Service Invoice" \
  --line-item="Stump grinding:1:400" --net-days=30

# Attach it to a job, and treat prices as tax-inclusive
getjobber-cli invoices create --client-id=CLIENT_ID --job-id=JOB_ID \
  --subject="Invoice" --line-item="Labour:4:95" --tax-method=INCLUSIVE

# Mark invoice as sent (flags the record; does not email the client)
getjobber-cli invoices mark-sent INVOICE_ID
```

### Raw GraphQL Query

```bash
# Execute inline query
getjobber-cli query '{ clients(first: 5) { nodes { id firstName lastName } } }'

# Execute query from file
getjobber-cli query --file=query.graphql

# Interactive query (opens editor)
getjobber-cli query --interactive
```

### Configuration Commands

```bash
# Set configuration value
getjobber-cli config set KEY VALUE

# Get configuration value
getjobber-cli config get KEY

# List all configuration
getjobber-cli config list

# Reset to defaults
getjobber-cli config reset
```

## Output Formats

All list commands support multiple output formats:

```bash
# Table format (default, human-readable)
getjobber-cli clients list --format=table

# JSON format (machine-readable)
getjobber-cli clients list --format=json

# CSV format (spreadsheet export)
getjobber-cli clients list --format=csv

# YAML format
getjobber-cli clients list --format=yaml
```

## Configuration

Configuration is stored in `~/.getjobber/config.json`:

```json
{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "default_output_format": "table",
  "items_per_page": 20
}
```

## Token Storage

Authentication tokens are stored securely using the OS keychain:
- **macOS**: Keychain
- **Windows**: Credential Manager
- **Linux**: Secret Service

If the keychain is unavailable, tokens fall back to `~/.getjobber/credentials.enc`.
**That file is not encrypted**, despite its `.enc` name: it holds the access and
refresh tokens as plain JSON. Its only protection is filesystem permissions —
the file is mode `0600` and the directory `0700`, so it is readable by your user
account alone. Anything running as your user, or any backup that copies the
file, can read those tokens. Prefer a working keychain where you can, and treat
this file as a secret if you cannot.

## Troubleshooting

### "Not authenticated" error

Run `getjobber-cli login` to authenticate.

### "OAuth credentials not configured" error

Configure your OAuth credentials:
```bash
getjobber-cli config set client_id YOUR_CLIENT_ID
getjobber-cli config set client_secret YOUR_CLIENT_SECRET
```

### Browser doesn't open during login

If the browser doesn't open automatically, copy the URL from the terminal and paste it into your browser.

### Token expired

Expired tokens are renewed automatically. When a command finds the access token
expired, it exchanges the stored refresh token for a new one and carries on, so
you should not normally see an expiry at all. `getjobber-cli auth status` reports
an expired-but-recoverable token rather than claiming you are signed out.

To renew immediately instead of waiting for the next command:

```bash
getjobber-cli auth refresh
```

Automatic renewal needs the stored refresh token and your configured OAuth
credentials. If either is missing, or Jobber rejects the refresh (a revoked or
long-unused refresh token), commands report `Not authenticated` and you need to
sign in again:

```bash
getjobber-cli login
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=getjobber_cli --cov-report=html
```

### Code Formatting

```bash
# Format code with black
black src/ tests/

# Type checking with mypy
mypy src/
```

Both run as blocking CI checks, alongside the test suite on Python 3.10, 3.11,
and 3.12.

### Reproducible installs

A `uv.lock` file is committed. With [uv](https://docs.astral.sh/uv/) installed,
`uv sync --extra dev` reproduces the exact pinned dependency set:

```bash
uv sync --extra dev
uv run pytest
```

## Maintainer

Maintained by Anthony Vincent Caracappa ([github.com/acaracappa](https://github.com/acaracappa)) at [dctreecutting.com](https://dctreecutting.com).

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- GitHub Issues: https://github.com/acaracappa/getjobber-cli/issues
- GetJobber API Documentation: https://developer.getjobber.com/

## Acknowledgments

Built with:
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [GQL](https://github.com/graphql-python/gql) - GraphQL client
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Keyring](https://github.com/jaraco/keyring) - Secure credential storage
