import unittest
from lib.cleaners import normalize_uri

class TestPipe(unittest.TestCase):
    def setUp(self):
        # Set up any resources needed for the tests
        pass

    def test_normalize_uri(self):
        # Test the functionality of my_function()
        self.assertEqual(normalize_uri('www.ecolunchboxes.com'), 'https://www.ecolunchboxes.com')

    def tearDown(self):
        # Clean up any resources used by the tests
        pass

if __name__ == '__main__':
    unittest.main()
