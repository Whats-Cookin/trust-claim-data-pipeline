import argparse
from claims_to_nodes import process_unprocessed, process_all
from lib.db import cleanup

parser = argparse.ArgumentParser(description='Process claims into nodes and edges')
parser.add_argument('--all', action='store_true', help='Reprocess ALL claims (not just new ones)')
args = parser.parse_args()

try:
    if args.all:
        print("Processing ALL claims...")
        process_all()
    else:
        print("Processing only unprocessed claims...")
        process_unprocessed()

finally:
    cleanup()

