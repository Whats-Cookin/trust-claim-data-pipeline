import unittest
from flask import Flask
from ...claims_to_nodes.pipe import process_targeted


class TestMicroservice(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def test_process_claim_success(self, claim_id):
        with self.app.test_request_context():
            response = self.client.post(f"/process_claim/{claim_id}")
            data = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertEqual(data["message"], "Claim processed successfully")

    def test_process_claim_failure(self, claim_id):
        with self.app.test_request_context():
            response = self.client.post(f"/process_claim/{claim_id}")
            data = response.get_json()

            self.assertEqual(response.status_code, 500)
            self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
