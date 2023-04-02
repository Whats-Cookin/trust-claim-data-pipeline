import psycopg2
from ..lib.db_config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
from ..lib.cleaners import normalize_uri
from ..lib.db import get_node_by_uri, get_edge_by_endpoints
   

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    database=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)

# Open a cursor to perform database operations
cur = conn.cursor()

# Read data from the Claim model
cur.execute("SELECT id, subject, claim, object, statement, effectiveDate, sourceURI, howKnown, dateObserved, digestMultibase, author, curator, aspect, score, stars, amt, unit, howMeasured, intendedAudience, respondAt, confidence, issuerId, issuerIdType, claimAddress, proof FROM Claim WHERE edges IS NULL")


def get_or_create_node(node_uri, row, new_node=None):

    node_uri = normalize_uri(node_uri, row['issuerId'])
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
        insert_node(node)
    # TODO possibly update the node if exists
    return node 

for row in cur.fetchall():
    # Create or update the nodes dictionary
    subject_node = add_or_create_node(row['subject'], row)
    object_node = None

    object_uri = row['object']
    if object_uri is not None:
        object_node = add_or_create_node(row['object'], row) 
  
    source_uri = row['sourceURI'] 
    if source_uri is not None:
        source_node = add_or_create_node(row['sourceURI'], row)
 
    # Create the claim node
    claim_uri = row['claimAddress']
    claim = row['claim']
    claim_node = add_or_create_node(claim_uri, row, {
        "nodeUri": claim_uri,
        "name": claim, 
        "entType": "Claim",
        "descrip": row['statement']  # TODO use the other fields too
    })
   
    
    # Create the edge from the subject node to the claim node
    subject_to_claim_edge = {
        "startNode": subject_node,
        "startNodeId": subject_node["id"],
        "endNode": claim_node,
        "endNodeId": claim_node["id"],
        "label": claim
    }
    edges.append(subject_to_claim_edge)
    
    # Create the edge from the claim node to the source node (if available)
    if source_uri is not None:
        source_node = nodes.get(source_uri)
        if source_node is None:
            source_node = {
                "id": len(nodes) + 1,
                "nodeUri": source_uri,
                "name": row[6],
                "entType": "Source",
                "descrip": row[7]
            }
            nodes[source_uri] = source_node
        claim_to_source_edge = {
            "id": len(edges) + 1,
            "startNode": claim_node,
            "startNodeId": claim_node["id"],
            "endNode": source_node,
            "endNodeId": source_node["id"],
            "label": "source"
        }
        edges.append(claim_to_source_edge)
