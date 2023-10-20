import requests 
import json
import sys

import csv

outfile = 'raw_claims.csv'
to_process = []
already_processed = [] 

def get_content(uri):
    response = requests.get(uri)
    response.raise_for_status() # Will raise an exception if the response status is not ok
    return response.json() # Returns a Python dictionary

# example uri for "knows"
# https://noo.network/api/murmur/network/ec26620b-9eb4-4ead-ba21-3067d99e31eb

# example uri for "vouches"
# https://noo.network/api/murmur/network/e3ad9e2c-40ec-4a89-afc8-b7fec35af6cf

def process_content(cn, uri):
   subj = cn['primary_url']
   subj_name = cn['name']
   raw_claims = []  
 
   for claim in cn['knows']:
     if claim['type'] != 'VOUCHES_FOR':
        next
     raw_claims.append([subj, subj_name, 'vouches_for', claim['url'], uri])
     if claim['url'] not in already_processed and claim['url'] not in to_process:
        to_process.append(claim['url'])

   with open(outfile, 'a', newline='') as cfile:
      writer = csv.writer(cfile)
      writer.writerows(raw_claims)
      

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <uri>")
        sys.exit(1)
    uri = sys.argv[1]
    to_process.append(uri)

    while to_process:
       uri = to_process.pop()
       print("on {}".format(uri))
       content = get_content(uri)
       process_content(content, uri)
       already_processed.append(uri)

    print(json.dumps(content, indent=4))

