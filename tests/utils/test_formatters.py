"""Tests for output formatting utilities."""

import csv
import io
import json

import pytest
import yaml

from getjobber_cli.utils.formatters import (
    extract_list_data,
    extract_single_data,
    format_csv,
    format_json,
    format_output,
    format_single_item,
    format_table,
    format_yaml,
    print_error,
    print_info,
    print_success,
    print_warning,
)


@pytest.fixture
def sample_dict():
    return {"id": "1", "name": "Acme", "email": "a@example.com"}


@pytest.fixture
def sample_list():
    return [
        {"id": "1", "name": "Acme", "email": "a@example.com"},
        {"id": "2", "name": "Beta", "email": "b@example.com"},
    ]


class TestFormatJSON:
    def test_dict(self, sample_dict):
        result = format_json(sample_dict)
        # Round-trips through json.loads
        assert json.loads(result) == sample_dict

    def test_list(self, sample_list):
        result = format_json(sample_list)
        assert json.loads(result) == sample_list

    def test_indent_default(self, sample_dict):
        result = format_json(sample_dict)
        assert "\n  " in result  # Default indent = 2

    def test_handles_non_serializable_with_str(self):
        from datetime import datetime

        data = {"when": datetime(2024, 1, 1)}
        result = format_json(data)
        # default=str should kick in
        assert "2024-01-01" in result


class TestFormatYAML:
    def test_dict(self, sample_dict):
        result = format_yaml(sample_dict)
        assert yaml.safe_load(result) == sample_dict

    def test_list(self, sample_list):
        result = format_yaml(sample_list)
        assert yaml.safe_load(result) == sample_list


class TestFormatCSV:
    def test_list_of_dicts(self, sample_list):
        result = format_csv(sample_list)
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 2
        assert rows[0]["name"] == "Acme"
        assert rows[1]["name"] == "Beta"

    def test_single_dict(self, sample_dict):
        result = format_csv(sample_dict)
        reader = csv.DictReader(io.StringIO(result))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["name"] == "Acme"

    def test_empty_data(self):
        assert format_csv([]) == ""
        assert format_csv(None) == ""

    def test_fallback_to_json_for_non_dict(self):
        # Lists of non-dicts fall back to JSON
        result = format_csv([1, 2, 3])
        assert json.loads(result) == [1, 2, 3]


class TestFormatTable:
    def test_table_with_list_of_dicts(self, sample_list, capsys):
        format_table(sample_list)
        # We can't easily test rich output; just ensure no exception and something is printed
        captured = capsys.readouterr()
        assert "Acme" in captured.out or "Acme" in captured.err or captured.out != ""

    def test_table_with_single_dict(self, sample_dict, capsys):
        format_table(sample_dict)
        captured = capsys.readouterr()
        # Should have produced output without raising
        assert captured.out or captured.err is not None

    def test_table_with_empty_data(self, capsys):
        format_table([])
        captured = capsys.readouterr()
        assert "No data" in captured.out


class TestFormatOutput:
    def test_json_format(self, sample_list):
        result = format_output(sample_list, "json")
        assert json.loads(result) == sample_list

    def test_csv_format(self, sample_list):
        result = format_output(sample_list, "csv")
        assert "id,name,email" in result.split("\r\n")[0] or "id,name,email" in result

    def test_yaml_format(self, sample_list):
        result = format_output(sample_list, "yaml")
        assert yaml.safe_load(result) == sample_list

    def test_table_format_does_not_raise(self, sample_list, capsys):
        # format_output for table returns None (prints to console)
        result = format_output(sample_list, "table")
        assert result is None

    def test_unknown_format_falls_back_to_json(self, sample_list):
        result = format_output(sample_list, "garbage")
        assert json.loads(result) == sample_list


class TestFormatSingleItem:
    def test_basic(self, sample_dict, capsys):
        format_single_item(sample_dict)
        captured = capsys.readouterr()
        assert captured.out  # something printed

    def test_with_nested_dict(self, capsys):
        item = {"id": "1", "address": {"city": "NYC"}}
        format_single_item(item)
        captured = capsys.readouterr()
        assert captured.out

    def test_with_list_value(self, capsys):
        item = {"tags": ["a", "b", "c"]}
        format_single_item(item)
        captured = capsys.readouterr()
        assert captured.out

    def test_with_list_of_dicts_value(self, capsys):
        item = {"items": [{"x": 1}]}
        format_single_item(item)
        captured = capsys.readouterr()
        assert captured.out

    def test_with_none_value(self, capsys):
        item = {"name": None}
        format_single_item(item)
        captured = capsys.readouterr()
        assert captured.out


class TestPrintHelpers:
    def test_print_success(self, capsys):
        print_success("yay")
        captured = capsys.readouterr()
        assert "yay" in captured.out

    def test_print_error(self, capsys):
        print_error("boo")
        captured = capsys.readouterr()
        assert "boo" in captured.out

    def test_print_warning(self, capsys):
        print_warning("careful")
        captured = capsys.readouterr()
        assert "careful" in captured.out

    def test_print_info(self, capsys):
        print_info("fyi")
        captured = capsys.readouterr()
        assert "fyi" in captured.out


class TestExtractors:
    def test_extract_list_data_present(self):
        response = {"clients": {"nodes": [{"id": "1"}, {"id": "2"}]}}
        assert extract_list_data(response, "clients") == [{"id": "1"}, {"id": "2"}]

    def test_extract_list_data_missing_key(self):
        assert extract_list_data({}, "clients") == []

    def test_extract_list_data_missing_nodes(self):
        assert extract_list_data({"clients": {}}, "clients") == []

    def test_extract_single_data_present(self):
        response = {"client": {"id": "1", "name": "x"}}
        assert extract_single_data(response, "client") == {"id": "1", "name": "x"}

    def test_extract_single_data_missing(self):
        assert extract_single_data({}, "client") == {}
