"""Tests for raw GraphQL query commands."""

from unittest.mock import MagicMock

import pytest
import typer
from typer.testing import CliRunner

from getjobber_cli.commands import query_commands

runner = CliRunner()


@pytest.fixture
def app():
    app = typer.Typer()
    app.command(name="query")(query_commands.execute_query)
    return app


@pytest.fixture
def fake_client(monkeypatch):
    mock_gql = MagicMock()
    mock_gql.query.return_value = {"ok": True}
    mock_tm = MagicMock()
    mock_tm.is_authenticated.return_value = True
    mock_tm.get_access_token.return_value = "tok"
    monkeypatch.setattr(query_commands, "GraphQLClient", lambda *a, **kw: mock_gql)
    monkeypatch.setattr(query_commands, "get_token_manager", lambda: mock_tm)
    return mock_gql


def test_interactive_opens_editor(app, fake_client, monkeypatch):
    monkeypatch.setattr(query_commands.click, "edit", lambda *a, **kw: "{ jobs { id } }")

    result = runner.invoke(app, ["--interactive"])

    assert result.exit_code == 0
    assert fake_client.query.call_args[0][0] == "{ jobs { id } }"


def test_interactive_aborts_when_editor_returns_nothing(app, fake_client, monkeypatch):
    monkeypatch.setattr(query_commands.click, "edit", lambda *a, **kw: None)

    result = runner.invoke(app, ["--interactive"])

    assert result.exit_code == 1
    fake_client.query.assert_not_called()


def test_interactive_strips_comment_lines(app, fake_client, monkeypatch):
    monkeypatch.setattr(
        query_commands.click,
        "edit",
        lambda *a, **kw: "# a comment\n{ jobs { id } }\n",
    )

    result = runner.invoke(app, ["--interactive"])

    assert result.exit_code == 0
    assert "#" not in fake_client.query.call_args[0][0]


def test_missing_token_reports_not_authenticated(app, monkeypatch):
    mock_tm = MagicMock()
    mock_tm.is_authenticated.return_value = True
    mock_tm.get_access_token.return_value = None
    monkeypatch.setattr(query_commands, "get_token_manager", lambda: mock_tm)

    result = runner.invoke(app, ["{ jobs { id } }"])

    assert result.exit_code == 1
