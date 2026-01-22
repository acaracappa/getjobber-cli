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
