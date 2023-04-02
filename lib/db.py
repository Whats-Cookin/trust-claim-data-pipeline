import psycopg2

from ..lib.db_config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT

# Connect to the PostgreSQL database
def get_conn():
    global conn
    try:
        # check if conn is open
        conn.status
    except (AttributeError, psycopg2.OperationalError):
        # conn is closed or doesn't exist yet
        conn = psycopg2.connect(
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
    return conn

def unprocessed_claims_generator():
    with get_conn().cursor() as cur:
        # Read data from the Claim model
        cur.execute("SELECT id, subject, claim, object, statement, effectiveDate, sourceURI, howKnown, dateObserved, digestMultibase, author, curator, aspect, score, stars, amt, unit, howMeasured, intendedAudience, respondAt, confidence, issuerId, issuerIdType, claimAddress, proof FROM Claim WHERE edges IS NULL")

        while True:
            rows = cur.fetchmany()
            if not rows:
                break
            for row in rows:
                yield row


def execute_sql_query(query, params):
    with get_conn().cursor() as cur:
        cur.execute(query, params)
        result = cur.fetchone()
        conn.commit()
        return result

def insert_data(table, data):
    conn = get_conn()
    query = f"INSERT INTO {table} ({', '.join(data.keys())}) VALUES ({', '.join(['%s']*len(data))}) RETURNING id;"
    return execute_sql_query(conn, query, tuple(data.values()))[0]

def insert_node(node):
    """Insert a Node into the database."""
    return insert_data(table='Node', data=node)

def insert_edge(edge):
    """Insert an Edge into the database."""
    return insert_data(table='Edge', data=edge)

def get_node_by_uri(node_uri):
    """Retrieve a Node from the database by its nodeUri value."""
    select_node_sql = """
        SELECT id, nodeUri, name, entType, descrip, image, thumbnail
        FROM Node
        WHERE nodeUri = %s;
    """
    row = execute_sql_query(select_node_sql, (node_uri,))
    if row is None:
        return None
    node_dict = {
            'id': row['id'],
            'nodeUri': row['nodeUri'],
            'name': row['name'],
            'entType': row['entType'],
            'descrip': row['descrip'],
            'image': row['image'],
            'thumbnail': row['thumbnail']
        }
    return node_dict

def get_edge_by_endpoints(start_node_id, end_node_id, claim_id):
    """Retrieve an Edge from the database by the IDs of its start and end Nodes."""
    select_edge_sql = """
        SELECT id, startNodeId, endNodeId, label, thumbnail, claimId
        FROM Edge
        WHERE startNodeId = %s AND endNodeId = %s AND claimId = %s;
    """
    row = execute_sql_query(select_edge_sql, (start_node_id, end_node_id, claim_id))
    if row is None:
        return None

    edge_dict = {
            'id': row['id'],
            'startNodeId': row['startNodeId'],
            'endNodeId': row['endNodeId'],
            'label': row['label'],
            'thumbnail': row['thumbnail'],
            'claimId': row['claimId']
        }
    return edge_dict


