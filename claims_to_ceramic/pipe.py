import datetime
import json
import os
import re
import subprocess
from lib.cleaners import normalize_uri
from lib.db import get_claim, unpublished_claims_generator, update_claim_address
from time import sleep


CERAMIC_URL = os.getenv('CERAMIC_URL')
DID_KEY = os.getenv('DID_KEY')
MODEL_ID = os.getenv('MODEL_ID')

def get_composedb_cmd(claim_json):
    if claim_json.get('effectiveDate') and type(claim_json['effectiveDate']) == datetime.datetime:
        claim_json['effectiveDate'] = claim_json['effectiveDate'].strftime('%Y-%m-%d')
    claim_json_str = re.sub(r'\'', '\u2019', json.dumps(claim_json))
    #cmd = f"""composedb document:create {MODEL_ID} '{claim_json_str}' -c '{CERAMIC_URL}' -k {DID_KEY}"""
    cmd = f"""cd /data/trust-claim-data-pipeline/nody; node publish.mjs '{claim_json_str}'"""
    return cmd

def is_useful(raw_claim):
    return bool(raw_claim.get('claim') and raw_claim.get('subject') and (raw_claim.get('statement') or raw_claim.get('object')) and raw_claim.get('effectiveDate'))

def publish_unpublished():
    for raw_claim in unpublished_claims_generator():
        if is_useful(raw_claim):
          publish_claim(raw_claim)
        else:
          print("Skipping claim about " + raw_claim.get('subject') + " bc of missing fields")

"""
'{"amt":{"unit":"USD","value":1500},"claim":"impact","source":{"howKnown":"FIRST_HAND","sourceID":"https://www.linkedin.com/in/goldavelez/"},"statement":"...","subjectID":"https://techsoup.org","confidence":1,"effectiveDate":"2023-11-27"}'
"""
SAME_KEYS = ['claim', 'statement', 'effectiveDate', 'confidence', 'object']
def make_compose_json(raw_claim):
    # first copy over the keys that directly map
    compose_json = {k:raw_claim[k] for k in SAME_KEYS if raw_claim.get(k)}
    compose_json['subjectID'] = raw_claim['subject'] # should be already normalized but don't change it

    if raw_claim.get('amt'):
        unit = raw_claim.get('unit') or 'USD'
        compose_json['amt'] = {'unit': unit, 'value':raw_claim['amt']}

    if raw_claim.get('source'):
        how_known = raw_claim.get('howKnown', 'WEB_DOCUMENT')
        compose_json['source'] = { "howKnown": how_known, "sourceID":raw_claim['source']}

    if raw_claim.get('score') or raw_claim.get('stars'):
        compose_json['rating'] = {k:raw_claim[k] for k in ('aspect', 'stars', 'score') if raw_claim.get(k)}
        score = compose_json['rating'].get('score')
        if score and score > 1:
            compose_json['rating']['score'] = 1
        if score and score < -1:
            compose_json['rating']['score'] = -1

        # score is required
        if score is None:
            compose_json['rating']['score'] = compose_json['rating']['stars']/5.0

    if 'effectiveDate' not in compose_json:
        compose_json['effectiveDate'] = datetime.datetime.today().strftime("%Y-%m-%d")

    return compose_json


def run_publish(claim_json):
    cmd = get_composedb_cmd(claim_json)

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        # first try just sleeping
        sleep(10)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
           return result.stdout

        sleep(100)
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
           return result.stdout

        # sleeping did not help, it is an error 

        # Handle error case
        raise Exception(f"Error: {result.stderr}")
    else:
        # Successful execution
        return result.stdout 

"""Creating the model instance document... Done!
kjzl6kcym7w8y6eknw5isnnxezsby9gq5tuaqbyeysjeidqerg4jvqvd2fepsz9"""
def extract_stream_id(composedb_out):
    # apparently the other stuff is on stderr
    return composedb_out.strip() 
    

def publish_claim(raw_claim):
    # Create or update the nodes dictionary
    print("On claim:" + raw_claim['subject'])
    claim_json = make_compose_json(raw_claim)

    cmd_out = run_publish(claim_json)
    ceramic_claim_id = extract_stream_id(cmd_out)
    if not ceramic_claim_id:
        import pdb; pdb.set_trace()
    #except Exception as e:
    #   print("Error on publishing claim: " + str(e))
    #   import pdb; pdb.set_trace()

    update_claim_address(raw_claim['id'], ceramic_claim_id)
    print("updated claim {} with {}".format(raw_claim['id'], ceramic_claim_id))
