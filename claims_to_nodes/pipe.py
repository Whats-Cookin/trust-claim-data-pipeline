from lib.cleaners import normalize_uri
from lib.db import unprocessed_claims_generator, get_node_by_uri, get_edge_by_endpoints, insert_node


def get_or_create_node(node_uri, raw_claim, new_node=None):

    node_uri = normalize_uri(node_uri, raw_claim['issuerId'])
    node = get_node_by_uri(node_uri)
    if node is None:
        if new_node is None:
            (name, thumbnail_uri) = infer_details(node_uri, save_thumbnail=True)
            entType = 'ORGANIZATION' # TODO infer or default to UNKNOWN for later edit
            node = {
                "nodeUri": node_uri,
                "name": name,
                "entType": entType,
                "thumbnail": thumbnail_uri,
                "descrip": ''
            }
        else:
            node = new_node
        node['id'] = insert_node(node)
    # TODO possibly update the node if exists
    return node 

def get_or_create_edge(start_node, end_node, label, claim_id):
    edge = get_edge_by_endpoints(start_node['id'], end_node['id'], claim_id)
    if edge is None:
        edge = {
           'startNodeId': start_node['id'],
           'endNodeId': end_node['id'],
           'label': label,
           'claimId': claim_id
        }
        edge['id'] = insert_edge(edge)
    # TODO check for consistency with existing edge
    return edge     
     
def process_unprocessed():
    for raw_claim in unprocessed_claims_generator():
        # Create or update the nodes dictionary
        subject_node = add_or_create_node(claim['subject'], raw_claim)
        object_node = None

        object_uri = raw_claim['object']
        if object_uri is not None:
            object_node = get_or_create_node(raw_claim['object'], raw_claim) 
      
        # if there is an object, the claim is just the relationship between the subject and object
        # likely something like "same_as" or "works_for"
        # currently we do not create a claim node for relationship claims
        if object_node:
           get_or_create_edge(subject_node, object_node, raw_claim['claim'], raw_claim['id'])
             
           # TODO maybe include the source node somehow with this edge; for now the claim itself is enough   
     
        # there is no object, so the point is to attach the claim to the subject
        # in this case we make a claim node and also attach the source
        else:
     
            source_uri = raw_claim['sourceURI'] 
            if source_uri is not None:
                source_node = get_or_create_node(raw_claim['sourceURI'], raw_claim)

            # Create the claim node
            claim_uri = row['claimAddress']
            claim_node = get_or_create_node(claim_uri, claim, {
                "nodeUri": claim_uri,
                "name": claim['claim'], 
                "entType": "Claim",
                "descrip": row['statement']  # TODO use the other fields too
            })
        
            # Create the edge from the subject node to the claim node
            get_or_create_edge(subject_node, claim_node, raw_claim['claim'], raw_claim['id'])
           
            # create the edge from the claim node to the source node
            get_or_create_edge(claim_node, source_node, 'source', raw_claim['id'])
