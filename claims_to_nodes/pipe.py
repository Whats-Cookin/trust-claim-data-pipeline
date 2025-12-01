import re

from lib.cleaners import make_subject_uri, normalize_uri
from lib.db import (
    all_claims_generator,
    get_claim,
    get_claim_image,
    get_edge_by_endpoints,
    get_node_by_uri,
    insert_edge,
    insert_node,
    unprocessed_claims_generator,
    update_node_type,
)
from lib.infer import extract_fallback_name, infer_details


def get_or_create_node(node_uri, raw_claim, new_node=None):
    print("IN GET OR CREATE for " + node_uri)
    normalized_uri = normalize_uri(node_uri, raw_claim["issuerId"])
    if normalized_uri is None:
        print(f"ERROR: Failed to normalize URI '{node_uri}' - skipping node creation")
        return None
    node_uri = normalized_uri
    existing_node = get_node_by_uri(node_uri)

    # If node exists and we're trying to set it as CLAIM, ensure entType is correct
    if existing_node is not None:
        if new_node and new_node.get('entType') == 'CLAIM' and existing_node.get('entType') != 'CLAIM':
            print(f"Updating existing node {node_uri} from {existing_node.get('entType')} to CLAIM")
            update_node_type(existing_node['id'], 'CLAIM')
            existing_node['entType'] = 'CLAIM'
        return existing_node

    # Node doesn't exist, create it
    if new_node is None:
        name = extract_fallback_name(node_uri)
        # Infer entity type from URI patterns
        ent_type = infer_entity_type(node_uri)
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
                "entType": ent_type,
                "thumbnail": thumbnail_uri,
                "descrip": "",
            }
        except Exception as e:
            print(f"Error inferring details: {e}")
            # Create a minimal node to prevent future 404 errors
            node = {
                "nodeUri": node_uri,
                "name": name,
                "entType": ent_type,
                "thumbnail": "",
                "descrip": "",
            }
    else:
        node = new_node

        # For CLAIM nodes, try to get image from Image table
        if node.get('entType') == 'CLAIM':
            claim_id = raw_claim.get('id')
            if claim_id and not node.get('image'):
                image_url = get_claim_image(claim_id)
                if image_url:
                    node['image'] = image_url
                    print(f"Set image on CLAIM node from Image table: {image_url}")

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


def infer_entity_type(uri):
    """
    Infer entity type from URI patterns for subject/object/source nodes.
    CLAIM nodes are handled separately with explicit entType.
    """
    uri_lower = uri.lower()

    # LinkedIn personal profiles
    if 'linkedin.com/in/' in uri_lower:
        return 'PERSON'

    # LinkedIn company pages
    if 'linkedin.com/company/' in uri_lower:
        return 'ORGANIZATION'

    # Twitter/X profiles
    if 'twitter.com/' in uri_lower or 'x.com/' in uri_lower:
        # Exclude common non-profile paths
        if not any(path in uri_lower for path in ['/status/', '/search', '/explore', '/home', '/i/']):
            return 'PERSON'

    # Bluesky profiles
    if 'bsky.app/profile/' in uri_lower or 'bsky.social' in uri_lower:
        return 'PERSON'

    # GitHub profiles (single path segment = user profile)
    if 'github.com/' in uri_lower:
        path = uri_lower.split('github.com/')[-1].strip('/')
        segments = [s for s in path.split('/') if s]
        if len(segments) == 1:
            return 'PERSON'

    # Default to ORGANIZATION for other URIs (websites, domains, etc.)
    return 'ORGANIZATION'


def process_unprocessed():
    for raw_claim in unprocessed_claims_generator():
        process_claim(raw_claim)


def process_all():
    """Process ALL claims, not just new ones. Use for regenerating all nodes/edges."""
    for raw_claim in all_claims_generator():
        process_claim(raw_claim)


def process_targeted(claim_id):
    # get claim by id
    raw_claim = get_claim(claim_id)
    process_claim(raw_claim)


def process_claim(raw_claim):
    """
    NEW MODEL: All claims are nodes with subject/object/source edges.

    Structure:
      [Claim Node] --subject--> [Subject Node]
      [Claim Node] --object--> [Object Node] (if object exists)
      [Claim Node] --source--> [Source Node] (if source exists)

    No special cases - every claim becomes a node.
    """
    print(raw_claim)

    # Step 1: Create the claim node (ALWAYS)
    claim_uri = make_subject_uri(raw_claim)
    claim_node = get_or_create_node(
        claim_uri,
        raw_claim,
        {
            "nodeUri": claim_uri,
            "name": raw_claim["claim"],
            "entType": "CLAIM",
            "descrip": make_description(raw_claim),
            "claimId": raw_claim["id"],  # Link claim node to its source claim
        },
    )
    if claim_node is None:
        print(f"ERROR: Failed to create claim node for claim {raw_claim['id']} - skipping")
        return

    # Step 2: Create subject node and edge: claim --subject--> subject
    subject_uri = raw_claim["subject"]
    if not is_uri(subject_uri):
        print(f"Subject {subject_uri} is NOT a valid URI, skipping claim {raw_claim['id']}")
        return

    subject_node = get_or_create_node(subject_uri, raw_claim)
    if subject_node is None:
        print(f"ERROR: Failed to create subject node for claim {raw_claim['id']} - skipping")
        return

    get_or_create_edge(claim_node, subject_node, "subject", raw_claim["id"])

    # Step 3: Create object node and edge if object exists: claim --object--> object
    object_uri = raw_claim["object"]
    if object_uri:
        object_node = get_or_create_node(object_uri, raw_claim)
        if object_node is None:
            print(f"WARNING: Failed to create object node for claim {raw_claim['id']} - continuing without object")
        else:
            get_or_create_edge(claim_node, object_node, "object", raw_claim["id"])

    # Step 4: Create source node and edge if source exists: claim --source--> source
    source_uri = raw_claim["sourceURI"]
    if source_uri is not None:
        source_node = get_or_create_node(source_uri, raw_claim)
        if source_node is None:
            print(f"WARNING: Failed to create source node for claim {raw_claim['id']} - continuing without source")
        else:
            get_or_create_edge(claim_node, source_node, "source", raw_claim["id"])
