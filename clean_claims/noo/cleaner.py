import requests
import json

def get_json_from_url(url):
    """Request a URL and parse the result as JSON."""
    response = requests.get(url)
    response.raise_for_status()  # Raises an exception if the response status is not 200
    return response.json()

def load_data_from_file(file_path):
    """Read a file and get JSON data from URLs in the last field of each line."""
    with open(file_path, 'r') as f:
        for line in f:
            (subj_url, subj_name, claim, obj_url, source_url) = line.strip().split(',')
            url = fields[-1]  # The last field
            data = get_json_from_url(url)
            # Now, data is a dictionary containing the JSON data. You can process it as needed.
            print(data)

# Test it with a file path
load_data_from_file('raw_claims_golda.csv')
#load_data_from_file('noo-raw-claims.csv')
