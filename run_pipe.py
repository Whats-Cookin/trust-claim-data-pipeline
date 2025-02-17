from claims_to_nodes import process_unprocessed
from lib.db import cleanup

try:
    process_unprocessed()

finally:
    cleanup()


