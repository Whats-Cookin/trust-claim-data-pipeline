import shutil
import subprocess
from io import BytesIO
from unittest.mock import MagicMock, patch

import boto3
import psycopg2
import pytest
import requests
from bs4 import BeautifulSoup
from PIL import Image

# Import optional dependencies with fallbacks
try:
    from pyvirtualdisplay import Display
    from selenium import webdriver

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

from lib.cleaners import construct_uri, make_subject_uri, normalize_uri
from lib.db import (
    del_claim,
    execute_sql_query,
    get_claim,
    get_conn,
    get_edge_by_endpoints,
    get_node_by_uri,
    insert_data,
    insert_edge,
    insert_node,
    unprocessed_claims_generator,
    unpublished_claims_generator,
    update_claim_address,
)
from lib.infer import close_display, infer_details, open_display


def check_xvfb_installed():
    return shutil.which("Xvfb") is not None


def check_chrome_installed():
    try:
        subprocess.run(
            ["google-chrome", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


# Cleaners tests
def test_construct_uri():
    assert construct_uri("test") == "https://linkedtrust.us/issuer/anon/labels/test"
    assert (
        construct_uri("test", "custom")
        == "https://linkedtrust.us/issuer/custom/labels/test"
    )


@pytest.mark.parametrize(
    "input_uri,expected",
    [
        ("www.example.com", "https://www.example.com"),
        ("https://www.example.com", "https://www.example.com"),
        ("http://www.example.com", "http://www.example.com"),
        ("just_a_word", "just_a_word"),
    ],
)
@patch("requests.get")
def test_normalize_uri(mock_get, input_uri, expected):
    # Mock responses for http/https checks
    mock_response = MagicMock()
    mock_response.ok = True
    mock_get.return_value = mock_response

    assert normalize_uri(input_uri) == expected


def test_make_subject_uri():
    raw_claim = {"id": "123"}
    expected = "https://live.linkedtrust.us/claims/123"
    assert make_subject_uri(raw_claim) == expected


# Database tests
@patch("psycopg2.connect")
def test_get_conn(mock_connect):
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    conn = get_conn()
    assert conn == mock_connect.return_value
    mock_connect.assert_called_once()


@patch("lib.db.get_conn")
def test_get_claim(mock_get_conn):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    mock_cursor.description = [("id",), ("subject",)]
    mock_cursor.fetchone.return_value = (1, "test_subject")

    result = get_claim(1)
    assert result == {"id": 1, "subject": "test_subject"}


@patch("lib.db.get_conn")
def test_unprocessed_claims_generator(mock_get_conn):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    mock_cursor.description = [("id",), ("subject",)]
    mock_cursor.fetchmany.side_effect = [[(1, "test1")], [(2, "test2")], []]

    generator = unprocessed_claims_generator()
    results = list(generator)

    assert len(results) == 2
    assert results[0] == {"id": 1, "subject": "test1"}
    assert results[1] == {"id": 2, "subject": "test2"}


@patch("lib.db.get_conn")
def test_execute_sql_query(mock_get_conn):
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn

    mock_cursor.description = [("id",)]
    mock_cursor.fetchone.return_value = (1,)

    result = execute_sql_query("SELECT * FROM test", ())
    assert result == {"id": 1}


@patch("lib.db.get_conn")
def test_update_claim_address(mock_get_conn):
    mock_cursor = MagicMock()
    mock_get_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor

    update_claim_address(1, "new_address")

    mock_cursor.execute.assert_called_once()
    mock_cursor.connection.commit.assert_called_once()


def test_update_claim_address_invalid():
    with pytest.raises(Exception):
        update_claim_address(None, "address")


# Infer tests
@patch("requests.get")
def test_infer_details_json(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"name": "Test Name", "image": "test.jpg"}
    mock_get.return_value = mock_response

    name, image = infer_details("http://example.com", save_thumbnail=False)
    assert name == "Test Name"
    assert image == "test.jpg"


@patch("requests.get")
def test_infer_details_html(mock_get):
    html_content = """
    <html>
        <head><title>Test Page</title></head>
        <body><h1>Test Header</h1></body>
    </html>
    """
    mock_response = MagicMock()
    mock_response.content = html_content.encode()
    mock_response.json.side_effect = ValueError
    mock_get.return_value = mock_response

    name, image = infer_details("http://example.com", save_thumbnail=False)
    assert name == "Test Page"
    assert image is None


@pytest.mark.skipif(
    not SELENIUM_AVAILABLE
    or not check_xvfb_installed()
    or not check_chrome_installed(),
    reason="Selenium, Xvfb or Chrome not available",
)
@patch("selenium.webdriver.Chrome")
@patch("pyvirtualdisplay.Display")
def test_open_display(mock_display, mock_chrome):
    mock_display_instance = MagicMock()
    mock_display.return_value = mock_display_instance

    display, driver = open_display()

    assert display == mock_display_instance
    mock_display_instance.start.assert_called_once()
    mock_chrome.assert_called_once()


@pytest.mark.skipif(
    not SELENIUM_AVAILABLE
    or not check_xvfb_installed()
    or not check_chrome_installed(),
    reason="Selenium, Xvfb or Chrome not available",
)
def test_close_display():
    mock_display = MagicMock()
    mock_driver = MagicMock()

    close_display(mock_display, mock_driver)

    mock_display.stop.assert_called_once()
    mock_driver.quit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
