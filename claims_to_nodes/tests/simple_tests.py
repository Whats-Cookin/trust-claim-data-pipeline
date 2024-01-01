import unittest
from unittest.mock import MagicMock, patch
from ..pipe import (
    get_or_create_node,
    get_or_create_edge,
    make_description,
    process_claim,
    process_single_claim,
    process_unprocessed,
)

class TestPipe(unittest.TestCase):

    @patch('lib.cleaners.normalize_uri', return_value='normalized_uri')
    @patch('lib.db.get_node_by_uri', return_value=None)
    @patch('lib.infer.infer_details', return_value=('name', 'thumbnail_uri'))
    @patch('lib.db.insert_node', return_value=1)
    def test_get_or_create_node(self, mock_insert_node, mock_infer_details, mock_get_node_by_uri, mock_normalize_uri):
        raw_claim = {
            'subject': 'subject_uri', 
            'issuerId': 1
            }
        result = get_or_create_node(raw_claim['subject'], raw_claim)
        self.assertEqual(result['nodeUri'], 'normalized_uri')
        self.assertEqual(result['name'], 'name')
        self.assertEqual(result['entType'], 'ORGANIZATION')
        self.assertEqual(result['thumbnail'], 'thumbnail_uri')
        self.assertEqual(result['descrip'], '')
        mock_normalize_uri.assert_called_once_with(raw_claim['subject'], raw_claim.get('issuerId', 1))
        mock_get_node_by_uri.assert_called_once_with('normalized_uri')
        mock_infer_details.assert_called_once_with('normalized_uri', save_thumbnail=True)
        mock_insert_node.assert_called_once_with(result)

    @patch('lib.db.get_edge_by_endpoints', return_value=None)
    @patch('lib.db.insert_edge', return_value=1)
    def test_get_or_create_edge(self, mock_insert_edge, mock_get_edge_by_endpoints):
        start_node = {'id': 1}
        end_node = {'id': 2}
        label = 'relationship'
        claim_id = 1
        result = get_or_create_edge(start_node, end_node, label, claim_id)
        self.assertEqual(result['startNodeId'], start_node['id'])
        self.assertEqual(result['endNodeId'], end_node['id'])
        self.assertEqual(result['label'], label)
        self.assertEqual(result['claimId'], claim_id)
        mock_get_edge_by_endpoints.assert_called_once_with(start_node['id'], end_node['id'], claim_id)
        mock_insert_edge.assert_called_once_with(result)

    def test_make_description(self):
        raw_claim = {'score': 0.75, 'aspect': 'reliability', 'stars': 4, 'statement': 'This is a claim'}
        result = make_description(raw_claim)
        expected_result = "reliability score: 75.00%\n4 out of 5\nThis is a claim"
        self.assertEqual(result, expected_result)

    @patch('lib.db.unprocessed_claims_generator', return_value=[{'id': 1}])
    @patch('claims_to_nodes.pipe.process_single_claim')
    def test_process_unprocessed(self, mock_process_single_claim, mock_unprocessed_claims_generator):
        process_unprocessed()
        mock_unprocessed_claims_generator.assert_called_once()
        mock_process_single_claim.assert_called_once_with({'id': 1})

    @patch('lib.db.get_claim', return_value={'id': 1})
    @patch('claims_to_nodes.process_claim')
    def test_process_single_claim(self, mock_process_claim, mock_get_claim):
        process_single_claim(1)
        mock_get_claim.assert_called_once_with(1)
        mock_process_claim.assert_called_once_with({'id': 1})

    @patch('claims_to_nodes.get_or_create_node', side_effect=[{'id': 1}, {'id': 2}])
    @patch('claims_to_nodes.get_or_create_edge')
    def test_process_claim_with_object(self, mock_get_or_create_edge, mock_get_or_create_node):
        raw_claim = {'subject': 'subject_uri', 'object': 'object_uri', 'claim': 'relationship', 'id': 1}
        process_claim(raw_claim)
        mock_get_or_create_node.assert_called_with(raw_claim['subject'], raw_claim)
        mock_get_or_create_node.assert_called_with(raw_claim['object'], raw_claim)
        mock_get_or_create_edge.assert_called_once_with({'id': 1}, {'id': 2}, 'relationship', 1)

    @patch('claims_to_nodes.get_or_create_node', side_effect=[{'id': 1}, None, {'id': 3}])
    @patch('claims_to_nodes.get_or_create_edge')
    def test_process_claim_without_object(self, mock_get_or_create_edge, mock_get_or_create_node):
        raw_claim = {'subject': 'subject_uri', 'claim': 'claim', 'id': 1, 'sourceURI': 'source_uri'}
        process_claim(raw_claim)
        mock_get_or_create_node.assert_called_with(raw_claim['subject'], raw_claim)
        mock_get_or_create_node.assert_called_with(raw_claim['sourceURI'], raw_claim)
        mock_get_or_create_edge.assert_called_once_with({'id': 1}, {'id': 3}, 'claim', 1)
        mock_get_or_create_edge.assert_called_once_with({'id': 3}, {'id': 1}, 'source', 1)

if __name__ == '__main__':
    unittest.main()
