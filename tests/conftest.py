"""Pytest configuration and fixtures for GetJobber CLI tests."""

import pytest
from unittest.mock import Mock, MagicMock


@pytest.fixture
def mock_config():
    """Mock configuration."""
    config = Mock()
    config.get.return_value = "test_value"
    config.is_configured.return_value = True
    return config


@pytest.fixture
def mock_token_manager():
    """Mock token manager."""
    token_manager = Mock()
    token_manager.is_authenticated.return_value = True
    token_manager.get_access_token.return_value = "test_access_token"
    token_manager.get_tokens.return_value = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_at": 9999999999,
        "token_type": "Bearer",
    }
    return token_manager


@pytest.fixture
def mock_graphql_client():
    """Mock GraphQL client."""
    client = Mock()
    client.query.return_value = {"clients": {"nodes": []}}
    client.mutate.return_value = {"clientCreate": {"client": {"id": "test_id"}}}
    return client


@pytest.fixture
def sample_client_data():
    """Sample client data."""
    return {
        "id": "123",
        "firstName": "John",
        "lastName": "Doe",
        "email": "john@example.com",
        "phoneNumber": "555-1234",
    }


@pytest.fixture
def sample_job_data():
    """Sample job data."""
    return {
        "id": "456",
        "title": "Test Job",
        "jobNumber": "JOB-001",
        "status": "active",
        "client": {
            "id": "123",
            "firstName": "John",
            "lastName": "Doe",
        },
    }


@pytest.fixture
def sample_quote_data():
    """Sample quote data."""
    return {
        "id": "789",
        "quoteNumber": "Q-001",
        "title": "Test Quote",
        "status": "draft",
        "totalAmount": "100.00",
    }


@pytest.fixture
def sample_invoice_data():
    """Sample invoice data."""
    return {
        "id": "999",
        "invoiceNumber": "INV-001",
        "subject": "Test Invoice",
        "status": "unpaid",
        "totalAmount": "200.00",
        "balance": "200.00",
    }


@pytest.fixture
def mock_authenticated_token_manager(mock_token_manager, monkeypatch):
    """Patch get_token_manager across command modules to return an
    authenticated mock token manager.
    """
    targets = [
        "getjobber_cli.commands.client_commands.get_token_manager",
        "getjobber_cli.commands.job_commands.get_token_manager",
        "getjobber_cli.commands.quote_commands.get_token_manager",
        "getjobber_cli.commands.invoice_commands.get_token_manager",
        "getjobber_cli.commands.auth_commands.get_token_manager",
    ]
    for target in targets:
        try:
            monkeypatch.setattr(target, lambda tm=mock_token_manager: tm)
        except (AttributeError, ImportError):
            pass
    return mock_token_manager


@pytest.fixture
def mock_graphql_client_factory(monkeypatch, mock_graphql_client):
    """Patch GraphQLClient construction across command modules to return a mock."""
    targets = [
        "getjobber_cli.commands.client_commands.GraphQLClient",
        "getjobber_cli.commands.job_commands.GraphQLClient",
        "getjobber_cli.commands.quote_commands.GraphQLClient",
        "getjobber_cli.commands.invoice_commands.GraphQLClient",
    ]
    for target in targets:
        try:
            monkeypatch.setattr(target, lambda *a, **kw: mock_graphql_client)
        except (AttributeError, ImportError):
            pass
    return mock_graphql_client
