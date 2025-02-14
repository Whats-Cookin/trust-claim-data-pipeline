import unittest
from unittest.mock import patch, MagicMock
import pytest

from claims_to_nodes.pipe import (
    get_or_create_node,
    get_or_create_edge,
    make_description,
    is_uri,
    process_claim,
    process_targeted,
    process_unprocessed,
)

# Define base patch path - still need this for mocking
PATCH_BASE = "claims_to_nodes.pipe."


class TestPipe(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.sample_raw_claim = {
            "id": "123",
            "subject": "http://example.com/entity1",
            "object": "http://example.com/entity2",
            "claim": "works_for",
            "issuerId": "issuer1",
            "score": 0.85,
            "aspect": "reliability",
            "stars": 4,
            "statement": "This is a test statement",
            "sourceURI": "http://example.com/source",
        }

    def tearDown(self):
        """Clean up after each test"""
        pass

    @patch(PATCH_BASE + "normalize_uri")
    @patch(PATCH_BASE + "get_node_by_uri")
    @patch(PATCH_BASE + "infer_details")
    @patch(PATCH_BASE + "insert_node")
    def test_get_or_create_node_new(
        self, mock_insert, mock_infer, mock_get_node, mock_normalize
    ):
        """Test creating a new node when it doesn't exist"""
        mock_normalize.return_value = "normalized_uri"
        mock_get_node.return_value = None
        mock_infer.return_value = ("Test Name", "thumbnail.jpg")
        mock_insert.return_value = 1

        result = get_or_create_node("http://example.com/entity", self.sample_raw_claim)

        assert result["nodeUri"] == "normalized_uri"
        assert result["name"] == "Test Name"
        assert result["thumbnail"] == "thumbnail.jpg"
        assert result["id"] == 1

    @patch(PATCH_BASE + "normalize_uri")
    @patch(PATCH_BASE + "get_node_by_uri")
    def test_get_or_create_node_existing(self, mock_get_node, mock_normalize):
        """Test retrieving an existing node"""
        existing_node = {"id": 1, "nodeUri": "normalized_uri", "name": "Existing"}
        mock_normalize.return_value = "normalized_uri"
        mock_get_node.return_value = existing_node

        result = get_or_create_node("http://example.com/entity", self.sample_raw_claim)

        assert result == existing_node

    @patch(PATCH_BASE + "get_edge_by_endpoints")
    @patch(PATCH_BASE + "insert_edge")
    def test_get_or_create_edge_new(self, mock_insert, mock_get_edge):
        """Test creating a new edge when it doesn't exist"""
        mock_get_edge.return_value = None
        mock_insert.return_value = 1

        start_node = {"id": 1}
        end_node = {"id": 2}

        result = get_or_create_edge(start_node, end_node, "works_for", "123")

        assert result["startNodeId"] == 1
        assert result["endNodeId"] == 2
        assert result["label"] == "works_for"
        assert result["id"] == 1

    def test_make_description(self):
        """Test description creation from raw claim"""
        result = make_description(self.sample_raw_claim)
        expected = "reliability score: 85.00%4 out of 5\nThis is a test statement"
        assert result == expected

    def test_is_uri(self):
        """Test URI validation"""
        assert is_uri("http://example.com")
        assert is_uri("https://example.com/path")
        assert not is_uri("not a uri")
        assert not is_uri("http:/missing-slashes")

    @patch(PATCH_BASE + "get_or_create_node")
    @patch(PATCH_BASE + "get_or_create_edge")
    def test_process_claim_with_object(self, mock_create_edge, mock_create_node):
        """Test processing a claim with subject and object"""
        mock_create_node.side_effect = [
            {"id": 1, "nodeUri": "subject"},
            {"id": 2, "nodeUri": "object"},
        ]

        process_claim(self.sample_raw_claim)

        assert mock_create_node.call_count == 2
        mock_create_edge.assert_called_once()

    @patch(PATCH_BASE + "get_claim")
    @patch(PATCH_BASE + "process_claim")
    def test_process_targeted(self, mock_process_claim, mock_get_claim):
        """Test processing a specific claim by ID"""
        mock_get_claim.return_value = self.sample_raw_claim

        process_targeted("123")

        mock_get_claim.assert_called_once_with("123")
        mock_process_claim.assert_called_once_with(self.sample_raw_claim)

    @patch(PATCH_BASE + "unprocessed_claims_generator")
    @patch(PATCH_BASE + "process_claim")
    def test_process_unprocessed(self, mock_process_claim, mock_generator):
        """Test processing all unprocessed claims"""
        mock_generator.return_value = [self.sample_raw_claim]

        process_unprocessed()

        mock_process_claim.assert_called_once_with(self.sample_raw_claim)


if __name__ == "__main__":
    unittest.main()
