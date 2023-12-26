from ..lib.db import insert_claim
from ..claims_to_nodes.pipe import *

def process_single_claim(raw_claim):
    # Create or update the nodes dictionary
    subject_node = get_or_create_node(raw_claim['subject'], raw_claim)
    object_node = None

    # Handle the claim based on the how_known value
    if raw_claim['how_known'] == "rated" or raw_claim['how_known'] == "helped" or raw_claim['how_known'] == "scam" or raw_claim['how_known'] == "owns" or raw_claim['how_known'] == "others":
        # Get or create the object node
        object_node = get_or_create_node(raw_claim['claim'], raw_claim)

        # Create the edge from the subject node to the object node
        get_or_create_edge(subject_node, object_node, raw_claim['claim'], raw_claim.get('id'))

        # TODO: Include the source node somehow with this edge; for now, the claim itself is enough

    else:
        source_node = None
        if raw_claim['sourceURI']:
            source_node = get_or_create_node(raw_claim['sourceURI'], raw_claim)

        # Create the claim node
        claim_id = raw_claim.get('id')
        claim_uri = f"https://linkedtrust.us/claims/{claim_id}" or raw_claim['claimAddress']
        claim_node = get_or_create_node(claim_uri, raw_claim, {
            "nodeUri": claim_uri,
            "name": raw_claim['claim'],
            "entType": "CLAIM",
            "descrip": make_description(raw_claim)
        })

        # Create the edge from the subject node to the claim node
        get_or_create_edge(subject_node, claim_node, raw_claim['claim'], raw_claim.get('id')) # TODO make the claim id get from claim model
        
        # Create the edge from the claim node to the source node
        if source_node:
            get_or_create_edge(claim_node, source_node, 'source', raw_claim.get('id'))# TODO make the claim id get from claim model

        # # Store the claim in the database
        insert_claim(raw_claim)