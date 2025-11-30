import re

from lib.cleaners import make_subject_uri, normalize_uri
from lib.db import (
    get_claim,
    get_edge_by_endpoints,
    get_node_by_uri,
    insert_edge,
    insert_node,
    unprocessed_claims_generator,
)
from lib.infer import extract_fallback_name, infer_details


def get_or_create_node(node_uri, raw_claim, new_node=None):
    print("IN GET OR CREATE for " + node_uri)
    normalized_uri = normalize_uri(node_uri, raw_claim["issuerId"])
    if normalized_uri is None:
        print(f"ERROR: Failed to normalize URI '{node_uri}' - skipping node creation")
        return None
    node_uri = normalized_uri
    node = get_node_by_uri(node_uri)
    if node is None:
        if new_node is None:
            name = extract_fallback_name(node_uri)
            try:
                # Infer details with proper error handling
                details = infer_details(node_uri, save_thumbnail=True)

                thumbnail_uri = ""

                if details:
                    (_, thumbnail_uri) = details

                # Create node with inferred or default details
                node = {
                    "nodeUri": node_uri,
                    "name": name or "Unknown Resource",
                    "entType": "ORGANIZATION",  # Default entity type
                    "thumbnail": thumbnail_uri,
                    "descrip": "",
                }
            except Exception as e:
                print(f"Error inferring details: {e}")
                # Create a minimal node to prevent future 404 errors
                node = {
                    "nodeUri": node_uri,
                    "name": name,
                    "entType": "ORGANIZATION",
                    "thumbnail": "",
                    "descrip": "",
                }
        else:
            node = new_node

        # Insert node
        try:
            print(f"INSERTING {node['nodeUri']}")
            node["id"] = insert_node(node)
        except Exception as e:
            print(f"Error inserting node: {e}")
            # Node object is still returned even if insertion fails

    return node


def get_or_create_edge(start_node, end_node, label, claim_id):
    print("IN GET OR CREATE EDGE for {}".format(claim_id))
    if start_node is None or end_node is None:
        print(f"ERROR: Cannot create edge for claim {claim_id} - one or both nodes are None")
        return None
    edge = get_edge_by_endpoints(start_node["id"], end_node["id"], claim_id)
    if edge is None:
        edge = {
            "startNodeId": start_node["id"],
            "endNodeId": end_node["id"],
            "label": label,
            "claimId": claim_id,
        }
        edge["id"] = insert_edge(edge)
    # TODO check for consistency with existing edge
    return edge


def make_description(raw_claim):
    descrip = ""
    if raw_claim["score"]:
        descrip += "{} score: {:.2%}".format(
            raw_claim.get("aspect", ""), raw_claim["score"]
        )

    if raw_claim["stars"]:
        descrip += "{} out of 5".format(raw_claim["stars"])

    if raw_claim["statement"]:
        descrip += "\n" + raw_claim["statement"]
    return descrip


def is_uri(string):
    pattern = re.compile(r"^(?:\w+:)?//([^\s/$.?#].[^\s]*)?$")
    return bool(re.match(pattern, string))


def process_unprocessed():
    for raw_claim in unprocessed_claims_generator():
        process_claim(raw_claim)


def process_targeted(claim_id):
    # get claim by id
    raw_claim = get_claim(claim_id)
    process_claim(raw_claim)


def process_claim(raw_claim):
    # Create or update the nodes dictionary
    print(raw_claim)
    uri = raw_claim.get("claimAddress") or raw_claim["subject"]
    if not is_uri(uri):
        print(f"Claim Address or subject {uri} is NOT valid a URI, skipping")
        return

    subject_node = get_or_create_node(uri, raw_claim)
    if subject_node is None:
        print(f"ERROR: Failed to create subject node for claim {raw_claim['id']} - skipping claim")
        return
        
    object_node = None
    object_uri = raw_claim["object"]

    if object_uri:
        object_node = get_or_create_node(raw_claim["object"], raw_claim)
        if object_node is None:
            print(f"ERROR: Failed to create object node for claim {raw_claim['id']} - skipping claim")
            return
        print("Object not source: " + object_uri)
    # if there is an object, the claim is just the relationship between the
    # subject and object likely something like "same_as" or "works_for"
    # currently we do not create a claim node for relationship claims
    if object_node:
        get_or_create_edge(
            subject_node, object_node, raw_claim["claim"], raw_claim["id"]
        )

    # TODO maybe include the source node somehow with this edge;
    # for now the claim itself is enough

    # there is no object, so the point is to attach the claim to the subject
    # in this case we make a claim node and also attach the source
    else:
        source_node = None
        source_uri = raw_claim["sourceURI"]
        if source_uri is not None:
            source_node = get_or_create_node(raw_claim["sourceURI"], raw_claim)
            if source_node is None:
                print(f"WARNING: Failed to create source node for claim {raw_claim['id']} - continuing without source")

        # Create the claim node
        claim_uri = make_subject_uri(raw_claim)

        claim_node = get_or_create_node(
            claim_uri,
            raw_claim,
            {
                "nodeUri": claim_uri,
                "name": raw_claim["claim"],
                "entType": "CLAIM",
                "descrip": make_description(raw_claim),
            },
        )
        if claim_node is None:
            print(f"ERROR: Failed to create claim node for claim {raw_claim['id']} - skipping")
            return
            
        # Create the edge from the subject node to the claim node
        get_or_create_edge(
            subject_node, claim_node, raw_claim["claim"], raw_claim["id"]
        )

        # create the edge from the claim node to the source node
        if source_node:
            get_or_create_edge(claim_node, source_node, "source", raw_claim["id"])
