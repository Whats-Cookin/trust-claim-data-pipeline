import sys

claim_id = sys.argv[1]

from claims_to_nodes import process_targeted

process_targeted(claim_id=claim_id)
