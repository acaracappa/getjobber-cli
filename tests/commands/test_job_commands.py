"""Tests for job management commands."""

from unittest.mock import MagicMock

import pytest
import typer
from typer.testing import CliRunner

from getjobber_cli.commands import job_commands

runner = CliRunner()


def _build_app():
    app = typer.Typer()
    app.command(name="list")(job_commands.list_jobs)
    app.command(name="get")(job_commands.get_job)
    app.command(name="create")(job_commands.create_job)
    app.command(name="update")(job_commands.update_job)
    app.command(name="complete")(job_commands.complete_job)
    return app


@pytest.fixture
def app():
    return _build_app()


@pytest.fixture
def fake_client(monkeypatch):
    mock_gql = MagicMock()
    mock_gql.query.return_value = {}
    mock_gql.mutate.return_value = {}
    mock_tm = MagicMock()
    mock_tm.is_authenticated.return_value = True
    mock_tm.get_access_token.return_value = "tok"
    monkeypatch.setattr(job_commands, "GraphQLClient", lambda *a, **kw: mock_gql)
    monkeypatch.setattr(job_commands, "get_token_manager", lambda: mock_tm)
    return mock_gql, mock_tm


@pytest.fixture
def unauthenticated(monkeypatch):
    mock_tm = MagicMock()
    mock_tm.is_authenticated.return_value = False
    monkeypatch.setattr(job_commands, "get_token_manager", lambda: mock_tm)
    return mock_tm


class TestListJobs:
    def test_happy_path(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {
            "jobs": {
                "nodes": [
                    {
                        "id": "1",
                        "title": "T",
                        "jobNumber": "JOB-1",
                        "status": "active",
                        "client": {"firstName": "X", "lastName": "Y"},
                    }
                ]
            }
        }
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

    def test_with_status_filter(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"jobs": {"nodes": []}}
        result = runner.invoke(app, ["list", "--status", "active"])
        assert result.exit_code == 0
        _, kwargs = gql.query.call_args
        assert kwargs["variables"]["status"] == "active"

    def test_json_format(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"jobs": {"nodes": [{"id": "1"}]}}
        result = runner.invoke(app, ["list", "--format", "json"])
        assert result.exit_code == 0

    def test_unauthenticated(self, app, unauthenticated):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 1


class TestGetJob:
    def test_happy_path(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"job": {"id": "1", "title": "T"}}
        result = runner.invoke(app, ["get", "1"])
        assert result.exit_code == 0

    def test_not_found(self, app, fake_client):
        gql, _ = fake_client
        gql.query.return_value = {"job": {}}
        result = runner.invoke(app, ["get", "missing"])
        assert result.exit_code == 1


class TestWriteCommandsGated:
    """Write commands are gated pending the v1.2.0 write redesign."""

    @pytest.mark.parametrize("fn_name", ['create_job', 'update_job', 'complete_job'])
    def test_gated(self, fn_name):
        fn = getattr(job_commands, fn_name)
        with pytest.raises(typer.Exit) as exc:
            fn()
        assert exc.value.exit_code == 2
