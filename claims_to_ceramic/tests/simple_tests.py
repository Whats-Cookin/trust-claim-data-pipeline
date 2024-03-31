import unittest
from unittest.mock import patch
from ..pipe import publish_claim, make_compose_json, run_publish, update_claim_address, extract_stream_id

# Test case for publish_claim function
class TestPublishClaim(unittest.TestCase):

    # Initializing raw_claim and expected_compose_json variables
    raw_claim = {
        'id': 'claim_id',
        'claim': 'claim',
        'statement': 'statement',
        'effectiveDate': '2023-11-27',
        'confidence': 1,
        'object': 'object',
        'subject': 'subject_uri',

        }
    
    expected_compose_json = {
        'claim': 'claim',
        'statement': 'statement',
        'effectiveDate': '2023-11-27',
        'confidence': 1,
        'object': 'object',
        'subjectID': 'subject_uri'
        }
    
    claim_json = {
        'claim': 'claim',
        }
    
    @patch('claims_to_ceramic.pipe.run_publish')
    @patch('claims_to_ceramic.pipe.update_claim_address')
    def test_publish_claim(self, mock_update_claim_address, mock_run_publish):
        mock_run_publish.return_value = 'kjzl6kcym7w8y6eknw5isnnxezsby9gq5tuaqbyeysjeidqerg4jvqvd2fepsz9'
        
        publish_claim(self.raw_claim)

        mock_run_publish.assert_called_once()
        mock_update_claim_address.assert_called_once_with('claim_id', 'kjzl6kcym7w8y6eknw5isnnxezsby9gq5tuaqbyeysjeidqerg4jvqvd2fepsz9')

    def test_make_compose_json(self):
        compose_json = make_compose_json(self.raw_claim)

        self.assertEqual(compose_json, self.expected_compose_json)

    @patch('subprocess.run')
    def test_run_publish(self, mock_subprocess_run):
        mock_subprocess_run.return_value.stdout = 'output'
        mock_subprocess_run.return_value.returncode = 0

        result = run_publish(self.claim_json)

        mock_subprocess_run.assert_called_once()
        self.assertEqual(result, 'output')

    def test_extract_stream_id(self):
        composedb_out = 'kjzl6kcym7w8y6eknw5isnnxezsby9gq5tuaqbyeysjeidqerg4jvqvd2fepsz9'
        stream_id = extract_stream_id(composedb_out)

        self.assertEqual(stream_id, 'kjzl6kcym7w8y6eknw5isnnxezsby9gq5tuaqbyeysjeidqerg4jvqvd2fepsz9')

if __name__ == '__main__':
    unittest.main()
