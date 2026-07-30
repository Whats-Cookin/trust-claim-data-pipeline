import os
from io import BytesIO
from unittest.mock import MagicMock, patch

import psycopg2
import pytest
import requests
from bs4 import BeautifulSoup
from PIL import Image

from lib.cleaners import construct_uri, make_subject_uri, normalize_uri, get_base_url
from lib.db import (
    del_claim,
    execute_sql_query,
    get_claim,
    get_db_connection,
    get_edge_by_endpoints,
    get_node_by_uri,
    insert_data,
    insert_edge,
    insert_node,
    unprocessed_claims_generator,
    unpublished_claims_generator,
    update_claim_address,
)
from lib.infer import infer_details


# Cleaners tests
@patch.dict("os.environ", {}, clear=True)
def test_construct_uri():
    assert construct_uri("test") == "https://live.linkedtrust.us/issuer/anon/labels/test"
    assert (
        construct_uri("test", "custom")
        == "https://live.linkedtrust.us/issuer/custom/labels/test"
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


# Test normalize_uri with numeric inputs (should return URI unchanged)
@pytest.mark.parametrize(
    "input_uri,issuer_id,expected_contains",
    [
        ("123", "anon", "123"),  # Bare number should be returned as-is
        ("456", "user123", "456"),  # Bare number with issuer
        ("https://example.com/123", None, "https://example.com/123"),  # Valid URI
    ],
)
def test_normalize_uri_numeric_inputs(input_uri, issuer_id, expected_contains):
    result = normalize_uri(input_uri, issuer_id)
    assert expected_contains in result


@patch.dict("os.environ", {}, clear=True)
def test_make_subject_uri():
    raw_claim = {"id": "123"}
    expected = "https://live.linkedtrust.us/claims/123"
    assert make_subject_uri(raw_claim) == expected


@patch.dict("os.environ", {"FRONTEND_URL": "https://test.com"})
def test_make_subject_uri_with_env():
    raw_claim = {"id": "456"}
    expected = "https://test.com/claims/456"
    assert make_subject_uri(raw_claim) == expected


# Test get_base_url with environment variables
@patch.dict("os.environ", {}, clear=True)
def test_get_base_url_default():
    assert get_base_url() == "https://live.linkedtrust.us"


@patch.dict("os.environ", {"BASE_URL": "https://test.example.com"})
def test_get_base_url_with_base_url():
    assert get_base_url() == "https://test.example.com"


@patch.dict("os.environ", {"FRONTEND_URL": "https://frontend.example.com"})
def test_get_base_url_with_frontend_url():
    assert get_base_url() == "https://frontend.example.com"


@patch.dict("os.environ", {
    "BASE_URL": "https://test.example.com",
    "FRONTEND_URL": "https://frontend.example.com"
})
def test_get_base_url_frontend_takes_precedence():
    assert get_base_url() == "https://frontend.example.com"


# Database tests
#
# lib.db hands out connections from a ThreadedConnectionPool, so the tests fake the
# pool rather than psycopg2.connect: get_pool() -> getconn() -> a connection whose
# cursor() is a context manager. `closed = False` matters — get_db_connection only
# commits and returns the connection to the pool when the connection is still open,
# and a bare MagicMock attribute would read as closed.
def _fake_pool(mock_get_pool):
    """Wire pool -> connection -> cursor and hand back the last two."""
    mock_cursor = MagicMock()
    mock_conn = MagicMock()
    mock_conn.closed = False
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_pool.return_value.getconn.return_value = mock_conn
    return mock_conn, mock_cursor


@patch("lib.db.get_pool")
def test_get_db_connection_commits_and_returns_the_connection(mock_get_pool):
    mock_conn, _ = _fake_pool(mock_get_pool)

    with get_db_connection() as conn:
        assert conn is mock_conn

    mock_conn.commit.assert_called_once()
    mock_get_pool.return_value.putconn.assert_called_once_with(mock_conn)


@patch("lib.db.get_pool")
def test_get_db_connection_leaves_a_closed_connection_alone(mock_get_pool):
    mock_conn, _ = _fake_pool(mock_get_pool)
    mock_conn.closed = True

    with get_db_connection():
        pass

    mock_conn.commit.assert_not_called()
    mock_get_pool.return_value.putconn.assert_not_called()


@patch("lib.db.get_pool")
def test_get_claim(mock_get_pool):
    _, mock_cursor = _fake_pool(mock_get_pool)

    mock_cursor.description = [("id",), ("subject",)]
    mock_cursor.fetchone.return_value = (1, "test_subject")

    result = get_claim(1)
    assert result == {"id": 1, "subject": "test_subject"}


@patch("lib.db.get_pool")
def test_get_claim_missing_returns_none(mock_get_pool):
    _, mock_cursor = _fake_pool(mock_get_pool)

    mock_cursor.description = [("id",), ("subject",)]
    mock_cursor.fetchone.return_value = None

    assert get_claim(404) is None


@patch("lib.db.get_pool")
def test_unprocessed_claims_generator(mock_get_pool):
    _, mock_cursor = _fake_pool(mock_get_pool)

    mock_cursor.description = [("id",), ("subject",)]
    # First fetchone is the latest processed claim id; then batches until one comes back empty.
    mock_cursor.fetchone.return_value = (0,)
    mock_cursor.fetchmany.side_effect = [[(1, "test1")], [(2, "test2")], []]

    generator = unprocessed_claims_generator()
    results = list(generator)

    assert len(results) == 2
    assert results[0] == {"id": 1, "subject": "test1"}
    assert results[1] == {"id": 2, "subject": "test2"}


@patch("lib.db.get_pool")
def test_execute_sql_query(mock_get_pool):
    _, mock_cursor = _fake_pool(mock_get_pool)

    mock_cursor.description = [("id",)]
    mock_cursor.fetchone.return_value = (1,)

    result = execute_sql_query("SELECT * FROM test", ())
    assert result == {"id": 1}


@patch("lib.db.get_pool")
def test_update_claim_address(mock_get_pool):
    mock_conn, mock_cursor = _fake_pool(mock_get_pool)

    update_claim_address(1, "new_address")

    mock_cursor.execute.assert_called_once()
    # The commit belongs to the connection context manager now, not the cursor.
    mock_conn.commit.assert_called_once()


def test_update_claim_address_invalid():
    with pytest.raises(Exception):
        update_claim_address(None, "address")


# Infer tests
#
# infer_details reads status_code, headers["Content-Type"] and history off the response,
# so a bare MagicMock is not enough: an unset status_code never equals 200, the HTML is
# never parsed, and every case quietly returns the hostname fallback. _fake_response
# spells the three out.
def _fake_response(content=b"", content_type="text/html", status_code=200):
    response = MagicMock()
    response.content = content
    response.status_code = status_code
    response.headers = {"Content-Type": content_type}
    response.history = []
    return response


@patch("requests.get")
def test_infer_details_json(mock_get):
    mock_response = _fake_response(content_type="application/json")
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
    mock_response = _fake_response(content=html_content.encode())
    mock_response.json.side_effect = ValueError
    mock_get.return_value = mock_response

    name, image = infer_details("http://example.com", save_thumbnail=False)
    assert name == "Test Page"
    assert image is None


@patch("requests.get")
def test_infer_details_falls_back_to_the_last_path_segment(mock_get):
    """A page that answers but carries no title falls back to the URI itself: the last
    path segment, tidied up, and the hostname only when there is no path."""
    mock_get.return_value = _fake_response(content=b"<html><body></body></html>")

    name, image = infer_details("http://example.com/some/annual-report", save_thumbnail=False)
    assert name == "Annual Report"
    assert image is None


@patch("requests.get")
def test_infer_details_falls_back_to_the_hostname_without_a_path(mock_get):
    mock_get.return_value = _fake_response(content=b"<html><body></body></html>")

    name, _ = infer_details("http://www.example.com/", save_thumbnail=False)
    assert name == "example.com"


# The browser-screenshot path (open_display / close_display, Selenium + Xvfb) is gone
# from lib/infer.py, so the two tests that drove it are gone with it, along with the
# Selenium and Xvfb availability checks that only those tests used.


if __name__ == "__main__":
    pytest.main([__file__])
