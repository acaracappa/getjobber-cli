"""Tests for job management commands."""

from unittest.mock import MagicMock

import pytest
import typer
from typer.testing import CliRunner

from getjobber_cli.commands import job_commands
from getjobber_cli.utils.errors import NotAuthenticatedError

runner = CliRunner()


def _build_app():
    app = typer.Typer()
    app.command(name="list")(job_commands.list_jobs)
    app.command(name="get")(job_commands.get_job)
    app.command(name="create")(job_commands.create_job)
    app.command(name="update")(job_commands.update_job)
    app.command(name="close")(job_commands.close_job)
    return app


@pytest.fixture
def app():
    return _build_app()


@pytest.fixture
def fake_client(monkeypatch):
    mock_gql = MagicMock()
    mock_gql.query.return_value = {}
    mock_gql.mutate.return_value = {}
    monkeypatch.setattr(job_commands, "get_authenticated_client", lambda: mock_gql)
    return mock_gql


@pytest.fixture
def unauthenticated(monkeypatch):
    def _unauthenticated():
        raise NotAuthenticatedError()

    monkeypatch.setattr(job_commands, "get_authenticated_client", _unauthenticated)


class TestListJobs:
    def test_happy_path(self, app, fake_client):
        gql = fake_client
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
        gql = fake_client
        gql.query.return_value = {"jobs": {"nodes": []}}
        result = runner.invoke(app, ["list", "--status", "active"])
        assert result.exit_code == 0
        _, kwargs = gql.query.call_args
        assert kwargs["variables"]["status"] == "active"

    def test_json_format(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {"jobs": {"nodes": [{"id": "1"}]}}
        result = runner.invoke(app, ["list", "--format", "json"])
        assert result.exit_code == 0

    def test_unauthenticated(self, app, unauthenticated):
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 1


class TestGetJob:
    def test_happy_path(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {"job": {"id": "1", "title": "T"}}
        result = runner.invoke(app, ["get", "1"])
        assert result.exit_code == 0

    def test_not_found(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {"job": {}}
        result = runner.invoke(app, ["get", "missing"])
        assert result.exit_code == 1


class TestCreateJob:
    def _created(self, gql):
        gql.mutate.return_value = {
            "jobCreate": {"job": {"id": "j1", "title": "Trim"}, "userErrors": []}
        }

    def test_resolves_the_single_property_and_sends_invoicing(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {"client": {"id": "c1", "properties": [{"id": "p1"}]}}
        self._created(gql)

        result = runner.invoke(app, ["create", "--client-id=c1", "--title=Trim"])

        assert result.exit_code == 0
        sent = gql.mutate.call_args.kwargs["variables"]["input"]
        # JobCreateAttributes requires both of these; the old command sent neither.
        assert sent["propertyId"] == "p1"
        assert sent["invoicing"] == {
            "invoicingType": "FIXED_PRICE",
            "invoicingSchedule": "ON_COMPLETION",
        }
        assert "clientId" not in sent

    def test_explicit_property_skips_the_lookup(self, app, fake_client):
        gql = fake_client
        self._created(gql)
        result = runner.invoke(
            app, ["create", "--client-id=c1", "--property-id=p9", "--title=Trim"]
        )
        assert result.exit_code == 0
        gql.query.assert_not_called()
        assert gql.mutate.call_args.kwargs["variables"]["input"]["propertyId"] == "p9"

    def test_multiple_properties_refuses_to_guess(self, app, fake_client):
        gql = fake_client
        gql.query.return_value = {
            "client": {"id": "c1", "properties": [{"id": "p1"}, {"id": "p2"}]}
        }
        result = runner.invoke(app, ["create", "--client-id=c1", "--title=Trim"])
        assert result.exit_code == 1
        gql.mutate.assert_not_called()
        assert "p1" in result.output and "p2" in result.output

    def test_no_properties_is_an_error(self, app, fake_client):
        fake_client.query.return_value = {"client": {"id": "c1", "properties": []}}
        result = runner.invoke(app, ["create", "--client-id=c1", "--title=Trim"])
        assert result.exit_code == 1
        fake_client.mutate.assert_not_called()

    def test_invoicing_options_are_passed_through(self, app, fake_client):
        gql = fake_client
        self._created(gql)
        result = runner.invoke(
            app,
            [
                "create",
                "--client-id=c1",
                "--property-id=p1",
                "--title=Trim",
                "--invoicing-type=VISIT_BASED",
                "--invoicing-schedule=PER_VISIT",
            ],
        )
        assert result.exit_code == 0
        assert gql.mutate.call_args.kwargs["variables"]["input"]["invoicing"] == {
            "invoicingType": "VISIT_BASED",
            "invoicingSchedule": "PER_VISIT",
        }


class TestUpdateJob:
    def test_edits_by_job_id(self, app, fake_client):
        gql = fake_client
        gql.mutate.return_value = {"jobEdit": {"job": {"id": "j1"}, "userErrors": []}}
        result = runner.invoke(app, ["update", "j1", "--title=New", "--instructions=Do it"])
        assert result.exit_code == 0
        sent = gql.mutate.call_args.kwargs["variables"]
        assert sent["jobId"] == "j1"
        assert sent["input"] == {"title": "New", "instructions": "Do it"}

    def test_no_fields_exits_nonzero(self, app, fake_client):
        result = runner.invoke(app, ["update", "j1"])
        assert result.exit_code == 1


class TestCloseJob:
    def _closed(self, gql):
        gql.mutate.return_value = {
            "jobClose": {"job": {"id": "j1", "jobStatus": "archived"}, "userErrors": []}
        }

    def test_requires_the_incomplete_visit_decision(self, app, fake_client):
        # No default: one of the choices deletes visit records.
        result = runner.invoke(app, ["close", "j1"])
        assert result.exit_code != 0
        fake_client.mutate.assert_not_called()

    def test_complete_past_needs_no_confirmation(self, app, fake_client):
        gql = fake_client
        self._closed(gql)
        result = runner.invoke(
            app, ["close", "j1", "--incomplete-visits=COMPLETE_PAST_DESTROY_FUTURE"]
        )
        assert result.exit_code == 0
        assert gql.mutate.call_args.kwargs["variables"]["input"] == {
            "modifyIncompleteVisitsBy": "COMPLETE_PAST_DESTROY_FUTURE"
        }

    def test_destroy_all_prompts_before_deleting(self, app, fake_client):
        result = runner.invoke(app, ["close", "j1", "--incomplete-visits=DESTROY_ALL"], input="n\n")
        assert result.exit_code == 0
        fake_client.mutate.assert_not_called()

    def test_destroy_all_proceeds_with_force(self, app, fake_client):
        gql = fake_client
        self._closed(gql)
        result = runner.invoke(app, ["close", "j1", "--incomplete-visits=DESTROY_ALL", "--force"])
        assert result.exit_code == 0
        assert gql.mutate.call_args.kwargs["variables"]["input"] == {
            "modifyIncompleteVisitsBy": "DESTROY_ALL"
        }
