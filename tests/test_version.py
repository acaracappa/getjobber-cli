"""The reported version must track packaging metadata, not a hand-edited copy."""

import re
from pathlib import Path

from typer.testing import CliRunner

import getjobber_cli
from getjobber_cli.cli import app
from getjobber_cli.constants import APP_VERSION

runner = CliRunner()
PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def test_version_is_resolved_not_fallback():
    assert APP_VERSION != "0.0.0+unknown", "package metadata was not found"
    assert re.fullmatch(r"\d+\.\d+\.\d+.*", APP_VERSION)


def test_dunder_version_matches_constant():
    assert getjobber_cli.__version__ == APP_VERSION


def test_cli_reports_the_same_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert APP_VERSION in result.output


def test_matches_pyproject():
    """Guards the drift that shipped a stale APP_VERSION before 1.2.0."""
    # Parsed by regex rather than tomllib, which is 3.11+ and this supports 3.10.
    match = re.search(r'^version = "([^"]+)"', PYPROJECT.read_text(), re.MULTILINE)
    assert match, "could not find version in pyproject.toml"
    declared = match.group(1)
    assert APP_VERSION == declared, (
        f"constants.APP_VERSION={APP_VERSION} but pyproject declares {declared}; "
        "reinstall the package or reconcile the two"
    )
