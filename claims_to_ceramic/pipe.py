import os
import re
import subprocess
from lib.cleaners import normalize_uri
from lib.db import get_claim, unpublished_claims_generator, update_claim_proof


CERAMIC_URL = os.get_env('CERAMIC_URL')
DID_KEY = os.get_env('DID_KEY')
MODEL_ID = os.get_env('MODEL_ID')

def get_composedb_cmd(claim_json):
    return f"""composedb document:create {MODEL_ID} '{claim_json}' -c '{CERAMIC_URL}' -k {DID_KEY}"""

def publish_unpublished():
    for raw_claim in unpublished_claims_generator():
        publish_claim(raw_claim)

"""
'{"amt":{"unit":"USD","value":1500},"claim":"impact","source":{"howKnown":"FIRST_HAND","sourceID":"https://www.linkedin.com/in/goldavelez/"},"statement":"...","subjectID":"https://techsoup.org","confidence":1,"effectiveDate":"2023-11-27"}'
"""
def make_composedb_json(raw_claim):
    import pdb; pdb.set_trace()

def publish_claim(claim_json):
    cmd = get_composedb_cmd(claim_json)

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        # Handle error case
        raise Exception("Error: {result.stderr}")
    else:
        # Successful execution
        return result.stdout 

"""Creating the model instance document... Done!
kjzl6kcym7w8y6eknw5isnnxezsby9gq5tuaqbyeysjeidqerg4jvqvd2fepsz9"""
def extract_stream_id(composedb_out):
    m = re.search("Done! (k\S+)$", composedb_out)
    return m.group(1)
    

def process_claim(raw_claim):
    # Create or update the nodes dictionary
    print("On claim:" + raw_claim['subject'])
    claim_json = make_composedb_json(raw_claim)

    try:
       ceramic_claim_id = extract_stream_id(publish_claim(claim_json))
    except Exception as e:
       print("Error on publishing claim: " + str(e))

    update_claim_proof(raw_claim['id'], ceramic_claim_id)

