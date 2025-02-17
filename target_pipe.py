import sys
from lib.db import cleanup

claim_id = sys.argv[1]

from claims_to_nodes import process_targeted

try:
    process_targeted(claim_id=claim_id)
finally:
    cleanup()
