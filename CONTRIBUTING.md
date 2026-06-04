# Contributing to getjobber-cli

`getjobber-cli` is an open-source CLI for the Jobber GraphQL API, maintained by
[DC Tree Cutting and Land Service](https://dctreecutting.com). Contributions from
Jobber customers, developers, and the broader community are welcome.

## Development setup

Clone the repository, create a virtual environment, and install the package in
editable mode with the development extras:

```bash
git clone https://github.com/acaracappa/getjobber-cli.git
cd getjobber-cli

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

This installs the CLI along with `pytest`, `pytest-cov`, `black`, `mypy`, and
`responses` for testing and linting.

## Running tests

Run the full test suite with:

```bash
pytest
```

Run tests with coverage reporting:

```bash
pytest --cov=getjobber_cli
```

For an HTML coverage report:

```bash
pytest --cov=getjobber_cli --cov-report=html
```

## Code style

This project uses [`black`](https://black.readthedocs.io/) for formatting and
[`mypy`](https://mypy.readthedocs.io/) for type checking. Both are configured in
`pyproject.toml`.

```bash
# Format code (line length is 100)
black src/ tests/

# Type-check
mypy src/
```

Please run `black` and `mypy` before submitting a pull request.

## Submitting pull requests

1. Fork the repository and create a feature branch off `main`.
2. Make your changes, including tests where applicable.
3. Ensure `pytest`, `black`, and `mypy` all pass locally.
4. Open a pull request against `main` with a clear description of the change.
5. Reference any related GitHub issue (e.g., `Fixes #123`).

Small, focused PRs are easier to review and land than large ones. If you're
planning a significant change, please open an issue first to discuss the
approach.

## Bug reports and feature requests

Please file bug reports and feature requests via
[GitHub Issues](https://github.com/acaracappa/getjobber-cli/issues). When
reporting a bug, include:

- Your OS and Python version
- The `getjobber-cli` version
- Steps to reproduce
- Expected vs. actual behavior
- Relevant error output (with secrets redacted)

## License

By contributing, you agree that your contributions will be licensed under the
MIT License, the same license that covers the project.
