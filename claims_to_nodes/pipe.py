import re

from lib.cleaners import make_subject_uri, normalize_uri
from lib.db import (
    get_claim,
    get_credential,
    get_edge_by_endpoints,
    get_node_by_uri,
    insert_edge,
    insert_node,
    unprocessed_entities_generator,
)
from lib.infer import infer_details


def get_or_create_node(node_uri, raw_entity, new_node=None):
    print("IN GET OR CREATE for " + node_uri)
    node_uri = normalize_uri(node_uri, raw_entity["issuerId"])
    node = get_node_by_uri(node_uri)
    if node is None:
        if new_node is None:
            details = infer_details(node_uri, save_thumbnail=True)

            name = ""
            thumbnail_uri = ""

            if details:
                (name, thumbnail_uri) = details

            # TODO infer or default to UNKNOWN for later edit
            entType = "ORGANIZATION"
            node = {
                "nodeUri": node_uri,
                "name": name,
                "entType": entType,
                "thumbnail": thumbnail_uri,
                "descrip": "",
            }
        else:
            node = new_node
        print("INSERTING " + node["nodeUri"])
        node["id"] = insert_node(node)
    # TODO possibly update the node if exists
    return node


def get_or_create_edge(start_node, end_node, label, claim_id):
    print("IN GET OR CREATE EDGE for {}".format(claim_id))
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


def make_description(raw_entity):
    descrip = ""
    if raw_entity["score"]:
        descrip += "{} score: {:.2%}".format(
            raw_entity.get("aspect", ""), raw_entity["score"]
        )

    if raw_entity["stars"]:
        descrip += "{} out of 5".format(raw_entity["stars"])

    if raw_entity["statement"]:
        descrip += "\n" + raw_entity["statement"]
    return descrip


def is_uri(string):
    pattern = re.compile(r"^(?:\w+:)?//([^\s/$.?#].[^\s]*)?$")
    return bool(re.match(pattern, string))


def process_unprocessed():
    for raw_entity in unprocessed_entities_generator():  # Update generator if needed to include credentials
        process_entity(raw_entity)


def process_targeted(entity_id, entity_type="claim"):
    # Get claim or credential by id
    raw_entity = get_claim(entity_id) if entity_type == "claim" else get_credential(entity_id)  # Ensure get_credential is defined
    process_entity(raw_entity, entity_type)


def process_entity(raw_entity, entity_type="claim"):
    uri = raw_entity.get("claimAddress") or raw_entity.get("subject") or raw_entity.get("credentialSubject")
    if not is_uri(uri):
        print(f"{entity_type.capitalize()} Address or subject {uri} is NOT a valid URI, skipping")
        return

    subject_node = get_or_create_node(uri, raw_entity)
    object_node = None
    object_uri = raw_entity.get("object")

    if object_uri:
        object_node = get_or_create_node(object_uri, raw_entity)
        print(f"Object not source: {object_uri}")

    if object_node:
        get_or_create_edge(subject_node, object_node, raw_entity["claim"], raw_entity["id"])
    else:
        source_node = None
        source_uri = raw_entity.get("sourceURI")
        if source_uri is not None:
            source_node = get_or_create_node(source_uri, raw_entity)

        # Create the entity node (claim/credential)
        entity_uri = make_subject_uri(raw_entity)

        entity_node = get_or_create_node(
            entity_uri,
            raw_entity,
            {
                "nodeUri": entity_uri,
                "name": raw_entity["claim"] if entity_type == "claim" else raw_entity["credentialName"],
                "entType": entity_type.upper(),
                "descrip": make_description(raw_entity),
            },
        )

        get_or_create_edge(subject_node, entity_node, raw_entity["claim"], raw_entity["id"])

        if source_node:
            get_or_create_edge(entity_node, source_node, "source", raw_entity["id"])

    # Create or update the nodes dictionary
    uri = raw_entity["claimAddress"] or raw_entity["subject"]
    if not is_uri(uri):
        print(f"Claim Address or subject {uri} is NOT valid a URI, skipping")
        return

    subject_node = get_or_create_node(uri, raw_entity)
    object_node = None
    object_uri = raw_entity["object"]

    if object_uri:
        object_node = get_or_create_node(raw_entity["object"], raw_entity)
        print("Object not source: " + object_uri)
    # if there is an object, the claim is just the relationship between the
    # subject and object likely something like "same_as" or "works_for"
    # currently we do not create a claim node for relationship claims
    if object_node:
        get_or_create_edge(
            subject_node, object_node, raw_entity["claim"], raw_entity["id"]
        )

    # TODO maybe include the source node somehow with this edge;
    # for now the claim itself is enough

    # there is no object, so the point is to attach the claim to the subject
    # in this case we make a claim node and also attach the source
    else:
        source_node = None
        source_uri = raw_entity["sourceURI"]
        if source_uri is not None:
            source_node = get_or_create_node(raw_entity["sourceURI"], raw_entity)

        # Create the claim node
        claim_uri = make_subject_uri(raw_entity)

        claim_node = get_or_create_node(
            claim_uri,
            raw_entity,
            {
                "nodeUri": claim_uri,
                "name": raw_entity["claim"],
                "entType": "CLAIM",
                "descrip": make_description(raw_entity),
            },
        )
        # Create the edge from the subject node to the claim node
        get_or_create_edge(
            subject_node, claim_node, raw_entity["claim"], raw_entity["id"]
        )

        # create the edge from the claim node to the source node
        if source_node:
            get_or_create_edge(claim_node, source_node, "source", raw_entity["id"])
