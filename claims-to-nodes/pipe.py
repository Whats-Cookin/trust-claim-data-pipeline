import psycopg2
from ..lib.db_config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
from ..lib.cleaners import normalize_uri
   

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

# Process the data and output the derived models
nodes = {}
edges = []

def add_or_create_node(node_uri, row):

    node_uri = normalize_uri(node_uri, row['issuerId'])
    node = nodes.get(subject_uri)
    if node is None:
        (name, thumbnail_uri) = infer_details(node_uri, save_thumbnail=True)
        entType = 'ORGANIZATION' # TODO infer or default to UNKNOWN for later edit
        node = {
            "nodeUri": node_uri,
            "name": name,
            "entType": entType,
            "thumbnail": thumbnail_uri,
            "descrip": ''
        }
        nodes[node_uri] = node
    return node 

for row in cur.fetchall():
    # Create or update the nodes dictionary
    subject_node = add_or_create_node(row['subject'], row)
    object_node = None

    if row['object'] is not None:
        object_node = add_or_create_node(row['object'], row) 
   
    if row['sourceURI'] is not None:
        source_node = add_or_create_node(row['sourceURI'], row)
 
    # Create the claim node
    claim_uri = row['claimAddress']
    claim_node = {
        "nodeUri": claim_uri,
        "name": row['claim'],
        "entType": "Claim",
        "descrip": row['statement']  # TODO use the other fields too
    }
    nodes[claim_uri] = claim_node
    
    # Create the edge from the subject node to the claim node
    subject_to_claim_edge = {
        "id": len(edges) + 1,
        "startNode": subject_node,
        "startNodeId": subject_node["id"],
        "endNode": claim_node,
        "endNodeId": claim_node["id"],
        "label": "claim"
    }
    edges.append(subject_to_claim_edge)
    
    # Create the edge from the claim node to the source node (if available)
    source_uri = row[6]
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
