"""Tests for configuration management."""

import pytest
from pathlib import Path
from getjobber_cli.utils.config import Config


def test_config_initialization(tmp_path):
    """Test config initialization."""
    config = Config(config_dir=tmp_path / ".getjobber")
    assert config.config_dir.exists()


def test_config_set_get(tmp_path):
    """Test setting and getting config values."""
    config = Config(config_dir=tmp_path / ".getjobber")
    config.set("test_key", "test_value")
    assert config.get("test_key") == "test_value"


def test_config_default_values(tmp_path):
    """Test default configuration values."""
    config = Config(config_dir=tmp_path / ".getjobber")
    assert config.get("default_output_format") == "table"
    assert config.get("items_per_page") == 20


def test_config_is_configured(tmp_path):
    """Test is_configured check."""
    config = Config(config_dir=tmp_path / ".getjobber")
    assert not config.is_configured()

    config.set("client_id", "test_id")
    config.set("client_secret", "test_secret")
    assert config.is_configured()


def test_config_reset(tmp_path):
    """Test configuration reset."""
    config = Config(config_dir=tmp_path / ".getjobber")
    config.set("test_key", "test_value")
    config.reset()
    assert config.get("test_key") is None
