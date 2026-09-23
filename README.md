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

### Write commands are temporarily disabled

As of v1.1.0 this CLI is **read-only**. Jobber's current GraphQL schema reworked
the write surface: several mutations the write commands used (`invoiceSend`,
`quoteSend`, `quoteApprove`, `jobComplete`) no longer exist, and the create
mutations now require nested inputs the commands don't yet collect. Rather than
fail with cryptic GraphQL errors, the eleven write commands below exit
immediately with an explanatory message:

`clients create` · `clients update` · `clients delete` · `jobs create` ·
`jobs update` · `jobs complete` · `quotes create` · `quotes send` ·
`quotes approve` · `invoices create` · `invoices send`

Everything else — `list`, `get`, `search`, `query`, and all authentication and
configuration commands — is fully supported against the current schema. The
write redesign is planned for v1.2.0.

## Features

- **OAuth 2.0 Authentication** - Secure browser-based authentication with automatic token refresh
- **Client Management** - List, retrieve, and search clients (write commands pending v1.2.0)
- **Job Management** - List and retrieve jobs (write commands pending v1.2.0)
- **Quote Management** - List and retrieve quotes (write commands pending v1.2.0)
- **Invoice Management** - List and retrieve invoices (write commands pending v1.2.0)
- **Raw GraphQL Queries** - Execute custom GraphQL queries directly
- **Multiple Output Formats** - Table, JSON, CSV, and YAML output formats
- **Secure Token Storage** - OS-level keychain integration (macOS Keychain, Windows Credential Manager, Linux Secret Service)

## About this tool

`getjobber-cli` was originally built by [DC Tree Cutting and Land Service](https://dctreecutting.com) — an Eastern North Carolina tree service operating from Rocky Mount and Goldsboro across nine counties — to automate internal workflows on top of the Jobber field-service platform. It is released as open source under the MIT License for any Jobber customer or developer who wants terminal access to the Jobber GraphQL API.

## Requirements

- Python 3.10 or higher
- GetJobber account with OAuth app credentials

Targets Jobber GraphQL API version `2025-04-16`, sent via the
`X-JOBBER-GRAPHQL-VERSION` header.

**This pin is old and needs attention.** Checked against
[Jobber's changelog](https://developer.getjobber.com/docs/changelog/) on
2026-09-23:

- `2025-04-16` is still listed among Jobber's **active** versions, so the CLI
  works today.
- It is **not** the latest. Jobber has published six newer versions:
  `2026-02-17`, `2026-03-10`, `2026-04-13`, `2026-04-16`, `2026-04-22`, and
  `2026-05-12` (the current latest).
- Jobber supports a version for a minimum of 12 months and keeps it accessible
  for **up to 18 months from its release date**. For `2025-04-16` that outer
  limit falls around **2026-10-16**, after which requests are automatically
  upgraded to the oldest still-supported version — which may well behave
  differently.

Every documented change between `2025-04-16` and `2026-05-12` is a *dangerous*
change rather than a breaking one: all six are new enum values
(`InvoiceStatusTypeEnum.voided`, `RequestStatusTypeEnum.needs_approval`, and
additions to `WorkObjectSendMessageType` and `EmailTypes`). Added enum values
only break a client that exhaustively matches on them, which this CLI does not,
so moving the pin forward should be low-risk — but it should be verified against
a real account before release.

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

# Create client (interactive) - pending v1.2.0
getjobber-cli clients create

# Create client (with flags) - pending v1.2.0
getjobber-cli clients create \
  --first-name="John" \
  --last-name="Doe" \
  --email="john@example.com" \
  --phone="555-1234"

# Update client - pending v1.2.0
getjobber-cli clients update CLIENT_ID --email="newemail@example.com"

# Search clients
getjobber-cli clients search "company name"

# Delete client - pending v1.2.0
getjobber-cli clients delete CLIENT_ID
```

### Job Commands

```bash
# List jobs
getjobber-cli jobs list
getjobber-cli jobs list --status=active

# Get job details
getjobber-cli jobs get JOB_ID

# Create job - pending v1.2.0
getjobber-cli jobs create --client-id=CLIENT_ID --title="Lawn Maintenance"

# Update job - pending v1.2.0
getjobber-cli jobs update JOB_ID --title="Updated Title"

# Complete job - pending v1.2.0
getjobber-cli jobs complete JOB_ID
```

### Quote Commands

```bash
# List quotes
getjobber-cli quotes list
getjobber-cli quotes list --status=draft

# Get quote details
getjobber-cli quotes get QUOTE_ID

# Create quote - pending v1.2.0
getjobber-cli quotes create --client-id=CLIENT_ID --title="Service Quote"

# Send quote to client - pending v1.2.0
getjobber-cli quotes send QUOTE_ID

# Approve quote - pending v1.2.0
getjobber-cli quotes approve QUOTE_ID
```

### Invoice Commands

```bash
# List invoices
getjobber-cli invoices list
getjobber-cli invoices list --unpaid

# Get invoice details
getjobber-cli invoices get INVOICE_ID

# Create invoice from job - pending v1.2.0
getjobber-cli invoices create --job-id=JOB_ID --subject="Service Invoice"

# Create invoice for client - pending v1.2.0
getjobber-cli invoices create --client-id=CLIENT_ID --subject="Invoice"

# Send invoice to client - pending v1.2.0
getjobber-cli invoices send INVOICE_ID
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

Tokens are automatically refreshed when they expire. If you encounter issues, run:
```bash
getjobber-cli auth refresh
```

Or login again:
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
