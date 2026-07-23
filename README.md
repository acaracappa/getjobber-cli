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

## Features

- **OAuth 2.0 Authentication** - Secure browser-based authentication with automatic token refresh
- **Client Management** - Create, read, update, delete, and search clients
- **Job Management** - Manage jobs with full CRUD operations
- **Quote Management** - Create, send, and approve quotes
- **Invoice Management** - Create and send invoices, track payments
- **Raw GraphQL Queries** - Execute custom GraphQL queries directly
- **Multiple Output Formats** - Table, JSON, CSV, and YAML output formats
- **Secure Token Storage** - OS-level keychain integration (macOS Keychain, Windows Credential Manager, Linux Secret Service)

## About this tool

`getjobber-cli` was originally built by [DC Tree Cutting and Land Service](https://dctreecutting.com) — an Eastern North Carolina tree service operating from Rocky Mount and Goldsboro across nine counties — to automate internal workflows on top of the Jobber field-service platform. It is released as open source under the MIT License for any Jobber customer or developer who wants terminal access to the Jobber GraphQL API.

## Requirements

- Python 3.10 or higher
- GetJobber account with OAuth app credentials

Targets Jobber GraphQL API version `2025-04-16` (the latest active version as of 2026-07-23), sent via the `X-JOBBER-GRAPHQL-VERSION` header.

## Installation

### From Source

```bash
# Clone the repository (or navigate to the project directory)
cd getjobber-cli

# Install in development mode
pip install -e .
```

### Via pip (future)

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

# Create a new client
getjobber-cli clients create --first-name="John" --last-name="Doe" --email="john@example.com"

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

# Delete client
getjobber-cli clients delete CLIENT_ID
```

### Job Commands

```bash
# List jobs
getjobber-cli jobs list
getjobber-cli jobs list --status=active

# Get job details
getjobber-cli jobs get JOB_ID

# Create job
getjobber-cli jobs create --client-id=CLIENT_ID --title="Lawn Maintenance"

# Update job
getjobber-cli jobs update JOB_ID --title="Updated Title"

# Complete job
getjobber-cli jobs complete JOB_ID
```

### Quote Commands

```bash
# List quotes
getjobber-cli quotes list
getjobber-cli quotes list --status=draft

# Get quote details
getjobber-cli quotes get QUOTE_ID

# Create quote
getjobber-cli quotes create --client-id=CLIENT_ID --title="Service Quote"

# Send quote to client
getjobber-cli quotes send QUOTE_ID

# Approve quote
getjobber-cli quotes approve QUOTE_ID
```

### Invoice Commands

```bash
# List invoices
getjobber-cli invoices list
getjobber-cli invoices list --unpaid

# Get invoice details
getjobber-cli invoices get INVOICE_ID

# Create invoice from job
getjobber-cli invoices create --job-id=JOB_ID --subject="Service Invoice"

# Create invoice for client
getjobber-cli invoices create --client-id=CLIENT_ID --subject="Invoice"

# Send invoice to client
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

If keychain is unavailable, tokens are stored in an encrypted file at `~/.getjobber/credentials.enc` with restricted permissions (0600).

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
